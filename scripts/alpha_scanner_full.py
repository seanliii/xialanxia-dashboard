#!/usr/bin/env python3
"""
美股 Alpha 机会扫描器 — 免费版
数据来源: Stooq（价格）+ SEC EDGAR Form 4（内部人买入）
2026-03-19 重构：移除所有 AISA Financial API 调用（机构持仓/分析师预期/基本面指标）
"""

import os
os.environ["https_proxy"] = "http://10.59.78.158:3128"
os.environ["http_proxy"] = "http://10.59.78.158:3128"
os.environ["HTTPS_PROXY"] = "http://10.59.78.158:3128"
os.environ["HTTP_PROXY"] = "http://10.59.78.158:3128"
import subprocess, json, csv, io, time
from datetime import datetime, date, timedelta

WATCHLIST = {
    "Meme/热门投机": ["GME", "AMC", "SPCE"],
    "科技小盘":      ["NVTS", "SNDX", "SOFI", "RKLB", "ACHR", "JOBY"],
    "生物医药":      ["ALDX", "HIMS", "CLOV"],
    "其他关注":      ["MVIS", "WKHS", "NKLA"],
}

ALL_TICKERS = [t for cats in WATCHLIST.values() for t in cats]

def get_price_stooq(ticker: str) -> dict:
    sym = ticker.lower() + ".us"
    try:
        r = subprocess.run(
            ['curl', '-s', '--max-time', '6',
             f'https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv'],
            capture_output=True, text=True, timeout=8)
        reader = csv.DictReader(io.StringIO(r.stdout))
        for row in reader:
            close = float(row.get('Close') or 0)
            open_ = float(row.get('Open') or close)
            chg = (close - open_) / open_ * 100 if open_ else 0
            return {'price': close, 'chg': round(chg, 2)}
    except:
        pass
    return {}

def get_insider_sec(ticker: str, days: int = 30) -> list:
    """SEC EDGAR Form 4 内部人买入（免费）"""
    try:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        r = subprocess.run(
            ['curl', '-s', '--max-time', '10',
             f'https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom'
             f'&startdt={cutoff}&forms=4',
             '-H', 'User-Agent: XiaLanXia/1.0 admin@example.com'],
            capture_output=True, text=True, timeout=12)
        data = json.loads(r.stdout)
        return data.get('hits', {}).get('hits', [])[:5]
    except:
        return []

def analyze_ticker(ticker):
    score = 0
    signals = []
    warnings = []

    snap = get_price_stooq(ticker)
    price = snap.get('price', 0)
    if not price:
        return None
    change_pct = snap.get('chg', 0)

    # 内部人买入（SEC EDGAR 免费）
    insider_hits = get_insider_sec(ticker, days=30)
    if insider_hits:
        score += min(len(insider_hits), 3)
        signals.append(f"🟢 SEC Form4活跃({len(insider_hits)}条,近30天)")

    # 价格动量
    if change_pct > 10:
        score += 2
        signals.append(f"🚀 今日暴涨+{change_pct:.1f}%")
    elif change_pct > 5:
        score += 1
        signals.append(f"📈 今日涨{change_pct:.1f}%")
    elif change_pct < -15:
        score -= 2
        warnings.append(f"💀 今日暴跌{change_pct:.1f}%")

    time.sleep(0.08)

    return {
        "ticker": ticker,
        "price": price,
        "change_pct": change_pct,
        "score": score,
        "signals": signals,
        "warnings": warnings,
    }

def run_scan():
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    print(f"🦐🔍 **Alpha 机会扫描** | {now}\n")
    print("*数据来源：Stooq（价格）+ SEC EDGAR Form 4（内部人买入）*\n")

    results = list(filter(None, [analyze_ticker(t) for t in ALL_TICKERS]))
    results.sort(key=lambda x: x["score"], reverse=True)

    strong = [r for r in results if r["score"] >= 3]
    moderate = [r for r in results if 1 <= r["score"] < 3]
    avoid = [r for r in results if r["score"] <= -2]

    if strong:
        print("## 🎯 强力买入信号（评分≥3）\n")
        for r in strong:
            arrow = "🟢" if r["change_pct"] >= 0 else "🔴"
            print(f"### {arrow} **{r['ticker']}** — ${r['price']:.2f} ({r['change_pct']:+.1f}%) — 评分 **{r['score']:+d}**")
            for s in r["signals"]:
                print(f"  - {s}")
            for w in r["warnings"]:
                print(f"  - {w}")
            print()

    if moderate:
        print("## 👀 关注标的（评分1-2）\n")
        for r in moderate:
            arrow = "🟢" if r["change_pct"] >= 0 else "🔴"
            sigs = " | ".join(r["signals"][:2])
            print(f"  {arrow} **{r['ticker']}** ${r['price']:.2f} ({r['change_pct']:+.1f}%) [{r['score']:+d}]  {sigs}")
        print()

    if avoid:
        print("## ⚠️ 规避标的\n")
        for r in avoid:
            warns = " | ".join(r["warnings"][:2])
            print(f"  🔴 **{r['ticker']}** ${r['price']:.2f} [{r['score']:+d}]  {warns}")
        print()

    print("---")
    print(f"🦐 小蓝虾 | {now}")

if __name__ == "__main__":
    run_scan()
