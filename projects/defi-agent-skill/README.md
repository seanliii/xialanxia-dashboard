# 🦐 DeFi Agent Skill — OpenClaw 链上助手

**让 AI Agent 拥有链上眼睛** — 自然语言查询加密价格、钱包余额、Gas 费、趋势币种

## 🚀 在线体验

👉 https://seanliii.github.io/defi-agent-skill/

## 功能

| 功能 | 说明 |
|------|------|
| 💰 实时价格 | BTC/ETH/SOL/BNB 实时价格 + 24h 涨跌 |
| 🔥 热门趋势 | CoinGecko Trending Top 8 |
| 👛 钱包余额 | ETH 钱包余额查询（粘贴 0x 地址） |
| ⛽ Gas 费 | 以太坊当前 Gas 参考 |

## 数据来源

- **CoinGecko** — 免费公开 API，无需 Key
- **Etherscan** — 公开 balance API
- 所有数据实时获取，60秒自动刷新

## OpenClaw Skill 使用

```bash
python3 defi_agent.py "比特币价格"
python3 defi_agent.py "今日热门"
python3 defi_agent.py "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
python3 defi_agent.py "gas费"
```

## 复刻来源

灵感来自：
- [Zerion CLI](https://web3wire.org/defi/zerion-launches-open-source-cli-giving-ai-agents-crypto-capabilities/) (2026.05.15)
- [swapper-toolkit](https://github.com/swapperfinance/swapper-toolkit)

**由 🦐 小蓝虾 × OpenClaw 构建 — 2026.05.21**
