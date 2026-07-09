#!/usr/bin/env python3
"""Scan micro-cap and penny stocks for aggressive account signals."""
import urllib.request, json, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Known micro-cap / penny stock tickers to scan for recent big moves
# Focus: crypto, EV, biotech, shell companies, OTC
micro_tickers = [
    # Crypto miners / related
    'SAG', 'BTBT', 'CLSK', 'MARA', 'HUT', 'RIOT', 'HIVE', 'CIFR', 'BITF', 'GLXY',
    # EV / auto
    'NKLA', 'LCID', 'RIVN', 'F', 'GM', 'STLA',
    # Tech micro-cap
    'PLTR', 'RBLX', 'SNOW', 'DOCN', 'VERX', 'DDOG', 'CRWD',
    # Biotech small cap / penny
    'INVO', 'CDTX', 'KTRA', 'BIOL', 'DYAI', 'ATNF', 'MNKD', 'SRNE', 'TCRX',
    # OTC / nano cap known for pumps
    'SHMN', 'CYBN', 'PHUN', 'SNDL', 'CGC', 
    # Already in watchlist
    'UPXI', 'SOUN', 'QUBT',
    # Recent meme / spec
    'WULF', 'CVRX', 'CRMD', 'NVTA', 'BEAM',
]

all_data = {}
for t in micro_tickers:
    try:
        url = f'https://stooq.com/q/l/?s={t}&f=sd2t2ohlcv&h&e=csv'
        r = urllib.request.urlopen(url, timeout=10, context=ctx)
        lines = r.read().decode().strip().split('\n')
        if len(lines) > 1:
            vals = lines[1].split(',')
            if len(vals) >= 7:
                close = float(vals[4])
                prev_close = float(vals[3]) if vals[3] else close
                chg = ((close - prev_close) / prev_close * 100) if prev_close > 0 else 0
                vol = int(vals[6]) if vals[6].isdigit() else 0
                all_data[t] = {'close': close, 'chg': round(chg, 1), 'vol': vol}
                print(f'  OK {t}', flush=True)
    except Exception as e:
        print(f'  ERR {t}: {e}', flush=True)

# Sort by change % desc
sorted_tickers = sorted(all_data.items(), key=lambda x: x[1]['chg'], reverse=True)

print('\n=== 激进账户 - 微盘股扫描结果 ===')
print(f'扫描 {len(micro_tickers)} 只 | 命中 {len(all_data)} 只')
print()
for t, d in sorted_tickers[:20]:
    flag = '🔴' if d['chg'] < -5 else ('🟢' if d['chg'] > 5 else '⚪')
    print(f'{flag} {t}: ${d["close"]:.2f} ({d["chg"]:+.1f}%) Vol={d["vol"]:,}')

# Filter for high movers (abs > 10%)
movers = [(t, d) for t, d in all_data.items() if abs(d['chg']) > 10]
if movers:
    print('\n=== 🔥 重点关注（涨跌幅>10%）===')
    for t, d in sorted(movers, key=lambda x: x[1]['chg'], reverse=True):
        print(f'  🟢 {t}: ${d["close"]:.2f} ({d["chg"]:+.1f}%) Vol={d["vol"]:,}')
else:
    print('\n=== 无显著异动 ===')

# Filter for super high movers (>50%)
super_movers = [(t, d) for t, d in all_data.items() if abs(d['chg']) > 50]
if super_movers:
    print('\n=== 🚀🚀🚀 超级异动（涨跌幅>50%）===')
    for t, d in sorted(super_movers, key=lambda x: x[1]['chg'], reverse=True):
        print(f'  🚀 {t}: ${d["close"]:.2f} ({d["chg"]:+.1f}%) Vol={d["vol"]:,}')

# Low price high volume (potential pump)
low_price_high_vol = [(t, d) for t, d in all_data.items() if d['close'] < 5 and d['vol'] > 1000000 and d['chg'] > 5]
if low_price_high_vol:
    print('\n=== 📈 低价高量（<$5, 放量>1M, 涨幅>5%）===')
    for t, d in sorted(low_price_high_vol, key=lambda x: x[1]['chg'], reverse=True):
        print(f'  💎 {t}: ${d["close"]:.2f} ({d["chg"]:+.1f}%) Vol={d["vol"]:,}')
