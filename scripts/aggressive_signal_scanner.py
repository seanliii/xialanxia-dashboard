#!/usr/bin/env python3
"""
激进账户新信号扫描 - 扩展扫描范围
"""

import json, os
from datetime import datetime
import urllib.request as ur

AISA_KEY = "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41"

def get_price_data(ticker):
    """获取股票价格和5日涨幅数据"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
        req = ur.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with ur.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        
        if not data['chart']['result']:
            return None
            
        result = data['chart']['result'][0]
        meta = result['meta']
        prices = result['indicators']['quote'][0].get('close', [])
        volumes = result['indicators']['quote'][0].get('volume', [])
        
        if len(prices) < 2:
            return None
        
        current_price = meta['regularMarketPrice']
        five_day_ago = prices[0] if prices[0] else current_price
        five_day_gain = (current_price - five_day_ago) / five_day_ago * 100 if five_day_ago else 0
        
        # 获取市值和成交量
        summary_url = f"https://query1.finance.yahoo.com/v11/finance/quoteSummary/{ticker}?modules=summaryDetail,defaultKeyStatistics"
        req2 = ur.Request(summary_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        market_cap = 0
        avg_volume = 0
        try:
            with ur.urlopen(req2, timeout=5) as r2:
                summary_data = json.loads(r2.read())
            
            if summary_data.get('quoteSummary') and summary_data['quoteSummary'].get('result'):
                sresult = summary_data['quoteSummary']['result'][0]
                if 'defaultKeyStatistics' in sresult:
                    mc = sresult['defaultKeyStatistics'].get('marketCap', {})
                    market_cap = mc.get('raw', 0) if mc else 0
                if 'summaryDetail' in sresult:
                    av = sresult['summaryDetail'].get('averageVolume', {})
                    avg_volume = av.get('raw', 0) if av else 0
        except:
            pass
        
        today_volume = volumes[-1] if volumes and volumes[-1] else 0
        volume_ratio = (today_volume / avg_volume) if avg_volume and avg_volume > 0 else 0
        
        return {
            'ticker': ticker,
            'price': current_price,
            'five_day_gain': round(five_day_gain, 2),
            'market_cap_m': round(market_cap / 1_000_000, 2) if market_cap else 0,
            'volume': today_volume,
            'avg_volume': avg_volume,
            'volume_ratio': round(volume_ratio, 2)
        }
    except Exception as e:
        return None

def scan_extended():
    """扩展扫描高爆发股票"""
    print("🔥 激进账户新信号扫描 - 扩展版")
    print("=" * 60)
    
    # 更大范围的扫描列表 - 包含更多OTC/粉单股和低价股
    extended_list = [
        # 原有持仓/关注
        "UPXI", "QUBT", "SOUN", "IREN", "MLEC", "ROLR", "TOI", "IMVT",
        # 高波动小微股
        "SBFM", "BETS", "PACB", "QS", "ENVX", "ASTS", "CLOV",
        "MGOL", "NXGL", "CRKN", "GDHG", "EFOI", "GRI", "FRZA",
        "SISI", "LGMK", "WLDS", "HKIT", "CRNT", "MKUL",
        # OTC/粉单热门
        "HBRM", "SPRV", "EWRC", "PLPL", "HIMR", "VAPE", "RMRK",
        # 潜在爆发股
        "NVDA", "TSLA", "PLTR", "MSTR", "COIN", "HOOD", "BITF",
        "MARA", "RIOT", "CLSK", "CORZ", "WULF", "BTBT", "DGHI",
        # 创新药/生物科技股
        "CRSP", "EDIT", "NTLA", "BEAM", "VERV", "SGMO", "BLUE",
        "KPTI", "ARVN", "SRPT", "VRTX", "BIIB", "REGN", "INCY",
        # 低价股
        "FCEL", "PLUG", "BLNK", "CHPT", "VLDR", "GOEV", "FFIE",
        # 其他热门
        "NNOX", "CYN", "BZFD", "VERB", "IDEX", "XELA", "APRN"
    ]
    
    print(f"📡 扫描 {len(extended_list)} 只股票...")
    
    high_gainers = []
    micro_cap_movers = []
    volume_spikes = []
    
    for i, ticker in enumerate(extended_list):
        if i % 20 == 0:
            print(f"   进度: {i}/{len(extended_list)}")
        
        data = get_price_data(ticker)
        if not data:
            continue
        
        price = data['price']
        gain = data['five_day_gain']
        mc = data['market_cap_m']
        vol_ratio = data['volume_ratio']
        
        # 1. 近5日涨幅超100%
        if gain > 100:
            high_gainers.append({**data, 'signal': f'🚀 5日暴涨 +{gain:.0f}%'})
        elif gain > 50:
            high_gainers.append({**data, 'signal': f'📈 5日大涨 +{gain:.0f}%'})
        
        # 2. 市值<$5000万的低价股异动
        if mc < 50 and price < 5 and gain > 20:
            micro_cap_movers.append({**data, 'signal': f'💎 小盘异动(市值${mc:.1f}M)'})
        
        # 3. 暴量（成交量>5倍平均且成交量>10万）
        if vol_ratio > 5 and data['volume'] > 100000:
            volume_spikes.append({**data, 'signal': f'⚡ 暴量 {vol_ratio:.1f}倍'})
    
    # 合并并去重
    all_signals = {}
    for s in high_gainers + micro_cap_movers + volume_spikes:
        ticker = s['ticker']
        if ticker not in all_signals:
            all_signals[ticker] = s
        else:
            all_signals[ticker]['signal'] += " | " + s['signal']
    
    signals = list(all_signals.values())
    signals.sort(key=lambda x: x['five_day_gain'], reverse=True)
    
    # 打印结果
    print(f"\n🎯 发现 {len(signals)} 个新信号:")
    print("-" * 60)
    
    for s in signals[:15]:
        print(f"\n🔥 {s['ticker']} @ ${s['price']:.2f}")
        print(f"   市值: ${s['market_cap_m']:.1f}M | 5日涨幅: {'+' if s['five_day_gain']>0 else ''}{s['five_day_gain']:.1f}%")
        print(f"   成交量: {s['volume_ratio']:.1f}倍日均 | 今日量: {s['volume']/1000:.0f}K")
        print(f"   {s['signal']}")
    
    return signals

if __name__ == "__main__":
    signals = scan_extended()
    
    output = {
        'scan_time': datetime.now().isoformat(),
        'total_signals': len(signals),
        'signals': signals
    }
    
    os.makedirs('/root/.openclaw/workspace/data', exist_ok=True)
    with open('/root/.openclaw/workspace/data/aggressive_signals_scan.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 结果已保存")
