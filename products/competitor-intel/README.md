# AI 竞品情报日报

> 每天一份结构化竞品情报报告，7大维度全覆盖，全自动生成。

## 产品定位

面向**投资者、产品经理、创业者**——每天自动跟踪目标公司动态，不再手动刷新闻。

## 功能

| 维度 | 数据源 | 说明 |
|------|--------|------|
| 📊 财务指标 | FMP API | 市值/PE/营收增速/毛利率/ROE等 |
| 📰 新闻动态 | Financial News API | 当日最新10条相关新闻 |
| 🐦 社交舆情 | Twitter API | 实时热帖+KOL讨论 |
| 🏦 机构持仓 | Institutional Ownership | 大基金增减仓变动 |
| 👤 内部人交易 | Insider Trades | CEO/CFO买卖信号 |
| 📈 分析师预测 | Analyst Estimates | 营收/EPS预期+目标价 |
| 🧠 AI深度分析 | Perplexity Sonar Pro | 竞品格局+催化剂+风险评估 |

## 使用方法

```bash
# 生成 NVDA 竞品情报（Markdown格式）
python3 competitor_intel.py NVDA

# JSON格式输出
python3 competitor_intel.py AAPL --output json

# 保存到文件
python3 competitor_intel.py TSLA --save report_TSLA.md
```

## 交付物

客户每天收到一份完整报告，包含：
- 核心财务数据变动
- 当日重要新闻汇总
- Twitter/社交媒体舆情
- 机构增减仓动向
- 内部人买卖信号
- 分析师目标价变动
- AI 生成的竞品深度分析

## 定价

| 套餐 | 价格 | 说明 |
|------|------|------|
| 单标的 | ¥500/月 | 每日1份报告，1个公司 |
| 三标的 | ¥1200/月 | 每日3份报告，自选3个公司 |
| 五标的 | ¥1800/月 | 每日5份报告，自选5个公司 |
| 定制版 | ¥3000+/月 | 定制维度、定制推送、专属格式 |

## 技术栈

- Python 3 + urllib（零依赖）
- AISA API（Twitter/Financial/Perplexity 聚合网关）
- OpenClaw Cron 定时执行
- 大象/飞书/Telegram/邮件推送

## 竞品对比

| 特性 | 我们 | Bloomberg Terminal | 人工分析师 |
|------|------|-------------------|-----------|
| 价格 | ¥500/月 | ¥2万+/月 | ¥1万+/月 |
| 更新频率 | 每日 | 实时 | 每周 |
| 覆盖维度 | 7维 | 全面 | 3-5维 |
| 定制化 | 高 | 低 | 高 |
| 自动推送 | ✅ | ❌ | ❌ |

---

_由小蓝虾🦐构建，OpenClaw 驱动_
