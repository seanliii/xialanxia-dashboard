#!/usr/bin/env python3
"""
全量扫描微盘股列表，验证 Stooq 能获取到价格，保存到 verified_microcap.json
每周运行一次更新列表。
2026-03-19 重构：从 AISA Financial 改为 Stooq（免费）
"""
import subprocess, json, csv, io, os, time
from datetime import datetime

DATA_DIR = "/root/.openclaw/workspace/data"

def get_price_stooq(stock: dict) -> dict:
    ticker = stock["symbol"]
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
            if close > 0:
                return {**stock, "price": close, "chg": round(chg, 2)}
    except:
        pass
    return None

def run():
    input_file = f"{DATA_DIR}/microcap_tickers.json"
    if not os.path.exists(input_file):
        print(f"❌ {input_file} 不存在")
        return

    with open(input_file) as f:
        all_stocks = json.load(f)

    print(f"[{datetime.now().strftime('%H:%M')}] 开始 Stooq 验证 {len(all_stocks)} 只...")

    results = []
    for i, stock in enumerate(all_stocks):
        res = get_price_stooq(stock)
        if res:
            results.append(res)
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(all_stocks)}... 有效: {len(results)}")
        time.sleep(0.05)  # Stooq rate limit

    print(f"[{datetime.now().strftime('%H:%M')}] 完成！有效: {len(results)}/{len(all_stocks)}")

    results.sort(key=lambda x: x.get("market_cap", 0), reverse=True)

    out_path = f"{DATA_DIR}/verified_microcap.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"已保存 {len(results)} 只到 {out_path}")
    print("市值分布:")
    for lo, hi in [(200, 300), (100, 200), (50, 100), (10, 50), (0, 10)]:
        cnt = sum(1 for r in results if lo * 1e6 <= r.get("market_cap", 0) < hi * 1e6)
        print(f"  ${lo}M-${hi}M: {cnt}只")

if __name__ == "__main__":
    run()
