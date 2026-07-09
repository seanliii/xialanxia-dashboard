#!/usr/bin/env python3
"""激进账户低价股/Penny Stock扫描器"""
import yfinance as yf
import json
from datetime import datetime, timedelta
import os

# 活跃低价股池（市值<$1亿，价格<$5，高波动）
PENNY_UNIVERSE = [
    # 量子/AI/新能源概念低价股
    "QUBT", "SOUN", "LTRX", "AIMD", "AIEV", "AIRE",
    # 生物科技股
    "ADTX", "AGEN", "AMPE", "ATOS", "AVXL", "BCTX",
    # 新能源/矿业
    "IREN", "BTBT", "HUT", "CLSK", "RIOT", "MARA",
    # OTC/粉单热门
    "TSLA", "GOEV", "MULN", "FFIE", "NKLA", "LCID",
    # 壳股/并购传闻
    "BIEI", "IMTL", "INKW", "HRAA", "SBES", "PVHO",
    # 其他活跃低价股
    "DPLS", "IGEX", "GGII", "HMBL", "OZSC", "ALPP",
]

# 市值<$5000万的微盘池
MICROCAP_UNIVERSE = [
    "SRNW", "TPTW", "HIRU", "EEENF", "INND", "OZSC",
    "ILUS", "CYBL", "ALYI", "HCMC", "GGII", "HMBL",
    "ALPP", "DPLS", "IGEX", "INKW", "BIEI", "IMTL",
]

def scan_momentum(tickers, days=5, min_gain=1.0):
    """扫描N日内涨幅超过阈值的票"""
    results = []
    end = datetime.now()
    start = end - timedelta(days=days+5)  # 多取几天确保有足够数据
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
            if len(hist) < 2:
                continue
            
            latest = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[0]
            change = (latest - prev) / prev
            volume = hist['Volume'].iloc[-1]
            avg_vol = hist['Volume'].mean()
            vol_ratio = volume / avg_vol if avg_vol > 0 else 1
            
            info = stock.info
            market_cap = info.get('marketCap', 0)
            
            # 条件筛选
            if change >= min_gain and latest >= 0.01:
                results.append({
                    'ticker': ticker,
                    'price': round(latest, 4),
                    f'{days}d_change': f"+{change*100:.1f}%",
                    'volume': int(volume),
                    'vol_ratio': round(vol_ratio, 1),
                    'market_cap': market_cap,
                    'market_cap_m': round(market_cap / 1e6, 2) if market_cap else None,
                })
        except Exception as e:
            pass
    
    return sorted(results, key=lambda x: float(x[f'{days}d_change'].replace('%','').replace('+','')), reverse=True)

def scan_volume_spike(tickers, min_turnover_ratio=0.5):
    """扫描成交量突然放大（换手率>50%）"""
    results = []
    end = datetime.now()
    start = end - timedelta(days=10)
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
            if len(hist) < 3:
                continue
            
            latest_close = hist['Close'].iloc[-1]
            latest_vol = hist['Volume'].iloc[-1]
            avg_vol = hist['Volume'].iloc[-5:].mean()
            vol_ratio = latest_vol / avg_vol if avg_vol > 0 else 1
            
            # 估算换手率（简化：成交量/流通股的1/4）
            info = stock.info
            shares = info.get('sharesOutstanding', 0)
            turnover = latest_vol / shares if shares > 0 else 0
            
            if vol_ratio >= 3 and turnover >= min_turnover_ratio:
                results.append({
                    'ticker': ticker,
                    'price': round(latest_close, 4),
                    'volume': int(latest_vol),
                    'vol_ratio': round(vol_ratio, 1),
                    'turnover': f"{turnover*100:.1f}%",
                })
        except:
            pass
    
    return sorted(results, key=lambda x: x['vol_ratio'], reverse=True)

def scan_merger_arb():
    """扫描并购/反向合并相关低价股"""
    merger_tickers = ["BIEI", "IMTL", "INKW", "HRAA", "SBES", "PVHO", "TGGI", "CYBL"]
    results = []
    
    for ticker in merger_tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            if len(hist) < 2:
                continue
            
            latest = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[0]
            change = (latest - prev) / prev
            
            info = stock.info
            market_cap = info.get('marketCap', 0)
            
            results.append({
                'ticker': ticker,
                'price': round(latest, 4),
                '5d_change': f"{change*100:+.1f}%",
                'market_cap_m': round(market_cap / 1e6, 2) if market_cap else None,
                'volume': int(hist['Volume'].iloc[-1]),
            })
        except:
            pass
    
    return sorted(results, key=lambda x: abs(float(x['5d_change'].replace('%','').replace('+',''))), reverse=True)

def main():
    print("=" * 60)
    print("🔥 激进账户 Penny Stock 新信号扫描")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
    print("=" * 60)
    
    # 1. 近5日涨幅超100%
    print("\n📈 近5日涨幅超100%的小微股:")
    momentum = scan_momentum(PENNY_UNIVERSE + MICROCAP_UNIVERSE, days=5, min_gain=1.0)
    if momentum:
        for s in momentum[:10]:
            mc = f"${s['market_cap_m']}M" if s['market_cap_m'] else "N/A"
            print(f"   🔥 {s['ticker']:5s} ${s['price']:.4f} | {s['5d_change']:>8s} | 市值{mc:>8s} | 量比{s['vol_ratio']:.1f}x")
    else:
        print("   无信号")
    
    # 2. 市值<$5000万的低价股异动
    print("\n💎 市值<$5000万的低价股异动:")
    microcap = scan_momentum(PENNY_UNIVERSE + MICROCAP_UNIVERSE, days=5, min_gain=0.2)
    microcap_filtered = [s for s in microcap if s.get('market_cap_m') and s['market_cap_m'] < 50]
    if microcap_filtered:
        for s in microcap_filtered[:10]:
            print(f"   💎 {s['ticker']:5s} ${s['price']:.4f} | {s['5d_change']:>8s} | 市值${s['market_cap_m']}M | 量比{s['vol_ratio']:.1f}x")
    else:
        print("   无信号")
    
    # 3. 暴量异动
    print("\n⚡ OTC/低价股暴量（换手率>50%或量比>5x）:")
    volume_spike = scan_volume_spike(PENNY_UNIVERSE + MICROCAP_UNIVERSE)
    if volume_spike:
        for s in volume_spike[:10]:
            print(f"   ⚡ {s['ticker']:5s} ${s['price']:.4f} | 量比{s['vol_ratio']:.1f}x | 换手{s['turnover']}")
    else:
        print("   无信号")
    
    # 4. 并购/壳股
    print("\n🔄 并购/反向合并相关壳股:")
    merger = scan_merger_arb()
    if merger:
        for s in merger[:10]:
            mc = f"${s['market_cap_m']}M" if s['market_cap_m'] else "N/A"
            print(f"   🔄 {s['ticker']:5s} ${s['price']:.4f} | {s['5d_change']:>8s} | 市值{mc:>8s}")
    else:
        print("   无信号")
    
    # 保存报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'momentum_5d_100pct': momentum[:10],
        'microcap_under_50m': microcap_filtered[:10],
        'volume_spike': volume_spike[:10],
        'merger_arb': merger[:10],
    }
    
    os.makedirs('/root/.openclaw/workspace/data', exist_ok=True)
    with open('/root/.openclaw/workspace/data/penny_scan_20260610_0400.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Penny扫描完成 | 报告: data/penny_scan_20260610_0400.json")

if __name__ == '__main__':
    main()
