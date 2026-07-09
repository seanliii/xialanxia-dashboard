#!/usr/bin/env python3
"""
每日盈亏模拟脚本
用法: python3 simulate_pnl.py
输出: 当日损益报告，写入 pnl_log.json
"""
import json, urllib.request, time, sys
from datetime import datetime

POSITIONS_FILE = '/root/.openclaw/workspace/portfolio/positions.json'
PNL_LOG_FILE   = '/root/.openclaw/workspace/portfolio/pnl_log.json'

def get_price_tavily(ticker):
    """用 Tavily 搜索最新收盘价"""
    KEY = "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"
    today = datetime.now().strftime("%B %d %Y")
    q = f"{ticker} stock price close {today}"
    data = json.dumps({"api_key": KEY, "query": q, "search_depth": "basic", "max_results": 2}).encode()
    req = urllib.request.Request("https://api.tavily.com/search", data=data,
        headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=8) as r:
        res = json.loads(r.read())
    snippet = ' '.join([x['content'][:300] for x in res.get('results',[])])
    return snippet

def parse_price_from_snippet(snippet, ticker):
    """从 Tavily 摘要中提取价格（简单正则）"""
    import re
    # 匹配 $XXX.XX 或 XXX.XX USD 格式
    patterns = [
        r'\$\s*([\d,]+\.?\d*)',
        r'([\d,]+\.\d{2})\s*USD',
        r'close[d]?\s+at\s+\$?([\d,]+\.?\d*)',
        r'price[d]?\s+at\s+\$?([\d,]+\.?\d*)',
        r'traded\s+at\s+\$?([\d,]+\.?\d*)',
    ]
    for pat in patterns:
        matches = re.findall(pat, snippet, re.IGNORECASE)
        for m in matches:
            try:
                val = float(m.replace(',',''))
                # 合理范围过滤
                if ticker == 'BTC-USD' and 50000 < val < 200000:
                    return val
                elif ticker != 'BTC-USD' and 0.1 < val < 10000:
                    return val
            except: pass
    return None

def run_daily_pnl():
    with open(POSITIONS_FILE) as f:
        portfolio = json.load(f)
    
    today = datetime.now().strftime("%Y-%m-%d")
    initial = portfolio['meta']['initial_capital']
    
    results = []
    total_current_value = 0
    total_cost = 0
    triggered_stops = []
    
    for pos in portfolio['positions']:
        if pos['status'] != 'open':
            continue
        
        ticker = pos['ticker']
        entry  = pos['entry_price']
        shares = pos['shares']
        cost   = pos['cost_basis']
        target = pos['target']
        stop   = pos['stop_loss']
        
        # 获取当前价
        print(f"  Fetching {ticker}...", end=' ', flush=True)
        try:
            snippet = get_price_tavily(ticker)
            price = parse_price_from_snippet(snippet, ticker)
            if not price:
                price = entry  # fallback to entry
                print(f"⚠️ parse failed, using entry ${entry}")
            else:
                print(f"${price:.2f}")
        except Exception as e:
            price = entry
            print(f"ERR: {e}")
        
        # 计算损益
        current_val = price * shares
        pnl_dollar  = current_val - cost
        pnl_pct     = pnl_dollar / cost * 100
        
        # 止损检查
        stop_hit = price <= stop
        target_hit = price >= target
        
        if stop_hit:
            triggered_stops.append({
                'ticker': ticker,
                'reason': f'止损触发 ${price:.2f} <= ${stop}',
                'pnl_pct': pnl_pct
            })
        
        results.append({
            'ticker':      ticker,
            'entry':       entry,
            'current':     round(price, 2),
            'shares':      shares,
            'cost':        cost,
            'current_val': round(current_val, 2),
            'pnl_dollar':  round(pnl_dollar, 2),
            'pnl_pct':     round(pnl_pct, 2),
            'target':      target,
            'stop':        stop,
            'stop_hit':    stop_hit,
            'target_hit':  target_hit,
            'win_rate_contribution': 1 if pnl_pct > 0 else 0
        })
        
        total_current_value += current_val
        total_cost += cost
        time.sleep(0.4)
    
    # 汇总
    cash = initial - total_cost
    total_portfolio_value = total_current_value + cash
    total_pnl = total_portfolio_value - initial
    total_pnl_pct = total_pnl / initial * 100
    
    winning = sum(1 for r in results if r['pnl_pct'] > 0)
    losing  = sum(1 for r in results if r['pnl_pct'] <= 0)
    
    summary = {
        'date':                today,
        'initial_capital':     initial,
        'total_cost_basis':    total_cost,
        'cash_remaining':      cash,
        'total_position_value': round(total_current_value, 2),
        'total_portfolio_value': round(total_portfolio_value, 2),
        'total_pnl_dollar':    round(total_pnl, 2),
        'total_pnl_pct':       round(total_pnl_pct, 4),
        'positions_winning':   winning,
        'positions_losing':    losing,
        'win_rate':            round(winning/(winning+losing)*100, 1) if (winning+losing) > 0 else 0,
        'stop_triggers':       triggered_stops,
        'positions':           results
    }
    
    # 写入日志
    try:
        with open(PNL_LOG_FILE) as f:
            log = json.load(f)
    except:
        log = []
    
    # 去重（同一天更新）
    log = [x for x in log if x['date'] != today]
    log.append(summary)
    
    with open(PNL_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    
    return summary

if __name__ == '__main__':
    print(f"\n{'='*50}")
    print(f"  小蓝虾模拟盘 日报 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")
    print("正在获取最新价格...")
    s = run_daily_pnl()
    
    print(f"\n{'='*50}")
    print(f"  总资产: ${s['total_portfolio_value']:>12,.2f}")
    pnl_sign = '+' if s['total_pnl_dollar'] >= 0 else ''
    print(f"  总损益: {pnl_sign}${s['total_pnl_dollar']:>11,.2f}  ({pnl_sign}{s['total_pnl_pct']:.2f}%)")
    print(f"  持仓胜率: {s['win_rate']}%  ({s['positions_winning']}赢/{s['positions_losing']}亏)")
    print(f"{'='*50}\n")
    
    print(f"{'代码':<8}{'建仓价':>10}{'当前价':>10}{'损益$':>12}{'损益%':>8}{'状态':>8}")
    print('-'*56)
    for r in s['positions']:
        status = '🎯目标!' if r['target_hit'] else ('🛑止损!' if r['stop_hit'] else '   ')
        pnl_sign = '+' if r['pnl_dollar'] >= 0 else ''
        print(f"{r['ticker']:<8}${r['entry']:>8.2f}${r['current']:>8.2f}  {pnl_sign}${r['pnl_dollar']:>9,.0f}  {pnl_sign}{r['pnl_pct']:>5.1f}%  {status}")
    
    if s['stop_triggers']:
        print(f"\n⚠️  止损触发:")
        for st in s['stop_triggers']:
            print(f"  {st['ticker']}: {st['reason']}  ({st['pnl_pct']:+.1f}%)")
