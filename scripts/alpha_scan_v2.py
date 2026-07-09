#!/usr/bin/env python3
"""Alpha scan v2 - SEC EDGAR (insiders) + web_fetch via skill for prices"""
import json, urllib.request, time
from datetime import date, timedelta

TICKERS = ["GME","HIMS","SNDX","NVTS","ALDX","SPCE","SOFI","RKLB","JOBY","ACHR"]

def get_insider_sec(ticker, days=30):
    """SEC EDGAR Form 4 - no proxy needed"""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    url = (
        "https://efts.sec.gov/LATEST/search-index?q=%%22%s%%22"
        "&dateRange=custom&startdt=%s&forms=4" % (ticker, cutoff)
    )
    req = urllib.request.Request(url, headers={"User-Agent": "XiaLanXia/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read())
        hits = data.get("hits", {}).get("hits", [])[:10]
        return hits
    except Exception as e:
        return []

def get_insider_details(hit):
    """Parse SEC hit for insider info"""
    src = hit.get("_source", {})
    name = src.get("file_name", "")
    dt = src.get("file_date", "")
    return {"name": name, "date": dt}

# Collect insider data
print("🦐 Alpha 机会扫描 v2")
print("=" * 55)
print("数据来源: SEC EDGAR (内部人) + 价格(Stooq/AISA 不可用)")
print()

results = []
for t in TICKERS:
    insiders = get_insider_sec(t, days=30)
    
    score = 0
    signals = []
    detail_strs = []
    
    if insiders:
        score += 3
        signals.append("内部人Form4(%d条,近30天)" % len(insiders))
        for h in insiders[:3]:
            d = get_insider_details(h)
            detail_strs.append("%s(%s)" % (d["name"][:60], d["date"]))
    
    results.append({"t": t, "score": score, "signals": signals, "insider_count": len(insiders), "insider_details": detail_strs})
    
    status = "✅" if insiders else "⬜"
    sigs = " | ".join(signals) or "无信号"
    print("%s %-6s [%+d]  %s" % (status, t, score, sigs))
    if detail_strs:
        for d in detail_strs[:2]:
            print("   └─ %s" % d)
    time.sleep(0.3)

results.sort(key=lambda x: x["score"], reverse=True)

print()
print("🎯 重点关注 (内部人买入):")
for r in results:
    if r["score"] >= 3:
        print("  ⭐ %s: %s" % (r["t"], ", ".join(r["signals"])))
        for d in r["insider_details"][:3]:
            print("     └─ %s" % d)

print()
print("📊 全部标的内部人活跃度:")
for r in results:
    bar = "█" * min(r["insider_count"], 10)
    print("  %-6s %s %d条" % (r["t"], bar, r["insider_count"]))

# Summary
strong = [r for r in results if r["score"] >= 3]
strong_str = ", ".join([r["t"] for r in strong]) if strong else "无"
total_insider = sum(r["insider_count"] for r in results)
print()
print("DASHBOARD_SUMMARY: 强力信号=%s | 内部人活跃度=%d条 | 数据源=SEC_EDGAR_only" % (strong_str, total_insider))
