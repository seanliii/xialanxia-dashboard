"""
Bayesian Signal Processing Engine
Based on QR-PM-2026-0041 Page 2

核心公式：
  P(H|D) = P(D|H)·P(H) / P(D)              ← Bayes 更新 (公式1)
  P(H|D1..Dt) ∝ P(H) · Π P(Dk|H)           ← 序贯更新 (公式2)
  log P(H|D) = log P(H) + Σ log P(Dk|H) - log Z  ← 数值稳定 log 空间 (公式3)
  EV = p̂·(1-p) - (1-p̂)·p = p̂ - p          ← 期望收益 (公式4)

仓位管理：
  Kelly% = (b·p - q) / b
  半凯利 = Kelly/2（警告："NEVER full Kelly on 5min markets!"）
  Fractional Kelly with confidence discount
"""

import math
import time
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────
# 公式核心：Bayesian Updater
# ─────────────────────────────────────────
class BayesianUpdater:
    """
    序贯贝叶斯更新器

    流式处理多源信号（Twitter、订单簿、新闻、NOAA...），
    每次新数据到来就更新后验概率，log 空间运算数值稳定。
    """

    def __init__(self, prior: float = 0.5):
        """
        Args:
            prior: 先验概率 P(H)，默认 0.5（无信息先验）
        """
        if not 0 < prior < 1:
            raise ValueError("Prior 必须在 (0,1) 之间")
        self.log_prior = math.log(prior / (1 - prior))  # 存 log-odds
        self.update_count = 0
        self.update_log: List[Dict] = []

    @property
    def posterior(self) -> float:
        """当前后验概率"""
        return self._logodds_to_prob(self.log_prior)

    @staticmethod
    def _logodds_to_prob(log_odds: float) -> float:
        """log-odds → 概率（数值稳定）"""
        if log_odds > 500:
            return 1.0 - 1e-9
        if log_odds < -500:
            return 1e-9
        return 1.0 / (1.0 + math.exp(-log_odds))

    # ─────────────────────────────────────────
    # 公式 1 & 3: 单次贝叶斯更新
    # ─────────────────────────────────────────
    def update(
        self,
        likelihood_true: float,
        likelihood_false: float,
        source: str = "unknown",
        weight: float = 1.0,
    ) -> float:
        """
        公式3 log 空间更新：
        log P(H|D) = log P(H) + log P(D|H) - log P(D|¬H) + const

        Args:
            likelihood_true:  P(D | H=True)  数据在 H 为真时的可能性
            likelihood_false: P(D | H=False) 数据在 H 为假时的可能性
            source: 信号来源（用于日志）
            weight: 信号权重（0-1），降低不可靠来源的影响

        Returns:
            更新后的后验概率
        """
        if likelihood_true <= 0 or likelihood_false <= 0:
            return self.posterior  # 无效数据，不更新

        # log-likelihood ratio，乘权重
        log_lr = math.log(likelihood_true / likelihood_false) * weight

        before = self.posterior
        self.log_prior += log_lr
        after = self.posterior

        self.update_count += 1
        self.update_log.append({
            "n": self.update_count,
            "source": source,
            "log_lr": round(log_lr, 4),
            "weight": weight,
            "before": round(before, 4),
            "after": round(after, 4),
        })

        return after

    # ─────────────────────────────────────────
    # 公式 2: 序贯批量更新
    # ─────────────────────────────────────────
    def batch_update(self, signals: List[Dict]) -> float:
        """
        P(H|D1..Dt) ∝ P(H) · Π P(Dk|H)
        在 log 空间等价于累加 log-likelihood

        Args:
            signals: [
                {
                    "likelihood_true": float,
                    "likelihood_false": float,
                    "source": str,
                    "weight": float,   # 可选，默认1.0
                }
            ]

        Returns:
            最终后验概率
        """
        for sig in signals:
            self.update(
                likelihood_true=sig["likelihood_true"],
                likelihood_false=sig["likelihood_false"],
                source=sig.get("source", "batch"),
                weight=sig.get("weight", 1.0),
            )
        return self.posterior

    def reset(self, prior: float = 0.5):
        """重置到先验"""
        self.log_prior = math.log(prior / (1 - prior))
        self.update_count = 0
        self.update_log.clear()

    def summary(self) -> Dict:
        return {
            "posterior": round(self.posterior, 4),
            "update_count": self.update_count,
            "last_3_updates": self.update_log[-3:],
        }


# ─────────────────────────────────────────
# 公式 4: 期望收益 & 仓位管理
# ─────────────────────────────────────────
class PositionSizer:
    """
    基于 EV + 凯利公式的仓位计算

    公式4: EV = p̂·(1-p) - (1-p̂)·p = p̂ - p
      p̂ = 贝叶斯预测概率
      p  = 市场当前价格

    Kelly = EV / (1-p)    ← 对 binary market 的 Kelly 近似
    建议用 半凯利 或 1/4 凯利
    """

    # 警告：原文手注 "NEVER full Kelly on 5min markets!"
    MAX_KELLY_FRACTION = 0.5   # 半凯利上限
    MAX_SINGLE_POSITION = 0.05 # 单仓绝对上限 5%

    def __init__(
        self,
        bankroll: float,
        kelly_fraction: float = 0.25,
        max_position_pct: float = 0.05,
    ):
        """
        Args:
            bankroll: 总资金
            kelly_fraction: 凯利分数 (0.25 = 1/4 Kelly，更保守)
            max_position_pct: 单仓上限占比
        """
        self.bankroll = bankroll
        self.kelly_fraction = min(kelly_fraction, self.MAX_KELLY_FRACTION)
        self.max_position_pct = min(max_position_pct, self.MAX_SINGLE_POSITION)

    # ─────────────────────────────────────────
    # 公式 4: EV 计算
    # ─────────────────────────────────────────
    def expected_value(self, bayesian_prob: float, market_price: float) -> float:
        """
        EV = p̂ - p

        Returns:
            期望收益 per dollar (正 = 有利可图)
        """
        return bayesian_prob - market_price

    def expected_value_full(
        self, bayesian_prob: float, market_price: float
    ) -> Dict:
        """
        EV 完整计算（含 win/lose 分解）

        EV = p̂·(1-p) - (1-p̂)·p
           = p̂ - p

        Returns:
            {ev, win_contribution, lose_contribution, ev_pct}
        """
        win = bayesian_prob * (1 - market_price)
        lose = (1 - bayesian_prob) * market_price
        ev = win - lose
        return {
            "ev": ev,
            "win_contribution": win,
            "lose_contribution": lose,
            "ev_simplified": bayesian_prob - market_price,  # 验证一致
            "ev_pct": ev / market_price if market_price > 0 else 0,
        }

    # ─────────────────────────────────────────
    # Kelly 公式仓位
    # ─────────────────────────────────────────
    def kelly_size(
        self,
        bayesian_prob: float,
        market_price: float,
        confidence: float = 1.0,
    ) -> Dict:
        """
        Kelly % = (b·p̂ - q) / b
        其中: b = 净赔率 = (1-p)/p，p̂ = 贝叶斯概率，q = 1-p̂

        Args:
            bayesian_prob: 贝叶斯预测
            market_price: 市场价格（即买入成本）
            confidence: 置信度折扣 0-1（信号不确定时缩减仓位）

        Returns:
            {
                kelly_pct: full kelly 百分比,
                fractional_pct: 调整后百分比,
                position_usdc: 建议仓位 (USDC),
                capped: 是否被上限截断,
            }
        """
        p_hat = bayesian_prob
        p = market_price

        if p <= 0 or p >= 1 or p_hat <= 0:
            return self._zero_position("无效概率")

        # 净赔率 b = (1-p)/p （即 $1 赢 b 赔 1）
        b = (1 - p) / p
        q_hat = 1 - p_hat

        # Full Kelly
        full_kelly = (b * p_hat - q_hat) / b  # = (p̂ - p) / (1-p)

        if full_kelly <= 0:
            return self._zero_position("负 Kelly — 无利可图")

        # Fractional Kelly + confidence discount
        adjusted = full_kelly * self.kelly_fraction * confidence

        # 上限截断
        capped = adjusted > self.max_position_pct
        final_pct = min(adjusted, self.max_position_pct)

        position_usdc = self.bankroll * final_pct

        return {
            "kelly_pct": round(full_kelly, 4),
            "fractional_pct": round(adjusted, 4),
            "final_pct": round(final_pct, 4),
            "position_usdc": round(position_usdc, 2),
            "capped": capped,
            "ev_per_dollar": round(self.expected_value(p_hat, p), 4),
            "kelly_fraction_used": self.kelly_fraction,
            "warning": "NEVER full Kelly on 5min markets!" if b > 5 else None,
        }

    def _zero_position(self, reason: str) -> Dict:
        return {
            "kelly_pct": 0,
            "fractional_pct": 0,
            "final_pct": 0,
            "position_usdc": 0,
            "capped": False,
            "ev_per_dollar": 0,
            "reason": reason,
        }


# ─────────────────────────────────────────
# 信号工厂：标准化各数据源 → 贝叶斯信号
# ─────────────────────────────────────────
class SignalFactory:
    """将各种原始信号转换为 (likelihood_true, likelihood_false) 格式"""

    @staticmethod
    def from_twitter_sentiment(
        sentiment: str,
        tweet_count: int,
        positive_ratio: float,
    ) -> Dict:
        """
        Twitter 情绪 → 贝叶斯信号

        Args:
            sentiment: "bullish" | "bearish" | "neutral"
            tweet_count: 推文数
            positive_ratio: 正面推文比例 (0-1)
        """
        # 基础可信度（推文越多越可信）
        base_weight = min(1.0, tweet_count / 20)

        if sentiment == "bullish":
            # P(看涨推文 | Yes 真实发生) > P(看涨推文 | No 真实发生)
            lr = 1.0 + positive_ratio  # 1.0 - 2.0
        elif sentiment == "bearish":
            lr = 1.0 / (1.0 + positive_ratio)
        else:
            lr = 1.0  # 中性信号 → 不更新

        return {
            "likelihood_true": lr,
            "likelihood_false": 1.0,
            "source": "twitter_sentiment",
            "weight": base_weight * 0.4,  # Twitter 权重较低
        }

    @staticmethod
    def from_orderbook_imbalance(imbalance: float) -> Dict:
        """
        订单簿买卖不平衡 → 贝叶斯信号

        Args:
            imbalance: (bid_depth - ask_depth) / total_depth，范围 [-1, 1]
        """
        # imbalance > 0 → 偏买（Yes 需求强）
        if abs(imbalance) < 0.05:
            return {"likelihood_true": 1.0, "likelihood_false": 1.0, "source": "orderbook", "weight": 0}

        # 信号强度
        strength = abs(imbalance)
        if imbalance > 0:
            lr = 1.0 + strength * 2  # 最高 3x
        else:
            lr = 1.0 / (1.0 + strength * 2)

        return {
            "likelihood_true": lr,
            "likelihood_false": 1.0,
            "source": "orderbook_imbalance",
            "weight": 0.6,  # 订单簿信号权重中等
        }

    @staticmethod
    def from_noaa_forecast(
        forecast_prob: float,
        accuracy_rate: float = 0.93,
    ) -> Dict:
        """
        NOAA 天气预报 → 贝叶斯信号
        xmayeth 原文策略核心：NOAA 93% 准确率 vs Polymarket 低流动性定价

        Args:
            forecast_prob: NOAA 预测概率
            accuracy_rate: NOAA 历史准确率（默认 0.93）
        """
        # P(NOAA预测Yes | 实际Yes) = accuracy_rate
        # P(NOAA预测Yes | 实际No)  = 1 - accuracy_rate
        if forecast_prob > 0.5:
            lt = accuracy_rate
            lf = 1 - accuracy_rate
        else:
            lt = 1 - accuracy_rate
            lf = accuracy_rate

        return {
            "likelihood_true": lt,
            "likelihood_false": lf,
            "source": "noaa_forecast",
            "weight": 1.0,  # 高权重，高准确率来源
        }

    @staticmethod
    def from_price_history(
        recent_price_trend: float,
        lookback_minutes: int = 30,
    ) -> Dict:
        """
        价格历史趋势 → 贝叶斯信号

        Args:
            recent_price_trend: 价格变化量 (-1 to 1)，正 = 价格上升
            lookback_minutes: 回看时间窗口
        """
        if abs(recent_price_trend) < 0.02:
            return {"likelihood_true": 1.0, "likelihood_false": 1.0, "source": "price_trend", "weight": 0}

        # 时间衰减：越近的信号越重要
        time_weight = max(0.1, 1.0 - lookback_minutes / 120)

        if recent_price_trend > 0:
            lr = 1.0 + recent_price_trend
        else:
            lr = 1.0 / (1.0 + abs(recent_price_trend))

        return {
            "likelihood_true": lr,
            "likelihood_false": 1.0,
            "source": "price_trend",
            "weight": time_weight * 0.5,
        }


# ─────────────────────────────────────────
# 完整分析流水线
# ─────────────────────────────────────────
class BayesianAnalyzer:
    """
    组合所有信号，输出标准化交易建议

    Update cycle latency (production):
    - Data ingestion: 120ms avg / 340ms p99
    - Bayesian computation: 15ms avg / 28ms p99
    - LMSR price comparison: 3ms avg / 8ms p99
    - Order execution: 690ms avg / 1400ms p99
    Total: ~828ms avg / 1776ms p99
    """

    def __init__(self, bankroll: float, prior: float = 0.5):
        self.bankroll = bankroll
        self.prior = prior

    def analyze(
        self,
        market_yes_price: float,
        signals_raw: List[Dict],
        min_edge: float = 0.05,
        confidence_override: Optional[float] = None,
    ) -> Dict:
        """
        完整贝叶斯分析流水线

        Args:
            market_yes_price: 市场当前 Yes 价格
            signals_raw: 原始信号列表（已转换为贝叶斯格式）
            min_edge: 最小入场 edge 阈值
            confidence_override: 手动设置置信度（0-1），None 则自动

        Returns:
            完整分析结果（含 EV、Kelly 仓位、信号摘要）
        """
        start_t = time.monotonic()

        # 1. 贝叶斯更新
        updater = BayesianUpdater(prior=self.prior)
        updater.batch_update(signals_raw)
        bayesian_prob = updater.posterior

        # 2. 自动置信度（基于更新次数和信号分散度）
        if confidence_override is not None:
            confidence = confidence_override
        else:
            update_count = updater.update_count
            confidence = min(0.95, 0.4 + update_count * 0.1)  # 每个信号+10%，上限95%

        # 3. EV 计算
        sizer = PositionSizer(
            bankroll=self.bankroll,
            kelly_fraction=0.25,
            max_position_pct=0.05,
        )
        ev_info = sizer.expected_value_full(bayesian_prob, market_yes_price)
        kelly_info = sizer.kelly_size(bayesian_prob, market_yes_price, confidence)

        # 4. 入场信号
        edge = bayesian_prob - market_yes_price
        abs_edge = abs(edge)

        if abs_edge < min_edge:
            action = "hold"
        elif edge > 0:
            action = "buy_yes"
        else:
            action = "buy_no"

        elapsed_ms = (time.monotonic() - start_t) * 1000

        return {
            # 核心输出
            "action": action,
            "bayesian_prob": round(bayesian_prob, 4),
            "market_price": round(market_yes_price, 4),
            "edge": round(edge, 4),
            "abs_edge": round(abs_edge, 4),
            "confidence": round(confidence, 2),

            # EV
            "ev_per_dollar": round(ev_info["ev"], 4),
            "ev_pct": round(ev_info["ev_pct"], 4),

            # 仓位
            "kelly_pct": kelly_info.get("kelly_pct", 0),
            "position_usdc": kelly_info.get("position_usdc", 0),
            "kelly_capped": kelly_info.get("capped", False),

            # 元信息
            "signal_count": updater.update_count,
            "bayesian_updates": updater.update_log,
            "latency_ms": round(elapsed_ms, 2),
            "entry_valid": abs_edge >= min_edge and kelly_info.get("position_usdc", 0) > 0,
        }


# ─────────────────────────────────────────
# 自测
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("Bayesian Engine — 公式验证")
    print("=" * 55)

    # --- 公式4 EV 验证 ---
    sizer = PositionSizer(bankroll=10_000)
    p_hat, p = 0.75, 0.62
    ev = sizer.expected_value(p_hat, p)
    ev_full = sizer.expected_value_full(p_hat, p)
    print(f"\n📐 公式4: EV = p̂ - p")
    print(f"   p̂={p_hat}, p={p}")
    print(f"   EV = {ev:.4f}  ({ev_full['ev_simplified']:.4f} simplified — 应一致)")

    # --- Kelly 公式 ---
    kelly = sizer.kelly_size(p_hat, p, confidence=0.8)
    print(f"\n📐 Kelly 仓位 (1/4 Kelly, confidence=0.8)")
    print(f"   Full Kelly: {kelly['kelly_pct']:.2%}")
    print(f"   1/4 Kelly: {kelly['fractional_pct']:.2%}")
    print(f"   建议仓位: ${kelly['position_usdc']}")

    # --- 完整贝叶斯流水线 ---
    print("\n" + "=" * 55)
    print("🎯 完整贝叶斯分析（天气套利场景）")
    analyzer = BayesianAnalyzer(bankroll=10_000, prior=0.5)

    signals = [
        SignalFactory.from_noaa_forecast(forecast_prob=0.80, accuracy_rate=0.93),
        SignalFactory.from_orderbook_imbalance(imbalance=0.30),
        SignalFactory.from_twitter_sentiment("bullish", tweet_count=25, positive_ratio=0.7),
    ]

    result = analyzer.analyze(
        market_yes_price=0.58,
        signals_raw=signals,
        min_edge=0.05,
    )

    print(f"\n  市场价格:   {result['market_price']:.2%}")
    print(f"  贝叶斯预测: {result['bayesian_prob']:.2%}")
    print(f"  Edge:       {result['abs_edge']:.2%}")
    print(f"  EV/dollar:  {result['ev_per_dollar']:.4f}")
    print(f"  Kelly 仓位: ${result['position_usdc']}")
    print(f"  信号:       {result['action']}")
    print(f"  置信度:     {result['confidence']:.0%}")
    print(f"  计算耗时:   {result['latency_ms']:.2f}ms")
    print(f"\n  更新日志:")
    for upd in result["bayesian_updates"]:
        print(f"    [{upd['n']}] {upd['source']:25s} | log_lr={upd['log_lr']:+.3f} | {upd['before']:.3f} → {upd['after']:.3f}")
