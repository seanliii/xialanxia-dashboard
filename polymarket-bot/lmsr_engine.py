"""
LMSR Engine — Logarithmic Market Scoring Rule
Based on QR-PM-2026-0041 Page 1

核心公式：
  C(q) = b · ln(Σ e^(qi/b))          ← LMSR 成本函数
  pi(q) = e^(qi/b) / Σ e^(qj/b)      ← Softmax 价格函数 (公式3)
  Cost of trade = C(...qi+δ...) - C(...qi...)  ← 交易成本 (公式4)
  Lmax = b · ln(n)                    ← 最大做市商损失 (公式2)

套利信号：
  Entry condition = |p_market - p_bayesian| > threshold
"""

import math
import numpy as np
from typing import List, Tuple, Optional


class LMSREngine:
    """LMSR 定价引擎 — 检测 Polymarket 内部定价低效"""

    def __init__(self, b: float = 100_000):
        """
        Args:
            b: 流动性参数 (Polymarket 标准 = 100,000)
               越大 → 流动性越好 → 最大做市商损失越高
        """
        self.b = b

    # ─────────────────────────────────────────
    # 公式 1: LMSR 成本函数
    # ─────────────────────────────────────────
    def cost(self, q: List[float]) -> float:
        """
        C(q) = b · ln(Σ e^(qi/b))

        Args:
            q: 各 outcome 的 outstanding quantity 向量

        Returns:
            成本 (USDC)
        """
        q_arr = np.array(q, dtype=float)
        # 数值稳定：减去最大值再做 logsumexp
        max_q = np.max(q_arr)
        log_sum = max_q / self.b + math.log(np.sum(np.exp((q_arr - max_q) / self.b)))
        return self.b * log_sum

    # ─────────────────────────────────────────
    # 公式 2: 最大做市商损失
    # ─────────────────────────────────────────
    def max_market_maker_loss(self, n: int) -> float:
        """
        Lmax = b · ln(n)

        n=2 binary market, b=100000 → ~$69,315
        """
        return self.b * math.log(n)

    # ─────────────────────────────────────────
    # 公式 3: 瞬时价格 (Softmax)
    # ─────────────────────────────────────────
    def price(self, q: List[float]) -> List[float]:
        """
        pi(q) = e^(qi/b) / Σ e^(qj/b)

        Returns:
            各 outcome 的概率价格，总和 = 1
        """
        q_arr = np.array(q, dtype=float)
        # 数值稳定 softmax
        q_shifted = q_arr - np.max(q_arr)
        exp_q = np.exp(q_shifted / self.b)
        return (exp_q / np.sum(exp_q)).tolist()

    # ─────────────────────────────────────────
    # 公式 4: 交易成本
    # ─────────────────────────────────────────
    def trade_cost(self, q: List[float], outcome_idx: int, delta: float) -> float:
        """
        Cost = C(q1, ..., qi+δ, ..., qn) - C(q)

        Args:
            q: 当前 quantity 向量
            outcome_idx: 要买的 outcome 索引 (0=Yes, 1=No)
            delta: 购买数量 (shares)

        Returns:
            实际支付成本 (USDC)
        """
        q_new = list(q)
        q_new[outcome_idx] += delta
        return self.cost(q_new) - self.cost(q)

    def trade_cost_per_share(self, q: List[float], outcome_idx: int, delta: float) -> float:
        """每股平均成本"""
        if delta == 0:
            return 0.0
        return self.trade_cost(q, outcome_idx, delta) / delta

    # ─────────────────────────────────────────
    # 核心：无效率检测 (Entry Condition)
    # ─────────────────────────────────────────
    def detect_inefficiency(
        self,
        market_yes_price: float,
        bayesian_prob: float,
        threshold: float = 0.05,
    ) -> dict:
        """
        Entry Condition: 当贝叶斯预测概率与市场价格偏差 > threshold 时入场

        Args:
            market_yes_price: 市场当前 Yes 价格 (0-1)
            bayesian_prob: 贝叶斯更新后的预测概率 (0-1)
            threshold: 最小入场阈值，默认 5%

        Returns:
            {
                "signal": "buy_yes" | "buy_no" | "hold",
                "edge": float,            # 绝对偏差
                "edge_pct": float,        # 相对偏差
                "market_price": float,
                "bayesian_prob": float,
                "entry_valid": bool,
            }
        """
        edge = bayesian_prob - market_yes_price  # 正 → Yes 被低估，负 → No 被低估
        abs_edge = abs(edge)

        if abs_edge < threshold:
            signal = "hold"
        elif edge > 0:
            signal = "buy_yes"
        else:
            signal = "buy_no"

        return {
            "signal": signal,
            "edge": edge,
            "abs_edge": abs_edge,
            "edge_pct": abs_edge / market_yes_price if market_yes_price > 0 else 0,
            "market_price": market_yes_price,
            "bayesian_prob": bayesian_prob,
            "entry_valid": abs_edge >= threshold,
        }

    def estimate_q_from_price(self, yes_price: float, n: int = 2) -> List[float]:
        """
        从已知 Yes 价格反推 quantity 向量（用于模拟）
        p = softmax(q/b), 解析解：q_yes - q_no = b * ln(p/(1-p))

        二元市场专用。
        """
        if n != 2:
            raise ValueError("只支持二元市场反推")
        yes_price = max(0.001, min(0.999, yes_price))
        log_odds = math.log(yes_price / (1 - yes_price))
        # 设 q_no = 0，q_yes = b * log_odds
        q_yes = self.b * log_odds
        return [q_yes, 0.0]

    def implied_price_after_trade(
        self, market_yes_price: float, delta: float, outcome_idx: int = 0
    ) -> float:
        """
        预测买入 delta 份后价格滑点（二元市场）

        Returns:
            交易后新的 Yes 价格
        """
        q = self.estimate_q_from_price(market_yes_price)
        q_new = list(q)
        q_new[outcome_idx] += delta
        new_prices = self.price(q_new)
        return new_prices[0]  # Yes 价格


# ─────────────────────────────────────────
# 便捷函数
# ─────────────────────────────────────────
def check_entry(
    market_price: float,
    your_prob: float,
    position_size: float = 100,
    b: float = 100_000,
    threshold: float = 0.05,
) -> dict:
    """
    一行调用：检查是否有入场机会

    Args:
        market_price: 市场 Yes 价格 (e.g. 0.62)
        your_prob: 你的贝叶斯预测 (e.g. 0.75)
        position_size: 计划买入金额 (USDC)
        b: 流动性参数
        threshold: 入场阈值

    Returns:
        含 signal/edge/cost/slippage 的完整分析
    """
    engine = LMSREngine(b=b)
    signal = engine.detect_inefficiency(market_price, your_prob, threshold)

    if signal["entry_valid"]:
        # 反推 quantity 向量
        q = engine.estimate_q_from_price(market_price)
        # 计算实际交易成本
        buy_idx = 0 if signal["signal"] == "buy_yes" else 1
        # 把 USDC 金额转换成 shares（近似：shares ≈ cost / price）
        approx_shares = position_size / market_price
        actual_cost = engine.trade_cost(q, buy_idx, approx_shares)
        post_price = engine.implied_price_after_trade(market_price, approx_shares, buy_idx)
        slippage = abs(post_price - market_price)

        signal["trade_cost_usdc"] = actual_cost
        signal["approx_shares"] = approx_shares
        signal["post_trade_price"] = post_price
        signal["slippage"] = slippage
        signal["max_mm_loss"] = engine.max_market_maker_loss(2)
    
    return signal


# ─────────────────────────────────────────
# 自测
# ─────────────────────────────────────────
if __name__ == "__main__":
    engine = LMSREngine(b=100_000)

    print("=" * 50)
    print("LMSR Engine — 公式验证")
    print("=" * 50)

    # 公式2 验证
    lmax = engine.max_market_maker_loss(2)
    print(f"\n📐 公式2: 最大做市商损失 (n=2, b=100K)")
    print(f"   Lmax = 100,000 × ln(2) = ${lmax:,.0f} (期望: ~$69,315)")

    # 公式3 验证
    q = [10000, 0]
    prices = engine.price(q)
    print(f"\n📐 公式3: Softmax 价格 (q=[10000,0])")
    print(f"   Yes={prices[0]:.4f}, No={prices[1]:.4f}, 和={sum(prices):.4f}")

    # 场景：市场定价 Yes=0.62，贝叶斯预测 0.78
    print("\n" + "=" * 50)
    print("🎯 套利场景测试")
    result = check_entry(
        market_price=0.62,
        your_prob=0.78,
        position_size=500,
        threshold=0.05,
    )
    print(f"  市场价格: {result['market_price']:.2%}")
    print(f"  贝叶斯预测: {result['bayesian_prob']:.2%}")
    print(f"  Edge: {result['abs_edge']:.2%}")
    print(f"  信号: {result['signal']}")
    print(f"  实际成本: ${result.get('trade_cost_usdc', 0):.2f}")
    print(f"  交易后价格: {result.get('post_trade_price', 0):.4f}")
    print(f"  滑点: {result.get('slippage', 0):.4f}")
