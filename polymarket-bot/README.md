# 🦐 Polymarket 智能交易机器人

基于 **双 Agent 架构** 的 Polymarket 自动交易系统，整合 AISA API + Polymarket API。

## 🏗️ 架构

```
┌─────────────────┐      ┌─────────────────┐
│  预测 Agent     │ ───► │  执行 Agent     │
│  (分析 + 信号)  │      │  (风控 + 下单)  │
└─────────────────┘      └─────────────────┘
        │                        │
        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐
│  AISA API       │      │  Polymarket     │
│  • Twitter 搜索 │      │  CLOB API       │
│  • AI 模型      │      │  (需要私钥)     │
│  • 趋势分析     │      │                 │
└─────────────────┘      └─────────────────┘
```

## 📦 安装

```bash
cd polymarket-bot
pip install -r requirements.txt
```

## 🔧 配置

### 必需
- `AISA_API_KEY`: AISA API 密钥（已预置）

### 可选（实盘需要）
- `POLYGON_PRIVATE_KEY`: Polygon 钱包私钥
- `POLYGON_WALLET_ADDRESS`: 钱包地址

## 🚀 使用

### 模拟模式（推荐先测试）
```bash
# 单次扫描
python trading_bot.py --scan

# 查看市场概览
python trading_bot.py --market

# 循环扫描（每 30 分钟）
python trading_bot.py --loop --interval 30
```

### 实盘模式
```bash
# 配置钱包
export POLYGON_PRIVATE_KEY="your_private_key"

# 实盘交易
python trading_bot.py --live --scan
```

## 🎯 策略说明

### α 来源

1. **时区套利** — Polymarket 70% 用户是美国人，北京时间 0-6 点定价可能偏低
2. **Twitter 情绪领先** — KOL 发推 → Polymarket 定价有 15-60 分钟延迟
3. **订单簿失衡** — 买卖盘深度差异暗示方向

### 风控规则

| 规则 | 参数 |
|------|------|
| 单注上限 | 本金 5%（凯利公式） |
| 日亏损止损 | -15% |
| 最低置信度 | 70% |
| 最小 Edge | 10% |

### 推荐市场类型

✅ 做：天气、体育、经济数据、加密（可验证结果）

❌ 不做：文化、娱乐（主观判断）

## 📁 文件结构

```
polymarket-bot/
├── config.py            # 配置文件
├── aisa_client.py       # AISA API 客户端
│   ├── Twitter 搜索/趋势
│   └── AI 模型调用
├── polymarket_client.py # Polymarket API 客户端
│   ├── 市场数据
│   ├── 订单簿
│   └── 排行榜/持仓
├── prediction_agent.py  # 预测 Agent（只分析）
├── execution_agent.py   # 执行 Agent（只执行）
│   └── RiskManager      # 风控模块
├── trading_bot.py       # 主程序
└── README.md            # 本文件
```

## 🔌 AISA API 能力

| API | 用途 | 端点 |
|-----|------|------|
| Twitter 搜索 | 情绪分析 | `/apis/v1/twitter/tweet/advanced_search` |
| Twitter 趋势 | 热点追踪 | `/apis/v1/twitter/trends` |
| 用户推文 | KOL 追踪 | `/apis/v1/twitter/user/user_tweets` |
| AI 模型 | 预测分析 | `/v1/chat/completions` |

### 可用模型

```
gpt-4.1, gpt-4.1-mini, gpt-5, gpt-5.4
claude-sonnet-4-6, claude-opus-4-6
gemini-2.5-pro, gemini-3-pro-preview
kimi-k2.5, qwen3-max
```

## 📊 Polymarket API

| API | 用途 | 认证 |
|-----|------|------|
| Gamma API | 市场列表/事件 | 无需 |
| Data API | 持仓/排行榜 | 无需 |
| CLOB API | 下单/订单簿 | 需要私钥 |

## ⚠️ 注意事项

1. **地理限制** — Polymarket 封锁中国 IP，需要代理
2. **USDC** — 资金使用 Polygon 网络的 USDC
3. **API 余额** — AISA API 需要充值（~$0.0004/次 Twitter 搜索）
4. **风险提示** — 预测市场有风险，本工具仅供学习，盈亏自负

## 📈 进阶玩法

### 鲸鱼跟单
```python
from polymarket_client import track_whale

# 跟踪排行榜前 3 名
leaderboard = client.get_leaderboard(limit=3)
for whale in leaderboard:
    data = track_whale(whale['address'])
    print(f"鲸鱼 {whale['address'][:10]}... 持仓: {len(data['positions'])} 个")
```

### AI 情绪分析
```python
from aisa_client import AISAModelClient

ai = AISAModelClient()
analysis = ai.analyze_market_sentiment(
    market_question="Will Fed raise rates in March?",
    tweets=tweets
)
print(analysis)  # {sentiment, confidence, recommended_action}
```

---

🦐 **小蓝虾出品** | 2026.03.16
