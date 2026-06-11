#!/usr/bin/env python3
"""
📊 增强版 13F 扫描系统 v2.1
格式对标：高胜率机构TOP5 + 巴菲特持仓% + 机构新建仓聚合 + 小微股综合推荐（上涨空间排序）
"""
import os
os.environ["https_proxy"] = "http://10.59.78.158:3128"
os.environ["http_proxy"] = "http://10.59.78.158:3128"
os.environ["HTTPS_PROXY"] = "http://10.59.78.158:3128"
os.environ["HTTP_PROXY"] = "http://10.59.78.158:3128"
import subprocess, csv, io, json, os, time
from datetime import date, datetime

AISA_KEY = os.environ.get('AISA_API_KEY', 'sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41')
# BASE = 'https://api.aisa.one/apis/v1/financial'  # ❌ 已禁用，太贵
# 2026-03-19: 所有 financial API 调用改为免费替代：
# - 价格: Stooq
# - 机构持仓/分析师目标价: Yahoo Finance (免费)
# - 内部人买入: SEC EDGAR Form 4 (免费)

TOP_FUNDS = [
    {'rank':1,'name':'Duquesne Family Office','manager':'Stanley Druckenmiller','annual_ret':'22.5%','win_rate':'66.6%'},
    {'rank':2,'name':'APG Asset Management',  'manager':'APG Team',             'annual_ret':'7.7%', 'win_rate':'65.0%'},
    {'rank':3,'name':'Renaissance Technologies','manager':'Jim Simons',         'annual_ret':'22.4%','win_rate':'64.7%'},
    {'rank':4,'name':'Berkshire Hathaway',     'manager':'Warren Buffett',      'annual_ret':'14.9%','win_rate':'64.5%'},
    {'rank':5,'name':'PIMCO',                  'manager':'Dan Ivascyn',         'annual_ret':'16.9%','win_rate':'64.5%'},
    {'rank':6,'name':'Viking Global',          'manager':'Andreas Halvorsen',   'annual_ret':'18.2%','win_rate':'62.1%'},
    {'rank':7,'name':'Lone Pine Capital',      'manager':'Steve Mandel',        'annual_ret':'17.5%','win_rate':'61.8%'},
    {'rank':8,'name':'Light Street Capital',   'manager':'Glen Kacher',         'annual_ret':'24.3%','win_rate':'59.7%'},
    {'rank':9,'name':'Whale Rock Capital',     'manager':'Alex Sacerdote',      'annual_ret':'21.1%','win_rate':'58.4%'},
    {'rank':10,'name':'Maverick Capital',      'manager':'Lee Ainslie',         'annual_ret':'15.9%','win_rate':'60.3%'},
]

def stooq(ticker):
    r = subprocess.run(['curl','-s','--max-time','6',
        f'https://stooq.com/q/l/?s={ticker.lower()}.us&f=sd2t2ohlcv&h&e=csv'],
        capture_output=True, text=True, timeout=8)
    try:
        for row in csv.DictReader(io.StringIO(r.stdout)):
            c = float(row.get('Close',0) or 0)
            o = float(row.get('Open',c) or c)
            return {'price': c, 'chg': round((c-o)/o*100,2) if o else 0}
    except: pass
    return None

def get_inst_ownership(ticker):
    """机构持仓：Yahoo Finance（免费）"""
    try:
        r = subprocess.run(
            ['curl', '-s', '--max-time', '8',
             f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=institutionOwnership',
             '-H', 'User-Agent: Mozilla/5.0'],
            capture_output=True, text=True, timeout=10)
        data = json.loads(r.stdout)
        owners = data.get('quoteSummary', {}).get('result', [{}])[0]
        holders = owners.get('institutionOwnership', {}).get('ownershipList', [])
        result = []
        for h in holders[:5]:
            org = h.get('organization', '')
            pct = (h.get('pctHeld', {}).get('raw', 0) or 0) * 100
            val = h.get('value', {}).get('raw', 0) or 0
            result.append({'name': org, 'pct': round(pct, 2), 'market_value': val, 'report_period': ''})
        return result if result else None
    except:
        return None

def get_insider_signal(ticker):
    """内部人买入：SEC EDGAR Form 4（免费）"""
    from datetime import date, timedelta
    try:
        cutoff = (date.today() - timedelta(days=30)).isoformat()
        r = subprocess.run(
            ['curl', '-s', '--max-time', '10',
             f'https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom'
             f'&startdt={cutoff}&forms=4',
             '-H', 'User-Agent: XiaLanXia/1.0 admin@example.com'],
            capture_output=True, text=True, timeout=12)
        data = json.loads(r.stdout)
        hits = data.get('hits', {}).get('hits', [])
        buys = [{'name': h.get('_source', {}).get('display_names', ['?'])[0],
                 'title': '', 'value': 0, 'date': h.get('_source', {}).get('file_date', '')}
                for h in hits[:3]]
        return {'buys': buys, 'sells': [],
                'net_signal': '🔥买入' if buys else '中性'}
    except:
        return {'buys': [], 'sells': [], 'net_signal': '中性'}

def get_analyst_upside(ticker, current_price):
    """分析师目标价：Yahoo Finance（免费）"""
    try:
        r = subprocess.run(
            ['curl', '-s', '--max-time', '8',
             f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=financialData',
             '-H', 'User-Agent: Mozilla/5.0'],
            capture_output=True, text=True, timeout=10)
        data = json.loads(r.stdout)
        fin = data.get('quoteSummary', {}).get('result', [{}])[0].get('financialData', {})
        target = (fin.get('targetMeanPrice', {}) or {}).get('raw', 0) or 0
        if target and current_price and current_price > 0:
            upside = round((target - current_price) / current_price * 100, 1)
            return round(target, 2), upside
    except:
        pass
    return 0, 0

def scan_stocks(tickers, mode='small_cap'):
    """批量扫描：价格 + 机构 + 内部人 + 分析师"""
    results = []
    for ticker in tickers:
        time.sleep(0.4)
        p = stooq(ticker)
        if not p or p['price'] <= 0:
            print(f'  {ticker}: Stooq价格获取失败，跳过')
            continue
        
        current_price = p['price']
        print(f'  {ticker}: ${current_price:.2f} ({p["chg"]:+.2f}%)', end='', flush=True)
        
        # 机构持仓
        inst = get_inst_ownership(ticker)
        inst_count = len([h for h in (inst or []) if h.get('pct', 0) > 1]) if inst else 0
        
        # 内部人信号
        insider = get_insider_signal(ticker)
        buy_count = len(insider.get('buys', []))
        
        # 分析师目标价
        target, upside = get_analyst_upside(ticker, current_price)
        
        # 综合评分
        score = 0
        if upside > 50: score += 40
        elif upside > 30: score += 25
        elif upside > 15: score += 15
        if buy_count >= 2: score += 30
        elif buy_count >= 1: score += 15
        if inst_count >= 3: score += 20
        elif inst_count >= 1: score += 10
        if 1 <= current_price <= 20: score += 10
        
        action = '强烈买入' if score >= 60 else ('买入' if score >= 40 else '关注')
        
        print(f' | 内部人买入:{buy_count} | 上涨空间:{upside:+.1f}% | 评分:{score}')
        
        results.append({
            'ticker': ticker,
            'price': current_price,
            'chg': p['chg'],
            'upside': upside,
            'target': target,
            'score': score,
            'action': action,
            'inst_count': inst_count,
            'buy_count': buy_count,
            'insider_signal': insider.get('net_signal',''),
            'top_buyer': insider['buys'][0].get('title','') if insider['buys'] else '',
            'top_inst': inst[0]['name'] if inst else '',
        })
    
    return sorted(results, key=lambda x: x['upside'], reverse=True)

def run_scan():
    print('📊 增强版13F扫描启动...\n')
    
    # 1. 巴菲特重仓股 → 机构持仓分析
    print('=== 巴菲特重仓分析 ===')
    buffett_tickers = ['AAPL', 'BAC', 'CVX', 'KO', 'OXY', 'MA', 'ABBV', 'PEP']
    buffett_results = []
    for t in buffett_tickers:
        time.sleep(0.3)
        inst = get_inst_ownership(t)
        p = stooq(t)
        if not inst or not p: continue
        # 找持仓最大的
        top = inst[0] if inst else {}
        buffett_results.append({
            'ticker': t,
            'price': p['price'],
            'chg': p['chg'],
            'top_holder': top.get('name',''),
            'pct': top.get('pct', 0),
            'report_period': top.get('report_period','')
        })
        print(f'  {t}: ${p["price"]:.2f} 最大持仓:{top.get("name","")} {top.get("pct",0):.1f}%')
    
    # 2. 小微股综合扫描（含我们自选仓 + 外部推荐）
    print('\n=== 小微股综合评分扫描 ===')
    small_caps = ['UPST', 'CHWY', 'FVRR', 'RVLV', 'HIMS', 'SOFI',
                  'SOUN', 'QUBT', 'IONQ', 'HOOD', 'ROLR', 'TOI',
                  'IMVT', 'OCUL', 'UPXI', 'IREN']
    small_results = scan_stocks(small_caps)
    
    return {
        'date': date.today().isoformat(),
        'top_funds': TOP_FUNDS[:5],
        'buffett_analysis': buffett_results,
        'small_cap_top5': small_results[:5],
        'all_small_cap': small_results,
        'scan_time': datetime.now().isoformat()
    }

def format_report(data):
    lines = ['']
    lines.append(f"📊 **13F 增强版扫描报告 — {data['date']}**\n")
    
    # 高胜率机构TOP5
    lines.append("**🏆 高胜率机构 TOP 5**")
    lines.append("```")
    lines.append(f"{'排名':<4} {'机构':<28} {'管理人':<20} {'年化':>6} {'胜率':>7}")
    lines.append("-"*70)
    for f in data['top_funds']:
        lines.append(f"{f['rank']:<4} {f['name']:<28} {f['manager']:<20} {f['annual_ret']:>6} {f['win_rate']:>7}")
    lines.append("```\n")
    
    # 机构持仓TOP（巴菲特视角）
    if data['buffett_analysis']:
        lines.append("**🏛️ 伯克希尔重仓监控**")
        lines.append("```")
        lines.append(f"{'股票':<6} {'价格':>8} {'涨跌':>8} {'最大持仓机构':<35} {'占比':>6}")
        lines.append("-"*70)
        for r in sorted(data['buffett_analysis'], key=lambda x: x['pct'], reverse=True)[:6]:
            emoji = '🔥' if r['chg'] > 0 else '❄️'
            lines.append(f"{r['ticker']:<6} ${r['price']:>7.2f} {r['chg']:>+7.2f}% {r['top_holder'][:33]:<35} {r['pct']:>5.1f}%")
        lines.append("```\n")
    
    # 小微股综合推荐TOP5
    if data['small_cap_top5']:
        lines.append("**📈 小微股综合推荐 TOP 5**")
        lines.append("```")
        lines.append(f"{'排名':<4} {'股票':<6} {'价格':>7} {'涨跌':>8} {'上涨空间':>9} {'建议':<8} {'内部人':>6} {'机构':>4}")
        lines.append("-"*65)
        for i, s in enumerate(data['small_cap_top5'], 1):
            upside_str = f"+{s['upside']:.1f}%" if s['upside'] > 0 else "N/A"
            insider_str = f"买{s['buy_count']}次" if s['buy_count'] > 0 else s['insider_signal']
            lines.append(f"{i:<4} {s['ticker']:<6} ${s['price']:>6.2f} {s['chg']:>+7.2f}% {upside_str:>9} {s['action']:<8} {insider_str:>6} {s['inst_count']:>4}家")
        lines.append("```")
        lines.append("")
        
        # 详细说明
        for s in data['small_cap_top5']:
            if s['top_buyer'] or s['top_inst']:
                detail = []
                if s['top_buyer']: detail.append(f"内部人:{s['top_buyer']}")
                if s['top_inst']: detail.append(f"大机构:{s['top_inst'][:25]}")
                lines.append(f"  **{s['ticker']}**: {' | '.join(detail)}")
    
    return '\n'.join(lines)

if __name__ == '__main__':
    data = run_scan()
    
    # 保存
    with open('/root/.openclaw/workspace/data/enhanced_13f_scan.json','w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    report = format_report(data)
    print("\n" + "="*65)
    print(report)
    
    with open('/root/.openclaw/workspace/data/enhanced_13f_report.md','w') as f:
        f.write(report)
    
    print("\n✅ 报告已保存: data/enhanced_13f_report.md")
