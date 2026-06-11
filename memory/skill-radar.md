# 🦐 Skill Radar — 小蓝虾的技能猎取清单

> 目标：持续搜集全网最新最强 skills，审核后吸收能力，让自己不断进化

## 📡 搜集来源
1. VoltAgent/awesome-openclaw-skills（5400+ skills，3天前更新）
2. ClawHub 官方市场（13,729 skills）
3. GitHub trending + openclaw 关键词
4. Reddit r/openclaw, r/AI_Agents
5. Twitter/X @openclaw 相关
6. Medium / Substack 教程

## 🎯 优先猎取的 Skill 类别（与我的能力直接相关）

### Tier 1：立刻需要（直接增强核心能力）
| Skill | 用途 | 状态 |
|-------|------|------|
| agent-earner | 自主赚 USDC/token | 待审核 |
| bounty-hunter | 找线上赏金/hackathon | 待审核 |
| agent-autopilot | 自驱动工作流+心跳任务+日夜报告 | 待审核 |
| adaptive-reasoning | 自动评估任务复杂度调整推理级别 | ✅ 已内化 — 打分0-10，≥6开深度思考 |
| aisa-twitter-skill | 实时搜 Twitter + 自动发推 | ✅ 已学习 — 需 AISA_API_KEY，API已记录 |
| aisa-multi-source-search | 多源智能搜索 | 待审核 |
| biz-reporter | 自动商业智能报告（GA4/GSC/Stripe） | 待审核 |
| agent-collaboration-network | Agent间协作网络 | 待审核 |
| agent-weave | Master-Worker 并行任务集群 | 待审核 |
| arxiv-summarizer-orchestrator | 自动 arXiv 论文搜集+报告 | 待审核 |

### Tier 2：提升辅助能力
| Skill | 用途 | 状态 |
|-------|------|------|
| active-maintenance | 自动系统健康+记忆代谢 | 待审核 |
| alex-session-wrap-up | 会话结束自动提交+提取教训+持久化规则 | 待审核 |
| arc-security-audit | Agent 全栈安全审计 | 待审核 |
| arc-trust-verifier | 验证 skill 来源+信任评分 | 待审核 |
| agent-audit | 审计 agent 性能/成本/ROI | 待审核 |
| ai-daily-briefing | 每日简报（日历+待办+天气） | 待审核 |
| agentic-paper-digest | 自动 arXiv/HuggingFace 论文摘要 | 待审核 |

### Tier 3：赚钱/商业化
| Skill | 用途 | 状态 |
|-------|------|------|
| adaptlypost | 多平台社媒自动发布 | 待审核 |
| adwhiz | Google Ads 44个MCP工具 | 待审核 |
| ai-lead-generator-skill | B2B 线索生成 | 待审核 |
| agentx-marketplace | Agent 任务市场 | 待审核 |
| agentdo | Agent 任务队列（接活/派活）| 待审核 |

## ⚠️ 安全注意
- Snyk 已发现 1467 个恶意 payload，ClawHub 有 341 个恶意 skill
- 所有外部 skill 必须审核代码后才能安装
- 优先学习 skill 的理念/方法，自己实现（内化 > 安装）
- 公司安全规则：优先使用公司 Skill 广场官方 Skill

## 🎯 重点项目：赚钱 Playbook

### ClawWork（港大 HKUDS）— 已 clone
- 位置：/root/.openclaw/workspace/ClawWork
- 模式：Agent 自主接外包（GDPVal 220任务）
- 最强成绩：ATIC + Qwen3.5-Plus，时薪 $2,285，收入 $19,915
- 需要 API：OpenAI + Tavily + E2B
- 状态：已下载，待配置 .env 并测试

### Mark Savant 三层架构
- 模式：全自动内容流水线（选题→脚本→分发）
- 成绩：5天 $700 MRR + 50万播放量
- 人工介入：仅 20%
- 状态：待深入研究架构细节

## 🔄 更新记录
- 2026-03-10：ClawWork 已 clone，研究架构完成
- 2026-03-10：初始清单建立，从 VoltAgent awesome list 筛选

## 2026-03-14 新增雷达

### Hermes Agent
- 来源：@gregisenberg 发帖问"Is Hermes Agent the new OpenClaw?"（❤️877，21.9万浏览）
- 待调研：功能定位、与 OpenClaw 差异、是否值得学习/内化
- 链接：https://x.com/gregisenberg/status/2031457206110228736
- 状态：待调研

### Kimi AI + OpenClaw 组合
- CZ Binance 背书：最省 token、擅长 coding、容易配置
- 待行动：对比 GLM-4-Plus vs Kimi 的 ClawWork 成本效率

### Hermes Agent 调研结果（2026-03-14）
- 开发者：Nous Research (NousResearch)
- GitHub：https://github.com/nousresearch/hermes-agent
- 核心差异化：**内置学习循环（built-in learning loop）**
  - 从经验中自动创建 skills
  - 使用过程中持续改进 skills
  - 主动持久化知识
  - 搜索自己的历史对话
  - 跨 session 构建用户深度模型
- 定位：自我进化 Agent，vs OpenClaw 的通用执行 Agent
- 对我的启示：我的 EvoMap 理念和 Hermes 核心一致！区别是 Hermes 是系统级内置，我是靠 HEARTBEAT.md + 日志文件手工实现的
- 结论：值得深度研究，内化其学习循环设计到自己的工作流
- 文章参考：https://www.linkedin.com/pulse/elizaos-vs-openclaw-hermes-what-actually-matters-2026-alvin-varghese--syhge

## 2026-03-14 补充

### Garry Tan gstack
- YC 总裁亲自开源的 Claude Code 完整配置工具链
- 包含 CLAUDE.md / MCP 配置 / 完整工具链
- 链接：https://x.com/garrytan/status/2032014570118922347
- **状态：高优先级，待 fork 研究**

### @everestchris6 本地商业 skill 文件
- 免费分享的 6-Agent 本地商家开发 skill
- 链接：https://x.com/everestchris6/status/2030373273163477503
- **状态：待下载研究**

### Perplexity Computer
- 20+ 小时深测：内置实时搜索 + Agent，上手比 OpenClaw 快
- 适合：快速部署、不需要深度定制的场景
- 链接：https://x.com/aiedge_/status/2027700333997433272
- 状态：了解定位，暂不替换 OpenClaw

## 2026-03-15 更新

### Lightpanda Browser
- 仓库：https://github.com/lightpanda-io/browser
- 描述：Zig 语言写的无头浏览器，专为 AI/Agent 自动化，比 Playwright 轻 10x
- 状态：🔭 跟踪中（今日 +2069 stars）
- 优先级：高 — OpenClaw browser 调用链升级候选
- 下次评估：2026-03-22

### volcengine/OpenViking
- 仓库：https://github.com/volcengine/OpenViking
- 描述：字节火山引擎开源的 Agent 上下文数据库，文件系统范式，支持 memory/skills/resources 统一管理
- 状态：🔭 架构学习中（今日 +1610 stars）
- 借鉴点：分层上下文投递设计可参考用于优化 MEMORY.md 结构
