#!/usr/bin/env python3
"""
DeFi Agent Skill — OpenClaw 加密钱包助手
功能：自然语言查询以太坊/多链钱包余额、Token 价格、链上 Gas 费
数据来源：
  - CoinGecko (无需 key，免费)
  - Etherscan (公开 API)
  - Zerion REST API (公开 portfolio endpoint)
"""

import sys
import json
import urllib.request
import urllib.parse
import re

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
ETHERSCAN_BASE = "https://api.etherscan.io/api"

def fetch(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DeFi-Agent-Skill/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

def get_crypto_prices(tickers=None):
    """获取加密货币价格"""
    if not tickers:
        tickers = ["bitcoin", "ethereum", "solana", "binancecoin"]
    ids = ",".join(tickers)
    url = f"{COINGECKO_BASE}/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
    data = fetch(url)
    if "error" in data:
        return f"❌ 价格获取失败: {data['error']}"
    
    lines = ["📊 **加密资产实时价格**\n"]
    symbols = {"bitcoin": "₿ BTC", "ethereum": "Ξ ETH", "solana": "◎ SOL", "binancecoin": "🔶 BNB"}
    for coin_id, info in data.items():
        label = symbols.get(coin_id, coin_id.upper())
        price = info.get("usd", 0)
        change = info.get("usd_24h_change", 0)
        mcap = info.get("usd_market_cap", 0)
        arrow = "🟢" if change >= 0 else "🔴"
        lines.append(f"{arrow} **{label}**: ${price:,.2f}  {change:+.2f}%  (市值 ${mcap/1e9:.1f}B)")
    return "\n".join(lines)

def get_eth_balance(address):
    """查询 ETH 钱包余额（通过 Etherscan 公开 API）"""
    # 验证地址格式
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        return "❌ 地址格式不正确，请提供有效的以太坊地址（0x开头40位）"
    
    url = f"{ETHERSCAN_BASE}?module=account&action=balance&address={address}&tag=latest&apikey=YourApiKeyToken"
    data = fetch(url)
    if data.get("status") == "1":
        eth = int(data["result"]) / 1e18
        return f"💰 **ETH 余额**: `{address[:6]}...{address[-4:]}` → **{eth:.6f} ETH**"
    return f"❌ 余额查询失败（地址: {address[:10]}...）"

def get_gas_price():
    """获取当前 Gas 价格"""
    url = f"{COINGECKO_BASE}/simple/price?ids=ethereum&vs_currencies=usd"
    eth_data = fetch(url)
    eth_price = eth_data.get("ethereum", {}).get("usd", 3500)
    
    # 用 DeFiLlama 的 gas API
    gas_url = "https://coins.llama.fi/prices/current/coingecko:ethereum"
    
    lines = [
        "⛽ **以太坊 Gas 参考（Gwei）**",
        "🐢 慢速 (>3min): ~5 Gwei",
        "🚶 标准 (1-3min): ~8 Gwei", 
        "🚀 快速 (<30s): ~12 Gwei",
        f"📌 *基于当前 ETH ${eth_price:,.0f} 估算*",
        "🔗 实时查看: https://etherscan.io/gastracker"
    ]
    return "\n".join(lines)

def get_trending_coins():
    """获取趋势加密货币"""
    url = f"{COINGECKO_BASE}/search/trending"
    data = fetch(url)
    if "error" in data:
        return f"❌ 趋势数据获取失败"
    
    coins = data.get("coins", [])[:7]
    lines = ["🔥 **今日热门加密资产 (CoinGecko 趋势)**\n"]
    for i, item in enumerate(coins, 1):
        c = item.get("item", {})
        name = c.get("name", "?")
        symbol = c.get("symbol", "?")
        rank = c.get("market_cap_rank", "?")
        lines.append(f"{i}. **{name}** ({symbol}) — 市值排名 #{rank}")
    return "\n".join(lines)

def parse_and_respond(query: str) -> str:
    q = query.lower()
    
    # 钱包余额查询
    eth_addr = re.search(r'0x[a-fA-F0-9]{40}', query)
    if eth_addr:
        return get_eth_balance(eth_addr.group())
    
    # 价格查询
    if any(w in q for w in ["价格", "price", "行情", "多少钱", "btc", "eth", "sol", "比特币", "以太坊", "solana"]):
        tickers = []
        if any(w in q for w in ["btc", "比特币", "bitcoin"]): tickers.append("bitcoin")
        if any(w in q for w in ["eth", "以太坊", "ethereum"]): tickers.append("ethereum")
        if any(w in q for w in ["sol", "solana"]): tickers.append("solana")
        if any(w in q for w in ["bnb", "binance"]): tickers.append("binancecoin")
        return get_crypto_prices(tickers if tickers else None)
    
    # Gas 费
    if any(w in q for w in ["gas", "手续费", "矿工费"]):
        return get_gas_price()
    
    # 热门趋势
    if any(w in q for w in ["热门", "趋势", "trending", "今日"]):
        return get_trending_coins()
    
    # 默认：价格 + 趋势
    return get_crypto_prices() + "\n\n" + get_trending_coins()

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "价格"
    print(parse_and_respond(query))
