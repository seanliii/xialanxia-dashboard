#!/usr/bin/env python3
"""
Polymarket 量化扫描器 v2
基于 QR-PM-2026-0041 两页纸公式

用法:
    python quant_scanner.py                  # 扫描所有热门市场
    python quant_scanner.py --tag weather    # 只扫天气市场（时区套利核心）
    python quant_scanner.py --top 5          # 只输出 Top 5 机会
    python quant_scanner.py --bankroll 5000  # 设置资金规模

公式体系:
    LMSR:    C(q) = b·ln(Σ e^(qi/b))
    Price:   pi = softmax(qi/b)
    Bayes:   P(H|D) = P(D|H)·P(H)/P(D)
    EV:      EV = p̂ - p
    Kelly:   f = (b·p̂ - q) / b × 0.25 (1/4 Kelly)
"""
import os
import sys
import argparse
import json
from datetime import datetime, timezone

# ── 代理配置（在所有 requests 调用之前）──────────────────
os.environ["https_proxy"] = "http://10.59.78.158:3128"
os.environ["http_proxy"] = "http://10.59.78.158:3128"
os.environ["HTTPS_PROXY"] = "http://10.59.78.158:3128"
os.environ["HTTP_PROXY"] = "http://10.59.78.158:3128"

import requests

from polymarket_client import PolymarketDataClient
from lmsr_engine import LMSREngine, check_entry
from bayesian_engine import BayesianAnalyzer, SignalFactory, PositionSizer


def scan_markets(
    tag: str = None,
    limit: int = 30,
    bankroll: float = 1000.0,
    min_edge: float = 0.05,
    top_n: int = 10,
) -> list:
    """
    扫描 Polymarket 市场，找出有 edge 的机会

    Returns:
        按 priority 排序的机会列表
    """
    print(f"\n{'='*60}")
    print(f"🦐 Polymarket 量化扫描器 v2 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   公式: LMSR + Bayesian + Kelly (QR-PM-2026-0041)")
    print(f"   资金: ${bankroll:,} | 最小Edge: {min_edge:.0%} | Tag: {tag or '全部'}")
    print(f"{'='*60}\n")

    client = PolymarketDataClient()
    lmsr = LMSREngine(b=100_000)
    analyzer = BayesianAnalyzer(bankroll=bankroll, prior=0.5)
    sizer = PositionSizer(bankroll=bankroll, kelly_fraction=0.25, max_position_pct=0.05)

    # 1. 获取市场
    if tag:
        markets = client.get_markets(tag=tag, limit=limit, order_by="volume24hr")
    else:
        markets = client.get_markets(limit=limit, order_by="volume24hr")

    print(f"📊 获取到 {len(markets)} 个市场，开始分析...\n")

    opportunities = []

    for market in markets:
        question = market.get("question", "")
        prices = market.get("outcome_prices", [])
        if not prices or len(prices) < 2:
            continue

        try:
            yes_price = float(prices[0])
            no_price = float(prices[1])
        except (ValueError, TypeError):
            continue

        if yes_price <= 0 or yes_price >= 1:
            continue

        # 2. 获取订单簿
        token_ids = market.get("clob_token_ids", [])
        ob_imbalance = 0.0
        if token_ids:
            ob = client.get_orderbook(token_ids[0])
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])
            bid_d = sum(float(b.get("size", 0)) for b in bids[:5])
            ask_d = sum(float(a.get("size", 0)) for a in asks[:5])
            total_d = bid_d + ask_d
            if total_d > 0:
                ob_imbalance = (bid_d - ask_d) / total_d

        # 3. 构造贝叶斯信号（无外部 API 时只用订单簿）
        bayes_signals = [
            SignalFactory.from_orderbook_imbalance(ob_imbalance),
        ]

        # 4. 贝叶斯分析
        bayes = analyzer.analyze(
            market_yes_price=yes_price,
            signals_raw=bayes_signals,
            min_edge=min_edge,
        )

        if not bayes["entry_valid"]:
            continue

        # 5. LMSR 验证
        lmsr_check = lmsr.detect_inefficiency(
            market_yes_price=yes_price,
            bayesian_prob=bayes["bayesian_prob"],
            threshold=min_edge,
        )

        # 6. EV & Kelly
        ev = sizer.expected_value(bayes["bayesian_prob"], yes_price)
        kelly = sizer.kelly_size(bayes["bayesian_prob"], yes_price)

        # 优先级 = EV × 置信度 × 成交量权重
        volume_weight = min(1.0, market.get("volume_24h", 0) / 100_000)
        priority = abs(ev) * bayes["confidence"] * (1 + volume_weight)

        opportunities.append({
            "question": question[:70],
            "yes_price": yes_price,
            "bayesian_prob": bayes["bayesian_prob"],
            "edge": bayes["abs_edge"],
            "ev": ev,
            "action": bayes["action"],
            "kelly_pct": kelly.get("final_pct", 0),
            "position_usdc": kelly.get("position_usdc", 0),
            "confidence": bayes["confidence"],
            "ob_imbalance": ob_imbalance,
            "volume_24h": market.get("volume_24h", 0),
            "priority": priority,
            "lmsr_valid": lmsr_check["entry_valid"],
            "market": market,
        })

    # 排序
    opportunities.sort(key=lambda x: x["priority"], reverse=True)
    return opportunities[:top_n]


def print_opportunities(opps: list, bankroll: float):
    """格式化输出"""
    if not opps:
        print("📭 未发现符合条件的机会（edge < 阈值 或 订单簿无信号）")
        print("\n💡 提示：订单簿信号较弱时，可降低 --min-edge 参数")
        return

    total_position = sum(o["position_usdc"] for o in opps)

    print(f"✅ 发现 {len(opps)} 个有效机会\n")
    print(f"{'─'*60}")

    for i, opp in enumerate(opps, 1):
        action_emoji = "🟢" if opp["action"] == "buy_yes" else "🔴"
        print(f"\n#{i} {action_emoji} {opp['action'].upper()}")
        print(f"  📌 {opp['question']}")
        print(f"  💰 市场价: {opp['yes_price']:.2%}  |  贝叶斯预测: {opp['bayesian_prob']:.2%}")
        print(f"  📈 Edge: {opp['edge']:.2%}  |  EV/dollar: {opp['ev']:+.4f}")
        print(f"  🎯 Kelly 仓位: ${opp['position_usdc']:.0f} ({opp['kelly_pct']:.2%} of bankroll)")
        print(f"  📊 置信度: {opp['confidence']:.0%}  |  24h 成交量: ${opp['volume_24h']:,.0f}")
        print(f"  📉 订单簿偏差: {opp['ob_imbalance']:+.3f}  |  LMSR验证: {'✅' if opp['lmsr_valid'] else '❌'}")

    print(f"\n{'─'*60}")
    print(f"💼 总建议仓位: ${total_position:.0f} / ${bankroll:,.0f} ({total_position/bankroll:.1%})")
    print(f"\n⚠️  提醒: 1/4 Kelly 已应用。NEVER full Kelly on 5min markets!")
    print(f"{'─'*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Polymarket 量化扫描器 (LMSR + Bayes + Kelly)")
    parser.add_argument("--tag", default=None, help="市场类型: weather/sports/politics/crypto")
    parser.add_argument("--limit", type=int, default=30, help="扫描市场数量")
    parser.add_argument("--top", type=int, default=10, help="显示 Top N 机会")
    parser.add_argument("--bankroll", type=float, default=1000.0, help="资金规模 (USDC)")
    parser.add_argument("--min-edge", type=float, default=0.05, help="最小 edge 阈值")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    opps = scan_markets(
        tag=args.tag,
        limit=args.limit,
        bankroll=args.bankroll,
        min_edge=args.min_edge,
        top_n=args.top,
    )

    if args.json:
        # 去除不可序列化的 market 对象
        output = [{k: v for k, v in o.items() if k != "market"} for o in opps]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print_opportunities(opps, args.bankroll)

    return opps


if __name__ == "__main__":
    main()
