"""
预测 Agent — 只负责分析和预测，不执行交易
采用双 Agent 架构中的「预测层」

v2: 集成 LMSR Engine + Bayesian Engine（QR-PM-2026-0041）
  - LMSR 定价检测真实价格偏差
  - 贝叶斯序贯更新多源信号
  - EV + 凯利公式精确仓位计算
"""
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from config import (
    MIN_CONFIDENCE_SCORE,
    MIN_EDGE_THRESHOLD,
    PREFERRED_MARKET_TAGS,
    BLACKLIST_MARKET_TAGS,
    TWITTER_KOLS,
)
from aisa_client import AISATwitterClient, AISAModelClient
from polymarket_client import PolymarketDataClient
from lmsr_engine import LMSREngine, check_entry
from bayesian_engine import BayesianAnalyzer, SignalFactory


class PredictionAgent:
    """预测 Agent — 分析市场并生成交易信号（v2: LMSR + Bayes）"""
    
    def __init__(self, bankroll: float = 1000.0):
        self.twitter = AISATwitterClient()
        self.ai = AISAModelClient()
        self.polymarket = PolymarketDataClient()
        self.bankroll = bankroll

        # 核心引擎 (QR-PM-2026-0041)
        self.lmsr = LMSREngine(b=100_000)
        self.bayesian = BayesianAnalyzer(bankroll=bankroll, prior=0.5)
        
        # 信号缓存（避免重复分析）
        self.signal_cache: Dict[str, Dict] = {}
    
    # ============ 核心预测方法 ============
    def scan_opportunities(self, limit: int = 20) -> List[Dict]:
        """
        扫描市场机会
        
        Returns:
            按 edge 排序的机会列表
        """
        opportunities = []
        
        # 1. 获取热门市场
        markets = self.polymarket.get_markets(limit=limit, order_by="volume24hr")
        
        for market in markets:
            # 跳过黑名单标签
            if any(tag in BLACKLIST_MARKET_TAGS for tag in market.get("tags", [])):
                continue
            
            # 分析市场
            signal = self.analyze_market(market)
            
            if signal["confidence"] >= MIN_CONFIDENCE_SCORE and signal["edge"] >= MIN_EDGE_THRESHOLD:
                opportunities.append({
                    "market": market,
                    "signal": signal,
                    "priority": signal["edge"] * signal["confidence"] / 100,
                })
        
        # 按优先级排序
        opportunities.sort(key=lambda x: x["priority"], reverse=True)
        return opportunities
    
    def analyze_market(self, market: Dict) -> Dict:
        """
        综合分析单个市场
        
        Args:
            market: 市场数据
            
        Returns:
            {
                "predicted_prob": 0-1,      # AI 预测概率
                "market_prob": 0-1,         # 市场当前定价
                "edge": 0-1,                # 边际收益
                "confidence": 0-100,        # 置信度
                "action": "buy_yes" | "buy_no" | "hold",
                "signals": [...],           # 信号来源
                "reasoning": "...",         # 分析理由
            }
        """
        market_id = market.get("id") or market.get("condition_id")
        question = market.get("question", "")
        
        # 检查缓存
        if market_id in self.signal_cache:
            cached = self.signal_cache[market_id]
            # 缓存 5 分钟有效
            if (datetime.now(timezone.utc) - cached["timestamp"]).seconds < 300:
                return cached["signal"]
        
        # 获取当前市场价格
        outcome_prices = market.get("outcome_prices", [])
        if len(outcome_prices) >= 2:
            yes_price = float(outcome_prices[0])
            no_price = float(outcome_prices[1])
        else:
            yes_price = 0.5
            no_price = 0.5
        
        # 收集多维度信号
        signals = []
        
        # 1. Twitter 情绪分析
        twitter_signal = self._analyze_twitter_sentiment(question)
        signals.append(("twitter", twitter_signal))
        
        # 2. KOL 动向
        kol_signal = self._check_kol_mentions(question)
        signals.append(("kol", kol_signal))
        
        # 3. 订单簿分析
        orderbook_signal = self._analyze_orderbook(market)
        signals.append(("orderbook", orderbook_signal))
        
        # 4. 将信号转换为贝叶斯格式
        bayes_signals = []
        
        # Twitter 信号
        tw = orderbook_signal  # 先用 orderbook
        twitter_data = signals[0][1]
        if twitter_data.get("tweet_count", 0) > 0:
            bayes_signals.append(SignalFactory.from_twitter_sentiment(
                sentiment=twitter_data.get("sentiment", "neutral"),
                tweet_count=twitter_data.get("tweet_count", 0),
                positive_ratio=twitter_data.get("positive", 0) / max(1, twitter_data.get("tweet_count", 1)),
            ))
        
        # 订单簿信号
        ob_data = signals[2][1]
        bayes_signals.append(SignalFactory.from_orderbook_imbalance(
            imbalance=ob_data.get("imbalance", 0)
        ))
        
        # 5. 贝叶斯分析（含 EV + Kelly 公式）
        bayes_result = self.bayesian.analyze(
            market_yes_price=yes_price,
            signals_raw=bayes_signals,
            min_edge=MIN_EDGE_THRESHOLD,
        )
        
        # 6. LMSR 入场验证
        lmsr_check = self.lmsr.detect_inefficiency(
            market_yes_price=yes_price,
            bayesian_prob=bayes_result["bayesian_prob"],
            threshold=MIN_EDGE_THRESHOLD,
        )
        
        # 7. AI 辅助推理（可选）
        ai_prediction = self._get_ai_prediction(market, signals)
        
        result = {
            "predicted_prob": bayes_result["bayesian_prob"],
            "market_prob": yes_price,
            "edge": bayes_result["abs_edge"],
            "confidence": int(bayes_result["confidence"] * 100),
            "action": bayes_result["action"],
            "signals": [s[0] for s in signals],
            "reasoning": ai_prediction.get("reasoning", ""),
            # 新增：完整量化输出
            "ev_per_dollar": bayes_result["ev_per_dollar"],
            "kelly_position_usdc": bayes_result["position_usdc"],
            "lmsr_entry_valid": lmsr_check["entry_valid"],
            "signal_count": bayes_result["signal_count"],
        }
        
        # 缓存结果
        self.signal_cache[market_id] = {
            "signal": result,
            "timestamp": datetime.now(timezone.utc),
        }
        
        return result
    
    # ============ 信号分析方法 ============
    def _analyze_twitter_sentiment(self, question: str) -> Dict:
        """分析 Twitter 情绪"""
        # 构造搜索查询
        keywords = question.split()[:5]  # 取前 5 个词
        query = " ".join(keywords)
        
        tweets = self.twitter.search_tweets(
            query=f"polymarket {query}",
            query_type="Top",
            limit=15,
        )
        
        if not tweets:
            return {
                "sentiment": "neutral",
                "confidence": 0,
                "tweet_count": 0,
            }
        
        # 简单情绪分析（基于关键词）
        positive_keywords = ["yes", "will", "definitely", "bullish", "buying", "bet on"]
        negative_keywords = ["no", "won't", "definitely not", "bearish", "selling", "against"]
        
        positive_count = 0
        negative_count = 0
        
        for tweet in tweets:
            text = tweet["text"].lower()
            if any(kw in text for kw in positive_keywords):
                positive_count += 1
            if any(kw in text for kw in negative_keywords):
                negative_count += 1
        
        total = positive_count + negative_count
        if total == 0:
            sentiment = "neutral"
            confidence = 30
        elif positive_count > negative_count:
            sentiment = "bullish"
            confidence = min(90, 50 + (positive_count - negative_count) * 10)
        else:
            sentiment = "bearish"
            confidence = min(90, 50 + (negative_count - positive_count) * 10)
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "tweet_count": len(tweets),
            "positive": positive_count,
            "negative": negative_count,
        }
    
    def _check_kol_mentions(self, question: str) -> Dict:
        """检查 KOL 提及"""
        mentions = []
        
        for kol in TWITTER_KOLS[:5]:  # 只检查前 5 个（节省 API 调用）
            tweets = self.twitter.search_tweets(
                query=f"from:{kol} polymarket",
                query_type="Latest",
                limit=3,
            )
            
            for tweet in tweets:
                if any(word.lower() in tweet["text"].lower() for word in question.split()[:3]):
                    mentions.append({
                        "kol": kol,
                        "text": tweet["text"][:200],
                        "likes": tweet["likes"],
                        "url": tweet["url"],
                    })
        
        return {
            "kol_mentions": len(mentions),
            "mentions": mentions,
            "signal_strength": min(100, len(mentions) * 20),
        }
    
    def _analyze_orderbook(self, market: Dict) -> Dict:
        """分析订单簿"""
        token_ids = market.get("clob_token_ids", [])
        if not token_ids:
            return {"depth": 0, "imbalance": 0}
        
        # 只分析 Yes token
        orderbook = self.polymarket.get_orderbook(token_ids[0])
        
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])
        
        bid_depth = sum(float(b.get("size", 0)) for b in bids[:5])
        ask_depth = sum(float(a.get("size", 0)) for a in asks[:5])
        
        total_depth = bid_depth + ask_depth
        if total_depth > 0:
            imbalance = (bid_depth - ask_depth) / total_depth
        else:
            imbalance = 0
        
        return {
            "bid_depth": bid_depth,
            "ask_depth": ask_depth,
            "imbalance": imbalance,  # > 0 偏向买入，< 0 偏向卖出
        }
    
    def _get_ai_prediction(self, market: Dict, signals: List[Tuple]) -> Dict:
        """AI 综合预测"""
        question = market.get("question", "")
        description = market.get("description", "")[:500]
        current_price = market.get("outcome_prices", [0.5])[0]
        
        # 构造信号摘要
        signal_summary = []
        for name, data in signals:
            if name == "twitter":
                signal_summary.append(f"Twitter 情绪: {data['sentiment']} (confidence: {data['confidence']}%)")
            elif name == "kol":
                signal_summary.append(f"KOL 提及: {data['kol_mentions']} 条")
            elif name == "orderbook":
                signal_summary.append(f"订单簿失衡: {data['imbalance']:.2f} (>0 偏买, <0 偏卖)")
        
        prompt = f"""你是 Polymarket 预测专家。分析以下市场并给出预测：

市场问题：{question}
市场描述：{description}
当前 Yes 价格：{float(current_price):.2%}

信号分析：
{chr(10).join(signal_summary)}

请输出 JSON：
{{
    "probability": 0.0-1.0,  // 你预测 Yes 的概率
    "confidence": 0-100,     // 你的置信度
    "reasoning": "分析理由（不超过100字）"
}}

注意：
1. 只做「可验证」预测，避免主观判断
2. 考虑当前市场定价是否已经充分反映信息
3. 如果信息不足，confidence 应该较低"""

        response = self.ai.chat(
            prompt=prompt,
            model="gpt-4.1",  # 用强模型做预测
            temperature=0.3,
        )
        
        if response:
            try:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    result = json.loads(response[start:end])
                    return {
                        "probability": float(result.get("probability", 0.5)),
                        "confidence": int(result.get("confidence", 50)),
                        "reasoning": result.get("reasoning", ""),
                    }
            except:
                pass
        
        return {
            "probability": 0.5,
            "confidence": 30,
            "reasoning": "AI 分析失败，使用默认值",
        }
    
    # ============ 高级策略 ============
    def find_timezone_arbitrage(self) -> List[Dict]:
        """
        寻找时区套利机会
        非美时区（北京 00:00-06:00）市场定价可能偏低
        """
        now = datetime.now(timezone.utc)
        beijing_hour = (now.hour + 8) % 24
        
        # 只在亚洲凌晨寻找机会
        if not (0 <= beijing_hour <= 6):
            return []
        
        opportunities = []
        markets = self.polymarket.get_markets(limit=30, order_by="volume24hr")
        
        for market in markets:
            # 寻找价格明显偏离的市场
            signal = self.analyze_market(market)
            if signal["edge"] > 0.15:  # 15%+ 边际
                opportunities.append({
                    "market": market,
                    "signal": signal,
                    "type": "timezone_arbitrage",
                })
        
        return opportunities
    
    def track_whale_activity(self, whale_addresses: List[str]) -> List[Dict]:
        """追踪鲸鱼活动"""
        whale_signals = []
        
        for address in whale_addresses[:5]:
            trades = self.polymarket.get_user_trades(address, limit=10)
            positions = self.polymarket.get_user_positions(address)
            
            if trades:
                latest_trade = trades[0]
                whale_signals.append({
                    "whale": address[:10] + "...",
                    "latest_trade": latest_trade,
                    "position_count": len(positions),
                })
        
        return whale_signals


# ============ 测试 ============
if __name__ == "__main__":
    print("=== 测试预测 Agent ===")
    agent = PredictionAgent()
    
    # 扫描机会
    print("\n🔍 扫描市场机会...")
    opportunities = agent.scan_opportunities(limit=5)
    
    for i, opp in enumerate(opportunities[:3], 1):
        market = opp["market"]
        signal = opp["signal"]
        print(f"\n{i}. 📌 {market['question'][:60]}...")
        print(f"   📈 市场价格: {signal['market_prob']:.1%} | AI 预测: {signal['predicted_prob']:.1%}")
        print(f"   💰 Edge: {signal['edge']:.1%} | 置信度: {signal['confidence']}%")
        print(f"   🎯 建议: {signal['action']}")
        print(f"   💭 理由: {signal['reasoning'][:100]}...")
