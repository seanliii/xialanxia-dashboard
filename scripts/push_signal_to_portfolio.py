#!/usr/bin/env python3
"""
push_signal_to_portfolio.py — 推送→持仓联动核心脚本

每次推送情报后调用此脚本，将推送内容中发现的投资信号写入 daily_signals.json
portfolio_scanner.py 扫描时会自动读取这些信号作为建仓候选

用法：
  python3 push_signal_to_portfolio.py --ticker NVDA --signal "Morgan Stanley上调目标价$280" --score 75
  python3 push_signal_to_portfolio.py --from-push-summary "推送内容..." --auto-extract

信号来源类型：
  - insider_buy: 内部人买入 (SEC Form 4)
  - institutional_13f: 机构13F持仓
  - twitter_momentum: Twitter社交动量
  - earnings_catalyst: 财报/FDA/并购催化剂
  - funding_news: 融资/IPO消息
"""

import os
os.environ["https_proxy"] = "http://10.59.78.158:3128"
os.environ["http_proxy"] = "http://10.59.78.158:3128"
os.environ["HTTPS_PROXY"] = "http://10.59.78.158:3128"
os.environ["HTTP_PROXY"] = "http://10.59.78.158:3128"
import json, os, sys, argparse
from datetime import datetime, date

WORKSPACE = "/root/.openclaw/workspace"
SIGNALS_FILE = f"{WORKSPACE}/data/daily_signals.json"
WATCHLIST_FILE = f"{WORKSPACE}/portfolio/watchlist.json"
# 使用美团内部 Maas 接口
MAAS_URL = "https://mmc.sankuai.com/openclaw/v1/chat/completions"

def _get_maas_key():
    try:
        with open('/root/.openclaw/openclaw.json') as f:
            d = json.load(f)
        return d['models']['providers']['kubeplex-maas']['apiKey']
    except Exception:
        return ""


def load_signals():
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE) as f:
            return json.load(f)
    return {"date": date.today().isoformat(), "new_signals": [], "push_signals": []}


def save_signals(data):
    with open(SIGNALS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_push_signal(ticker, company, signal_text, signal_type, score, source, 
                    price=None, target=None, stop_loss=None, hold_days=30, account_hint=None):
    """将推送信号写入 daily_signals.json 的 push_signals 区块"""
    data = load_signals()
    today = date.today().isoformat()
    
    # 如果日期变了，重置push_signals
    if data.get("date") != today:
        data = {"date": today, "new_signals": data.get("new_signals", []), "push_signals": []}
    
    if "push_signals" not in data:
        data["push_signals"] = []
    
    # 检查是否已存在同一ticker+同一signal的条目（去重）
    existing = [s for s in data["push_signals"] if s.get("ticker") == ticker and s.get("signal")[:50] == signal_text[:50]]
    if existing:
        print(f"⏭️ 信号已存在，跳过: {ticker} - {signal_text[:50]}")
        return
    
    signal = {
        "ticker": ticker,
        "company": company,
        "signal": signal_text,
        "signal_type": signal_type,  # insider_buy / institutional_13f / twitter_momentum / earnings_catalyst
        "score": score,  # 0-100，≥70触发建仓评估
        "source": source,  # 来自哪条推送（如"09:05早间情报"）
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M CST"),
        "price": price,
        "target": target,
        "stop_loss": stop_loss,
        "hold_days": hold_days,
        "account_hint": account_hint or "blueshrimp",  # 建议哪个账户
        "status": "pending",  # pending → evaluated → watchlist → position / dismissed
    }
    
    data["push_signals"].append(signal)
    save_signals(data)
    print(f"✅ 信号已写入: {ticker} (score={score}) [{signal_type}] - {signal_text[:60]}")
    return signal


def auto_extract_from_push(push_text):
    """用 GLM 从推送文本中自动提取投资信号"""
    import urllib.request as ur
    
    prompt = f"""从以下推送内容中提取投资信号。只提取有明确股票代码(ticker)的信号。
输出JSON数组，每个元素包含:
- ticker: 股票代码(大写)
- company: 公司名
- signal: 信号描述(一句话)
- signal_type: insider_buy/institutional_13f/twitter_momentum/earnings_catalyst/funding_news之一
- score: 投资价值评分0-100(内部人买入+催化剂=高分，普通新闻=低分)
- account_hint: institutional/aggressive/blueshrimp(建议哪个账户)

推送内容：
{push_text[:2000]}

只返回JSON数组，不含其他文字。如果没有明确股票信号返回[]。"""

    apikey = _get_maas_key()
    body_data = json.dumps({
        "model": "catclaw-proxy-model",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "stream": False
    }).encode()
    
    req = ur.Request(MAAS_URL, data=body_data, headers={
        "Authorization": f"Bearer {apikey}",
        "Content-Type": "application/json"
    })
    
    with ur.urlopen(req, timeout=25) as r:
        raw_resp = r.read().decode()
    
    # 解析SSE格式
    content = ""
    for line in raw_resp.split('\n'):
        line = line.strip()
        raw = None
        if line.startswith('data:data:'):
            raw = line[len('data:data:'):].strip()
        elif line.startswith('data:'):
            raw = line[5:].strip()
        if not raw or raw == '[DONE]':
            continue
        try:
            chunk = json.loads(raw)
            delta = chunk.get('choices', [{}])[0].get('delta', {})
            content += delta.get('content', '')
            if chunk.get('lastOne'):
                break
        except:
            pass
    content = content.strip()
    # 尝试提取JSON
    if "[" in content:
        start = content.index("[")
        end = content.rindex("]") + 1
        signals = json.loads(content[start:end])
        return signals
    return []


def main():
    parser = argparse.ArgumentParser(description="推送→持仓联动信号写入")
    parser.add_argument("--ticker", help="股票代码")
    parser.add_argument("--company", default="", help="公司名称")
    parser.add_argument("--signal", help="信号描述")
    parser.add_argument("--type", dest="signal_type", default="twitter_momentum", help="信号类型")
    parser.add_argument("--score", type=int, default=60, help="投资评分(0-100)")
    parser.add_argument("--source", default="手动添加", help="信号来源")
    parser.add_argument("--price", type=float, help="当前价格")
    parser.add_argument("--target", type=float, help="目标价格")
    parser.add_argument("--stop", type=float, help="止损价格")
    parser.add_argument("--days", type=int, default=30, help="预计持有天数")
    parser.add_argument("--account", default="blueshrimp", help="建议账户")
    parser.add_argument("--from-push-summary", dest="push_summary", help="从推送摘要自动提取")
    
    args = parser.parse_args()
    
    if args.push_summary:
        print("🤖 自动提取推送信号...")
        signals = auto_extract_from_push(args.push_summary)
        print(f"找到 {len(signals)} 个信号:")
        for s in signals:
            result = add_push_signal(
                ticker=s["ticker"],
                company=s.get("company", ""),
                signal_text=s["signal"],
                signal_type=s.get("signal_type", "twitter_momentum"),
                score=s.get("score", 60),
                source=args.source or "推送自动提取",
                account_hint=s.get("account_hint", "blueshrimp")
            )
            if result:
                print(f"  {s['ticker']}: {s['signal'][:60]} (score={s['score']})")
    
    elif args.ticker and args.signal:
        add_push_signal(
            ticker=args.ticker,
            company=args.company,
            signal_text=args.signal,
            signal_type=args.signal_type,
            score=args.score,
            source=args.source,
            price=args.price,
            target=args.target,
            stop_loss=args.stop,
            hold_days=args.days,
            account_hint=args.account
        )
    
    else:
        # 显示当日所有信号
        data = load_signals()
        push_signals = data.get("push_signals", [])
        high_score = [s for s in push_signals if s.get("score", 0) >= 70]
        print(f"\n📊 今日推送信号汇总 ({data.get('date', 'unknown')})")
        print(f"总信号: {len(push_signals)} | 高分(≥70): {len(high_score)}")
        
        for s in sorted(push_signals, key=lambda x: x.get("score", 0), reverse=True):
            status = "🟢" if s.get("score", 0) >= 70 else "🟡" if s.get("score", 0) >= 50 else "⚪"
            print(f"\n{status} [{s['ticker']}] score={s.get('score')} | {s.get('signal_type')}")
            print(f"   {s['signal'][:80]}")
            print(f"   账户: {s.get('account_hint')} | 来源: {s.get('source')}")


if __name__ == "__main__":
    main()
