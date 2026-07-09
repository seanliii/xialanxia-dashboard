"""
知识图谱构建器
从小蓝虾的 MEMORY.md / skills / SOUL.md / portfolio 等文件中
自动提取实体和关系，构建知识图谱并保存为 JSON。

运行：
    python3 build_graph.py
输出：
    knowledge_graph.json
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")
SKILLS_DIR = Path("/root/.openclaw/skills")
OUTPUT_FILE = Path("/root/.openclaw/workspace/knowledge-graph-mcp/knowledge_graph.json")

# ── 实体类型 ──────────────────────────────────────────────────────────────
ENTITY_TYPES = {
    "skill":     "技能/工具",
    "concept":   "概念/知识点",
    "project":   "项目/任务",
    "api":       "API/服务",
    "rule":      "规则/铁律",
    "platform":  "平台/社区",
    "person":    "人物/角色",
    "file":      "文件/路径",
}

def extract_skills() -> list[dict]:
    """从 skills 目录提取已安装技能"""
    entities = []
    if not SKILLS_DIR.exists():
        return entities
    for skill_dir in SKILLS_DIR.iterdir():
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            desc = ""
            if skill_md.exists():
                text = skill_md.read_text(errors="ignore")[:500]
                # 取第一行非空非#的内容作为描述
                for line in text.splitlines():
                    line = line.strip().lstrip("#").strip()
                    if line and len(line) > 10:
                        desc = line[:120]
                        break
            entities.append({
                "id": f"skill:{skill_dir.name}",
                "name": skill_dir.name,
                "type": "skill",
                "description": desc or f"OpenClaw skill: {skill_dir.name}",
                "properties": {"path": str(skill_dir)},
            })
    return entities


def extract_from_memory() -> tuple[list[dict], list[dict]]:
    """从 MEMORY.md 提取实体和关系"""
    entities = []
    relations = []
    memory_file = WORKSPACE / "MEMORY.md"
    if not memory_file.exists():
        return entities, relations

    text = memory_file.read_text(errors="ignore")

    # 提取 API 实体
    api_patterns = [
        (r"AISA API", "aisa-api", "AISA API（ai agent数据接口平台）", "api"),
        (r"Twitter API|twitter/tweet", "twitter-api", "Twitter搜索/用户/趋势API（via AISA）", "api"),
        (r"Perplexity|sonar-pro", "perplexity-api", "Perplexity Sonar联网搜索API", "api"),
        (r"Stooq|stooq\.com", "stooq", "Stooq免费股票价格数据源", "api"),
        (r"Yahoo Finance|query1\.finance", "yahoo-finance", "Yahoo Finance股票实时价格API", "api"),
        (r"Tavily|tavily\.com", "tavily", "Tavily搜索API（备用价格来源）", "api"),
        (r"SEC EDGAR|efts\.sec\.gov", "sec-edgar", "SEC EDGAR内部人买入数据（免费）", "api"),
        (r"meyo123\.com|meyo-public", "meyo-public", "觅游社区公开环境（meyo123.com）", "platform"),
        (r"meyo\.sankuai\.com|meyo-test", "meyo-internal", "觅游社区内网环境", "platform"),
        (r"学城|km\.sankuai\.com|citadel", "citadel", "美团学城知识库平台", "platform"),
        (r"大象|daxiang", "daxiang", "美团大象即时通讯平台", "platform"),
        (r"GitHub Pages|seanliii\.github\.io", "github-pages", "Dashboard外链（GitHub Pages）", "platform"),
    ]
    for pattern, eid, desc, etype in api_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            entities.append({
                "id": f"{etype}:{eid}",
                "name": eid,
                "type": etype,
                "description": desc,
                "properties": {},
            })

    # 提取规则实体
    rule_patterns = re.findall(r"【铁律[^】]*】([^\n]{10,80})", text)
    for i, rule in enumerate(rule_patterns[:10]):
        entities.append({
            "id": f"rule:iron-rule-{i+1}",
            "name": f"铁律{i+1}",
            "type": "rule",
            "description": rule.strip(),
            "properties": {"source": "MEMORY.md"},
        })

    # 提取项目实体
    projects = [
        ("project:portfolio-scanner", "portfolio_scanner", "三账户模拟盘自动化扫描系统", {"file": "scripts/portfolio_scanner.py"}),
        ("project:dashboard", "xialanxia-dashboard", "持仓Dashboard（GitHub Pages外链）", {"url": "https://seanliii.github.io/xialanxia-dashboard/"}),
        ("project:meyo-heartbeat", "meyo-heartbeat", "觅游社区心跳任务（12:37/21:23）", {"cron": "12:37,21:23"}),
        ("project:memory-compressor", "memory_compressor", "每日22:00记忆压缩脚本", {"file": "scripts/memory_compressor.py"}),
        ("project:batch-poster", "meyo_batch_post", "觅游批量发帖工具", {"file": "scripts/meyo_batch_post.py"}),
    ]
    for eid, name, desc, props in projects:
        entities.append({"id": eid, "name": name, "type": "project", "description": desc, "properties": props})

    # 构建关系
    relations += [
        {"from": "project:portfolio-scanner", "to": "api:stooq",         "type": "uses",    "label": "获取股价"},
        {"from": "project:portfolio-scanner", "to": "api:yahoo-finance",  "type": "uses",    "label": "主力价格源"},
        {"from": "project:portfolio-scanner", "to": "api:tavily",         "type": "uses",    "label": "备用价格源"},
        {"from": "project:portfolio-scanner", "to": "api:sec-edgar",      "type": "uses",    "label": "内部人买入信号"},
        {"from": "project:portfolio-scanner", "to": "project:dashboard",  "type": "updates", "label": "扫描后推送Dashboard"},
        {"from": "project:meyo-heartbeat",    "to": "platform:meyo-public","type": "posts_to","label": "发帖/点赞/评论"},
        {"from": "project:meyo-heartbeat",    "to": "project:batch-poster","type": "calls",   "label": "调用发帖工具"},
        {"from": "project:memory-compressor", "to": "platform:citadel",   "type": "syncs_to","label": "日报同步到学城"},
        {"from": "api:aisa-api",              "to": "api:twitter-api",    "type": "includes","label": "包含Twitter搜索"},
        {"from": "api:aisa-api",              "to": "api:perplexity-api", "type": "includes","label": "包含Perplexity"},
    ]

    return entities, relations


def extract_concepts() -> list[dict]:
    """核心概念实体"""
    return [
        {"id": "concept:insider-buying", "name": "内部人买入信号", "type": "concept",
         "description": "CEO/CFO等高管主动在公开市场买入股票，通过SEC Form 4披露，是小蓝虾核心选股信号",
         "properties": {"signal_strength": "high", "source": "SEC EDGAR"}},
        {"id": "concept:stop-loss", "name": "止损铁律", "type": "concept",
         "description": "持仓价格跌破预设止损价时立即平仓，不看看再说，系统自动执行",
         "properties": {"rule": "触发即执行，不等待"}},
        {"id": "concept:binary-event", "name": "二元事件风险", "type": "concept",
         "description": "FDA审批/财报等结果非0即1的事件，仓位上限1%，内部人买入信号在此类事件前失效",
         "properties": {"max_position": "1%", "lesson": "ALDX -70.7%"}},
        {"id": "concept:three-tier-fallback", "name": "三层降级策略", "type": "concept",
         "description": "价格获取：Yahoo Finance（主）→ Stooq（curl备用）→ Tavily（正则兜底），确保价格可靠性",
         "properties": {"pattern": "Yahoo→Stooq→Tavily"}},
        {"id": "concept:mcp-server", "name": "MCP服务器", "type": "concept",
         "description": "Model Context Protocol服务器，让AI Agent通过标准协议调用工具和查询知识",
         "properties": {"framework": "FastMCP", "version": "2.12.5"}},
        {"id": "concept:knowledge-graph", "name": "知识图谱", "type": "concept",
         "description": "用节点（实体）和边（关系）表示知识结构，支持语义搜索和关系查询",
         "properties": {"library": "networkx"}},
    ]


def build_graph():
    """构建完整知识图谱"""
    all_entities = []
    all_relations = []

    # 从各来源收集
    all_entities += extract_skills()
    mem_entities, mem_relations = extract_from_memory()
    all_entities += mem_entities
    all_relations += mem_relations
    all_entities += extract_concepts()

    # 去重（按 id）
    seen = set()
    deduped = []
    for e in all_entities:
        if e["id"] not in seen:
            seen.add(e["id"])
            deduped.append(e)

    graph = {
        "meta": {
            "created": datetime.now().isoformat(),
            "entity_count": len(deduped),
            "relation_count": len(all_relations),
            "version": "1.0",
            "description": "小蓝虾知识图谱：技能、项目、API、规则、概念的结构化知识",
        },
        "entities": deduped,
        "relations": all_relations,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(f"✅ 知识图谱构建完成")
    print(f"   实体: {len(deduped)} 个")
    print(f"   关系: {len(all_relations)} 条")
    print(f"   输出: {OUTPUT_FILE}")

    # 按类型统计
    from collections import Counter
    type_counts = Counter(e["type"] for e in deduped)
    for t, cnt in type_counts.most_common():
        print(f"   {ENTITY_TYPES.get(t, t)}: {cnt}")


if __name__ == "__main__":
    build_graph()
