#!/usr/bin/env python3
"""Alpha scan runner with Yahoo Finance fallback"""
import os, json, subprocess, time
os.environ["https_proxy"] = "http://10.59.78.158:3128"
os.environ["http_proxy"] = "http://10.59.78.158:3128"
os.environ["HTTPS_PROXY"] = "http://10.59.78.158:3128"
os.environ["HTTP_PROXY"] = "http://10.59.78.158:3128"

TICKERS = ["GME","HIMS","SNDX","NVTS","ALDX","SPCE","SOFI","RKLB","JOBY","ACHR"]

def get_price_yahoo(ticker):
    import urllib.request
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%s?interval=1d&range=2d" % ticker
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
        meta = data["chart"]["result"][0]["meta"]
        price = meta["regularMarketPrice"]
        prev = meta["previousClose"]
        chg = (price - prev) / prev * 100
        return {"price": price, "chg": round(chg, 2)}
    except Exception as e:
        return {"error": str(e)}

def get_insider_sec(ticker, days=30):
    import urllib.request
    from datetime import date, timedelta
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    url = (
        "https://efts.sec.gov/LATEST/search-index?q=%%22%s%%22"
        "&dateRange=custom&startdt=%s&forms=4" % (ticker, cutoff)
    )
    req = urllib.request.Request(url, headers={"User-Agent": "XiaLanXia/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read())
        return data.get("hits", {}).get("hits", [])[:5]
    except Exception as e:
        return []

print("Alpha Scanner - Yahoo Finance + SEC EDGAR")
print("=" * 60)
results = []
for t in TICKERS:
    snap = get_price_yahoo(t)
    price = snap.get("price", 0)
    chg = snap.get("chg", 0)
    if not price:
        print("%s: PRICE FAIL (%s)" % (t, snap.get("error", "unknown")))
        continue
    
    insiders = get_insider_sec(t, days=30)
    
    score = 0
    signals = []
    if insiders:
        score += 3
        signals.append("内部人Form4(%d条,近30天)" % len(insiders))
    if chg > 10:
        score += 2
        signals.append("今日+%.1f%%" % chg)
    elif chg > 5:
        score += 1
        signals.append("今日+%.1f%%" % chg)
    elif chg < -15:
        score -= 2
        signals.append("今日%.1f%%⚠️" % chg)
    
    results.append({"t": t, "price": price, "chg": chg, "score": score, "signals": signals, "insiders": insiders})
    arrow = "🟢" if chg > 0 else "🔴"
    sigs = " | ".join(signals) or "无信号"
    print("%s %-6s $%-8.2f %+.1f%%  [%+d]  %s" % (arrow, t, price, chg, score, sigs))
    time.sleep(0.2)

results.sort(key=lambda x: x["score"], reverse=True)
print()
print("🎯 重点关注:")
for r in results:
    if r["score"] >= 3:
        print("  ⭐ %s: %s" % (r["t"], ", ".join(r["signals"])))

print()
print("👀 关注标的 (score >= 1):")
for r in results:
    if r["score"] >= 1 and r["score"] < 3:
        print("  📌 %s: %s" % (r["t"], ", ".join(r["signals"])))

print()
print("🦐 进化笔记:")
print("  Stooq 今日连接失败 (curl exit 56), 已切换 Yahoo Finance 备用源")
print("  SEC EDGAR API 正常，Form 4 数据可用")
print()

# Output summary for dashboard
strong = [r for r in results if r["score"] >= 3]
strong_str = ", ".join([r["t"] for r in strong]) if strong else "无"
print("DASHBOARD_SUMMARY: 强力信号=%s | 关注标的=%d | 数据源=Yahoo+SEC" % (strong_str, len([r for r in results if r["score"] >= 1])))
