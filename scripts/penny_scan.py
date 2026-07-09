#!/usr/bin/env python3
"""激进账户penny stock / 小微股异动扫描"""
import sys, math
sys.path.insert(0, '/root/.openclaw/workspace/scripts')

print("🔍 激进账户新信号扫描 — 2026-07-08")
print("=" * 60)
print("目标：近5日涨幅超100%小微股 / <$5000万低价股 / OTC异动 / 并购壳股")
print()

try:
    import yfinance as yf
except ImportError:
    print("❌ yfinance not available")
    sys.exit(0)

penny_watchlist = [
    "ILAG","OXBR","APLD","STRK","NXTT","LGMK","NIVF","ALAR","REVB",
    "QUBT","ASTR","MIRA","LUNR","MULN","GOTU","BBAI","SOUN","BTAI","IMVT",
    "METC","TOI","ROLR","MLEC","IVP","KULR","AVBP","CXAI","SNAL","ALVO",
    "SPWH","JAGX","LGVN","ARQQ","NRXP","APLM","AMC","GOEV","WULF",
    "SOS","PHUN","CEI","BBIG","CYDY","DPLS","SIRC","HMBL","ENZC",
    "SYSX","GVSI","HSTO","VBHI","USDP","PLPL","SANP","TRKA",
    "BTBT","RIOT","MARA","CLSK","HUT","BITF","CIFR","HIVE",
    "NVDA","TSLA","PLTR","SOFI","ASTS","RKLB","CHPT","LCID",
    "IREN","VST","HBAN","CENN","BBRW","PMCB","SAIT","OUST",
    "GNS","MCOM","TTOO","ATNF","NUKK","RDBX","FFIE","GME"
]

print(f"📡 扫描 {len(penny_watchlist)} 只候选股...")
results = []

for ticker in penny_watchlist:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if len(hist) < 2:
            continue
        price = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2])
        week_ago = float(hist["Close"].iloc[0])

        if price <= 0 or prev <= 0 or week_ago <= 0:
            continue

        day_change = (price / prev - 1) * 100
        week_change = (price / week_ago - 1) * 100
        volume = float(hist["Volume"].iloc[-1]) if not math.isnan(hist["Volume"].iloc[-1]) else 0
        avg_vol = float(hist["Volume"].mean()) if len(hist) > 0 else 0
        vol_ratio = volume / avg_vol if avg_vol > 0 else 0

        if price >= 0.01 and (week_change > 50 or day_change > 30 or vol_ratio > 3 or price < 1):
            try:
                info = t.info
                market_cap = info.get("marketCap", 0) or 0
            except:
                market_cap = 0
            mcap_mil = round(market_cap / 1e6, 2) if market_cap > 0 else "N/A"
            results.append({
                "ticker": ticker,
                "price": round(price, 4),
                "day_change": round(day_change, 1),
                "week_change": round(week_change, 1),
                "volume": int(volume),
                "vol_ratio": round(vol_ratio, 1),
                "mcap_mil": mcap_mil
            })
    except:
        pass

results.sort(key=lambda x: x["week_change"], reverse=True)

print(f"\n🔥 发现 {len(results)} 只异动股：")
print("-" * 80)
for r in results[:20]:
    mcap_str = f"${r['mcap_mil']}M" if r["mcap_mil"] != "N/A" else "N/A"
    vol_flag = " 🔥暴量" if r["vol_ratio"] > 3 else ""
    week_flag = " 🚀5日+" if r["week_change"] > 100 else ""
    penny_flag = " 💎Penny" if r["price"] < 1 else ""
    print(f"  {r['ticker']:6} | ${r['price']:>8.4f} | 日{r['day_change']:>+6.1f}% | 5日{r['week_change']:>+6.1f}% | 量比{r['vol_ratio']:>5.1f}x | 市值{mcap_str:>10}{vol_flag}{week_flag}{penny_flag}")

print()
print("=" * 60)
print("💡 激进账户关注建议（Top 5）：")
for r in results[:5]:
    mcap_str = f"市值{r['mcap_mil']}M" if r["mcap_mil"] != "N/A" else "市值N/A"
    if r["price"] < 1:
        print(f"  • {r['ticker']} @ ${r['price']:.4f} — penny stock，{mcap_str}，5日{r['week_change']:.0f}%")
    elif r["week_change"] > 100:
        print(f"  • {r['ticker']} @ ${r['price']:.2f} — 5日暴涨{r['week_change']:.0f}%，量比{r['vol_ratio']:.1f}x")
    elif r["vol_ratio"] > 3:
        print(f"  • {r['ticker']} @ ${r['price']:.2f} — 突然暴量，量比{r['vol_ratio']:.1f}x，{mcap_str}")
    else:
        print(f"  • {r['ticker']} @ ${r['price']:.2f} — 日涨幅{r['day_change']:.0f}%，{mcap_str}")

print()
print("⚠️  注意：penny stock和OTC股风险极高，建议单只<5%仓位，严格止损-15%")
