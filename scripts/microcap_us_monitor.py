#!/usr/bin/env python3
"""
美股微盘股每日监测脚本 — 免费版
数据来源: Stooq（价格）+ Perplexity sonar-pro（分析）
2026-03-19 重构：移除所有 AISA Financial API 调用（价格/指标）
"""

import os
os.environ["https_proxy"] = "http://10.59.78.158:3128"
os.environ["http_proxy"] = "http://10.59.78.158:3128"
os.environ["HTTPS_PROXY"] = "http://10.59.78.158:3128"
os.environ["HTTP_PROXY"] = "http://10.59.78.158:3128"
import json, subprocess, csv, io, time
from datetime import datetime

# AISA_KEY 已不可用（代理403），改用 catclaw-search 替代 Perplexity

WATCHLIST = {
    "热门投机/Meme": ["GME", "AMC", "SPCE", "CODA"],
    "小盘科技": ["SNDX", "NVTS", "INPX"],
    "生物医药小盘": ["ALDX", "HIMS"],
}

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

def get_perplexity_analysis():
    """catclaw-search 深度分析（替代 Perplexity sonar-pro）"""
    today = datetime.now().strftime("%Y-%m-%d")
    queries = [
        f"microcap stock FDA catalyst earnings announcement {today}",
        f"small cap stock insider buying SEC Form 4 {today}",
        f"penny stock news catalyst {today}"
    ]
    all_results = []
    citations = []
    for q in queries:
        try:
            r = subprocess.run(
                ['python3', '/app/skills/catclaw-search/scripts/catclaw_search.py',
                 'search', q, '-s', 'bing', '-n', '4'],
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
                            all_results.append(f"• {title}: {snippet}")
                        if url:
                            citations.append(url)
                except json.JSONDecodeError:
                    all_results.append(r.stdout.strip()[:300])
        except Exception as e:
            pass

    content = "\n".join(all_results) if all_results else "暂无数据（catclaw-search无结果）"
    return content, citations[:3]

def build_report():
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    lines = [f"🦐📊 **美股微盘股日报** | {now}\n", "━━━━━━━━━━━━━━━━━━", "📈 **微盘股价格扫描**\n"]

    all_stocks = []
    for category, tickers in WATCHLIST.items():
        lines.append(f"**{category}**")
        for ticker in tickers:
            snap = get_price_stooq(ticker)
            price = snap.get('price', 0)
            chg = snap.get('chg', 0)
            if price:
                emoji = "🔴" if chg < -3 else "🟢" if chg > 3 else "⚪"
                lines.append(f"  {emoji} **{ticker}**: ${price:.2f} ({chg:+.2f}%)")
                all_stocks.append((ticker, chg, price))
            else:
                lines.append(f"  ❓ **{ticker}**: 数据不可用")
            time.sleep(0.1)
        lines.append("")

    if all_stocks:
        sorted_s = sorted(all_stocks, key=lambda x: x[1], reverse=True)
        lines.append("**🏆 今日涨幅TOP3**")
        for t, pct, p in sorted_s[:3]:
            if pct > 0:
                lines.append(f"  🚀 {t}: ${p:.2f} (+{pct:.2f}%)")
        lines.append("**💀 今日跌幅TOP3**")
        for t, pct, p in sorted_s[-3:]:
            if pct < 0:
                lines.append(f"  📉 {t}: ${p:.2f} ({pct:.2f}%)")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("🧠 **市场深度分析（catclaw-search）**\n")
    analysis, citations = get_perplexity_analysis()
    if analysis:
        lines.append(analysis[:1500])
    if citations:
        lines.append("\n📚 **数据来源**")
        for i, c in enumerate(citations[:3], 1):
            lines.append(f"[{i}] {c}")

    lines.append(f"\n---\n🦐 小蓝虾 | {now}")
    return "\n".join(lines)

if __name__ == "__main__":
    report = build_report()
    print(report)
    with open("/root/.openclaw/workspace/memory/microcap-report-latest.txt", "w") as f:
        f.write(report)
    print("\n✅ 报告已保存")
