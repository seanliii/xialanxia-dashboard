# 热门 Skill 需求（基于真实搜索，有来源）

---

## Skill 1：Codex PR 自动审查（@codex review）

**真实来源**：
- OpenAI 官方文档：https://openai.com/codex-github
- Reddit 讨论 Claude Code guardrails：https://www.reddit.com/r/ClaudeCode/comments/1q19o4r/what_guardrails_are_you_using_in_the_claudeCode_workflow/

**触发场景**：code review 排队等人，或接手陌生代码库

**核心功能**：
- 在 PR 评论里 `@codex review` 触发
- 自动分析 diff：潜在 bug、安全问题、代码风格
- 输出三级报告（严重/警告/建议），自动回复 PR

**实现思路**：
```python
# GitHub Webhook 监听 PR comment
# 检测到 @codex review 触发 OpenAI Codex API
# 读取 PR diff，生成审查报告
# 自动 post comment 回 PR
```

**变现方向**：GitHub App 订阅 $10-30/月/repo，程序员客栈接单 ¥800/项

**帖子标题草稿**：code review 排队等了两天——写了个 @codex review skill，PR提上去5分钟出报告

---

## Skill 2：Claude Code 代码库文档自动生成

**真实来源**：
- Wix Engineering：https://medium.com/wix-engineering/turning-claude-code-into-a-management-platform
- 8个workflow省40小时文章：https://medium.com/@bandenawaz.bagwan/8-claude-code-workflows-that-saved-me-40-hours-last-week
  - "技术文档更新"是8个workflow中省时最多的之一（每周6小时）

**触发场景**：代码写了半年没文档，新人接手一脸懵

**核心功能**：
- 读取代码库，自动生成 README / API 文档 / 架构图
- 支持增量更新（只写改动了的部分）
- 输出 Markdown，可直接提 PR

**实现思路**：
```bash
# 用 Claude Code 读整个代码库
claude code "Read this codebase and generate:
1. README.md with setup instructions
2. API.md with all endpoints
3. ARCHITECTURE.md with system diagram"
# 自动提 PR 更新文档
```

**变现方向**：GitHub Action $5-15/月，程序员客栈接单 ¥500-1500/项

**帖子标题草稿**：代码写了半年没有文档——Claude Code读了一遍代码库，自动生成了README和API文档

---

## Skill 3：ClawFlows 式全天自动化工作流

**真实来源**：
- GitHub：https://github.com/nikilster/clawflows
  - "101 prebuilt agent workflows for OpenClaw. From morning briefings to sleep mode, email processing to habit tracking"
- OpenClaw Map：https://openclawmap.com/tools/clawflows-github
  - "one command installs them all"
- OpenClaw TypeScript 自主 agent 指南：https://tirnav.com/blog/build-autonomous-ai-agents-openclaw

**触发场景**：每天重复的信息汇总、日程整理、邮件处理占据大量时间

**核心功能**：
- 早起 briefing（日程+待办+资讯）
- 工作时段自动化（邮件/任务/代码）
- 晚间 sleep mode（日结+明日准备）

**安装方式（来自真实项目）**：
```bash
# 从 GitHub 安装 ClawFlows
git clone https://github.com/nikilster/clawflows
cd clawflows && ./install.sh
# 一键启用 morning briefing workflow
claw workflow enable morning-briefing
```

**变现方向**：帮别人配置全套 workflow，¥299-999/次

**帖子标题草稿**：装了ClawFlows之后——早起自动收到今日简报，下班自动生成日结，101个workflow一条命令装完

---

## Skill 4：Codex 并行任务工厂（Solo 开发加速器）

**真实来源**：
- Pieter Levels 推文：https://x.com/levelsio/status/2027566773814403448
- OpenAI Sora Android 28天案例：https://openai.com/index/shipping-sora-for-android-with-codex/
- YouTube "Solopreneur Agent Harness"（16个子agent）：https://www.youtube.com/watch?v=eKbdk0MUhsU
- Sam Altman：用Codex的工程师多完成70% PR

**触发场景**：solo developer 或小团队，任务积压，想并行推进多个模块

**核心功能**：
- 同时给多个 Codex 实例分配不同 issue/feature
- 统一汇总 PR，人只做最终 review
- 学 Sora 团队：4人完成通常需要几个月的 Android 开发

**实现思路**：
```python
# 并行启动多个 Codex 任务
tasks = [
    "Implement user authentication module",
    "Build payment integration with Stripe",
    "Create admin dashboard",
    "Write comprehensive test suite"
]
# 每个任务独立沙盒，互不干扰
# 每个任务完成后自动提 draft PR
```

**变现方向**：外包项目提速工具，接单 ¥2000-8000/项

**帖子标题草稿**：4个工程师28天上线App——OpenAI用Codex并行跑任务，我抄了这个方法，效率翻了

---

## Skill 5：竞品监控日报（Tencent Cloud 实战案例级）

**真实来源**：
- Tencent Cloud 技术百科，OpenClaw 生产级 agent 指南（30+生产agent案例，包含竞品监控）：
  https://www.tencentcloud.com/techpedia/140790
- OpenClaw 25 Ways 案例：https://www.tencentcloud.com/techpedia/140931
  - "After extensive experimentation and community sharing, clear patterns emerge around the most valuable automation"

**触发场景**：产品/创业者不知道竞品在做什么，总是后知后觉

**核心功能**：
- 每天监控竞品官网/定价/功能更新/招聘变化
- Claude 分析变化意义（这意味着什么战略意图）
- 推送日报，重大变化单独提醒

**实现思路（OpenClaw cron 模式）**：
```python
# OpenClaw cron 每天 8:00 触发
# Tavily 搜竞品最新内容
# Perplexity sonar 分析战略意义
# Claude 生成 300字以内日报
# 推送到大象/Slack
```

**变现方向**：对外提供竞品监控服务，$20-100/月/套，企业版定制 ¥5000+

**帖子标题草稿**：竞品发布新功能我总是最后知道——配了个每天8点自动跑的竞品日报，现在提前一步
