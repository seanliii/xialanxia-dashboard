#!/usr/bin/env python3
"""
AI 竞品情报日报 v2 — 基于 catclaw-search 搜索引擎
沙箱内可运行版本，使用 Bing/Google 搜索替代直连 API
"""

import sys
import os
import json
import subprocess
import argparse
from datetime import datetime, timezone, timedelta

SEARCH_SCRIPT = "/app/skills/catclaw-search/scripts/catclaw_search.py"
ENGINE = "bing"  # bing 最稳定


def search(query, num=5, timeout=15):
    """调用 catclaw-search 搜索"""
    cmd = [
        "python3", SEARCH_SCRIPT, "search", query,
        "-s", ENGINE, "-n", str(num), "--timeout", str(timeout)
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(r.stdout)
        return data.get("results", [])
    except Exception as e:
        return [{"error": str(e)}]


def format_results(results, max_items=8):
    """格式化搜索结果为 markdown"""
    lines = []
    for item in results[:max_items]:
        if "error" in item:
            continue
        title = item.get("title", "")
        snippet = item.get("snippet", item.get("content", ""))
        url = item.get("url", "")
        date = item.get("publish_time", "")
        
        line = f"- **{title}**"
        if date:
            line += f" ({date})"
        if snippet:
            line += f"\n  {snippet[:200]}"
        lines.append(line)
    return "\n".join(lines) if lines else "暂无数据\n"


def generate_report(ticker):
    """生成完整报告"""
    now = datetime.now(timezone(timedelta(hours=8)))
    timestamp = now.strftime("%Y-%m-%d %H:%M CST")
    
    print(f"🔍 正在生成 {ticker} 竞品情报日报...\n")
    
    # 1. 股价和分析师目标
    print("  📊 搜索分析师预测...")
    analyst_results = search(f"{ticker} stock analyst price target forecast 2026", 5)
    
    # 2. 最新新闻
    print("  📰 搜索最新新闻...")
    news_results = search(f"{ticker} news earnings May 2026", 8)
    
    # 3. 机构持仓
    print("  🏦 搜索机构持仓...")
    inst_results = search(f"{ticker} institutional ownership 13F 2026", 5)
    
    # 4. 内部人交易
    print("  👤 搜索内部人交易...")
    insider_results = search(f"{ticker} insider trading SEC Form 4 2026", 5)
    
    # 5. 竞品格局
    print("  🧠 搜索竞品格局...")
    competitor_results = search(f"{ticker} competitor market share analysis 2026", 5)
    
    # 6. Twitter/社交讨论
    print("  🐦 搜索社交讨论...")
    social_results = search(f"{ticker} stock twitter discussion catalyst", 5)
    
    print("\n✅ 搜索完成，生成报告...\n")
    print("=" * 60)
    
    report = f"""# 📊 {ticker} 竞品情报日报

> 生成时间: {timestamp}
> 数据来源: catclaw-search (Bing) + 公开数据聚合
> 系统: AI 竞品情报日报 v2

---

## 📈 分析师预测 & 目标价

{format_results(analyst_results)}

---

## 📰 最新新闻动态

{format_results(news_results)}

---

## 🏦 机构持仓动向

{format_results(inst_results)}

---

## 👤 内部人交易信号

{format_results(insider_results)}

---

## 🧠 竞品格局分析

{format_results(competitor_results)}

---

## 🐦 社交媒体讨论

{format_results(social_results)}

---

## 📋 报告说明

| 项目 | 详情 |
|------|------|
| 标的 | {ticker} |
| 生成时间 | {timestamp} |
| 数据源 | catclaw-search ({ENGINE}), 公开财经网站 |
| 覆盖维度 | 分析师预测、新闻、机构持仓、内部人交易、竞品格局、社交讨论 |
| 免责声明 | 本报告仅供参考，不构成投资建议 |

---
_报告由「AI 竞品情报日报」系统自动生成 | 小蓝虾🦐 x OpenClaw_
"""
    return report


def main():
    parser = argparse.ArgumentParser(description="AI 竞品情报日报 v2 (catclaw-search)")
    parser.add_argument("ticker", help="股票代码，如 NVDA, AAPL, TSLA")
    parser.add_argument("--save", help="保存到文件")
    args = parser.parse_args()
    
    ticker = args.ticker.upper()
    report = generate_report(ticker)
    print(report)
    
    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n💾 已保存: {args.save}")


if __name__ == "__main__":
    main()
