# 🔍 搜索词自动扩词系统

自动发现、测试、评估新的搜索关键词，减少人工搜索优化工作量。

## 功能

- **候选词生成**：基于当前词库自动推导新词（年月更新、热点组合、语义变体）
- **自动搜索测试**：多引擎并行测试候选词命中率
- **智能评分**：根据成功率+URL数+相关性过滤给出建议
- **一键应用**：将高价值词自动加入 search-keywords.json

## 用法

```bash
# 基本运行（测试10个候选词）
python3 expander.py

# 测试更多候选词
python3 expander.py --test-count 20

# 指定引擎
python3 expander.py --engines bocha-search,quark-search

# 测试后自动将强建议词加入词库 tier3
python3 expander.py --apply
```

## 候选词生成策略

1. **年月更新**：将旧年月词替换为当前年月
2. **热点组合**：热点产品 × 场景词 × 当前年月
3. **语义变体**：同义词替换（AI Agent → AI智能体）

## 评分规则

| 成功率 | URL数 | 建议 |
|--------|-------|------|
| ≥2引擎 | ≥5 | strong_add_tier2 |
| ≥2引擎 | ≥3 | add_tier3 |
| ≥1引擎 | ≥2 | weak_signal |
| 其他 | - | skip |

## 输出

- 终端：彩色摘要报告
- 文件：`data/keyword-expansion-report.json`（详细结果）
