#!/usr/bin/env python3
"""
Alpha 机会扫描器 — 应急版 (SEC数据可用，Stooq暂时不可用)
2026-04-18
"""
import os
os.environ["https_proxy"] = "http://10.59.78.158:3128"
os.environ["http_proxy"] = "http://10.59.78.158:3128"
import subprocess, json
from datetime import datetime, date, timedelta

TICKERS = ["GME","HIMS","SNDX","NVTS","ALDX","SPCE","SOFI","RKLB","JOBY","ACHR"]

def get_insider_sec(ticker: str, days: int = 30) -> list:
    """SEC EDGAR Form 4 内部人交易"""
    try:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        r = subprocess.run(
            ['curl', '-s', '--max-time', '10',
             f'https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom'
             f'&startdt={cutoff}&forms=4',
             '-H', 'User-Agent: XiaLanXia/1.0 admin@example.com'],
            capture_output=True, text=True, timeout=12)
        data = json.loads(r.stdout)
        hits = data.get('hits', {}).get('hits', [])
        # 过滤出近30天的
        recent = []
        for h in hits:
            src = h.get('_source', {})
            file_date = src.get('file_date', '')
            if file_date >= cutoff:
                recent.append(src)
        return recent[:5]
    except Exception as e:
        return []

print("🦐 Alpha 机会扫描 | " + datetime.now().strftime("%Y-%m-%d %H:%M"))
print("⚠️  价格数据服务暂时不可用，仅显示内部人交易信号\n")

results = []
all_insider = {}
for t in TICKERS:
    insider = get_insider_sec(t, days=90)  # 扩展到90天
    all_insider[t] = insider
    if insider:
        results.append({
            'ticker': t,
            'count': len(insider),
            'recent': insider[0].get('file_date', 'N/A') if insider else 'N/A'
        })

print("📊 近90天内部人交易活跃标的：")
if results:
    for r in sorted(results, key=lambda x: x['count'], reverse=True)[:5]:
        print(f"   • {r['ticker']}: {r['count']}条Form4, 最近: {r['recent']}")
else:
    print("   无显著内部人交易信号")

print("\n🎯 重点关注：")
for r in results[:3]:
    print(f"   ⭐ {r['ticker']}: 近90天{r['count']}条内部人交易披露")

print("\n⚠️ 数据说明：")
print("   • 价格数据源(Stooq)暂时不可用")
print("   • Form4 = 内部人交易披露（买入/卖出/期权行权）")
print("   • 数据来自SEC EDGAR官方API")
