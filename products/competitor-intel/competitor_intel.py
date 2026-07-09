#!/usr/bin/env python3
"""
AI 竞品情报日报 — 自动化竞品情报生成器
输入一个 ticker，调用多个数据源生成结构化竞品情报报告。
"""

import sys
import os
import json
import urllib.request
import urllib.error
import argparse
from datetime import datetime, timezone, timedelta

# 绕过代理
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)

API_KEY = "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41"
BASE_URL = "https://api.aisa.one/apis/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 创建不使用代理的 opener
_no_proxy_handler = urllib.request.ProxyHandler({})
_opener = urllib.request.build_opener(_no_proxy_handler)


def api_get(endpoint, params=None):
    """GET request to AISA API."""
    url = f"{BASE_URL}{endpoint}"
    if params:
        query = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items())
        url = f"{url}?{query}"
    req = urllib.request.Request(url, headers=HEADERS, method="GET")
    try:
        with _opener.open(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception) as e:
        return {"error": str(e)}


def api_post(endpoint, body):
    """POST request to AISA API."""
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
    try:
        with _opener.open(req, timeout=45) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception) as e:
        return {"error": str(e)}


def fetch_twitter(ticker):
    """获取 Twitter 最新讨论。"""
    return api_get("/twitter/tweet/advanced_search", {
        "query": f"${ticker} news",
        "queryType": "Latest"
    })


def fetch_financial_news(ticker):
    """获取财经新闻。"""
    return api_get("/financial/news", {"ticker": ticker})


def fetch_insider_trades(ticker):
    """获取内部人交易。"""
    return api_get("/financial/insider-trades", {"ticker": ticker})


def fetch_institutional_ownership(ticker):
    """获取机构持仓。"""
    return api_get("/financial/institutional-ownership", {"ticker": ticker})


def fetch_financial_metrics(ticker):
    """获取财务指标快照。"""
    return api_get("/financial/financial-metrics/snapshot", {"ticker": ticker})


def fetch_analyst_estimates(ticker):
    """获取分析师预测。"""
    return api_get("/financial/analyst-estimates", {"ticker": ticker})


def fetch_perplexity_analysis(ticker):
    """通过 Perplexity Sonar Pro 获取深度分析。"""
    body = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "user",
                "content": f"请用中文分析 {ticker} 公司的最新竞品动态、市场地位变化、重大战略调整、以及未来3个月可能的催化剂事件。重点关注：1) 主要竞争对手的最新动作 2) 行业格局变化 3) 值得关注的风险和机会。请提供具体数据和来源。"
            }
        ]
    }
    return api_post("/perplexity/sonar-pro", body)


def format_twitter_section(data):
    """格式化 Twitter 板块。"""
    if "error" in data:
        return "⚠️ Twitter 数据获取失败\n"
    
    tweets = data.get("tweets", data.get("data", []))
    if not tweets:
        # 尝试其他可能的数据结构
        if isinstance(data, list):
            tweets = data
        elif isinstance(data, dict):
            for key in data:
                if isinstance(data[key], list) and len(data[key]) > 0:
                    tweets = data[key]
                    break
    
    if not tweets:
        return "暂无相关 Twitter 讨论\n"
    
    lines = []
    count = 0
    for tweet in tweets[:8]:
        if isinstance(tweet, dict):
            text = tweet.get("text", tweet.get("full_text", tweet.get("content", "")))
            user = tweet.get("user", {})
            if isinstance(user, dict):
                username = user.get("name", user.get("screen_name", "Unknown"))
            else:
                username = tweet.get("userName", tweet.get("author", "Unknown"))
            likes = tweet.get("favorite_count", tweet.get("likes", tweet.get("likeCount", "")))
            created = tweet.get("created_at", tweet.get("createdAt", ""))
            
            if text:
                line = f"- **@{username}**"
                if likes:
                    line += f" (❤️ {likes})"
                line += f": {text[:200]}"
                if created:
                    line += f"\n  _({created})_"
                lines.append(line)
                count += 1
        if count >= 8:
            break
    
    return "\n".join(lines) if lines else "暂无相关 Twitter 讨论\n"


def format_news_section(data):
    """格式化新闻板块。"""
    if "error" in data:
        return "⚠️ 新闻数据获取失败\n"
    
    news_list = data if isinstance(data, list) else data.get("data", data.get("news", []))
    if not news_list:
        for key in data if isinstance(data, dict) else []:
            if isinstance(data[key], list):
                news_list = data[key]
                break
    
    if not news_list:
        return "暂无最新新闻\n"
    
    lines = []
    for item in news_list[:10]:
        if isinstance(item, dict):
            title = item.get("title", item.get("headline", ""))
            source = item.get("source", item.get("publisher", ""))
            date = item.get("publishedDate", item.get("date", item.get("published_at", "")))
            url = item.get("url", item.get("link", ""))
            
            if title:
                line = f"- **{title}**"
                if source:
                    line += f" — _{source}_"
                if date:
                    line += f" ({date[:10]})"
                lines.append(line)
    
    return "\n".join(lines) if lines else "暂无最新新闻\n"


def format_insider_trades(data):
    """格式化内部人交易。"""
    if "error" in data:
        return "⚠️ 内部人交易数据获取失败\n"
    
    trades = data if isinstance(data, list) else data.get("data", data.get("trades", []))
    if not trades:
        for key in data if isinstance(data, dict) else []:
            if isinstance(data[key], list):
                trades = data[key]
                break
    
    if not trades:
        return "暂无内部人交易记录\n"
    
    lines = []
    for trade in trades[:8]:
        if isinstance(trade, dict):
            name = trade.get("reportingName", trade.get("ownerName", trade.get("name", "Unknown")))
            ttype = trade.get("transactionType", trade.get("type", ""))
            shares = trade.get("securitiesTransacted", trade.get("shares", trade.get("amount", "")))
            price = trade.get("price", "")
            date = trade.get("filingDate", trade.get("transactionDate", trade.get("date", "")))
            
            line = f"- **{name}**"
            if ttype:
                emoji = "🟢 买入" if "buy" in str(ttype).lower() or "purchase" in str(ttype).lower() else "🔴 卖出"
                line += f" {emoji}"
            if shares:
                line += f" {shares:,} 股" if isinstance(shares, (int, float)) else f" {shares} 股"
            if price:
                line += f" @ ${price}"
            if date:
                line += f" ({date[:10]})"
            lines.append(line)
    
    return "\n".join(lines) if lines else "暂无内部人交易记录\n"


def format_institutional(data):
    """格式化机构持仓。"""
    if "error" in data:
        return "⚠️ 机构持仓数据获取失败\n"
    
    holders = data if isinstance(data, list) else data.get("data", data.get("holders", []))
    if not holders:
        for key in data if isinstance(data, dict) else []:
            if isinstance(data[key], list):
                holders = data[key]
                break
    
    if not holders:
        return "暂无机构持仓数据\n"
    
    lines = []
    for holder in holders[:10]:
        if isinstance(holder, dict):
            name = holder.get("investorName", holder.get("holder", holder.get("name", "Unknown")))
            shares = holder.get("sharesNumber", holder.get("shares", holder.get("position", "")))
            change = holder.get("changeInSharesNumberPercentage", holder.get("change", ""))
            value = holder.get("totalInvested", holder.get("value", ""))
            
            line = f"- **{name}**"
            if shares:
                if isinstance(shares, (int, float)):
                    line += f": {shares:,.0f} 股"
                else:
                    line += f": {shares} 股"
            if change:
                if isinstance(change, (int, float)):
                    emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    line += f" {emoji} {change:+.2f}%"
            if value:
                if isinstance(value, (int, float)):
                    line += f" (价值 ${value/1e6:.1f}M)"
            lines.append(line)
    
    return "\n".join(lines) if lines else "暂无机构持仓数据\n"


def format_metrics(data):
    """格式化财务指标。"""
    if "error" in data:
        return "⚠️ 财务指标获取失败\n"
    
    metrics = data
    if isinstance(data, list) and len(data) > 0:
        metrics = data[0]
    elif isinstance(data, dict) and "data" in data:
        metrics = data["data"]
        if isinstance(metrics, list) and len(metrics) > 0:
            metrics = metrics[0]
    
    if not isinstance(metrics, dict) or not metrics:
        return "暂无财务指标数据\n"
    
    lines = []
    key_metrics = {
        "marketCap": ("市值", lambda v: f"${v/1e9:.1f}B" if v and v > 1e9 else f"${v/1e6:.1f}M" if v else "N/A"),
        "peRatio": ("P/E 市盈率", lambda v: f"{v:.1f}x" if v else "N/A"),
        "pegRatio": ("PEG", lambda v: f"{v:.2f}" if v else "N/A"),
        "revenueGrowth": ("营收增速", lambda v: f"{v*100:.1f}%" if v and abs(v) < 10 else f"{v:.1f}%" if v else "N/A"),
        "netIncomeGrowth": ("净利润增速", lambda v: f"{v*100:.1f}%" if v and abs(v) < 10 else f"{v:.1f}%" if v else "N/A"),
        "grossProfitMargin": ("毛利率", lambda v: f"{v*100:.1f}%" if v and v < 1 else f"{v:.1f}%" if v else "N/A"),
        "operatingProfitMargin": ("营业利润率", lambda v: f"{v*100:.1f}%" if v and v < 1 else f"{v:.1f}%" if v else "N/A"),
        "returnOnEquity": ("ROE", lambda v: f"{v*100:.1f}%" if v and v < 1 else f"{v:.1f}%" if v else "N/A"),
        "debtToEquity": ("负债/权益比", lambda v: f"{v:.2f}" if v else "N/A"),
        "currentRatio": ("流动比率", lambda v: f"{v:.2f}" if v else "N/A"),
        "dividendYield": ("股息率", lambda v: f"{v*100:.2f}%" if v and v < 1 else f"{v:.2f}%" if v else "N/A"),
        "price": ("当前股价", lambda v: f"${v:.2f}" if v else "N/A"),
        "beta": ("Beta", lambda v: f"{v:.2f}" if v else "N/A"),
    }
    
    for key, (label, formatter) in key_metrics.items():
        # 尝试多种命名风格
        value = metrics.get(key) or metrics.get(key.lower()) or metrics.get(
            ''.join(['_'+c.lower() if c.isupper() else c for c in key]).lstrip('_')
        )
        if value is not None:
            try:
                lines.append(f"| {label} | {formatter(value)} |")
            except (TypeError, ValueError):
                lines.append(f"| {label} | {value} |")
    
    if lines:
        header = "| 指标 | 数值 |\n|------|------|\n"
        return header + "\n".join(lines)
    else:
        # 如果标准字段没匹配上，输出前15个字段
        fallback_lines = ["| 指标 | 数值 |", "|------|------|"]
        count = 0
        for k, v in metrics.items():
            if v is not None and k not in ("symbol", "ticker", "date", "period"):
                fallback_lines.append(f"| {k} | {v} |")
                count += 1
                if count >= 15:
                    break
        return "\n".join(fallback_lines) if count > 0 else "暂无财务指标数据\n"


def format_analyst(data):
    """格式化分析师预测。"""
    if "error" in data:
        return "⚠️ 分析师预测数据获取失败\n"
    
    estimates = data if isinstance(data, list) else data.get("data", data.get("estimates", []))
    if not estimates:
        for key in data if isinstance(data, dict) else []:
            if isinstance(data[key], list):
                estimates = data[key]
                break
    
    if not estimates:
        return "暂无分析师预测数据\n"
    
    # 取最近的预测
    lines = []
    for est in estimates[:4]:
        if isinstance(est, dict):
            date = est.get("date", est.get("period", ""))
            rev_avg = est.get("estimatedRevenueAvg", est.get("revenueAvg", ""))
            rev_high = est.get("estimatedRevenueHigh", est.get("revenueHigh", ""))
            rev_low = est.get("estimatedRevenueLow", est.get("revenueLow", ""))
            eps_avg = est.get("estimatedEpsAvg", est.get("epsAvg", ""))
            eps_high = est.get("estimatedEpsHigh", est.get("epsHigh", ""))
            eps_low = est.get("estimatedEpsLow", est.get("epsLow", ""))
            num = est.get("numberAnalystsEstimatedRevenue", est.get("numAnalysts", ""))
            
            line = f"**{date}**\n"
            if rev_avg:
                rev_str = f"  - 营收预期: ${rev_avg/1e9:.2f}B" if isinstance(rev_avg, (int, float)) and rev_avg > 1e6 else f"  - 营收预期: {rev_avg}"
                if rev_low and rev_high:
                    if isinstance(rev_low, (int, float)) and isinstance(rev_high, (int, float)):
                        rev_str += f" (区间: ${rev_low/1e9:.2f}B ~ ${rev_high/1e9:.2f}B)"
                line += rev_str + "\n"
            if eps_avg:
                eps_str = f"  - EPS 预期: ${eps_avg:.2f}" if isinstance(eps_avg, (int, float)) else f"  - EPS 预期: {eps_avg}"
                if eps_low and eps_high:
                    if isinstance(eps_low, (int, float)) and isinstance(eps_high, (int, float)):
                        eps_str += f" (区间: ${eps_low:.2f} ~ ${eps_high:.2f})"
                line += eps_str + "\n"
            if num:
                line += f"  - 覆盖分析师: {num} 人\n"
            lines.append(line)
    
    return "\n".join(lines) if lines else "暂无分析师预测数据\n"


def format_perplexity(data):
    """格式化 Perplexity 深度分析。"""
    if "error" in data:
        return "⚠️ Perplexity 深度分析获取失败\n"
    
    # Perplexity 返回 OpenAI 兼容格式
    choices = data.get("choices", [])
    if choices and isinstance(choices, list):
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if content:
            return content
    
    # 尝试其他格式
    if "content" in data:
        return data["content"]
    if "text" in data:
        return data["text"]
    if "answer" in data:
        return data["answer"]
    
    return "暂无深度分析数据\n"


def generate_report(ticker, output_format="markdown"):
    """生成完整竞品情报报告。"""
    now = datetime.now(timezone(timedelta(hours=8)))
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S CST")
    
    print(f"🔍 正在生成 {ticker} 竞品情报报告...")
    print(f"⏰ 数据获取时间: {timestamp}\n")
    
    # 并行获取所有数据（顺序执行，但有错误隔离）
    print("  📊 获取财务指标...")
    metrics_data = fetch_financial_metrics(ticker)
    
    print("  📰 获取最新新闻...")
    news_data = fetch_financial_news(ticker)
    
    print("  🐦 获取 Twitter 讨论...")
    twitter_data = fetch_twitter(ticker)
    
    print("  🏦 获取机构持仓...")
    institutional_data = fetch_institutional_ownership(ticker)
    
    print("  👤 获取内部人交易...")
    insider_data = fetch_insider_trades(ticker)
    
    print("  📈 获取分析师预测...")
    analyst_data = fetch_analyst_estimates(ticker)
    
    print("  🧠 获取 Perplexity 深度分析...")
    perplexity_data = fetch_perplexity_analysis(ticker)
    
    print("\n✅ 数据获取完成，生成报告中...\n")
    print("=" * 60)
    
    if output_format == "json":
        report = {
            "ticker": ticker,
            "generated_at": timestamp,
            "financial_metrics": metrics_data,
            "news": news_data,
            "twitter": twitter_data,
            "institutional_ownership": institutional_data,
            "insider_trades": insider_data,
            "analyst_estimates": analyst_data,
            "deep_analysis": perplexity_data
        }
        return json.dumps(report, ensure_ascii=False, indent=2)
    
    # Markdown 格式
    report = f"""# 📊 {ticker} 竞品情报日报

> 生成时间: {timestamp}
> 数据来源: AISA API + Perplexity Sonar Pro

---

## 📈 核心财务指标

{format_metrics(metrics_data)}

---

## 📰 最新新闻动态

{format_news_section(news_data)}

---

## 🐦 Twitter 热点讨论

{format_twitter_section(twitter_data)}

---

## 🏦 机构持仓动向

{format_institutional(institutional_data)}

---

## 👤 内部人交易信号

{format_insider_trades(insider_data)}

---

## 📈 分析师预测

{format_analyst(analyst_data)}

---

## 🧠 深度竞品分析 (Perplexity Sonar Pro)

{format_perplexity(perplexity_data)}

---

## 📋 报告说明

| 项目 | 详情 |
|------|------|
| 标的 | {ticker} |
| 生成时间 | {timestamp} |
| 数据源 | AISA Financial API, Twitter API, Perplexity Sonar Pro |
| 覆盖维度 | 财务指标、新闻、社交媒体、机构持仓、内部人交易、分析师预测、AI深度分析 |
| 免责声明 | 本报告仅供参考，不构成投资建议 |

---
_报告由 AI 竞品情报日报系统自动生成_
"""
    return report


def main():
    parser = argparse.ArgumentParser(description="AI 竞品情报日报 — 自动化竞品情报生成器")
    parser.add_argument("ticker", help="股票代码，如 NVDA, AAPL, TSLA")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown",
                        help="输出格式: markdown(默认) 或 json")
    parser.add_argument("--save", help="保存到文件路径（可选）")
    
    args = parser.parse_args()
    ticker = args.ticker.upper()
    
    report = generate_report(ticker, args.output)
    
    # 输出到 stdout
    print(report)
    
    # 可选保存到文件
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n💾 报告已保存到: {args.save}")


if __name__ == "__main__":
    main()
