#!/usr/bin/env python3
"""
激进账户新信号扫描 v2 — 基于Yahoo Finance直接获取
重点：penny stock ($0.01-$5), 5日异动, 小微市值
"""
import json, urllib.request as ur
from datetime import datetime
import concurrent.futures, time

AISA_KEY = "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41"

# 已知的热门低价股/小盘股列表（待验证）
PENNY_WATCHLIST = [
    "CRKN", "PACB", "UPXI", "TOI", "IMVT", "MLEC", "METC", "SOUN", "QUBT",
    "TCRT", "BMEA", "ALAR", "IONM", "ONCO", "APVO", "RENB", "RAPT", "CDIO",
    "SWVL", "ACDC", "ATNF", "MLGO", "CMPO", "PRZO", "AIRE", "EVOK", "GDC",
    "STIX", "TRUG", "JAGX", "DIBS", "AGEN", "ACON", "BTAI", "BSGM", "INMB",
    "ALXO", "IMNM", "PRQR", "SYRA", "EYEN", "TNGX", "BFRI", "BLPH", "CYN",
    "DTIL", "GBIO", "IMMX", "LSTA", "LXRX", "MGNX", "NEPH", "NRSN", "OMGA",
    "PNTG", "SBFM", "SPRB", "STRO", "TCRT", "VINC", "VIRX", "VYNE", "XLO",
    "ZVSA", "AIMD", "AMIX", "APLD", "APVO", "ARDX", "AULT", "BCLI", "BDRX",
    "BIAF", "BPTH", "BTTX", "CALC", "CANF", "CERO", "CETX", "CLSK", "COEP",
    "CORZ", "CRBP", "CRKN", "CRVO", "CURI", "CUTR", "DRTS", "DUOT", "ELEV",
    "ELWS", "ENGN", "ENVB", "EOSE", "ERNA", "ESLA", "EVGN", "EWTX", "FBRX",
    "FCUV", "FFIE", "FRGT", "FSRN", "FTHM", "GRI", "HCDI", "HEPA", "HOTH",
    "HOWL", "HPCO", "HRYU", "HUDA", "IBIO", "ICCC", "IDAI", "IFBD", "IMPP",
    "INDP", "INM", "INTS", "IPDN", "ISPC", "IVDA", "JANX", "JXJT", "KULR",
    "LASE", "LGMK", "LIAN", "LIDR", "LILM", "LITM", "LMDX", "LODE", "LSTA",
    "LTRX", "LUCY", "LUNR", "MARK", "MATH", "MBOT", "MEDS", "MIRA", "MIST",
    "MKFG", "MLGO", "MNDY", "MOTS", "MRIN", "MSSA", "MTEM", "MULN", "NAOV",
    "NCPL", "NERV", "NEWP", "NIR", "NLSP", "NMTC", "NOTV", "NTCO", "NUTX",
    "NXU", "OCEA", "OESX", "ONCO", "ONMD", "OPFI", "ORGS", "OTLK", "PALI",
    "PALT", "PBYI", "PHUN", "PLUR", "POAI", "PRZO", "PSTV", "PTIX", "PULM",
    "QMCO", "QRHC", "RAPT", "REAX", "RENB", "RENT", "RETO", "RKLB", "ROMA",
    "RSLS", "RVP", "SBFM", "SCPS", "SEED", "SEER", "SGD", "SHLT", "SLDB",
    "SNGX", "SNOA", "SONN", "SOUN", "SPRB", "SQL", "SRZN", "STIX", "STSS",
    "SWVL", "SYRE", "TBLA", "TCON", "TCRT", "TENX", "TFFP", "TGL", "THAR",
    "TIVC", "TMBR", "TMPO", "TNGX", "TRUG", "TTSH", "TYGO", "UAVS", "UNCY",
    "UNCY", "UTRS", "VBIV", "VGZ", "VINC", "VIRX", "VLD", "VLCN", "VNCE",
    "VOR", "VSTM", "VTYX", "VVOS", "VYGR", "VYNE", "WAVD", "WISA", "WKEY",
    "WWR", "XBIT", "XBIO", "XCUR", "XELB", "XFOR", "XLO", "XOMA", "XPON",
    "XTNT", "YJ", "YMAB", "YVR", "ZAPP", "ZCMD", "ZJYL", "ZTEK", "ZVSA",
    "AMC", "GME", "BBBY", "BB", "NOK", "PLTR", "RIVN", "LCID", "NKLA", "SOFI"
]

def get_yahoo_data(ticker):
    """获取Yahoo Finance 5日数据"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
        req = ur.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with ur.urlopen(req, timeout=6) as r:
            data = json.loads(r.read())
        
        result = data['chart']['result'][0]
        meta = result['meta']
        price = meta['regularMarketPrice']
        prev_close = meta.get('chartPreviousClose', price)
        
        # 5-day change
        timestamps = result.get('timestamp', [])
        quotes = result['indicators']['quote'][0]
        closes = [c for c in quotes.get('close', []) if c is not None]
        
        if len(closes) >= 2 and closes[0] > 0:
            five_day_ago = closes[0]
            five_day_chg = (price - five_day_ago) / five_day_ago * 100
        else:
            five_day_ago = prev_close
            five_day_chg = (price - prev_close) / prev_close * 100 if prev_close else 0
        
        # 1-day change
        if len(closes) >= 2:
            one_day_chg = (price - closes[-2]) / closes[-2] * 100 if closes[-2] else 0
        else:
            one_day_chg = (price - prev_close) / prev_close * 100 if prev_close else 0
        
        volume = meta.get('regularMarketVolume', 0)
        
        return {
            'ticker': ticker,
            'price': round(price, 4),
            'prev_close': round(prev_close, 4),
            'chg_1d': round(one_day_chg, 2),
            'chg_5d': round(five_day_chg, 2),
            'volume': volume,
            'valid': True
        }
    except Exception:
        return {'ticker': ticker, 'valid': False}

def main():
    print("=" * 60)
    print(f"🎯 激进账户新信号扫描 v2 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(f"\n📡 扫描 {len(PENNY_WATCHLIST)} 只候选股票...")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_yahoo_data, t): t for t in PENNY_WATCHLIST}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result['valid']:
                results.append(result)
    
    print(f"   ✅ 成功获取 {len(results)} 只")
    
    # Filter 1: 近5日涨幅 > 50% (放宽到50%因为100%太严格)
    movers_5d = [r for r in results if r['chg_5d'] > 50 and r['price'] <= 5]
    movers_5d.sort(key=lambda x: x['chg_5d'], reverse=True)
    
    # Filter 2: 近1日涨幅 > 20% (日内异动)
    movers_1d = [r for r in results if r['chg_1d'] > 20 and r['price'] <= 5 and r not in movers_5d]
    movers_1d.sort(key=lambda x: x['chg_1d'], reverse=True)
    
    # Filter 3: 价格 <= $1 的任何正涨幅 (penny stock)
    penny_movers = [r for r in results if r['price'] <= 1 and r['chg_1d'] > 5]
    penny_movers.sort(key=lambda x: x['chg_1d'], reverse=True)
    
    # Filter 4: 所有低价股按5日涨幅排序
    all_cheap = [r for r in results if r['price'] <= 5]
    all_cheap.sort(key=lambda x: x['chg_5d'], reverse=True)
    
    print(f"\n{'='*60}")
    print("🚀 近5日涨幅>50% 的小微股")
    print("="*60)
    for r in movers_5d[:10]:
        print(f"   {r['ticker']}: ${r['price']:.2f} | 5日+{r['chg_5d']:.1f}% | 1日{r['chg_1d']:+.1f}%")
    
    print(f"\n{'='*60}")
    print("⚡ 近1日涨幅>20% 的异动股")
    print("="*60)
    for r in movers_1d[:10]:
        print(f"   {r['ticker']}: ${r['price']:.2f} | 1日+{r['chg_1d']:.1f}% | 5日{r['chg_5d']:+.1f}%")
    
    print(f"\n{'='*60}")
    print("💎 低价股($≤1) 异动")
    print("="*60)
    for r in penny_movers[:10]:
        print(f"   {r['ticker']}: ${r['price']:.4f} | 1日{r['chg_1d']:+.1f}% | 5日{r['chg_5d']:+.1f}%")
    
    print(f"\n{'='*60}")
    print("📊 全部$5以下股票 TOP20 (按5日涨幅)")
    print("="*60)
    for r in all_cheap[:20]:
        flag = "🚀" if r['chg_5d'] > 50 else "⚡" if r['chg_5d'] > 20 else ""
        print(f"   {flag} {r['ticker']}: ${r['price']:.2f} | 5日{r['chg_5d']:+.1f}% | 1日{r['chg_1d']:+.1f}%")
    
    # Save results
    output = {
        'scan_time': datetime.now().isoformat(),
        'movers_5d': movers_5d,
        'movers_1d': movers_1d,
        'penny_movers': penny_movers,
        'all_cheap_top20': all_cheap[:20]
    }
    
    with open('/root/.openclaw/workspace/data/aggressive_new_signals_v2.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 结果已保存")
    return output

if __name__ == '__main__':
    main()
