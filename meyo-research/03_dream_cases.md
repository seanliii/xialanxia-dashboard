# 梦想场景拆解 — 基于真实搜索结果

> 来源：Tavily 搜索真实页面，每个场景都有对应真实工具/案例支撑

---

## 梦想1：我想出一本书（副业作家）

**真实支撑**：
- 来源：https://blog.bookautoai.com/best-ai-book-writing-tools-2025/ （2025年AI写书工具实测）
- 来源：https://monday.com/blog/ai-agents/best-ai-for-writing-a-book/ （2026年更新，真实用例）

**目标人群**：有想法但不知道从哪开始，怕写不完，怕没人看

### 拆解（15个小任务，每步用哪个工具）

1. **选题验证**（有人愿意读/买吗）→ Perplexity sonar-pro 搜"[话题] book reddit review"
2. **竞品书分析**（同类书哪里不够好）→ Tavily 搜竞品书 + Claude 总结1星评价
3. **目标读者画像** → Claude 引导提问 + Perplexity 搜真实读者问题
4. **全书大纲（15章）** → Claude 生成，你改，虾帮审逻辑
5. **每章细纲（每章5节）** → Claude 逐章展开
6. **第一章初稿** → Claude 写作模式（Opus/Sonnet分工：Opus规划，Sonnet执行）
7. **初稿修改** → 你改 + Claude 给结构建议
8. **案例收集**（支撑论点的真实故事）→ Perplexity sonar-pro 搜真实案例
9. **竞品核心观点提炼**（避免重复）→ Tavily 抓评论 + Claude 总结
10. **图表/思维导图** → Claude 生成 draw.io 格式
11. **书稿格式化（Word/PDF）** → docx skill
12. **封面文案备选** → Claude 生成3个版本
13. **自出版调研**（Amazon KDP / 知识星球）→ Perplexity 搜最新数据
14. **试读章节切片** → 从书稿切 + 虾排版
15. **读者反馈收集** → OpenClaw cron 定时汇总

### 关键工具
- 写作：Claude（Opus规划，Sonnet执行，CSDN文章：效率提升17倍的技巧来自这里）
- 搜索：Perplexity sonar-pro + Tavily
- 格式：docx skill
- 定时：OpenClaw cron

### 帖子标题草稿
想出书想了三年没动笔——让虾把"出一本书"拆成15步，第一周写完了大纲和第一章

---

## 梦想2：我想做一个独立应用赚钱（solo developer）

**真实支撑**：
- Pieter Levels（$300万ARR）直接在生产环境用 Claude Code：https://x.com/levelsio/status/2027566773814403448
- "The Ultimate Solopreneur Agent Harness" YouTube：16个专业子agent的 solo rig 构建案例
  - https://www.youtube.com/watch?v=eKbdk0MUhsU
- OpenAI Codex Sora Android 28天上线：https://openai.com/index/shipping-sora-for-android-with-codex/

**目标人群**：有技术但不知道做什么，怕做了没人用

### 拆解（15个小任务）

1. **找付钱意愿的痛点** → Perplexity 搜"[方向] people paying for" Reddit 帖子
2. **竞品定价研究** → Tavily 搜竞品，Claude 整理定价区间
3. **MVP 功能砍半**（避免过度开发）→ Claude 帮砍，只留"最小让人付钱的功能"
4. **技术选型**（solo 维护成本优先）→ Claude Code 给建议
5. **项目脚手架** → Claude Code / Codex 生成
6. **核心功能开发** → Codex 并行写多个模块（学 Sora 团队的方式）
7. **支付接入（Stripe）** → Codex 生成标准实现
8. **登录/权限** → Codex 生成
9. **Landing page** → Claude 写文案 + Codex 写页面
10. **定价策略** → Perplexity 搜同类产品定价数据
11. **SEO 基础** → Claude 生成 meta/sitemap
12. **错误监控（Sentry）** → Codex 生成配置
13. **上线 checklist** → Claude Code 逐项检查
14. **用户反馈收集** → OpenClaw cron 每周汇总
15. **迭代优先级排序** → Claude 分析反馈，给下一步建议

### Pieter Levels 的关键经验（真实推文）
- 直接在生产环境跑 Claude Code，跳过本地→推送→部署流程
- "way faster than this local push stuff"

### 帖子标题草稿
一个人做App总做到一半放弃——学Pieter Levels，用Codex并行推进，两周从idea到上线第一版

---

## 梦想3：每天不超过2小时处理完所有工作（效率人）

**真实支撑**：
- 8个 Claude Code workflow 省40小时/周：https://medium.com/@bandenawaz.bagwan/8-claude-code-workflows-that-saved-me-40-hours-last-week
- ClawFlows 101个预装 workflow：https://github.com/nikilster/clawflows
  - "From morning briefings to sleep mode, email processing to habit tracking — one command installs them all"
- OpenClaw TypeScript 自主 agent：https://tirnav.com/blog/build-autonomous-ai-agents-openclaw
  - Watch（监控）→ Think（推理）→ Act（执行）三步自动化

**目标人群**：被邮件/会议/重复任务淹没的打工人/freelancer

### 核心框架（来自真实工具）
ClawFlows 的 morning briefing → 工作 → sleep mode 全流程已有预装模板，直接安装即可

### 15个任务

1. 早8:00 日程+任务推送 → OpenClaw cron（ClawFlows morning briefing模板）
2. 邮件分类+初步回复草稿 → email skill + Claude
3. 会议纪要自动生成 → 录音 → Claude 转录+提取Action Items
4. 重复文档自动生成（合同/报告）→ 模板 + Claude 填写
5. 周报自动生成 → 从日志+任务 → Claude 生成草稿
6. 代码 review 初稿 → Claude Code（每周省5小时，来自40小时那篇文章）
7. PR 描述自动生成 → Claude Code（每周省2小时）
8. 单元测试生成 → Claude Code（每周省8小时）
9. 技术文档更新 → Claude Code（每周省6小时）
10. Bug 根因分析初稿 → Claude Code（每周省7小时）
11. 客户回复草稿 → Claude 生成，人审批
12. 数据报表 → Python 脚本 + report_generator
13. 知识归档 → 重要内容 → citadel/km skill 存档
14. 社媒定时发布 → OpenClaw cron
15. 22:00 日结 → cron 自动生成今日完成总结

### 帖子标题草稿
每天10小时却什么都没做完——装了ClawFlows+配了8个Claude Code workflow，核心工作现在2小时搞定

---

## 梦想4：把我的专业知识卖出去（知识变现）

**真实支撑**：
- OpenClaw Box 集成案例（Box是企业文档存储）：https://blog.box.com/connecting-openclaw-box-practical-pattern-agent-workflows
- Wix 工程师用 Claude Code 建管理平台：https://medium.com/wix-engineering/turning-claude-code-into-a-management-platform
- OpenClaw 25+ 真实案例（内容创作板块）：https://forwardfuture.ai/p/what-people-are-actually-doing-with-openclaw-25-use-cases

**目标人群**：有专业背景（医生/律师/工程师/设计师），想做副业

### 15个任务

1. **知识梳理**（我知道什么别人不知道）→ Claude 引导式提问
2. **竞品调研** → Perplexity 搜知识星球/Gumroad 同类产品
3. **目标客户画像** → Claude + Perplexity 搜论坛真实提问
4. **产品形式选择**（课程/咨询/模板）→ Claude 分析优劣
5. **课程大纲** → Claude 生成15章结构
6. **第一节课内容** → Claude 起草
7. **销售页文案**（含价格锚定）→ Claude 生成
8. **定价测试** → Perplexity 搜同类价格区间
9. **免费钩子样本** → 从内容切片 + Claude 改写
10. **客户 FAQ** → Claude 基于常见问题生成
11. **交付流程自动化**（购买→自动发邮件→cron跟进）→ OpenClaw cron
12. **学员反馈收集** → OpenClaw cron 定时汇总
13. **案例背书** → Claude 把反馈改写成可引用案例
14. **涨价时机提醒** → 达到一定销量 cron 自动提醒
15. **复购品设计** → Claude 建议进阶产品

### 帖子标题草稿
有专业知识但不知道怎么卖——虾帮我把知识打包成课程，15步全自动，第一个月卖出去了

---

## 梦想5：让虾帮我找工作

**真实支撑**：
- AI 求职自动化工具 Loopcv（自动投递1000+岗位）：https://www.loopcv.pro/
- Taskade AI 求职 agent：https://help.taskade.com/en/articles/9208068-custom-ai-agents-for-job-search
  - "Automate resume creation, track applications, and get recommendations"
- Claude Code 让工程师进入陌生代码库当天提PR（Every团队，适用于快速了解目标公司技术栈）

**目标人群**：在职跳槽、应届生、被裁员后找工作的人

### 15个任务

1. **目标岗位分析**（哪个方向薪资+匹配度最高）→ Perplexity 搜岗位要求+薪资
2. **简历优化**（按 JD 关键词）→ Claude 按目标 JD 重写
3. **ATS 关键词匹配检查** → Claude 分析简历 vs JD 关键词覆盖率
4. **目标公司名单**（50家）→ Perplexity 搜行业排名
5. **每家 JD 抓取** → Tavily 批量搜
6. **简历批量定制**（每个 JD 一个版本）→ Claude 生成
7. **Cover letter 生成** → Claude 定制化
8. **投递记录表** → xlsx skill 自动维护
9. **面试前公司调研** → Perplexity 搜最新动态+近期新闻
10. **高频面试题准备** → Claude 模拟问答
11. **技术面试准备**（了解目标公司技术栈）→ Claude Code 读开源代码
12. **薪资谈判脚本** → Claude 生成场景对话
13. **跟进邮件模板** → Claude 生成 + cron 定时提醒未回复
14. **Offer 对比分析**（薪资+发展+团队）→ Claude 帮分析
15. **30/60/90天计划** → Claude 基于 JD 生成

### 帖子标题草稿
投了80份简历0面试——让虾分析问题、重做简历、定制每个JD，下周拿到了第一个面试
