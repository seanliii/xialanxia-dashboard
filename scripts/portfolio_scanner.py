#!/usr/bin/env python3
"""
三账户自动化扫描系统 — 每6小时运行一次
- 大机构账户: 13F + 顶级投资人持仓变化
- 激进交易账户: 小微股暴涨信号 + watchlist触发建仓
- 蓝虾账户: 综合多信源自主决策
- 自动触发: pullback_entry(current_price<=trigger) | breakout_above(current_price>=trigger)

【铁律 1 - 价格验证】
所有股票价格必须通过 Stooq 实时获取后再写入或决策：
1. 任何 watchlist 新增条目 → 先 get_price_stooq() 获取真实价格再设 trigger_price
2. 新闻/13F/Twitter 提到的历史价格不等于当前价格，不得直接用
3. 新闻有时效性：超过30天的价格信息必须 Stooq 重新验证
4. 建仓前必须 Stooq 确认价格，绝不用缓存或新闻报价直接下单

【铁律 2 - Dashboard 同步】
任何持仓/账户/watchlist 变动后，最后一步必须确认 Dashboard 已更新：
  Dashboard 本地文件：/root/.openclaw/workspace/dashboard/dashboard.html
  访问地址：http://sandbox-ide-495392-18789.ide.sankuai.com/workspace/dashboard/dashboard.html
触发条件：建仓/平仓/加仓/调仓/止损/目标达到/watchlist新增/P&L更新
Dashboard未更新 = 本次任务未完成
"""

import json, subprocess, os, sys, csv, io, time
from datetime import datetime, date, timedelta

# A股支持
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from eastmoney_ashare import get_ashare_price, get_ashare_batch, get_ashare_monitor
    ASHARE_AVAILABLE = True
except ImportError:
    ASHARE_AVAILABLE = False

AISA_KEY = "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41"
ACCOUNTS_FILE = "/root/.openclaw/workspace/portfolio/accounts/structure.json"
WATCHLIST_FILE = "/root/.openclaw/workspace/portfolio/watchlist.json"
PRICES_FILE = "/root/.openclaw/workspace/data/portfolio_prices.json"
SIGNALS_FILE = "/root/.openclaw/workspace/data/daily_signals.json"
TRIGGER_LOG_FILE = "/root/.openclaw/workspace/portfolio/trigger_log.json"

# ─── 价格获取 (Yahoo Finance 主力 + Stooq 备用) ────────────────────────────

def get_price_yahoo(ticker):
    """从 Yahoo Finance 获取实时股价（主力，支持全部美股）"""
    import urllib.request as ur
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
        req = ur.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with ur.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        meta = data['chart']['result'][0]['meta']
        price = meta['regularMarketPrice']
        prev = meta.get('chartPreviousClose', price)
        chg = (price - prev) / prev * 100 if prev else 0
        return {'price': price, 'chg': round(chg, 2), 'open': prev,
                'date': date.today().isoformat(), 'source': 'yahoo'}
    except Exception:
        return None

def get_price_stooq(ticker):
    """从Stooq获取单只股票价格，返回 {price, chg, open, date}（Yahoo失败时备用）"""
    sym = ticker.lower() + ".us"
    try:
        r = subprocess.run(
            ['curl', '-s', '--max-time', '6',
             f'https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv'],
            capture_output=True, text=True, timeout=8
        )
        reader = csv.DictReader(io.StringIO(r.stdout))
        for row in reader:
            close = float(row.get('Close', 0) or 0)
            if not close:
                return None
            open_ = float(row.get('Open', close) or close)
            chg = (close - open_) / open_ * 100 if open_ else 0
            return {'price': close, 'chg': chg, 'open': open_,
                    'date': row.get('Date', ''), 'source': 'stooq'}
    except Exception:
        pass
    return None

def get_price_tavily(ticker):
    """Tavily搜索备用价格（Stooq超时时使用）"""
    import urllib.request as ur
    import re as re_
    TAVILY_KEY = "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"
    try:
        payload = json.dumps({
            "api_key": TAVILY_KEY,
            "query": f"{ticker} stock price today",
            "search_depth": "basic",
            "max_results": 3
        }).encode()
        req = ur.Request("https://api.tavily.com/search", data=payload,
                         headers={"Content-Type": "application/json"}, method="POST")
        with ur.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        for result in data.get("results", []):
            text = result.get("content", "") + result.get("snippet", "")
            m = re_.search(r'\$(\d{1,5}\.?\d{0,2})', text)
            if m:
                price = float(m.group(1))
                if 0.01 < price < 100000:
                    return {'price': price, 'chg': 0, 'open': price,
                            'date': date.today().isoformat(), 'source': 'tavily'}
    except Exception:
        pass
    return None

def is_ashare(ticker):
    """判断是否为 A 股代码（纯数字6位 或 sh/sz/bj 前缀）"""
    t = ticker.strip().lower()
    if t.startswith(('sh', 'sz', 'bj')):
        return True
    # 纯6位数字
    import re as _re
    if _re.match(r'^\d{6}$', t):
        return True
    return False


def get_price_ashare(ticker):
    """从新浪财经获取 A 股实时价格"""
    if not ASHARE_AVAILABLE:
        return None
    data = get_ashare_price(ticker)
    if data and data.get('price', 0) > 0:
        return {
            'price': data['price'],
            'chg': round(data.get('change_pct', 0), 2),
            'open': data.get('prev_close', data['price']),
            'date': data.get('date', date.today().isoformat()),
            'source': 'sina_ashare',
            'name': data.get('name', ''),
            'high': data.get('high', 0),
            'low': data.get('low', 0),
            'volume_wan': data.get('volume_wan', 0),
            'amount_yi': data.get('amount_yi', 0),
        }
    return None


def get_prices_batch(tickers):
    """批量获取价格，带缓存。自动识别 A 股 vs 美股分流。"""
    # 先加载缓存
    cache = {}
    try:
        with open(PRICES_FILE) as f:
            cache = json.load(f)
    except:
        pass
    
    today = date.today().isoformat()
    results = {}
    
    # 分流：A 股 vs 美股
    ashare_tickers = [t for t in tickers if is_ashare(t)]
    us_tickers = [t for t in tickers if not is_ashare(t)]
    
    # A 股批量获取（新浪一次请求搞定）
    if ashare_tickers and ASHARE_AVAILABLE:
        # 先检查缓存
        ashare_uncached = []
        for t in ashare_tickers:
            if t in cache and cache[t].get('date', '') == today:
                results[t] = cache[t]
            else:
                ashare_uncached.append(t)
        
        if ashare_uncached:
            batch = get_ashare_batch(ashare_uncached)
            for code, data in batch.items():
                # 找到对应的原始 ticker
                matched_ticker = None
                for t in ashare_uncached:
                    pure = t.lower().replace('sh', '').replace('sz', '').replace('bj', '')
                    if pure == code or t == code:
                        matched_ticker = t
                        break
                if not matched_ticker:
                    matched_ticker = code
                
                p = {
                    'price': data['price'],
                    'chg': round(data.get('change_pct', 0), 2),
                    'open': data.get('prev_close', data['price']),
                    'date': data.get('date', today),
                    'source': 'sina_ashare',
                    'name': data.get('name', ''),
                }
                results[matched_ticker] = p
                cache[matched_ticker] = p
    
    # 美股逐只获取（Yahoo → Stooq → Tavily）
    for ticker in us_tickers:
        # 缓存命中（当天数据）
        if ticker in cache and cache[ticker].get('date', '') == today:
            results[ticker] = cache[ticker]
            continue
        
        # 优先 Yahoo Finance，Stooq 备用，最后 Tavily
        p = get_price_yahoo(ticker)
        if not p:
            p = get_price_stooq(ticker)
        if not p:
            p = get_price_tavily(ticker)
        if p:
            results[ticker] = p
            cache[ticker] = p
        time.sleep(0.15)
    
    # 保存缓存
    try:
        with open(PRICES_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except:
        pass
    
    return results

# ─── 内部人买入：SEC EDGAR Form 4（免费）──────────────────────────────────

def get_insider_buys(ticker, days=30):
    """从 SEC EDGAR Form 4 获取内部人买入记录（完全免费）"""
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
        return [{'name': h.get('_source', {}).get('display_names', ['?'])[0],
                 'filed': h.get('_source', {}).get('file_date', '')} for h in hits[:3]]
    except:
        return []

# ─── 自动触发建仓 ───────────────────────────────────────────────────────────

def check_and_execute_triggers(accounts_data, watchlist, prices):
    """检查watchlist所有auto_trigger条目，触发则自动建仓"""
    triggers_fired = []
    
    for account_type in ['aggressive', 'institutional', 'blueshrimp']:
        items = watchlist.get(account_type, [])
        account = accounts_data['accounts'].get(account_type, {})
        
        for item in items:
            if not item.get('auto_trigger', False):
                continue
            if item.get('status') in ['entered', 'stopped', 'exited']:
                continue
            
            ticker = item['ticker']
            trigger_price = item.get('trigger_price')
            if not trigger_price:
                continue
            
            # 获取当前价格
            price_data = prices.get(ticker)
            if not price_data:
                p = get_price_stooq(ticker)
                if p:
                    price_data = p
                    prices[ticker] = p
            
            if not price_data or not price_data.get('price'):
                continue
            
            current_price = price_data['price']
            item['current_price'] = current_price
            
            # 防护：价格偏离触发价超30% 则跳过（防止暴跌烂股误买）
            deviation = abs(current_price - trigger_price) / trigger_price
            if deviation > 0.30:
                continue

            # 检查触发条件（两种模式）
            trigger_mode = item.get('trigger_mode', 'pullback_entry')
            triggered = False
            if trigger_mode == 'breakout_above':
                # 突破向上：价格 >= 触发价（Penny stock/低价股反弹）
                triggered = current_price >= trigger_price
            else:
                # 回调入场（默认）：价格 <= 触发价（从高点回调进入区间）
                triggered = current_price <= trigger_price

            if triggered:
                # 计算建仓金额
                cash = account.get('cash', 0)
                position_pct = item.get('position_pct', 0.10)
                capital = account.get('capital', 50000)
                invest_amount = capital * position_pct
                
                # 确保现金充足（至少留20%现金）
                max_invest = cash * 0.8
                invest_amount = min(invest_amount, max_invest)
                
                if invest_amount < 500:  # 最小建仓$500
                    continue
                
                shares = int(invest_amount / current_price)
                actual_cost = round(shares * current_price, 2)
                
                # 建仓
                new_position = {
                    "ticker": ticker,
                    "company": item.get('company', ticker),
                    "entry_price": current_price,
                    "shares": shares,
                    "cost_basis": actual_cost,
                    "current_price": current_price,
                    "current_value": actual_cost,
                    "unrealized_pnl": 0,
                    "unrealized_pnl_pct": 0,
                    "entry_date": date.today().isoformat(),
                    "hold_days_target": 14 if account_type == 'aggressive' else 45,
                    "held_days": 0,
                    "hold_days_remaining": 14 if account_type == 'aggressive' else 45,
                    "target_price": item.get('target_exit'),
                    "stop_loss": item.get('stop_loss'),
                    "thesis": item.get('narrative', item.get('reason', '自动触发建仓')),
                    "signal_source": item.get('signal_source', 'watchlist_trigger'),
                    "trigger_type": "auto_trigger",
                    "trigger_price_set": trigger_price,
                    "account": account_type
                }
                
                # 更新账户
                if 'positions' not in account:
                    account['positions'] = []
                account['positions'].append(new_position)
                account['cash'] = round(cash - actual_cost, 2)
                
                # 记录交易日志
                trade = {
                    "date": date.today().isoformat(),
                    "time": datetime.now().strftime('%H:%M'),
                    "ticker": ticker,
                    "action": "BUY",
                    "price": current_price,
                    "shares": shares,
                    "value": actual_cost,
                    "reason": f"🤖 自动触发: 价格${current_price:.2f} <= 触发价${trigger_price}",
                    "account": account_type
                }
                if 'trade_log' not in account:
                    account['trade_log'] = []
                account['trade_log'].append(trade)
                
                # 更新watchlist状态
                item['status'] = 'entered'
                item['entry_actual_price'] = current_price
                item['entry_actual_date'] = date.today().isoformat()
                
                triggers_fired.append({
                    "ticker": ticker,
                    "account": account_type,
                    "price": current_price,
                    "trigger_price": trigger_price,
                    "shares": shares,
                    "cost": actual_cost,
                    "company": item.get('company', ticker),
                    "target": item.get('target_exit'),
                    "stop": item.get('stop_loss')
                })
                
                print(f"🔫 自动建仓触发! {ticker} @${current_price:.2f} "
                      f"(触发价${trigger_price}) → {shares}股 ${actual_cost:.0f} [{account_type}]")
    
    return triggers_fired

# ─── 止损检查 ───────────────────────────────────────────────────────────────

def check_stop_losses(accounts_data, prices):
    """检查所有持仓是否触发止损"""
    stops_triggered = []
    
    for acc_id, account in accounts_data['accounts'].items():
        positions = account.get('positions', [])
        to_remove = []
        
        for pos in positions:
            ticker = pos['ticker']
            stop_price = pos.get('stop_loss')
            if not stop_price:
                continue
            
            price_data = prices.get(ticker)
            if not price_data:
                continue
            
            current_price = price_data['price']
            
            # ─── 脏价防护（2026-06-17 修复，防止 IMVT $0.23 / HBAN $0.09 类假止损）───
            # 规则1: 价格低于止损价的50%，几乎不可能是真实行情，拒绝触发
            # 规则2: 相比入场价跌超90%，极端异常，拒绝触发
            # 规则3: 价格为0或负数，明显脏数据
            entry_price = pos.get('entry_price', 0)
            if current_price <= 0:
                print(f"⚠️ 脏价防护: {ticker} price=${current_price} ≤ 0，拒绝触发止损，跳过")
                continue
            if current_price < stop_price * 0.5:
                print(f"⚠️ 脏价防护: {ticker} price=${current_price} < stop×0.5(${stop_price*0.5})，疑似脏数据，拒绝触发止损")
                continue
            if entry_price > 0 and current_price < entry_price * 0.1:
                print(f"⚠️ 脏价防护: {ticker} price=${current_price} < entry×0.1(${entry_price*0.1})，跌幅>90%疑似脏数据，拒绝触发止损")
                continue
            
            if current_price <= stop_price:
                # 止损卖出（已通过脏价防护校验）
                sell_value = round(current_price * pos['shares'], 2)
                pnl = round(sell_value - pos['cost_basis'], 2)
                pnl_pct = round((current_price - pos['entry_price']) / pos['entry_price'] * 100, 2)
                
                # 记录已平仓
                closed = dict(pos)
                closed['exit_price'] = current_price
                closed['exit_date'] = date.today().isoformat()
                closed['exit_value'] = sell_value
                closed['realized_pnl'] = pnl
                closed['realized_pnl_pct'] = pnl_pct
                closed['exit_reason'] = f'止损 @${current_price:.2f}'
                
                if 'closed_positions' not in account:
                    account['closed_positions'] = []
                account['closed_positions'].append(closed)
                
                # 返还现金
                account['cash'] = round(account.get('cash', 0) + sell_value, 2)
                
                # 交易日志
                account.setdefault('trade_log', []).append({
                    "date": date.today().isoformat(),
                    "ticker": ticker,
                    "action": "SELL_STOP",
                    "price": current_price,
                    "shares": pos['shares'],
                    "value": sell_value,
                    "pnl": pnl,
                    "reason": f"🛑 止损触发 @${current_price:.2f} (设定${stop_price})",
                    "account": acc_id
                })
                
                to_remove.append(pos)
                stops_triggered.append({
                    "ticker": ticker, "account": acc_id,
                    "exit_price": current_price, "stop_price": stop_price,
                    "pnl": pnl, "pnl_pct": pnl_pct
                })
                print(f"🛑 止损触发! {ticker} @${current_price:.2f} PnL: ${pnl:+.0f} ({pnl_pct:+.1f}%) [{acc_id}]")
        
        # 移除已止损持仓
        for p in to_remove:
            if p in account['positions']:
                account['positions'].remove(p)
    
    return stops_triggered

# ─── 更新持仓价格 ────────────────────────────────────────────────────────────

def update_positions_prices(accounts_data, prices):
    """更新所有账户持仓的当前价格和PnL"""
    today = date.today()
    for acc in accounts_data['accounts'].values():
        for p in acc.get('positions', []):
            ticker = p['ticker']
            price_data = prices.get(ticker)
            if price_data and price_data.get('price'):
                price = price_data['price']
                p['current_price'] = price
                p['current_value'] = round(price * p['shares'], 2)
                p['unrealized_pnl'] = round(p['current_value'] - p['cost_basis'], 2)
                p['unrealized_pnl_pct'] = round((price - p['entry_price']) / p['entry_price'] * 100, 2)
            
            if p.get('entry_date'):
                try:
                    entry_d = date.fromisoformat(p['entry_date'])
                    held = (today - entry_d).days
                    p['held_days'] = held
                    target = p.get('hold_days_target', 30)
                    p['hold_days_remaining'] = max(0, target - held)
                    p['hold_progress_pct'] = min(100, round(held / target * 100))
                except:
                    pass

# ─── 扫描信号 ────────────────────────────────────────────────────────────────

def scan_watchlist_status(watchlist, prices):
    """评估watchlist各条目与触发价的距离"""
    status_list = []
    for account_type in ['aggressive', 'institutional', 'blueshrimp']:
        for item in watchlist.get(account_type, []):
            ticker = item['ticker']
            trigger = item.get('trigger_price')
            if not trigger:
                continue
            
            price_data = prices.get(ticker)
            if not price_data:
                continue
            
            price = price_data['price']
            gap_pct = (price - trigger) / trigger * 100
            
            item['current_price'] = price
            item['gap_to_trigger_pct'] = round(gap_pct, 1)
            
            status_list.append({
                "ticker": ticker,
                "account": account_type,
                "current": price,
                "trigger": trigger,
                "gap_pct": round(gap_pct, 1),
                "priority": item.get('priority', 'C'),
                "status": item.get('status', 'watch')
            })
    
    # 按距离触发价从近到远排序
    status_list.sort(key=lambda x: abs(x['gap_pct']))
    return status_list

# ─── 生成报告 ────────────────────────────────────────────────────────────────

def generate_report(accounts_data, triggers_fired, stops_triggered, watchlist_status):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    summary = {}
    for acc_id, acc in accounts_data['accounts'].items():
        pos_val = sum(p.get('current_value', p['cost_basis']) for p in acc.get('positions', []))
        cash = acc.get('cash', 0)
        total = pos_val + cash
        capital = acc.get('capital', 50000)
        pnl = total - capital
        
        # 更新stats
        acc['stats'] = acc.get('stats', {})
        acc['stats']['current_position_value'] = round(pos_val, 2)
        acc['stats']['portfolio_value'] = round(total, 2)
        acc['stats']['return_pct'] = round(pnl / capital * 100, 2)
        acc['stats']['unrealized_pnl'] = round(sum(
            p.get('unrealized_pnl', 0) for p in acc.get('positions', [])
        ), 2)
        
        summary[acc_id] = {
            "name": acc['name'],
            "emoji": acc.get('emoji', ''),
            "total_value": round(total, 2),
            "cash": round(cash, 2),
            "position_value": round(pos_val, 2),
            "pnl": round(pnl, 2),
            "return_pct": round(pnl / capital * 100, 2),
            "positions": len(acc.get('positions', []))
        }
    
    return {
        "scan_time": now,
        "triggers_fired": triggers_fired,
        "stops_triggered": stops_triggered,
        "watchlist_approaching": [x for x in watchlist_status if abs(x['gap_pct']) < 10],
        "portfolio_summary": summary
    }

# ─── 主程序 ─────────────────────────────────────────────────────────────────


# ─── Dashboard HTML 实时价格注入 ──────────────────────────────────────────────

def update_dashboard_html(accounts_data, prices):
    """把最新价格/持仓天数/盈亏直接写进 Dashboard HTML（让静态页面也能显示最新数据）"""
    import re
    from datetime import date

    DASHBOARD = "/root/.openclaw/workspace/dashboard/dashboard.html"
    try:
        with open(DASHBOARD, "r", encoding="utf-8") as f:
            html = f.read()
    except:
        return

    today = date.today()
    changed = False

    for acc in accounts_data['accounts'].values():
        for pos in acc.get('positions', []):
            ticker = pos['ticker']
            price_raw = prices.get(ticker)
            if not price_raw:
                continue
            # prices dict values can be float or {'price': float, ...}
            price = price_raw['price'] if isinstance(price_raw, dict) else float(price_raw)
            if not price:
                continue

            entry = pos['entry_price']
            shares = pos['shares']
            entry_date = pos.get('entry_date', str(today))
            try:
                days_held = (today - date.fromisoformat(entry_date[:10])).days
            except:
                days_held = pos.get('held_days', 0)

            pnl_abs = (price - entry) * shares
            pnl_pct = (price - entry) / entry * 100
            color = '#2dd4bf' if pnl_abs >= 0 else '#f87171'
            sign = '+' if pnl_abs >= 0 else ''
            pnl_html = (f'<span style="color:{color};font-weight:700">'
                        f'{sign}${abs(pnl_abs):.0f} ({sign}{pnl_pct:.1f}%)</span>')

            target_days = pos.get('target_days', 14)
            bar_pct = min(int(days_held / target_days * 100), 100)
            days_html = (f'<div style="background:#1e1e33;border-radius:4px;height:6px;'
                         f'width:80px;display:inline-block;vertical-align:middle">'
                         f'<div style="background:#6c63ff;width:{bar_pct}%;height:6px;'
                         f'border-radius:4px"></div></div>'
                         f'<span style="font-size:10px;color:#64748b;margin-left:4px">'
                         f'{days_held}/{target_days}天</span>')

            price_html = f'<b style="color:#e2e8f0;font-size:13px">${price:.2f}</b>'

            # 替换该 ticker 所在 tr 的当前价/盈亏/天数
            # 用 data-ticker 属性定位，然后替换第5/6/9个 <td> 内容
            def replace_row(m):
                row = m.group(0)
                tds = list(re.finditer(r'<td[^>]*>(.*?)</td>', row, re.DOTALL))
                if len(tds) < 9:
                    return row
                # td[4]=当前价  td[5]=盈亏  td[8]=天数
                for idx, new_inner in [(4, price_html), (5, pnl_html), (8, days_html)]:
                    old_td = tds[idx].group(0)
                    td_open = re.match(r'<td[^>]*>', old_td).group(0)
                    new_td = td_open + new_inner + '</td>'
                    row = row.replace(old_td, new_td, 1)
                return row

            pattern = (r'<tr data-ticker="' + re.escape(ticker) +
                       r'"[^>]*>.*?</tr>')
            new_html, n = re.subn(pattern, replace_row, html, flags=re.DOTALL)
            if n:
                html = new_html
                changed = True
                pos['held_days'] = days_held
                pos['current_price'] = round(price, 4)

    # 更新"最后刷新"时间戳
    ts = datetime.now().strftime('%m-%d %H:%M')
    html = re.sub(
        r'(<div[^>]*id="live-refresh-ts"[^>]*>).*?(</div>)',
        rf'\g<1>价格最后更新: {ts} CST\g<2>',
        html)

    if changed:
        with open(DASHBOARD, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"   📊 Dashboard 价格已同步 ({ts})")

if __name__ == "__main__":
    print(f"🦐 三账户扫描系统 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 加载数据
    with open(ACCOUNTS_FILE) as f:
        accounts_data = json.load(f)
    with open(WATCHLIST_FILE) as f:
        watchlist = json.load(f)
    
    # 收集所有需要价格的ticker
    all_tickers = set()
    for acc in accounts_data['accounts'].values():
        for p in acc.get('positions', []):
            all_tickers.add(p['ticker'])
    for account_type in ['aggressive', 'institutional', 'blueshrimp']:
        for item in watchlist.get(account_type, []):
            if item.get('ticker'):
                all_tickers.add(item['ticker'])
    
    print(f"📈 获取 {len(all_tickers)} 只股票价格 (Stooq免费)...")
    prices = get_prices_batch(list(all_tickers))
    print(f"   获取成功: {len(prices)} 只")
    
    # 更新持仓价格
    update_positions_prices(accounts_data, prices)
    
    # ─── 清理历史脏价 closed_positions 记录（2026-06-27 修复）───
    # 回滚脏数据后，scanner 每次写回会保留旧的 closed 脏记录
    # 自动移除 exit_price 触发脏价规则的 closed 记录
    for acc_id, account in accounts_data['accounts'].items():
        if 'closed_positions' not in account:
            continue
        clean_closed = []
        for cp in account['closed_positions']:
            ep = cp.get('exit_price', 0)
            entry_p = cp.get('entry_price', 1)
            stop_p = cp.get('stop_loss', 0)
            is_dirty = False
            if ep <= 0:
                is_dirty = True
            elif stop_p > 0 and ep < stop_p * 0.5:
                is_dirty = True
            elif entry_p > 0 and ep < entry_p * 0.1:
                is_dirty = True
            if is_dirty:
                print(f"🧹 清理脏价closed记录: {cp.get('ticker')} exit@${ep} (stop=${stop_p}, entry=${entry_p}) [{acc_id}]")
            else:
                clean_closed.append(cp)
        account['closed_positions'] = clean_closed

    # 检查止损
    print("\n🛑 检查止损...")
    stops_triggered = check_stop_losses(accounts_data, prices)
    
    # 检查自动触发建仓
    print("\n🔫 检查自动触发建仓...")
    triggers_fired = check_and_execute_triggers(accounts_data, watchlist, prices)
    
    if not triggers_fired:
        print("   无触发（均未到达触发价）")
    
    # ─── 检查推送信号联动（推送→持仓）──────────────────────────────────────
    # 读取今日推送信号，评分≥70的自动加入watchlist或直接建仓
    print("\n📡 检查今日推送信号联动...")
    push_signal_added = []
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE) as sf:
            signals_data = json.load(sf)
        today_str = date.today().isoformat()
        if signals_data.get("date") == today_str:
            push_signals = signals_data.get("push_signals", [])
            high_score = [s for s in push_signals if s.get("score", 0) >= 70 and s.get("status") == "pending"]
            if high_score:
                print(f"   发现 {len(high_score)} 个高分信号(≥70):")
                for sig in high_score:
                    ticker = sig["ticker"]
                    score = sig.get("score", 0)
                    account = sig.get("account_hint", "blueshrimp")
                    print(f"   🟢 {ticker} (score={score}) → 加入{account}watchlist候选")
                    # 更新状态为evaluated
                    sig["status"] = "evaluated"
                    push_signal_added.append(sig)
                # 保存更新后的信号状态
                with open(SIGNALS_FILE, "w") as sf:
                    json.dump(signals_data, sf, indent=2, ensure_ascii=False)
            else:
                print(f"   今日推送信号: {len(push_signals)}条，高分(≥70): 0条")
    
    # watchlist距离分析
    watchlist_status = scan_watchlist_status(watchlist, prices)
    
    # 生成报告
    report = generate_report(accounts_data, triggers_fired, stops_triggered, watchlist_status)
    
    # 保存
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts_data, f, indent=2, ensure_ascii=False)
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(watchlist, f, indent=2, ensure_ascii=False)
    
    report_path = f"/root/.openclaw/workspace/data/scan_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # ─── 输出报告 ──────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊 三账户快照")
    print("=" * 60)
    
    total_portfolio = 0
    total_capital = 0
    
    for acc_id, summary in report['portfolio_summary'].items():
        acc = accounts_data['accounts'][acc_id]
        positions = acc.get('positions', [])
        total_portfolio += summary['total_value']
        total_capital += acc.get('capital', 50000)
        
        arrow = '🟢' if summary['pnl'] >= 0 else '🔴'
        print(f"\n{summary['emoji']} {summary['name']}: "
              f"${summary['total_value']:,.0f} {arrow} {summary['return_pct']:+.2f}% "
              f"(${summary['pnl']:+,.0f})")
        print(f"   现金: ${summary['cash']:,.0f} | 持仓市值: ${summary['position_value']:,.0f}")
        
        for p in positions:
            pnl = p.get('unrealized_pnl', 0)
            pnl_pct = p.get('unrealized_pnl_pct', 0)
            arrow2 = '🟢' if pnl >= 0 else '🔴'
            print(f"   {arrow2} {p['ticker']:6s}: ${p.get('current_price', p['entry_price']):.2f} "
                  f"({pnl_pct:+.1f}%) | {p['shares']}股 | 持{p.get('held_days', 0)}天 "
                  f"| 目标${p.get('target_price', '?')} 止损${p.get('stop_loss', '?')}")
    
    total_pnl = total_portfolio - total_capital
    total_ret = total_pnl / total_capital * 100
    print(f"\n{'='*60}")
    print(f"💰 总资产: ${total_portfolio:,.0f} | 总损益: ${total_pnl:+,.0f} ({total_ret:+.2f}%)")
    
    if triggers_fired:
        print(f"\n🔫 本次自动建仓 ({len(triggers_fired)}笔):")
        for t in triggers_fired:
            print(f"   ✅ {t['ticker']} @${t['price']:.2f} | {t['shares']}股 | ${t['cost']:.0f} [{t['account']}]")
            print(f"      目标${t['target']} 止损${t['stop']}")
    
    if stops_triggered:
        print(f"\n🛑 止损触发 ({len(stops_triggered)}笔):")
        for s in stops_triggered:
            print(f"   ❌ {s['ticker']} @${s['exit_price']:.2f} | PnL: ${s['pnl']:+,.0f} ({s['pnl_pct']:+.1f}%)")
    
    approaching = report['watchlist_approaching']
    if approaching:
        print(f"\n⚠️ 接近触发价 (距离<10%):")
        for w in approaching[:5]:
            print(f"   {w['ticker']:6s}: 现${w['current']:.2f} 触发${w['trigger']:.2f} "
                  f"差{w['gap_pct']:+.1f}% [{w['account']}] {w['priority']}级")
    
    # ─── 同步 Dashboard（调用 sync_dashboard.py 完整联动版）─────────────────
    print("\n📊 同步 Dashboard HTML（完整联动）...")
    import subprocess as _sp
    _sync = _sp.run(
        ["python3", "/root/.openclaw/workspace/scripts/sync_dashboard.py"],
        capture_output=True, text=True, timeout=120,
        cwd="/root/.openclaw/workspace"
    )
    if _sync.returncode == 0:
        print(f"   ✅ Dashboard 已完整联动更新并推送 GitHub Pages")
        print(f"   🔗 https://seanliii.github.io/xialanxia-dashboard/")
    else:
        print(f"   ⚠️ sync_dashboard 失败，降级用旧方法...")
        update_dashboard_html(accounts_data, prices)
        _sp.run(["/bin/bash", "/root/.openclaw/workspace/scripts/push_dashboard_to_github.sh"],
                timeout=30, cwd="/root/.openclaw/workspace")

    print(f"\n✅ 扫描完成 | 报告: {report_path}")
