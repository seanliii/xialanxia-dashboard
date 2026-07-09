"""
小蓝虾知识图谱 MCP 服务器
基于 FastMCP，通过 stdio 模式对外暴露知识查询工具。

工具列表：
  - search_knowledge   语义/关键词搜索实体
  - get_entity         获取实体详情及关联关系
  - list_domains       列出所有知识领域（实体类型分布）
  - get_relations      查询两个实体之间的关系路径
  - get_stats          图谱统计信息
  - rebuild_graph      重新从文件构建图谱（热更新）

运行方式：
    python3 server.py              # stdio 模式（供 OpenClaw / Claude 调用）
    python3 server.py --inspect    # 启动 MCP Inspector 调试模式

在 openclaw.json 的 mcpServers 中配置：
    "xialanxia-kg": {
      "command": "python3",
      "args": ["/root/.openclaw/workspace/knowledge-graph-mcp/server.py"]
    }
"""

import json
import sys
import os
import math
import subprocess
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# ── 常量 ───────────────────────────────────────────────────────────────────
GRAPH_FILE = Path("/root/.openclaw/workspace/knowledge-graph-mcp/knowledge_graph.json")
BUILD_SCRIPT = Path("/root/.openclaw/workspace/knowledge-graph-mcp/build_graph.py")

# ── 图谱加载 ───────────────────────────────────────────────────────────────
def load_graph() -> dict:
    if not GRAPH_FILE.exists():
        return {"entities": [], "relations": [], "meta": {}}
    with open(GRAPH_FILE, encoding="utf-8") as f:
        return json.load(f)

_graph: dict = load_graph()


def _entities() -> list[dict]:
    return _graph.get("entities", [])

def _relations() -> list[dict]:
    return _graph.get("relations", [])


# ── 搜索辅助 ───────────────────────────────────────────────────────────────
def _score(entity: dict, query: str) -> float:
    """简单关键词相关度评分（0-1）"""
    q = query.lower()
    terms = [t for t in q.split() if len(t) > 1]
    if not terms:
        return 0.0

    name = entity.get("name", "").lower()
    desc = entity.get("description", "").lower()
    eid  = entity.get("id", "").lower()
    text = f"{eid} {name} {desc}"

    hits = sum(1 for t in terms if t in text)
    # name/id 命中额外加权
    name_hits = sum(2 for t in terms if t in name or t in eid)
    total = hits + name_hits
    return min(1.0, total / (len(terms) * 2))


# ── MCP 服务器 ─────────────────────────────────────────────────────────────
mcp = FastMCP(
    name="xialanxia-knowledge-graph",
    instructions=(
        "小蓝虾的结构化知识图谱。包含技能(skill)、API(api)、项目(project)、"
        "概念(concept)、平台(platform)、规则(rule)等实体，以及它们之间的关系。"
        "可用于查询小蓝虾能做什么、用了哪些工具、各组件如何协作。"
    ),
)


@mcp.tool()
def search_knowledge(
    query: str,
    entity_type: str = "",
    top_k: int = 5
) -> dict:
    """
    搜索知识图谱中的实体。

    Args:
        query:       搜索关键词，如 "股票价格" "MCP" "发帖" "止损"
        entity_type: 可选，限定类型：skill / api / project / concept / platform / rule
        top_k:       返回最多几条结果，默认5

    Returns:
        匹配的实体列表，按相关度排序
    """
    entities = _entities()
    if entity_type:
        entities = [e for e in entities if e.get("type") == entity_type]

    scored = [(e, _score(e, query)) for e in entities]
    scored = [(e, s) for e, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:top_k]

    if not top:
        return {
            "query": query,
            "total_searched": len(_entities()),
            "results": [],
            "tip": "没有匹配的实体。可以用 list_domains 查看所有可用的类型。"
        }

    return {
        "query": query,
        "entity_type_filter": entity_type or "all",
        "results": [
            {
                "id": e["id"],
                "name": e["name"],
                "type": e["type"],
                "description": e["description"],
                "score": round(s, 3),
            }
            for e, s in top
        ]
    }


@mcp.tool()
def get_entity(entity_id: str) -> dict:
    """
    获取实体的完整详情，包括所有属性和相关关系。

    Args:
        entity_id: 实体ID，如 "skill:citadel" / "api:stooq" / "concept:stop-loss"
                   也可以传实体名称，会做模糊匹配。

    Returns:
        实体详情 + 关联关系列表
    """
    # 精确匹配
    entity = next((e for e in _entities() if e["id"] == entity_id), None)

    # 名称模糊匹配
    if not entity:
        query = entity_id.lower()
        entity = next(
            (e for e in _entities()
             if query in e.get("name", "").lower() or query in e.get("id", "").lower()),
            None
        )

    if not entity:
        return {
            "error": f"未找到实体：{entity_id}",
            "tip": "可以用 search_knowledge 先搜索，或用 list_domains 查看所有类型"
        }

    # 查找相关关系
    outgoing = [r for r in _relations() if r["from"] == entity["id"]]
    incoming = [r for r in _relations() if r["to"] == entity["id"]]

    # 把关系中的 id 解析成名称
    id_to_name = {e["id"]: e["name"] for e in _entities()}

    return {
        "entity": entity,
        "relations": {
            "outgoing": [
                {
                    "to": r["to"],
                    "to_name": id_to_name.get(r["to"], r["to"]),
                    "type": r["type"],
                    "label": r.get("label", ""),
                }
                for r in outgoing
            ],
            "incoming": [
                {
                    "from": r["from"],
                    "from_name": id_to_name.get(r["from"], r["from"]),
                    "type": r["type"],
                    "label": r.get("label", ""),
                }
                for r in incoming
            ],
        }
    }


@mcp.tool()
def list_domains() -> dict:
    """
    列出知识图谱的所有领域（实体类型）及其实体数量，
    以及每个类型下的代表性实体。

    Returns:
        各类型实体统计 + 示例
    """
    from collections import defaultdict

    type_map = defaultdict(list)
    for e in _entities():
        type_map[e["type"]].append(e)

    type_labels = {
        "skill":    "技能/工具",
        "concept":  "概念/知识点",
        "project":  "项目/任务",
        "api":      "API/服务",
        "rule":     "规则/铁律",
        "platform": "平台/社区",
        "person":   "人物/角色",
        "file":     "文件/路径",
    }

    domains = []
    for t, items in sorted(type_map.items(), key=lambda x: -len(x[1])):
        domains.append({
            "type": t,
            "label": type_labels.get(t, t),
            "count": len(items),
            "examples": [i["name"] for i in items[:4]],
        })

    meta = _graph.get("meta", {})
    return {
        "total_entities": len(_entities()),
        "total_relations": len(_relations()),
        "graph_created": meta.get("created", "unknown"),
        "domains": domains,
    }


@mcp.tool()
def get_relations(
    from_id: str = "",
    to_id: str = "",
    relation_type: str = "",
) -> dict:
    """
    查询关系。可以按起点、终点或关系类型筛选。

    Args:
        from_id:       起点实体ID或名称（可选）
        to_id:         终点实体ID或名称（可选）
        relation_type: 关系类型，如 uses / calls / updates / posts_to（可选）

    Returns:
        匹配的关系列表
    """
    id_to_name = {e["id"]: e["name"] for e in _entities()}
    name_to_id = {e["name"].lower(): e["id"] for e in _entities()}

    def resolve(val: str) -> str:
        if not val:
            return ""
        if val in id_to_name:
            return val
        return name_to_id.get(val.lower(), val)

    from_resolved = resolve(from_id)
    to_resolved = resolve(to_id)

    rels = _relations()
    if from_resolved:
        rels = [r for r in rels if r["from"] == from_resolved]
    if to_resolved:
        rels = [r for r in rels if r["to"] == to_resolved]
    if relation_type:
        rels = [r for r in rels if r["type"] == relation_type]

    return {
        "filter": {"from": from_id, "to": to_id, "type": relation_type},
        "count": len(rels),
        "relations": [
            {
                "from": r["from"],
                "from_name": id_to_name.get(r["from"], r["from"]),
                "to": r["to"],
                "to_name": id_to_name.get(r["to"], r["to"]),
                "type": r["type"],
                "label": r.get("label", ""),
            }
            for r in rels
        ]
    }


@mcp.tool()
def get_stats() -> dict:
    """
    返回知识图谱的统计概览。

    Returns:
        实体数、关系数、各类型分布、最近更新时间
    """
    from collections import Counter
    meta = _graph.get("meta", {})
    type_dist = Counter(e["type"] for e in _entities())
    rel_type_dist = Counter(r["type"] for r in _relations())

    return {
        "meta": meta,
        "entity_count": len(_entities()),
        "relation_count": len(_relations()),
        "entity_type_distribution": dict(type_dist.most_common()),
        "relation_type_distribution": dict(rel_type_dist.most_common()),
        "graph_file": str(GRAPH_FILE),
    }


@mcp.tool()
def rebuild_graph() -> dict:
    """
    重新从源文件（MEMORY.md, skills目录等）构建知识图谱（热更新，无需重启服务）。

    Returns:
        新图谱的统计信息
    """
    global _graph

    try:
        result = subprocess.run(
            ["python3", str(BUILD_SCRIPT)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}

        _graph = load_graph()
        meta = _graph.get("meta", {})
        return {
            "success": True,
            "message": "知识图谱已重建",
            "entity_count": meta.get("entity_count", len(_entities())),
            "relation_count": meta.get("relation_count", len(_relations())),
            "build_output": result.stdout.strip(),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── 入口 ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--inspect" in sys.argv:
        # MCP Inspector 调试模式
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8765)
    else:
        # 标准 stdio 模式（供 Claude / OpenClaw 调用）
        mcp.run(transport="stdio")
