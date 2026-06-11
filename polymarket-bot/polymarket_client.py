"""
Polymarket API 客户端
整合市场数据、订单簿、持仓追踪
"""
import requests
from typing import List, Dict, Optional, Tuple
from config import GAMMA_API, DATA_API, CLOB_API


class PolymarketDataClient:
    """Polymarket 数据 API 客户端（公开，无需认证）"""
    
    def __init__(self):
        self.gamma_api = GAMMA_API
        self.data_api = DATA_API
    
    # ============ 市场数据 ============
    def get_markets(
        self,
        active: bool = True,
        closed: bool = False,
        limit: int = 20,
        tag: str = None,
        order_by: str = "volume24hr",
        ascending: bool = False,
    ) -> List[Dict]:
        """
        获取市场列表
        
        Args:
            active: 是否只获取活跃市场
            closed: 是否包含已关闭市场
            limit: 返回数量
            tag: 筛选标签（weather/sports/politics 等）
            order_by: 排序字段（volume24hr/volumeNum/createdAt）
            ascending: 是否升序
            
        Returns:
            市场列表
        """
        url = f"{self.gamma_api}/markets"
        params = {
            "active": str(active).lower(),
            "closed": str(closed).lower(),
            "limit": limit,
            "order": order_by,
            "ascending": str(ascending).lower(),
        }
        if tag:
            params["tag"] = tag
        
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return [self._parse_market(m) for m in r.json()]
        except Exception as e:
            print(f"[Polymarket] 获取市场失败: {e}")
            return []
    
    def get_market_by_slug(self, slug: str) -> Optional[Dict]:
        """通过 slug 获取单个市场"""
        url = f"{self.gamma_api}/markets/{slug}"
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            return self._parse_market(r.json())
        except Exception as e:
            print(f"[Polymarket] 获取市场失败: {e}")
            return None
    
    def get_market_by_id(self, condition_id: str) -> Optional[Dict]:
        """通过 condition_id 获取市场"""
        url = f"{self.gamma_api}/markets"
        params = {"id": condition_id}
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            markets = r.json()
            if markets:
                return self._parse_market(markets[0])
            return None
        except Exception as e:
            print(f"[Polymarket] 获取市场失败: {e}")
            return None
    
    def search_markets(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索市场"""
        url = f"{self.gamma_api}/markets"
        params = {
            "active": "true",
            "closed": "false",
            "limit": limit,
            "_q": query,
        }
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return [self._parse_market(m) for m in r.json()]
        except Exception as e:
            print(f"[Polymarket] 搜索市场失败: {e}")
            return []
    
    # ============ 价格数据 ============
    def get_prices(self, token_ids: List[str]) -> Dict[str, float]:
        """
        获取 token 价格（批量）
        
        Args:
            token_ids: token ID 列表
            
        Returns:
            {token_id: price} 字典
        """
        url = f"{CLOB_API}/prices"
        params = {"token_ids": ",".join(token_ids)}
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[Polymarket] 获取价格失败: {e}")
            return {}
    
    def get_orderbook(self, token_id: str) -> Dict:
        """
        获取订单簿
        
        Args:
            token_id: token ID
            
        Returns:
            {bids: [...], asks: [...]}
        """
        url = f"{CLOB_API}/book"
        params = {"token_id": token_id}
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[Polymarket] 获取订单簿失败: {e}")
            return {"bids": [], "asks": []}
    
    def get_spread(self, token_id: str) -> Tuple[float, float, float]:
        """
        获取买卖价差
        
        Returns:
            (best_bid, best_ask, spread)
        """
        orderbook = self.get_orderbook(token_id)
        
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])
        
        best_bid = float(bids[0]["price"]) if bids else 0
        best_ask = float(asks[0]["price"]) if asks else 1
        spread = best_ask - best_bid
        
        return best_bid, best_ask, spread
    
    # ============ 排行榜/跟单 ============
    def get_leaderboard(self, limit: int = 20) -> List[Dict]:
        """获取排行榜（鲸鱼追踪）"""
        url = f"{self.data_api}/leaderboard"
        params = {"limit": limit}
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[Polymarket] 获取排行榜失败: {e}")
            return []
    
    def get_user_positions(self, address: str) -> List[Dict]:
        """
        获取用户持仓
        
        Args:
            address: 钱包地址
            
        Returns:
            持仓列表
        """
        url = f"{self.data_api}/positions"
        params = {"user": address}
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[Polymarket] 获取持仓失败: {e}")
            return []
    
    def get_user_trades(self, address: str, limit: int = 50) -> List[Dict]:
        """获取用户交易历史"""
        url = f"{self.data_api}/trades"
        params = {"user": address, "limit": limit}
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[Polymarket] 获取交易历史失败: {e}")
            return []
    
    # ============ 事件数据 ============
    def get_events(self, active: bool = True, limit: int = 20) -> List[Dict]:
        """获取事件列表"""
        url = f"{self.gamma_api}/events"
        params = {
            "active": str(active).lower(),
            "closed": "false",
            "limit": limit,
        }
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[Polymarket] 获取事件失败: {e}")
            return []
    
    # ============ 辅助方法 ============
    def _parse_market(self, market: Dict) -> Dict:
        """解析市场数据"""
        # 解析 outcomes
        import json
        outcomes = market.get("outcomes", "[]")
        if isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except:
                outcomes = []
        
        # 解析 token IDs
        clob_token_ids = market.get("clobTokenIds", "[]")
        if isinstance(clob_token_ids, str):
            try:
                clob_token_ids = json.loads(clob_token_ids)
            except:
                clob_token_ids = []
        
        # 解析 outcome prices
        outcome_prices = market.get("outcomePrices", "[]")
        if isinstance(outcome_prices, str):
            try:
                outcome_prices = json.loads(outcome_prices)
            except:
                outcome_prices = []
        
        return {
            "id": market.get("id"),
            "condition_id": market.get("conditionId"),
            "question": market.get("question"),
            "description": market.get("description", ""),
            "slug": market.get("slug"),
            "outcomes": outcomes,
            "outcome_prices": outcome_prices,
            "clob_token_ids": clob_token_ids,
            "volume_24h": market.get("volume24hr", 0),
            "volume_total": market.get("volumeNum", 0),
            "liquidity": market.get("liquidityNum", 0),
            "end_date": market.get("endDate"),
            "active": market.get("active", False),
            "closed": market.get("closed", False),
            "tags": market.get("tags", []),
        }


# ============ 便捷函数 ============
def get_hot_markets(limit: int = 10) -> List[Dict]:
    """获取热门市场（按 24h 交易量排序）"""
    client = PolymarketDataClient()
    return client.get_markets(limit=limit, order_by="volume24hr")


def get_weather_markets(limit: int = 10) -> List[Dict]:
    """获取天气相关市场"""
    client = PolymarketDataClient()
    return client.get_markets(tag="weather", limit=limit)


def get_sports_markets(limit: int = 10) -> List[Dict]:
    """获取体育相关市场"""
    client = PolymarketDataClient()
    return client.get_markets(tag="sports", limit=limit)


def track_whale(address: str) -> Dict:
    """追踪鲸鱼持仓"""
    client = PolymarketDataClient()
    return {
        "positions": client.get_user_positions(address),
        "trades": client.get_user_trades(address, limit=20),
    }


# ============ 测试 ============
if __name__ == "__main__":
    print("=== 测试 Polymarket 数据客户端 ===")
    client = PolymarketDataClient()
    
    # 获取热门市场
    print("\n📊 热门市场 (Top 5):")
    markets = client.get_markets(limit=5, order_by="volume24hr")
    for m in markets:
        print(f"\n  📌 {m['question']}")
        print(f"     💰 24h Volume: ${m['volume_24h']:,.0f}")
        print(f"     📈 Outcomes: {m['outcomes']}")
        print(f"     💵 Prices: {m['outcome_prices']}")
    
    # 获取排行榜
    print("\n\n🐳 排行榜 (Top 3):")
    leaderboard = client.get_leaderboard(limit=3)
    for i, user in enumerate(leaderboard, 1):
        print(f"  {i}. {user.get('address', 'Unknown')[:10]}... | Profit: ${user.get('pnl', 0):,.0f}")
