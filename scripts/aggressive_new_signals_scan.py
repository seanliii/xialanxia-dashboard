#!/usr/bin/env python3
"""
激进账户新信号扫描 — Penny Stock / 小微股异动 / 并购壳股
"""
import json, urllib.request as ur, urllib.parse as up, csv, io, subprocess, os
from datetime import datetime, date, timedelta

AISA_KEY = "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41"
TAVILY_KEY = "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"

def tavily_search(query, max_results=5):
    """Tavily搜索"""
    try:
        payload = json.dumps({
            "api_key": TAVILY_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results
        }).encode()
        req = ur.Request("https://api.tavily.com/search", data=payload,
                         headers={"Content-Type": "application/json"}, method="POST")
        with ur.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return data.get("results", [])
    except Exception as e:
        print(f"   Tavily error: {e}")
        return []

def get_price_yahoo(ticker):
    """从Yahoo获取实时价格"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
        req = ur.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with ur.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        result = data['chart']['result'][0]
        meta = result['meta']
        price = meta['regularMarketPrice']
        prev = meta.get('chartPreviousClose', price)
        chg = (price - prev) / prev * 100 if prev else 0
        # 5-day data
        timestamps = result.get('timestamp', [])
        closes = result['indicators']['quote'][0].get('close', [])
        if len(closes) >= 2:
            five_day_ago = [c for c in closes if c is not None][0] if closes else price
            five_day_chg = (price - five_day_ago) / five_day_ago * 100 if five_day_ago else 0
        else:
            five_day_ago = prev
            five_day_chg = chg
        return {
            'price': round(price, 4),
            'chg_1d': round(chg, 2),
            'chg_5d': round(five_day_chg, 2),
            'prev': round(prev, 4),
            'volume': meta.get('regularMarketVolume', 0),
            'source': 'yahoo'
        }
    except Exception as e:
        return None

def get_financial_snapshot(ticker):
    """从AISA获取财务快照"""
    try:
        url = f"https://api.aisa.one/apis/v1/financial/financial-metrics/snapshot?ticker={ticker}"
        req = ur.Request(url, headers={'Authorization': f'Bearer {AISA_KEY}'})
        with ur.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return data
    except Exception:
        return None

def search_microcap_movers():
    """搜索近5日涨幅超100%的小微股"""
    print("\n🔍 扫描1: 近5日涨幅超100%的小微股")
    queries = [
        "microcap stock 100% gain past 5 days 2026",
        "penny stock doubled this week 2026",
        "small cap stock 100% rally past week",
    ]
    signals = []
    for q in queries:
        results = tavily_search(q, max_results=3)
        for r in results:
            title = r.get('title', '')
            url = r.get('url', '')
            content = r.get('content', '')
            # Extract tickers
            import re
            tickers = re.findall(r'\b([A-Z]{1,5})\b', title + ' ' + content)
            for t in tickers:
                if t in ['CEO', 'CFO', 'USD', 'SEC', 'FDA', 'AI', 'IPO', 'ETF', 'USA', 'NYSE', 'NASDAQ']:
                    continue
                price_data = get_price_yahoo(t)
                if price_data and price_data['price'] <= 5.0 and price_data['chg_5d'] > 50:
                    signals.append({
                        'ticker': t,
                        'price': price_data['price'],
                        'chg_1d': price_data['chg_1d'],
                        'chg_5d': price_data['chg_5d'],
                        'source': title,
                        'url': url,
                        'reason': f"5日涨幅{price_data['chg_5d']:.0f}% 小微股异动",
                        'type': 'microcap_mover'
                    })
                    print(f"   ✅ {t}: ${price_data['price']:.2f} | 5日+{price_data['chg_5d']:.0f}% | {title[:50]}")
    return signals

def search_sub_50m_movers():
    """搜索市值<$5000万的低价股异动"""
    print("\n🔍 扫描2: 市值<$5000万低价股异动")
    queries = [
        "sub 50 million market cap stock surge 2026",
        "microcap stock under 1 dollar volume spike",
        "OTC penny stock unusual volume today",
    ]
    signals = []
    for q in queries:
        results = tavily_search(q, max_results=3)
        for r in results:
            title = r.get('title', '')
            content = r.get('content', '')
            import re
            tickers = re.findall(r'\b([A-Z]{1,5})\b', title + ' ' + content)
            for t in tickers:
                if t in ['CEO', 'CFO', 'USD', 'SEC', 'FDA', 'AI', 'IPO', 'ETF', 'NYSE', 'NASDAQ']:
                    continue
                price_data = get_price_yahoo(t)
                if price_data and price_data['price'] <= 2.0:
                    fin = get_financial_snapshot(t)
                    mkt_cap = None
                    if fin and isinstance(fin, dict):
                        mkt_cap = fin.get('market_cap') or fin.get('marketCap') or fin.get('market_capitalization')
                    signals.append({
                        'ticker': t,
                        'price': price_data['price'],
                        'chg_1d': price_data['chg_1d'],
                        'volume': price_data['volume'],
                        'market_cap': mkt_cap,
                        'source': title,
                        'url': r.get('url', ''),
                        'reason': f"低价股${price_data['price']:.2f} 异动",
                        'type': 'sub_50m'
                    })
                    print(f"   ✅ {t}: ${price_data['price']:.2f} | 1日{price_data['chg_1d']:+.1f}% | {title[:50]}")
    return signals

def search_otc_volume_spike():
    """搜索OTC/粉单股暴量"""
    print("\n🔍 扫描3: OTC/粉单股突然暴量")
    queries = [
        "OTC stock volume spike 50% turnover 2026",
        "pink sheets penny stock surge volume today",
        "OTCQB stock breakout unusual volume",
    ]
    signals = []
    for q in queries:
        results = tavily_search(q, max_results=3)
        for r in results:
            title = r.get('title', '')
            content = r.get('content', '')
            import re
            tickers = re.findall(r'\b([A-Z]{1,5})\b', title + ' ' + content)
            for t in tickers:
                if t in ['CEO', 'CFO', 'USD', 'SEC', 'FDA', 'AI', 'IPO', 'ETF', 'NYSE', 'NASDAQ']:
                    continue
                price_data = get_price_yahoo(t)
                if price_data and price_data['price'] <= 1.0:
                    signals.append({
                        'ticker': t,
                        'price': price_data['price'],
                        'chg_1d': price_data['chg_1d'],
                        'volume': price_data['volume'],
                        'source': title,
                        'url': r.get('url', ''),
                        'reason': f"OTC/粉单股暴量 ${price_data['price']:.2f}",
                        'type': 'otc_volume'
                    })
                    print(f"   ✅ {t}: ${price_data['price']:.2f} | 1日{price_data['chg_1d']:+.1f}% | {title[:50]}")
    return signals

def search_merger_shell():
    """搜索并购/反向合并的壳股"""
    print("\n🔍 扫描4: 并购/反向合并壳股")
    queries = [
        "reverse merger shell company 2026",
        "SPAC merger completion penny stock",
        "shell company acquisition announced 2026",
        "reverse takeover microcap stock 2026",
    ]
    signals = []
    for q in queries:
        results = tavily_search(q, max_results=3)
        for r in results:
            title = r.get('title', '')
            content = r.get('content', '')
            import re
            tickers = re.findall(r'\b([A-Z]{1,5})\b', title + ' ' + content)
            for t in tickers:
                if t in ['CEO', 'CFO', 'USD', 'SEC', 'FDA', 'AI', 'IPO', 'ETF', 'SPAC', 'NYSE', 'NASDAQ']:
                    continue
                price_data = get_price_yahoo(t)
                if price_data and price_data['price'] <= 5.0:
                    signals.append({
                        'ticker': t,
                        'price': price_data['price'],
                        'chg_1d': price_data['chg_1d'],
                        'source': title,
                        'url': r.get('url', ''),
                        'reason': f"并购/反向合并壳股 ${price_data['price']:.2f}",
                        'type': 'merger_shell'
                    })
                    print(f"   ✅ {t}: ${price_data['price']:.2f} | 1日{price_data['chg_1d']:+.1f}% | {title[:50]}")
    return signals

def main():
    print("="*60)
    print(f"🎯 激进账户新信号扫描 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60)
    
    all_signals = []
    
    # Scan 1: 近5日涨幅超100%的小微股
    s1 = search_microcap_movers()
    all_signals.extend(s1)
    
    # Scan 2: 市值<$5000万低价股异动
    s2 = search_sub_50m_movers()
    all_signals.extend(s2)
    
    # Scan 3: OTC/粉单股暴量
    s3 = search_otc_volume_spike()
    all_signals.extend(s3)
    
    # Scan 4: 并购/反向合并壳股
    s4 = search_merger_shell()
    all_signals.extend(s4)
    
    # Deduplicate by ticker
    seen = set()
    unique_signals = []
    for s in all_signals:
        if s['ticker'] not in seen:
            seen.add(s['ticker'])
            unique_signals.append(s)
    
    print(f"\n📊 共发现 {len(unique_signals)} 个新信号")
    
    # Save results
    output_file = "/root/.openclaw/workspace/data/aggressive_new_signals_latest.json"
    with open(output_file, 'w') as f:
        json.dump({
            'scan_time': datetime.now().isoformat(),
            'signals': unique_signals
        }, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("📋 新信号摘要")
    print("="*60)
    for s in unique_signals[:10]:
        print(f"   {s['ticker']}: ${s['price']:.2f} | {s['chg_1d']:+.1f}% | {s['reason']}")
    
    return unique_signals

if __name__ == '__main__':
    main()
