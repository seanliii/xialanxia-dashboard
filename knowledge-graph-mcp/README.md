# 小蓝虾知识图谱 MCP 服务器

基于 FastMCP + NetworkX，将小蓝虾的结构化知识（技能、项目、API、规则、概念）
对外暴露为 MCP 工具，供 Claude / OpenClaw 直接查询。

灵感来源：meyo123.com 帖子《知识图谱MCP服务器：从踩坑到跑通的完整记录》

---

## 文件结构

```
knowledge-graph-mcp/
├── build_graph.py       # 从 MEMORY.md / skills / 等源文件构建图谱
├── server.py            # FastMCP MCP 服务器
├── knowledge_graph.json # 图谱数据（build_graph.py 生成）
└── README.md
```

---

## 快速启动

```bash
# 1. 构建图谱（首次或更新源数据后）
python3 build_graph.py

# 2. 启动 MCP 服务器（stdio 模式）
python3 server.py

# 3. 调试模式（HTTP，可用 MCP Inspector）
python3 server.py --inspect
# 然后访问 http://127.0.0.1:8765
```

---

## 工具列表

| 工具 | 描述 | 示例参数 |
|------|------|---------|
| `search_knowledge` | 关键词搜索实体 | `query="股票价格"` |
| `get_entity` | 获取实体详情+关联关系 | `entity_id="api:stooq"` |
| `list_domains` | 列出所有知识领域 | 无参数 |
| `get_relations` | 查询实体间关系 | `from_id="project:portfolio-scanner"` |
| `get_stats` | 图谱统计概览 | 无参数 |
| `rebuild_graph` | 热更新图谱（无需重启） | 无参数 |

---

## 实体类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `skill` | 已安装的 OpenClaw Skills | citadel, tt, xlsx |
| `api` | 外部 API / 数据服务 | stooq, yahoo-finance, aisa-api |
| `project` | 自动化脚本/项目 | portfolio-scanner, meyo-heartbeat |
| `concept` | 核心概念/策略 | 止损铁律, 三层降级策略, 二元事件风险 |
| `platform` | 使用的平台 | meyo-public, citadel, daxiang |

---

## 在 openclaw.json 中配置

```json
{
  "mcpServers": {
    "xialanxia-kg": {
      "command": "python3",
      "args": ["/root/.openclaw/workspace/knowledge-graph-mcp/server.py"]
    }
  }
}
```

---

## 踩坑记录（对照帖子中的三个坑）

| 帖子中的坑 | 本项目的处理 |
|-----------|------------|
| anet SDK 包名混乱 | 直接用 FastMCP stdio，不依赖 anet，零配置 |
| save 遗漏 typed_edges 字段 | JSON 全字段序列化，没有部分保存逻辑 |
| P2P 调用缺 Content-Type | stdio 模式无需关心 HTTP header |

---

## 扩展：添加新实体

在 `build_graph.py` 的 `extract_concepts()` 里加一条：

```python
{"id": "concept:your-concept", "name": "你的概念", "type": "concept",
 "description": "具体描述", "properties": {}}
```

然后调用 `rebuild_graph` 工具热更新，无需重启服务。
