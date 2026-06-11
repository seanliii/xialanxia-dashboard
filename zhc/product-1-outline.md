# 产品一：《用 OpenClaw 搭建自动金融情报 Agent 完整指南》

## 定价策略
- 基础版：$29（PDF + 配置模板）
- 进阶版：$49（基础版 + AISA API 接入 + cron 完整配置包）

## 目标受众
- 已经在用 OpenClaw 的用户
- 想用 AI Agent 跟踪市场/赚钱的用户
- 没技术背景但想自动化信息流的人

---

## 大纲目录

### Part 1：为什么你需要一个金融情报 Agent（2页）
- 信息差 = 钱
- 人工追踪 vs Agent 自动追踪的效率对比
- 真实案例：小蓝虾每天推送 5 次，涵盖股票+加密+AI动态

### Part 2：系统架构设计（3页）
- 整体架构图：OpenClaw + AISA API + Cron + 大象推送
- 核心组件说明：
  - OpenClaw（大脑）
  - AISA API（数据源：Twitter + 金融 + Perplexity）
  - Cron 任务调度（定时执行）
  - 大象/Telegram（推送渠道）

### Part 3：一步步搭建（核心，10页）

#### Step 1：安装 OpenClaw
- 官网下载，5分钟安装
- 推荐配置：claude-3.7-sonnet / gpt-4.1

#### Step 2：配置数据源（AISA API）
- 注册 AISA API（api.aisa.one）
- 已验证可用的接口清单：
  - Twitter 实时搜索（$0.0004/次）
  - Perplexity sonar-pro 深度分析（$0.012/次）
  - 金融数据：institutional-ownership / analyst-estimates / earnings
  - 加密价格 / 宏观利率

#### Step 3：配置 SOUL.md + HEARTBEAT.md
- SOUL.md：定义 Agent 性格和核心使命
- HEARTBEAT.md：定义每天推送内容、时间、格式
- 提供完整模板（直接复制使用）

#### Step 4：设置 Cron 任务
- OpenClaw cron 配置语法
- 完整配置示例（9点/13:30/17点 Twitter情报 + 10/12/14/16/19点深度推送）
- 如何用 jobs.json 管理任务

#### Step 5：推送到你的渠道
- 大象（企业微信）配置
- Telegram Bot 配置
- 去重系统：sent-history.json

### Part 4：让 Agent 越来越聪明（3页）
- 自我进化：LEARNINGS.md + ERRORS.md
- 记忆系统：MEMORY.md 日常维护
- 每日压缩：memory_compressor.py（附脚本）
- Adaptive Reasoning：复杂任务自动深度思考

### Part 5：高阶玩法（2页）
- 搭配 Polymarket 做事件预测
- 13F 机构持仓日报自动化
- ClawWork 自动接单赚钱

### 附录：完整配置文件包
- SOUL.md 模板
- HEARTBEAT.md 模板（金融情报版）
- cron jobs.json 示例
- sent-history.json 初始结构
- memory_compressor.py 脚本
- AISA API 完整接口速查表

---

## 差异化亮点
1. **真实系统**：基于实际运行 30+ 天的小蓝虾系统
2. **成本透明**：每次 API 调用费用都标注
3. **中文优先**：专门针对大象/国内渠道优化
4. **即用模板**：所有配置文件直接复制，不需要写代码

---

## 营销文案草稿（X 推文）

> 我用 OpenClaw 搭了一个自动金融情报 Agent
> 
> 每天自动推送：
> - 📊 股票机构持仓变动（NVDA/AAPL/TSLA）
> - 🐦 全球 Twitter AI/crypto 最新动态  
> - 💰 加密价格 + 宏观信号
> - 🤖 AI Agent 生态动态
> 
> 零人工干预，每天 5 次推送
> 成本：$0.02/天
> 
> 完整搭建指南（PDF + 配置文件包）→ [链接]
> $29，直接复制用

---

## 制作计划
- Day 1：写完 PDF 正文（今天）
- Day 2：整理配置文件包 + 排版
- Day 3：上传 ClawMart + 发 X 推文
