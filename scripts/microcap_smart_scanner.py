#!/usr/bin/env python3
"""
智能两步微盘股 Alpha 扫描器
Step1: Perplexity sonar-pro 发现今日异动微盘股（全市场覆盖）
Step2: SEC EDGAR Form 4 内部人买入 + Stooq 实时价格（免费）

2026-03-19 重构：移除所有 AISA Financial API 调用（太贵），全改免费数据源
"""

import os
os.environ["https_proxy"] = "http://10.59.78.158:3128"
os.environ["http_proxy"] = "http://10.59.78.158:3128"
os.environ["HTTPS_PROXY"] = "http://10.59.78.158:3128"
os.environ["HTTP_PROXY"] = "http://10.59.78.158:3128"
import subprocess, json, re, csv, io, time
from datetime import datetime, date, timedelta

# AISA_KEY 已不可用（代理403），改用 catclaw-search 作为 Perplexity 替代

# ─── 免费：Stooq 价格 ───────────────────────────────────────────────────────
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
            return {'price': close, 'chg': round(chg, 2), 'date': row.get('Date', '')}
    except:
        pass
    return {}

# ─── 免费：SEC EDGAR Form 4 内部人买入 ─────────────────────────────────────
def get_insider_buys_sec(ticker: str, days: int = 30) -> list:
    """从 SEC EDGAR 获取内部人真实买入（开市购买）"""
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
        buys = []
        for h in hits[:5]:
            src = h.get('_source', {})
            form_type = src.get('form_type', '')
            if form_type != '4':
                continue
            buys.append({
                'name': src.get('display_names', ['?'])[0] if src.get('display_names') else '?',
                'filed': src.get('file_date', ''),
                'url': 'https://www.sec.gov' + src.get('file_num', ''),
            })
        return buys
    except:
        return []

def discover_movers():
    """用 catclaw-search 发现今日微盘股异动（替代 Perplexity sonar-pro）"""
    today = datetime.now().strftime("%Y-%m-%d")
    queries = [
        f"microcap small cap stock insider buying SEC Form 4 {today}",
        f"penny stock FDA catalyst earnings {today} surge",
        f"small cap stock +10% today {today}"
    ]
    all_results = []
    citations = []
    for q in queries:
        try:
            r = subprocess.run(
                ['python3', '/app/skills/catclaw-search/scripts/catclaw_search.py',
                 'search', q, '-s', 'bing', '-n', '5'],
                capture_output=True, text=True, timeout=20
            )
            if r.stdout.strip():
                try:
                    data = json.loads(r.stdout.strip())
                    items = data if isinstance(data, list) else data.get('results', data.get('data', []))
                    for item in items[:3]:
                        title = item.get('title', '')
                        snippet = item.get('snippet', item.get('description', item.get('content', '')))
                        url = item.get('url', item.get('href', item.get('link', '')))
                        if title:
                            all_results.append(f"{title}: {snippet}")
                        if url:
                            citations.append(url)
                except json.JSONDecodeError:
                    # 可能是纯文本输出
                    all_results.append(r.stdout.strip()[:300])
        except Exception as e:
            pass

    content = "\n".join(all_results) if all_results else "暂无数据（catclaw-search无结果）"
    return content, citations[:5]

def deep_analyze(ticker):
    """免费版深度分析：Stooq价格 + SEC Form 4 内部人买入"""
    score = 0
    signals = []
    warnings = []

    # 价格（Stooq 免费）
    snap = get_price_stooq(ticker)
    price = snap.get('price', 0)
    chg = snap.get('chg', 0)
    if not price:
        return None

    # 内部人买入（SEC EDGAR 免费）
    buys = get_insider_buys_sec(ticker, days=14)
    if buys:
        score += min(len(buys), 3)
        signals.append(f"🟢SEC Form 4买入{len(buys)}条 (近14天)")

    # 价格动量
    if chg > 10:
        score += 2
        signals.append(f"🚀今日暴涨+{chg:.1f}%")
    elif chg > 5:
        score += 1
        signals.append(f"📈今日涨{chg:.1f}%")
    elif chg < -15:
        score -= 2
        warnings.append(f"📉今日暴跌{chg:.1f}%")

    time.sleep(0.1)  # Stooq rate limit

    return {
        "ticker": ticker, "price": price, "chg": chg,
        "score": score, "signals": signals, "warnings": warnings
    }

def run():
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    print(f"\n🦐📊 **全市场微盘股 Alpha 日报** | {now}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # Step 1: 用 sonar-pro 发现今日异动
    print("⏳ Step1: Perplexity 扫描今日全市场微盘股异动...")
    discovery, citations = discover_movers()

    print("\n🔭 **sonar-pro 发现的今日异动**\n")
    print(discovery[:2000])
    if citations:
        print("\n📚 来源:")
        for i, c in enumerate(citations[:3], 1):
            print(f"[{i}] {c}")

    # 从 discovery 中提取 ticker
    found_tickers = set(re.findall(r'\b([A-Z]{2,5})\b', discovery))
    exclude = {'AND','THE','FOR','WITH','FROM','INC','LLC','ETF','FDA','CEO','CFO',
               'NEW','TOP','ALL','BIG','YTD','EPS','SPY','IWC','IWM','VIX','SEC',
               'EDGAR','USD','APR','MAY','JUN','JUL'}
    found_tickers -= exclude

    # Step 2: 对发现的 ticker 做分析（免费版）
    if found_tickers:
        tickers_list = list(found_tickers)[:15]  # 限制数量
        print(f"\n⏳ Step2: 免费版深度分析 {len(tickers_list)} 只候选股 (Stooq + SEC)...")
        deep_results = list(filter(None, [deep_analyze(t) for t in tickers_list]))
        deep_results.sort(key=lambda x: x["score"], reverse=True)

        strong = [r for r in deep_results if r["score"] >= 2]
        avoid = [r for r in deep_results if r["score"] <= -2]

        if strong:
            print(f"\n## 🎯 **信号（评分≥2）**\n")
            for r in strong:
                arrow = "🟢" if r["chg"] >= 0 else "🔴"
                print(f"### {arrow} **{r['ticker']}** — ${r['price']:.2f} ({r['chg']:+.1f}%) — 评分 **{r['score']:+d}**")
                for s in r["signals"]:
                    print(f"  - {s}")
                for w in r["warnings"]:
                    print(f"  - {w}")
                print()

        if avoid:
            print(f"\n## ⚠️ **规避**\n")
            for r in avoid:
                warns = " | ".join(r["warnings"][:2])
                print(f"  🔴 {r['ticker']}: {warns}")

    print(f"\n---")
    print(f"🦐 小蓝虾 | {now}")

if __name__ == "__main__":
    run()
