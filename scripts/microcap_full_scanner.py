#!/usr/bin/env python3
"""
全市场美股微盘股 Alpha 扫描器（市值 < $3亿）— 免费版
策略:
  Step1: Stooq 批量价格（免费，无限制）
  Step2: 筛出今日异动股（涨跌>5%）
  Step3: SEC EDGAR Form 4 内部人买入验证
  Step4: 评分排序，输出 Top 机会

2026-03-19 重构：移除所有 AISA Financial API 调用
"""

import subprocess, json, csv, io, os, time
from datetime import datetime, date, timedelta

DATA_DIR = "/root/.openclaw/workspace/data"
TICKER_FILE = f"{DATA_DIR}/microcap_tickers.json"

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

def get_insider_sec(ticker: str, days: int = 14) -> int:
    """返回 SEC Form 4 近期文件数量（用于评分）"""
    try:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        r = subprocess.run(
            ['curl', '-s', '--max-time', '10',
             f'https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom'
             f'&startdt={cutoff}&forms=4',
             '-H', 'User-Agent: XiaLanXia/1.0 admin@example.com'],
            capture_output=True, text=True, timeout=12)
        data = json.loads(r.stdout)
        return len(data.get('hits', {}).get('hits', []))
    except:
        return 0

def run():
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    print(f"🦐🔍 全市场微盘股 Alpha 扫描 | {now}")
    print(f"数据来源：Stooq（免费）+ SEC EDGAR（免费）\n")

    if not os.path.exists(TICKER_FILE):
        print("❌ ticker 列表不存在，请先运行 update_microcap_list.py")
        return

    with open(TICKER_FILE) as f:
        all_stocks = json.load(f)

    tickers_meta = {s["symbol"]: s for s in all_stocks}
    all_tickers = list(tickers_meta.keys())[:200]  # 每次最多200只，避免过慢

    print(f"📋 本批扫描：{len(all_tickers)} 只\n")

    # Step 1: 批量价格
    price_results = []
    for ticker in all_tickers:
        snap = get_price_stooq(ticker)
        if snap.get('price', 0):
            price_results.append({
                "ticker": ticker,
                "price": snap['price'],
                "chg": snap['chg'],
            })
        time.sleep(0.05)  # Stooq rate limit

    print(f"✅ 价格扫描：{len(price_results)}/{len(all_tickers)} 只")

    # Step 2: 筛今日异动
    movers = [r for r in price_results if abs(r["chg"]) >= 5]
    movers.sort(key=lambda x: abs(x["chg"]), reverse=True)
    candidates = movers[:20]

    print(f"📌 今日异动候选：{len(candidates)} 只（涨跌≥5%）\n")

    # Step 3: SEC Form 4 验证
    for r in candidates:
        r['insider_cnt'] = get_insider_sec(r['ticker'], days=14)
        r['score'] = (min(r['insider_cnt'], 3) +
                      (2 if r['chg'] > 10 else 1 if r['chg'] > 5 else 0))
        time.sleep(0.1)

    candidates.sort(key=lambda x: x['score'], reverse=True)

    # 输出
    print("=" * 60)
    print(f"🦐📊 **全市场微盘股 Alpha 日报** | {now}")
    print("=" * 60)

    print("\n📈 **今日涨幅 TOP5**")
    for r in sorted(price_results, key=lambda x: x['chg'], reverse=True)[:5]:
        meta = tickers_meta.get(r['ticker'], {})
        print(f"  🚀 {r['ticker']}: ${r['price']:.2f} (+{r['chg']:.1f}%)  {meta.get('name','')[:30]}")

    print("\n📉 **今日跌幅 TOP5**")
    for r in sorted(price_results, key=lambda x: x['chg'])[:5]:
        meta = tickers_meta.get(r['ticker'], {})
        print(f"  💀 {r['ticker']}: ${r['price']:.2f} ({r['chg']:.1f}%)  {meta.get('name','')[:30]}")

    strong = [r for r in candidates if r['score'] >= 4]
    if strong:
        print(f"\n## 🎯 **强力信号（评分≥4，内部人+价格双确认）**\n")
        for r in strong:
            arrow = "🟢" if r['chg'] >= 0 else "🔴"
            print(f"  {arrow} **{r['ticker']}** ${r['price']:.2f} ({r['chg']:+.1f}%) — "
                  f"Form4={r['insider_cnt']}条 — 评分{r['score']:+d}")

    print(f"\n---\n🦐 小蓝虾 | {now}")

if __name__ == "__main__":
    run()
