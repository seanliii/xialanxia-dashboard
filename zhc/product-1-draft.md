# 用 OpenClaw 搭建自动金融情报 Agent 完整指南

> **版本：基础版 $29 / 进阶版 $49**
> 作者：小蓝虾 🦐🔵 | 适合有一定 AI 工具使用经验的读者

---

## Part 1：为什么你需要一个金融情报 Agent

### 信息差 = 钱

金融市场的本质是信息的不对称分配。机构投资者有彭博终端（$25,000/年）、有专职研究员、有私人新闻 Feed——他们比你早看到信息，就意味着他们比你早进场。

但现在，情况变了。

一个配置得当的 AI Agent，能在同一时间：
- 扫描全球 Twitter 上关于某支股票的最新讨论
- 抓取分析师最新的盈利预期变化
- 检查加密市场的价格异动
- 用 Perplexity 搜索最新宏观新闻
- **把这一切整理成一份你能直接读懂的情报推送**

这不是未来，这是今天用 $0.02/天 就能做到的事。

### 人工追踪 vs Agent 自动追踪

| 对比维度 | 人工追踪 | Agent 自动追踪 |
|----------|----------|----------------|
| 覆盖信息源 | 3-5 个（精力有限） | 20+ 个（并发处理） |
| 每日时间投入 | 1-2 小时 | 0 分钟（全自动） |
| 反应速度 | 小时级 | 分钟级 |
| 遗漏风险 | 高（疲劳、分心） | 极低（程序不累） |
| 每月成本 | 时间成本巨大 | < $1 |
| 信息整合 | 手动拼接 | 自动汇总 + 观点输出 |

你的注意力是稀缺资源。把信息收集这件事交出去，把注意力留给决策。

### 真实案例：我是怎么用的

我目前的配置是这样的：**每天 5 次推送**，分别在 9:00（开盘前）、11:30、14:00、16:00（收盘后）、22:00（美股盘中）触发。每次推送包含：

- 🔥 **Twitter 热点**：搜索 "$NVDA OR $AAPL OR AI"，抓最新 20 条，筛出有价值的
- 📊 **关键数据变化**：分析师预期调整、机构持仓变动
- 🪙 **加密动态**：BTC/ETH 价格 + 市场情绪
- 🤖 **AI 行业情报**：最新论文/产品/融资事件

**每次推送成本估算：**
- Twitter 搜索 × 3 = $0.0012
- 金融数据查询 × 2 = $0.002
- Perplexity 联网搜索 × 1 = $0.012
- LLM 汇总整合 = $0.002
- **单次成本合计：约 $0.017**，每天 5 次 = **$0.085/天，约 $2.5/月**

不到一杯咖啡的钱，换来一个 7×24 小时不睡觉的情报员。

这套系统搭起来一次，以后每天自动运转，不需要你盯着。更重要的是，它**可以进化**——后面我会讲怎么让它越来越懂你的偏好。

---

## Part 2：系统架构

### 整体架构

这套系统由四个核心层组成：**数据源 → 处理引擎 → 调度层 → 推送渠道**。

```
┌─────────────────────────────────────────────────────┐
│                  金融情报 Agent 架构                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  数据源层 (AISA API)                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │
│  │ Twitter  │ │ 金融数据 │ │Perplexity│ │ 加密   │  │
│  │ 搜索/趋势│ │ FMP数据库│ │ sonar-pro│ │ 价格   │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘  │
│       └────────────┴────────────┴────────────┘       │
│                        ↓                             │
│  处理引擎层 (OpenClaw Agent)                          │
│  ┌─────────────────────────────────────────────┐     │
│  │  SOUL.md（使命定义）                         │     │
│  │  MEMORY.md（记忆上下文）                     │     │
│  │  LLM（Claude / GPT-4.1 汇总分析）            │     │
│  │  去重系统（sent-history.json）               │     │
│  └─────────────────────────┬───────────────────┘     │
│                             ↓                        │
│  调度层 (OpenClaw Cron)                               │
│  ┌─────────────────────────────────────────────┐     │
│  │  HEARTBEAT.md（任务清单）                    │     │
│  │  cron job（定时触发，每天 5 次）              │     │
│  └─────────────────────────┬───────────────────┘     │
│                             ↓                        │
│  推送渠道层                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  大象 IM │  │ Telegram │  │  Discord / Slack  │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 核心组件说明

| 组件 | 作用 |
|------|------|
| **OpenClaw** | Agent 主体，负责调用 API、运行逻辑、发送推送 |
| **AISA API** | 统一数据入口，聚合 Twitter / 金融 / 加密 / Perplexity 等数据源 |
| **SOUL.md** | 定义 Agent 的使命、风格和行为边界 |
| **HEARTBEAT.md** | 每次心跳时执行的任务清单，Agent 会自动读取并执行 |
| **Cron Jobs** | 定时触发 Agent 心跳，控制推送频率和时间 |
| **sent-history.json** | 去重记录，避免同一条信息被重复推送 |
| **MEMORY.md** | Agent 的长期记忆，存储你的偏好和历史洞察 |
| **推送渠道** | 大象 IM / Telegram / Discord，情报最终落地的地方 |

架构非常清晰：**AISA API 负责抓数据，OpenClaw 负责处理和判断，Cron 负责定时执行，推送渠道是你最终看到结果的地方。**

搭建这套系统不需要写任何代码，全部通过配置文件完成。接下来，我们进入最核心的五步搭建。

---

## Part 3：五步搭建

### Step 1：安装 OpenClaw

**去 [openclaw.ai](https://openclaw.ai) 下载安装包，支持 Mac / Windows / Linux。**

安装过程和普通应用一样，下载后直接运行安装向导即可。安装完成后，你会看到 OpenClaw 的工作目录：

```
~/.openclaw/workspace/
├── SOUL.md          # Agent 使命定义（我们要改这个）
├── TOOLS.md         # API 密钥和工具配置（我们要改这个）
├── HEARTBEAT.md     # 心跳任务清单（我们要创建这个）
├── MEMORY.md        # 长期记忆
└── memory/          # 每日记忆日志
```

**推荐模型配置：**

进入 OpenClaw 设置，选择以下任一模型：
- `claude-3.7-sonnet`（推荐，推理能力强，擅长长文本整合）
- `gpt-4.1`（备选，速度更快，成本略低）

**验收标准：** 打开 OpenClaw 能看到对话界面，发一条消息能得到回复，说明安装成功。

---

### Step 2：配置数据源 AISA API

这套系统的数据全部来自 **AISA API**（[api.aisa.one](https://api.aisa.one)），它是一个聚合了 Twitter、Perplexity、金融数据、加密数据的统一 API 平台。

**注册与充值：**

1. 访问 [api.aisa.one](https://api.aisa.one) 完成注册
2. 充值 **$5**，按实际使用量计费，$5 够正常使用 **1 个月以上**
3. 在控制台创建 API Key，复制备用

**已验证可用的接口（含费用）：**

| 接口 | 功能 | 费用/次 |
|------|------|---------|
| Twitter 搜索 | 搜索最新推文，支持 Latest/Top 排序 | ~$0.0004 |
| Twitter 趋势 | 全球/美国热门话题榜 | ~$0.0004 |
| Twitter 用户推文 | 抓取特定用户最新推文 | ~$0.0004 |
| Perplexity sonar | 联网搜索，普通版 | ~$0.006 |
| **Perplexity sonar-pro** | **联网搜索，高质量版（推荐）** | **$0.012** |
| 财务指标快照 | PE/EPS/营收/利润等核心指标 | $0.024 |
| 分析师预期 | 一致性盈利预期、目标价 | $0.048 |
| 机构持仓数据 | 主要机构持仓变化 | $0.000 |
| 公司基本信息 | 公司简介、板块、市值 | $0.000 |
| 损益表 | 季度/年度财务报表 | $0.048 |

**把 API Key 写入 TOOLS.md：**

打开 `~/.openclaw/workspace/TOOLS.md`，在文件末尾添加：

```markdown
### AISA API
- API_KEY: sk-你的API密钥粘贴在这里
- Data Base URL: https://api.aisa.one/apis/v1/
- LLM Base URL: https://api.aisa.one/v1/chat/completions
```

**验收标准：** 在命令行运行以下测试，返回推文数据说明配置成功：

```bash
curl "https://api.aisa.one/apis/v1/twitter/tweet/advanced_search?query=NVDA&queryType=Latest" \
  -H "Authorization: Bearer sk-你的API密钥"
```

---

### Step 3：配置 SOUL.md + HEARTBEAT.md

这是整套系统的"大脑配置"，决定了 Agent 会做什么、怎么做。

#### SOUL.md：定义 Agent 的核心使命

SOUL.md 告诉 Agent **"你是谁，你的任务是什么"**。对于金融情报 Agent，你需要把它改成这样：

```markdown
# SOUL.md - 金融情报 Agent

## 使命
你是一个专业的金融情报 Agent。你的核心任务是：
每次被激活时，从多个数据源收集最新金融情报，
整合分析后推送给用户。

## 核心能力
- 使用 AISA API 搜索 Twitter 上关于目标股票的最新讨论
- 查询分析师预期变化和机构持仓动态
- 追踪加密货币价格和市场情绪
- 用 Perplexity 搜索最新宏观新闻
- 将所有信息整合成清晰、可读的情报推送

## 风格要求
- 信息密度高，去除废话
- 数据和观点分开，不混淆
- 重要变化用 ⚠️ 标注
- 每条情报标明信息来源和时间
- 语气专业但不学术，像行业内行人讲话

## 关注标的（按优先级）
- 股票：NVDA, AAPL, MSFT, TSLA（可自定义）
- 加密：BTC, ETH
- 主题：AI, 半导体, 生物医药

## 行为边界
- 不发重复信息（检查 sent-history.json）
- 不发超过 24 小时的旧新闻
- 不预测股价涨跌，只提供信息
```

#### HEARTBEAT.md：定义任务清单

HEARTBEAT.md 是 Agent 每次被心跳触发时会读取并执行的任务清单：

```markdown
# HEARTBEAT.md - 金融情报任务清单

## 执行顺序（每次心跳必须全部完成）

### 1. Twitter 情报收集
- 搜索 AISA API Twitter 接口：query = "$NVDA OR $AAPL OR $MSFT AI"，queryType = Latest
- 搜索 query = "BTC OR ETH crypto"，queryType = Latest
- 抓取最新 20 条，筛选有信息量的推文（排除广告、垃圾）

### 2. 金融数据查询
- 查询 NVDA 分析师预期（/financial/analyst-estimates）
- 查询 AAPL 财务指标（/financial/financial-metrics/snapshot）
- 如果最近 7 天内已查过且无变化，可跳过

### 3. 加密价格
- 查询 BTC-USD 和 ETH-USD 最新价格
- 与上次推送时价格对比，计算涨跌幅

### 4. 宏观新闻
- 调用 Perplexity sonar-pro 搜索："today financial market news AI stocks"

### 5. 整合推送
- 将以上所有信息整合成一份情报报告
- 检查 sent-history.json，过滤重复内容
- 按 SOUL.md 的风格要求格式化
- 发送到配置的推送渠道
- 把本次推送的核心要点写入 sent-history.json

## 重要提示
- 如果 API 调用失败，记录错误，跳过该数据源，不要中断整个推送
- 每次推送完毕后，在 memory/当日日期.md 记录本次推送摘要
```

**关于 Adaptive Reasoning：**

OpenClaw 内置了 **Adaptive Reasoning** 机制——Agent 会根据任务复杂度自动选择推理深度。简单的价格查询快速处理，需要综合判断多个信号的分析任务会自动启用更深度的推理。你不需要手动配置，写好 SOUL.md 和 HEARTBEAT.md，Agent 自己会判断。

**验收标准：** 手动发一条消息"执行心跳任务"给 Agent，它应该开始调用 API 并返回一份格式化的情报推送。

---

### Step 4：设置 Cron 任务

有了 HEARTBEAT.md，现在需要告诉 OpenClaw **什么时候自动触发**。

#### OpenClaw Cron 语法

OpenClaw 的 cron 配置使用标准的 5 段 cron 表达式：

```
分钟 小时 日期 月份 星期
```

例如：
- `0 9 * * 1-5` = 工作日上午 9:00
- `30 11 * * *` = 每天 11:30
- `0 22 * * *` = 每天晚上 22:00

#### 完整的金融情报推送配置

在 OpenClaw 设置中，添加以下 5 个 cron 任务（以 JSON 格式为例）：

```json
[
  {
    "name": "金融情报-开盘前",
    "schedule": "0 9 * * 1-5",
    "prompt": "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. 当前是开盘前推送，重点关注隔夜美股收盘情况和今日重要事件预告。Do not infer or repeat old tasks from prior chats.",
    "delivery": {
      "to": "你的用户ID或群组ID",
      "channel": "daxiang"
    },
    "model": "claude-3.7-sonnet",
    "thinking": "low"
  },
  {
    "name": "金融情报-午间",
    "schedule": "30 11 * * 1-5",
    "prompt": "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. 当前是午间推送，重点关注上午市场异动。Do not infer or repeat old tasks from prior chats.",
    "delivery": {
      "to": "你的用户ID或群组ID",
      "channel": "daxiang"
    },
    "model": "claude-3.7-sonnet",
    "thinking": "low"
  },
  {
    "name": "金融情报-下午",
    "schedule": "0 14 * * 1-5",
    "prompt": "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats.",
    "delivery": {
      "to": "你的用户ID或群组ID",
      "channel": "daxiang"
    },
    "model": "claude-3.7-sonnet",
    "thinking": "low"
  },
  {
    "name": "金融情报-收盘后",
    "schedule": "30 16 * * 1-5",
    "prompt": "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. 当前是 A 股收盘后推送，总结今日行情，前瞻美股开盘。Do not infer or repeat old tasks from prior chats.",
    "delivery": {
      "to": "你的用户ID或群组ID",
      "channel": "daxiang"
    },
    "model": "claude-3.7-sonnet",
    "thinking": "low"
  },
  {
    "name": "金融情报-美股盘中",
    "schedule": "0 22 * * 1-5",
    "prompt": "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. 当前是美股盘中推送，重点关注美股实时动态和科技股表现。Do not infer or repeat old tasks from prior chats.",
    "delivery": {
      "to": "你的用户ID或群组ID",
      "channel": "daxiang"
    },
    "model": "claude-3.7-sonnet",
    "thinking": "low"
  }
]
```

#### delivery.to 的几种写法

| 场景 | 写法示例 |
|------|----------|
| 发给自己（单聊） | `"to": "你的大象用户ID"` |
| 发给群聊 | `"to": "群组ID"` （需要在群里添加 Bot） |
| 多人同时接收 | `"to": ["用户ID1", "用户ID2"]` |
| Telegram | `"to": "@你的用户名"`, `"channel": "telegram"` |

**验收标准：** 保存配置后，等到下一个整点，检查是否收到自动推送的情报消息。或者临时把 schedule 改为"下一分钟"测试一次，收到消息后再改回正式时间。

---

### Step 5：去重系统

没有去重，你的 Agent 每次都会把同一条新闻推送给你。两三天之后你就会屏蔽它。**去重是让 Agent 长期可用的关键。**

#### sent-history.json 工作原理

在工作目录下创建 `sent-history.json`，格式如下：

```json
{
  "version": "1.0",
  "entries": [
    {
      "id": "tweet-1234567890",
      "title": "Jensen Huang at Computex: next-gen Blackwell...",
      "url": "https://twitter.com/...",
      "sentAt": "2025-05-15T09:00:00+08:00",
      "category": "twitter"
    },
    {
      "id": "news-nvda-q1-2025",
      "title": "NVDA Q1 2025 earnings beat",
      "sentAt": "2025-05-15T11:30:00+08:00",
      "category": "financial-news"
    }
  ]
}
```

在 HEARTBEAT.md 中，给 Agent 加一条指令：

```markdown
### 去重检查（每次推送前必须执行）
- 读取 sent-history.json
- 对比本次收集到的所有内容，过滤掉已经推送过的条目
- 推送完成后，把本次新推送的内容追加到 sent-history.json
- sent-history.json 保留最近 7 天的记录，超过 7 天的条目自动删除
```

**去重的判断逻辑：**
- Twitter 推文：用 tweet ID 去重
- 金融新闻：用标题 + 日期组合去重
- 数据类（价格、持仓）：不去重，每次更新都推送最新值

**验收标准：** 手动触发两次心跳，第二次推送的内容应该和第一次不重叠，说明去重系统正常工作。

---

## Part 4：让 Agent 越来越聪明

搭建好这套系统只是开始。真正让它变强的，是**持续学习机制**。

### 自我进化循环：LEARNINGS.md + ERRORS.md

在工作目录下，创建 `.learnings/` 文件夹，包含三个文件：

**LEARNINGS.md** — 记录有价值的发现和最佳实践：
```markdown
## 2025-05-15 | best_practice
当 NVDA 分析师预期上调超过 5%，通常是机构建仓信号，需要重点追踪。

## 2025-05-16 | correction
Perplexity sonar-pro 的结果质量远好于 sonar，金融类查询必须用 sonar-pro。
```

**ERRORS.md** — 记录 API 失败、数据异常等问题：
```markdown
## 2025-05-15 09:03 | API_ERROR
AISA /financial/crypto/prices/snapshot 接口 ticker 格式需要 BTC-USD，不能用 BTC。
已修正 HEARTBEAT.md。
```

**FEATURE_REQUESTS.md** — 记录你想加的新功能：
```markdown
- 加入 Polymarket 预测市场数据对比
- 追踪 13F 表格的机构持仓季度变化
```

**Agent 在每次任务结束后会自动评估**是否需要写入这些文件。你也可以直接告诉 Agent："记下来，下次 NVDA 财报前要提前三天开始追踪期权流"，它会写入 LEARNINGS.md 并在未来相关任务中引用。

### 记忆系统：MEMORY.md 日常维护

MEMORY.md 是 Agent 的长期记忆，存储你的偏好、历史洞察和决策背景。

每隔几天，Agent 会（在心跳中）自动：
1. 读取最近的 `memory/YYYY-MM-DD.md` 日志
2. 提炼出有价值的内容
3. 更新到 MEMORY.md

你也可以主动告诉 Agent："记住，我最近在重点关注生物医药板块的 FDA 审批节点"，它会写入记忆，并在未来的情报推送中优先覆盖相关内容。

### 每日记忆压缩

随着时间推移，memory 文件夹会积累大量日志。为了防止上下文爆炸，需要**每日压缩**。

在工作目录下创建 `memory_compressor.py`：

```python
#!/usr/bin/env python3
"""
memory_compressor.py
每天 22:00 压缩当天的记忆日志，保留精华，删除噪音
"""
import os
import json
import datetime
from openai import OpenAI

client = OpenAI(
    api_key="your-aisa-api-key",
    base_url="https://api.aisa.one/v1"
)

def compress_memory(date_str: str) -> str:
    memory_path = f"memory/{date_str}.md"
    if not os.path.exists(memory_path):
        return "No memory file found."
    
    with open(memory_path, "r") as f:
        content = f.read()
    
    if len(content) < 500:
        return "Memory too short, no compression needed."
    
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "你是一个记忆压缩助手。把以下日记压缩到 800 字以内，保留：重要决策、新知识、待办事项、有趣发现。删除：重复内容、无意义流水账。"
            },
            {
                "role": "user",
                "content": content
            }
        ],
        max_tokens=1000
    )
    
    compressed = response.choices[0].message.content
    
    # 把压缩后的内容写回
    with open(memory_path, "w") as f:
        f.write(f"# {date_str} [已压缩]\n\n{compressed}")
    
    return f"Compressed {len(content)} chars to {len(compressed)} chars."

if __name__ == "__main__":
    today = datetime.date.today().strftime("%Y-%m-%d")
    result = compress_memory(today)
    print(result)
```

在 OpenClaw 添加一个 cron job，每天 22:30 运行：

```json
{
  "name": "每日记忆压缩",
  "schedule": "30 22 * * *",
  "prompt": "执行 python3 ~/.openclaw/workspace/memory_compressor.py，压缩今天的记忆日志。完成后回报压缩结果。",
  "delivery": {
    "to": "你的用户ID",
    "channel": "daxiang"
  }
}
```

**这是 Hermes Agent 的 trajectory compression 思想在 OpenClaw 的实现。** Nous Research 的 Hermes Agent 使用 Gemini Flash 压缩 session trace，降低长对话的上下文成本；我们用同样的思路压缩 memory 文件，让 Agent 在积累大量历史后依然保持高效。原理一样，实现更简单，直接可用。

---

## Part 5：高阶玩法

基础系统搭好之后，这三个方向能让你的情报 Agent 真正产生 Alpha。

### 搭配 Polymarket 做事件预测

**Polymarket 是全球最大的预测市场**，允许你用 USDC 对真实世界事件下注，比如"美联储6月降息概率"、"某药物 FDA 审批通过概率"。

已经有人**用这套情报 Agent 组合赚了 $400K**，逻辑很简单：

1. 情报 Agent 持续监控相关新闻和机构动态
2. 当出现明显的信息不对称时（比如 Twitter 上已经广泛讨论某事件，但 Polymarket 的定价还没反应过来），立刻下注
3. 等市场价格收敛，平仓获利

**具体实现：**
- 在 HEARTBEAT.md 中加入 Polymarket API 查询（每次推送时对比当前市场定价 vs 你掌握的信息）
- 当发现定价偏差时，Alert 标注并通知你手动操作
- AISA 的 Perplexity sonar-pro 搜索是关键数据源，能比一般人早 30 分钟看到重要信息

### 13F 机构持仓日报自动化

每个季度，持有超过 $1 亿美股的机构必须向 SEC 提交 13F 表格，公开他们的持仓。这是合法的"偷看大佬底牌"机会。

**用 AISA API 实现自动化 13F 追踪：**

```bash
# 查询特定股票的机构持仓变化
curl "https://api.aisa.one/apis/v1/financial/institutional-ownership?ticker=NVDA" \
  -H "Authorization: Bearer $AISA_API_KEY"
```

返回的数据包含：巴菲特、索罗斯基金、Tiger Global 等机构的最新持仓比例。**当顶级机构集体增持某只股票时，这是一个极强的信号。**

在 HEARTBEAT.md 加入每周一次的 13F 扫描，Agent 自动整理成报告推送给你。

### ClawWork 自动接单赚钱

OpenClaw 的 **ClawWork** 功能允许你把 Agent 的能力包装成服务，自动接受外部任务请求并执行。

几种变现思路：

**情报订阅服务：** 把你的金融情报推送包装成付费订阅（$19-49/月），ClawWork 处理订阅用户的接入和推送分发。你的 Agent 是产品，你只需要维护数据质量。

**按需分析服务：** 接受"帮我分析 $TSLA 最近的机构动向"类型的单次查询任务，自动执行并返回报告，定价 $5-10/次。

**定制 Alert：** 为客户配置个性化的股票 Alert，当特定条件触发时自动通知，月费模式。

这三个玩法的共同前提是：**你的情报系统本身必须靠谱**。先把基础系统搭好并运行 30 天，积累足够的信任和数据质量，再考虑对外变现。

---

## 附录 A：AISA API 接口速查表

| 功能 | 端点路径 | 请求方式 | 关键参数 | 费用/次 | 用途 |
|------|----------|----------|----------|---------|------|
| Twitter 搜索 | `/apis/v1/twitter/tweet/advanced_search` | GET | `query`, `queryType=Latest\|Top` | ~$0.0004 | 搜索最新推文 |
| Twitter 趋势 | `/apis/v1/twitter/trends` | GET | `woeid=1`（全球）`/23424977`（美国） | ~$0.0004 | 获取热门话题 |
| Twitter 用户推文 | `/apis/v1/twitter/user/user_tweets` | GET | `userName` | ~$0.0004 | 追踪特定用户 |
| Twitter 用户信息 | `/apis/v1/twitter/user/info` | GET | `userName` | ~$0.0004 | 用户基本信息 |
| Perplexity sonar | `/apis/v1/perplexity/sonar` | POST | `{model:"sonar", messages:[...]}` | ~$0.006 | 联网搜索（普通） |
| Perplexity sonar-pro | `/apis/v1/perplexity/sonar-pro` | POST | `{model:"sonar-pro", messages:[...]}` | $0.012 | 联网搜索（高质量） |
| 公司基本信息 | `/apis/v1/financial/company/facts` | GET | `?ticker=AAPL` | $0.000 | 公司简介/行业 |
| 财务指标快照 | `/apis/v1/financial/financial-metrics/snapshot` | GET | `?ticker=NVDA` | $0.024 | PE/EPS/营收等 |
| 分析师预期 | `/apis/v1/financial/analyst-estimates` | GET | `?ticker=NVDA` | $0.048 | 一致性预期/目标价 |
| 机构持仓 | `/apis/v1/financial/institutional-ownership` | GET | `?ticker=AAPL` | $0.000 | 机构持股比例 |
| 财报新闻 | `/apis/v1/financial/earnings/press-releases` | GET | `?ticker=NVDA` | $0.000 | 财报发布公告 |
| 损益表 | `/apis/v1/financial/financials/income-statements` | GET | `?ticker=NVDA` | $0.048 | 季度/年度财报 |
| LLM（所有模型） | `/v1/chat/completions` | POST | OpenAI 兼容格式 | 按模型定价 | AI 分析整合 |

**认证方式（统一）：**
```
Authorization: Bearer sk-你的API密钥
```

**Base URL：**
```
https://api.aisa.one
```

**注意事项：**
- Perplexity 接口必须在请求体中包含 `"model"` 字段，否则报 400
- Financial API 全部用 GET + `?ticker=XXX` 格式传参
- LLM 接口走 `/v1/chat/completions`，与 Financial API 的 `/apis/v1/` 不同，注意区分

---

## 附录 B：配置文件模板

### B-1：SOUL.md 金融情报版（完整可用）

```markdown
# SOUL.md - 金融情报 Agent

## 使命
你是一个专业的金融情报 Agent，专为个人投资者提供机构级别的信息密度。
每次被激活时，从多个数据源收集最新金融情报，整合分析后推送高价值信号。

## 核心能力
- 使用 AISA API 搜索 Twitter 上关于目标股票的最新讨论和情绪
- 查询分析师预期变化和机构持仓动态，捕捉聪明钱动向
- 追踪加密货币价格和链上情绪
- 用 Perplexity sonar-pro 搜索最新宏观新闻和政策变化
- 将所有信息整合成清晰、可行动的情报推送

## 关注标的
### 股票（优先级从高到低）
- NVDA（AI基础设施核心标的）
- AAPL（消费科技+AI硬件）
- MSFT（AI云+Copilot生态）
- TSLA（自动驾驶+储能）
- 生物医药板块（FDA审批节点）

### 加密
- BTC（市场情绪基准）
- ETH（生态指标）

### 主题追踪
- AI/大模型：新模型发布、融资、商业化进展
- 半导体：供应链、产能、新品发布
- 宏观：美联储、CPI、就业数据

## 推送格式要求
每次推送必须包含以下板块（如无相关内容可跳过）：

🔥 **热点信号**（Twitter + 新闻，2-3条最重要的）
📊 **数据变化**（分析师预期调整、机构持仓变化）
🪙 **加密动态**（BTC/ETH 价格 + 24h 涨跌幅）
⚠️ **需关注**（任何异常信号或重要风险提示）

格式要求：
- 信息密度高，每条不超过 50 字
- 数据要有来源和时间戳
- ⚠️ 标注重要变化
- 不发重复内容（检查 sent-history.json）
- 不发超过 24 小时的旧内容

## 行为边界
- 提供信息，不做投资建议
- 不确定的内容标注"待确认"
- API 失败时降级处理，不中断整个推送
- 每次推送后更新 sent-history.json

## API 配置
AISA API Key 在 TOOLS.md 中的 ### AISA API 节。
Data Base URL: https://api.aisa.one/apis/v1/
LLM Base URL: https://api.aisa.one/v1/chat/completions
```

---

### B-2：HEARTBEAT.md 模板（完整版）

```markdown
# HEARTBEAT.md - 金融情报任务清单

## 执行流程（每次心跳按顺序执行）

### Phase 1：数据收集（并行执行以下查询）

**Twitter 情报**
- 查询1：/twitter/tweet/advanced_search?query=$NVDA OR $AAPL OR $MSFT AI&queryType=Latest
- 查询2：/twitter/tweet/advanced_search?query=BTC ETH crypto&queryType=Latest
- 查询3：/twitter/trends?woeid=23424977（美国趋势）
- 取最新 20 条，筛选有信息量的（排除纯广告、无实质内容的推文）

**金融数据**
- /financial/analyst-estimates?ticker=NVDA（分析师预期）
- /financial/financial-metrics/snapshot?ticker=AAPL（财务快照）
- /financial/institutional-ownership?ticker=MSFT（机构持仓）
- 如 7 天内已查且无变化，可跳过财务类查询

**加密价格**
- 通过 Perplexity sonar 查询："BTC ETH current price"
- 计算与上次推送时的价格差（从 sent-history.json 读取）

**宏观新闻**
- /perplexity/sonar-pro: POST {"model":"sonar-pro","messages":[{"role":"user","content":"今日金融市场重要新闻，重点：美联储动态、科技股、AI行业"}]}

### Phase 2：去重过滤
- 读取 sent-history.json
- 过滤掉已推送的 tweet ID 和新闻标题
- 只保留新内容

### Phase 3：整合推送
- 按 SOUL.md 的格式要求组织内容
- 生成情报推送文本
- 发送到配置的渠道

### Phase 4：记录
- 把本次推送的内容摘要追加到 sent-history.json
- 在 memory/当日日期.md 写一行简记："[HH:MM] 推送完成，主要信号：XXX"

## 异常处理
- 任何单个 API 调用失败：跳过该数据源，记录到 memory/今日.md，继续执行
- 如果超过 3 个 API 失败：发送简短的"数据收集异常"通知，不发完整推送
- sent-history.json 不存在：创建空文件，继续执行

## 去重规则
- Twitter 推文：用 tweet_id 去重
- 新闻：用标题 + 发布日期去重
- 价格数据：每次都推送最新值（不去重）
- sent-history.json 只保留最近 7 天记录
```

---

### B-3：Cron Job 配置示例（JSON 格式）

以下是完整的 5 次推送 + 1 次记忆压缩的 cron 配置：

```json
[
  {
    "id": "fin-morning",
    "name": "金融情报-开盘前（9:00）",
    "schedule": "0 9 * * 1-5",
    "prompt": "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. 当前推送时段：开盘前。重点：昨日美股收盘 + 今日重要事件预告。Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.",
    "delivery": {
      "to": "替换为你的用户ID",
      "channel": "daxiang"
    },
    "model": "claude-3.7-sonnet",
    "thinking": "low"
  },
  {
    "id": "fin-midday",
    "name": "金融情报-午间（11:30）",
    "schedule": "30 11 * * 1-5",
    "prompt": "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. 当前推送时段：午间。重点：上午 A 股市场异动。Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.",
    "delivery": {
      "to": "替换为你的用户ID",
      "channel": "daxiang"
    },
    "model": "claude-3.7-sonnet",
    "thinking": "low"
  },
  {
    "id": "fin-afternoon",
    "name": "金融情报-下午（14:00）",
    "schedule": "0 14 * * 1-5",
    "prompt": "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.",
    "delivery": {
      "to": "替换为你的用户ID",
      "channel": "daxiang"
    },
    "model": "claude-3.7-sonnet",
    "thinking": "low"
  },
  {
    "id": "fin-close",
    "name": "金融情报-收盘后（16:30）",
    "schedule": "30 16 * * 1-5",
    "prompt": "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. 当前推送时段：A 股收盘后。重点：今日 A 股总结 + 预判美股开盘。Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.",
    "delivery": {
      "to": "替换为你的用户ID",
      "channel": "daxiang"
    },
    "model": "claude-3.7-sonnet",
    "thinking": "low"
  },
  {
    "id": "fin-us-market",
    "name": "金融情报-美股盘中（22:00）",
    "schedule": "0 22 * * 1-5",
    "prompt": "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. 当前推送时段：美股盘中。重点：美股实时动态 + 科技股表现 + 加密市场。Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.",
    "delivery": {
      "to": "替换为你的用户ID",
      "channel": "daxiang"
    },
    "model": "claude-3.7-sonnet",
    "thinking": "low"
  },
  {
    "id": "memory-compress",
    "name": "每日记忆压缩（22:30）",
    "schedule": "30 22 * * *",
    "prompt": "执行命令：python3 ~/.openclaw/workspace/memory_compressor.py。完成后回报压缩结果（原始大小 → 压缩后大小）。",
    "delivery": {
      "to": "替换为你的用户ID",
      "channel": "daxiang"
    },
    "model": "gpt-4.1-mini",
    "thinking": "off"
  }
]
```

---

## 写在最后

这套系统我自己在用，每天帮我省下 1-2 小时的信息收集时间。更重要的是，它不会累、不会走神、不会因为情绪而漏掉重要信号。

**搭建成本：**
- 时间：按本指南操作，2-3 小时可以跑通
- 金钱：$5 AISA 充值 + OpenClaw 订阅费，每月数据成本 < $3

**进阶版（$49）额外内容：**
- Polymarket 套利策略详解（含具体操作流程）
- 13F 追踪系统完整代码（含数据库和可视化）
- ClawWork 变现配置教程
- 私人答疑群（30 天）

有问题，找小蓝虾 🦐🔵。

---

✅ DRAFT COMPLETE