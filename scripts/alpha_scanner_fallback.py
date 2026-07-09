#!/usr/bin/env python3
"""
Alpha 机会扫描器 — 带 AISA 回退
数据来源: Stooq（价格）→ AISA Financial API 回退 + SEC EDGAR（内部人买入）
"""
import os, subprocess, json, csv, io, time
from datetime import datetime, date, timedelta

# Use proxy for outbound
for k in ["https_proxy","http_proxy","HTTPS_PROXY","HTTP_PROXY"]:
    os.environ[k] = "http://10.59.78.158:3128"

TICKERS = ["GME","HIMS","SNDX","NVTS","ALDX","SPCE","SOFI","RKLB","JOBY","ACHR"]
AISA_KEY = "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41"

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

def get_price_aisa(ticker: str) -> dict:
    """Fallback: AISA Financial API"""
    try:
        r = subprocess.run(
            ['curl', '-s', '--max-time', '10',
             f'https://api.aisa.one/apis/v1/financial/company/facts?ticker={ticker}',
             '-H', f'Authorization: Bearer {AISA_KEY}'],
            capture_output=True, text=True, timeout=12)
        d = json.loads(r.stdout)
        data = d.get('data', {})
        price = data.get('price', 0)
        if price:
            return {'price': float(price), 'chg': 0}  # AISA doesn't return intraday change
    except:
        pass
    return {}

def get_insider_sec(ticker: str, days: int = 30) -> list:
    """SEC EDGAR Form 4 内部人买入"""
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

def analyze(ticker):
    score = 0
    signals = []

    snap = get_price_stooq(ticker)
    if not snap:
        snap = get_price_aisa(ticker)
    price = snap.get('price', 0)
    if not price:
        return None
    change = snap.get('chg', 0)

    # 内部人买入（SEC EDGAR 免费）
    insider_hits = get_insider_sec(ticker, days=30)
    if insider_hits:
        score += 3
        signals.append(f"内部人Form4活跃({len(insider_hits)}条,近30天)")

    # 价格动量信号
    if change > 10:
        score += 2
        signals.append(f"今日暴涨+{change:.1f}%")
    elif change > 5:
        score += 1
        signals.append(f"今日涨{change:.1f}%")
    elif change < -15:
        score -= 2
        signals.append(f"今日暴跌{change:.1f}%⚠️")

    time.sleep(0.1)
    return {"t": ticker, "price": price, "chg": change, "score": score, "signals": signals}

print("🦐 Alpha 机会扫描 | " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n")
res = list(filter(None, [analyze(t) for t in TICKERS]))
res.sort(key=lambda x: x["score"], reverse=True)

for r in res:
    arrow = "🟢" if r["chg"] > 0 else "🔴"
    sigs = " | ".join(r["signals"]) or "无信号"
    print(f"{arrow} {r['t']:<6} \${r['price']:<8.2f} {r['chg']:+.1f}%  [{r['score']:+d}]  {sigs}")

print("\n🎯 重点关注:")
for r in res:
    if r["score"] >= 3:
        print(f"  ⭐ {r['t']}: {', '.join(r['signals'])}")
