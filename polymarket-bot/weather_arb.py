#!/usr/bin/env python3
"""
天气套利模块 — xmayeth 核心策略
"NOAA 93% 准确率 vs Polymarket 低流动性定价"

策略逻辑：
1. 获取 Polymarket 天气市场（如 "Will NYC exceed 80°F on April 3?"）
2. 从 NOAA API 获取对应预报概率（免费，官方，93%准确率）
3. 计算 edge = NOAA概率 - 市场价格
4. 贝叶斯更新（NOAA + 订单簿）
5. 凯利公式计算仓位
6. 输出建议

NOAA API（免费，无需注册）：
  https://api.weather.gov/gridpoints/{office}/{x},{y}/forecast
  https://api.weather.gov/points/{lat},{lon}

时区套利窗口：北京时间 00:00-06:00（美国用户睡觉，流动性最差）
"""

import os
import re
import json
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

os.environ.setdefault("https_proxy", "http://10.59.78.158:3128")
os.environ.setdefault("http_proxy", "http://10.59.78.158:3128")

from polymarket_client import PolymarketDataClient
from lmsr_engine import LMSREngine
from bayesian_engine import BayesianAnalyzer, SignalFactory, PositionSizer


# ─────────────────────────────────────────
# NOAA 客户端
# ─────────────────────────────────────────
class NOAAClient:
    """NOAA 天气预报 API（免费，官方，93% 准确率）"""

    BASE = "https://api.weather.gov"
    HEADERS = {"User-Agent": "polymarket-bot/2.0 (research@example.com)"}

    # 常用城市坐标
    CITIES = {
        "nyc": (40.7128, -74.0060),
        "new york": (40.7128, -74.0060),
        "los angeles": (34.0522, -118.2437),
        "la": (34.0522, -118.2437),
        "chicago": (41.8781, -87.6298),
        "miami": (25.7617, -80.1918),
        "houston": (29.7604, -95.3698),
        "dallas": (32.7767, -96.7970),
        "phoenix": (33.4484, -112.0740),
        "seattle": (47.6062, -122.3321),
        "boston": (42.3601, -71.0589),
        "denver": (39.7392, -104.9903),
        "atlanta": (33.7490, -84.3880),
        "washington": (38.9072, -77.0369),
        "dc": (38.9072, -77.0369),
        "san francisco": (37.7749, -122.4194),
        "sf": (37.7749, -122.4194),
    }

    def get_forecast(self, lat: float, lon: float) -> Optional[Dict]:
        """获取指定坐标的天气预报"""
        try:
            # Step 1: 获取 gridpoint
            r = requests.get(
                f"{self.BASE}/points/{lat:.4f},{lon:.4f}",
                headers=self.HEADERS,
                timeout=15,
            )
            if r.status_code != 200:
                return None
            data = r.json()
            forecast_url = data["properties"]["forecast"]

            # Step 2: 获取预报
            r2 = requests.get(forecast_url, headers=self.HEADERS, timeout=15)
            if r2.status_code != 200:
                return None
            return r2.json()
        except Exception as e:
            print(f"[NOAA] 获取失败: {e}")
            return None

    def get_hourly_forecast(self, lat: float, lon: float) -> Optional[Dict]:
        """获取逐小时预报"""
        try:
            r = requests.get(
                f"{self.BASE}/points/{lat:.4f},{lon:.4f}",
                headers=self.HEADERS, timeout=15,
            )
            if r.status_code != 200:
                return None
            forecast_url = r.json()["properties"]["forecastHourly"]
            r2 = requests.get(forecast_url, headers=self.HEADERS, timeout=15)
            if r2.status_code != 200:
                return None
            return r2.json()
        except Exception as e:
            print(f"[NOAA] 逐小时预报失败: {e}")
            return None

    def estimate_temp_prob(
        self,
        lat: float,
        lon: float,
        target_temp_f: float,
        above: bool = True,
        target_date: Optional[str] = None,
    ) -> Optional[float]:
        """
        估算气温超过/低于阈值的概率

        Args:
            lat, lon: 坐标
            target_temp_f: 目标温度（华氏度）
            above: True = 超过阈值, False = 低于阈值
            target_date: 目标日期 "YYYY-MM-DD"（None = 明天）

        Returns:
            概率 0-1，或 None（无法获取预报）
        """
        forecast = self.get_hourly_forecast(lat, lon)
        if not forecast:
            return None

        periods = forecast.get("properties", {}).get("periods", [])
        if not periods:
            return None

        # 筛选目标日期的预报
        if target_date:
            day_periods = [
                p for p in periods if p.get("startTime", "").startswith(target_date)
            ]
        else:
            day_periods = periods[:24]

        if not day_periods:
            return None

        # 高温概率（用当天最高温 vs 阈值的正态分布近似）
        temps = [p.get("temperature", 0) for p in day_periods if p.get("temperatureUnit") == "F"]
        if not temps:
            return None

        max_temp = max(temps)
        # 使用简单线性插值：±5°F 对应概率从 10% 到 90%
        diff = max_temp - target_temp_f
        if diff >= 5:
            prob = 0.90
        elif diff <= -5:
            prob = 0.10
        else:
            prob = 0.50 + diff * 0.08

        return prob if above else 1 - prob

    def city_coords(self, city_name: str) -> Optional[Tuple[float, float]]:
        """城市名 → 坐标"""
        key = city_name.lower().strip()
        for k, v in self.CITIES.items():
            if k in key:
                return v
        return None


# ─────────────────────────────────────────
# 问题解析器
# ─────────────────────────────────────────
def parse_weather_question(question: str) -> Optional[Dict]:
    """
    从市场问题解析天气预测参数

    Examples:
      "Will NYC exceed 80°F on April 3?" → {city: "nyc", temp: 80, above: True, date: "04-03"}
      "Will it rain in Chicago on March 28?" → {city: "chicago", precip: True}
    """
    q = question.lower()

    # 城市识别
    city = None
    city_map = {
        "nyc": "nyc", "new york": "nyc", "manhattan": "nyc",
        "los angeles": "la", "l.a.": "la",
        "chicago": "chicago", "miami": "miami",
        "houston": "houston", "dallas": "dallas",
        "phoenix": "phoenix", "seattle": "seattle",
        "boston": "boston", "denver": "denver",
        "atlanta": "atlanta", "washington": "dc",
        "san francisco": "sf",
    }
    for k, v in city_map.items():
        if k in q:
            city = v
            break

    if not city:
        return None

    result = {"city": city}

    # 温度识别
    temp_match = re.search(r"(\d+)\s*[°º]?\s*f(?:ahrenheit)?", q)
    if temp_match:
        result["temp_f"] = int(temp_match.group(1))
        result["above"] = any(w in q for w in ["exceed", "above", "over", "reach", "hit", "top"])
        result["type"] = "temperature"

    # 降水识别
    elif any(w in q for w in ["rain", "snow", "precipitation", "precip"]):
        result["type"] = "precipitation"

    # 日期识别
    date_patterns = [
        r"(?:on\s+)?(\w+)\s+(\d+)(?:st|nd|rd|th)?",
        r"(\d{4})-(\d{2})-(\d{2})",
    ]
    for pat in date_patterns:
        m = re.search(pat, q)
        if m:
            result["date_raw"] = m.group(0)
            break

    return result if "type" in result else None


# ─────────────────────────────────────────
# 天气套利扫描器
# ─────────────────────────────────────────
class WeatherArbScanner:
    """
    天气套利扫描器

    xmayeth 策略核心：
    - NOAA 93% 准确率是信息优势
    - Polymarket 天气市场流动性低 → 价格偏差大
    - 时区套利：北京 00:00-06:00 是最佳窗口
    """

    def __init__(self, bankroll: float = 1000.0):
        self.bankroll = bankroll
        self.client = PolymarketDataClient()
        self.noaa = NOAAClient()
        self.lmsr = LMSREngine(b=100_000)
        self.analyzer = BayesianAnalyzer(bankroll=bankroll, prior=0.5)
        self.sizer = PositionSizer(bankroll=bankroll, kelly_fraction=0.25)

    def scan(self, limit: int = 20) -> List[Dict]:
        """扫描天气市场，找套利机会"""
        print("\n🌤️  扫描天气市场...")
        markets = self.client.get_markets(tag="weather", limit=limit, order_by="volume24hr")
        print(f"   找到 {len(markets)} 个天气市场")

        opportunities = []

        for market in markets:
            question = market.get("question", "")
            prices = market.get("outcome_prices", [])
            if not prices or len(prices) < 2:
                continue

            try:
                yes_price = float(prices[0])
            except (ValueError, TypeError):
                continue

            if yes_price <= 0.01 or yes_price >= 0.99:
                continue

            # 解析问题
            params = parse_weather_question(question)
            if not params:
                # 无法解析但仍是天气市场，用纯订单簿分析
                opp = self._analyze_orderbook_only(market, yes_price)
                if opp:
                    opportunities.append(opp)
                continue

            # 获取 NOAA 数据
            city = params.get("city", "")
            coords = self.noaa.city_coords(city)
            noaa_prob = None

            if coords and params.get("type") == "temperature":
                noaa_prob = self.noaa.estimate_temp_prob(
                    lat=coords[0],
                    lon=coords[1],
                    target_temp_f=params.get("temp_f", 75),
                    above=params.get("above", True),
                )

            if noaa_prob is not None:
                # 完整贝叶斯分析（NOAA + 订单簿）
                opp = self._analyze_with_noaa(market, yes_price, noaa_prob, params)
            else:
                # 降级：纯订单簿分析
                opp = self._analyze_orderbook_only(market, yes_price)

            if opp:
                opportunities.append(opp)

        opportunities.sort(key=lambda x: x.get("priority", 0), reverse=True)
        return opportunities

    def _analyze_with_noaa(
        self,
        market: Dict,
        yes_price: float,
        noaa_prob: float,
        params: Dict,
    ) -> Optional[Dict]:
        """NOAA + 订单簿联合分析"""
        # 获取订单簿
        token_ids = market.get("clob_token_ids", [])
        ob_imbalance = self._get_ob_imbalance(token_ids)

        signals = [
            SignalFactory.from_noaa_forecast(noaa_prob, accuracy_rate=0.93),
            SignalFactory.from_orderbook_imbalance(ob_imbalance),
        ]

        bayes = self.analyzer.analyze(
            market_yes_price=yes_price,
            signals_raw=signals,
            min_edge=0.05,
            confidence_override=0.80,  # NOAA 高置信度
        )

        if not bayes["entry_valid"]:
            return None

        kelly = self.sizer.kelly_size(bayes["bayesian_prob"], yes_price, confidence=0.80)

        priority = bayes["abs_edge"] * 0.80 * min(1.0, market.get("volume_24h", 0) / 50_000)

        return {
            "type": "noaa_arb",
            "question": market["question"][:70],
            "yes_price": yes_price,
            "noaa_prob": noaa_prob,
            "bayesian_prob": bayes["bayesian_prob"],
            "edge": bayes["abs_edge"],
            "ev": bayes["ev_per_dollar"],
            "action": bayes["action"],
            "position_usdc": kelly.get("position_usdc", 0),
            "kelly_pct": kelly.get("final_pct", 0),
            "confidence": 0.80,
            "ob_imbalance": ob_imbalance,
            "volume_24h": market.get("volume_24h", 0),
            "priority": priority,
            "city": params.get("city", ""),
        }

    def _analyze_orderbook_only(self, market: Dict, yes_price: float) -> Optional[Dict]:
        """无 NOAA 时的纯订单簿分析"""
        token_ids = market.get("clob_token_ids", [])
        ob_imbalance = self._get_ob_imbalance(token_ids)

        if abs(ob_imbalance) < 0.3:  # 订单簿信号不够强就跳过
            return None

        signals = [SignalFactory.from_orderbook_imbalance(ob_imbalance)]
        bayes = self.analyzer.analyze(
            market_yes_price=yes_price,
            signals_raw=signals,
            min_edge=0.08,  # 纯订单簿要求更高 edge
            confidence_override=0.50,
        )

        if not bayes["entry_valid"]:
            return None

        kelly = self.sizer.kelly_size(bayes["bayesian_prob"], yes_price, confidence=0.50)
        priority = bayes["abs_edge"] * 0.50 * min(1.0, market.get("volume_24h", 0) / 50_000)

        return {
            "type": "ob_only",
            "question": market["question"][:70],
            "yes_price": yes_price,
            "noaa_prob": None,
            "bayesian_prob": bayes["bayesian_prob"],
            "edge": bayes["abs_edge"],
            "ev": bayes["ev_per_dollar"],
            "action": bayes["action"],
            "position_usdc": kelly.get("position_usdc", 0),
            "kelly_pct": kelly.get("final_pct", 0),
            "confidence": 0.50,
            "ob_imbalance": ob_imbalance,
            "volume_24h": market.get("volume_24h", 0),
            "priority": priority,
            "city": "",
        }

    def _get_ob_imbalance(self, token_ids: List[str]) -> float:
        if not token_ids:
            return 0.0
        try:
            ob = self.client.get_orderbook(token_ids[0])
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])
            bid_d = sum(float(b.get("size", 0)) for b in bids[:5])
            ask_d = sum(float(a.get("size", 0)) for a in asks[:5])
            total = bid_d + ask_d
            return (bid_d - ask_d) / total if total > 0 else 0.0
        except Exception:
            return 0.0


# ─────────────────────────────────────────
# 时区套利窗口检测
# ─────────────────────────────────────────
def is_timezone_arb_window() -> Tuple[bool, str]:
    """
    检查当前是否在时区套利窗口
    北京 00:00-06:00 = 美东 12:00-18:00 前一天 = 流动性最差

    Returns:
        (is_window, message)
    """
    now_utc = datetime.now(timezone.utc)
    beijing_hour = (now_utc.hour + 8) % 24

    if 0 <= beijing_hour < 6:
        return True, f"🎯 时区套利窗口激活！北京 {beijing_hour:02d}:00（美国用户睡觉中）"
    else:
        next_window = (24 - beijing_hour) % 24
        return False, f"⏰ 当前北京 {beijing_hour:02d}:00，距离套利窗口还有约 {next_window}h"


# ─────────────────────────────────────────
# CLI 入口
# ─────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="天气套利扫描器 (NOAA + LMSR + Bayes)")
    parser.add_argument("--bankroll", type=float, default=1000.0)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    # 检查时区窗口
    is_window, msg = is_timezone_arb_window()
    print(f"\n{msg}")

    scanner = WeatherArbScanner(bankroll=args.bankroll)
    opps = scanner.scan(limit=args.limit)

    if not opps:
        print("\n📭 暂无天气套利机会")
    else:
        print(f"\n✅ 发现 {len(opps)} 个天气套利机会：\n")
        for i, opp in enumerate(opps, 1):
            src = "🌤️ NOAA" if opp["type"] == "noaa_arb" else "📊 OB"
            action_emoji = "🟢" if opp["action"] == "buy_yes" else "🔴"
            print(f"#{i} {src} {action_emoji} {opp['action'].upper()}")
            print(f"  📌 {opp['question']}")
            print(f"  💰 市场价: {opp['yes_price']:.2%}", end="")
            if opp["noaa_prob"]:
                print(f"  |  NOAA预测: {opp['noaa_prob']:.2%}", end="")
            print(f"  |  贝叶斯: {opp['bayesian_prob']:.2%}")
            print(f"  📈 Edge: {opp['edge']:.2%}  |  Kelly仓位: ${opp['position_usdc']:.0f}")
            print()

    print(f"\n⚠️  1/4 Kelly 已应用。NEVER full Kelly on short-duration markets!")
