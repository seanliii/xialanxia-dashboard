"""
AISA API 客户端
整合 Twitter 搜索、趋势、KOL 追踪、AI 模型调用
"""
import requests
from typing import List, Dict, Optional
from config import AISA_API_KEY, AISA_BASE_URL


class AISATwitterClient:
    """AISA Twitter API 客户端"""
    
    def __init__(self, api_key: str = AISA_API_KEY):
        self.api_key = api_key
        self.base_url = f"{AISA_BASE_URL}/apis/v1/twitter"
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def search_tweets(
        self, 
        query: str, 
        query_type: str = "Latest",  # Latest | Top
        limit: int = 20
    ) -> List[Dict]:
        """
        搜索推文
        
        Args:
            query: 搜索关键词（支持高级语法）
            query_type: "Latest"（最新）或 "Top"（热门）
            limit: 返回数量
            
        Returns:
            推文列表
        """
        url = f"{self.base_url}/tweet/advanced_search"
        params = {
            "query": query,
            "queryType": query_type,
        }
        
        try:
            r = requests.get(url, headers=self.headers, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            tweets = data.get("tweets", [])[:limit]
            return [self._parse_tweet(t) for t in tweets]
        except Exception as e:
            print(f"[AISA Twitter] 搜索失败: {e}")
            return []
    
    def get_trends(self, woeid: int = 1) -> List[Dict]:
        """
        获取 Twitter 趋势
        
        Args:
            woeid: 地区代码（1=全球，23424977=美国）
            
        Returns:
            趋势列表
        """
        url = f"{self.base_url}/trends"
        params = {"woeid": woeid}
        
        try:
            r = requests.get(url, headers=self.headers, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            if data and len(data) > 0 and "trends" in data[0]:
                return data[0]["trends"][:20]
            return []
        except Exception as e:
            print(f"[AISA Twitter] 获取趋势失败: {e}")
            return []
    
    def get_user_tweets(self, username: str, limit: int = 10) -> List[Dict]:
        """获取用户最近推文"""
        url = f"{self.base_url}/user/user_tweets"
        params = {"userName": username, "limit": limit}
        
        try:
            r = requests.get(url, headers=self.headers, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            tweets = data.get("tweets", [])
            return [self._parse_tweet(t) for t in tweets]
        except Exception as e:
            print(f"[AISA Twitter] 获取用户推文失败: {e}")
            return []
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """获取用户信息"""
        url = f"{self.base_url}/user/info"
        params = {"userName": username}
        
        try:
            r = requests.get(url, headers=self.headers, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            return {
                "name": data.get("name"),
                "username": data.get("userName"),
                "followers": data.get("followers"),
                "following": data.get("following"),
                "description": data.get("profile_bio", {}).get("description", ""),
                "verified": data.get("isBlueVerified", False),
            }
        except Exception as e:
            print(f"[AISA Twitter] 获取用户信息失败: {e}")
            return None
    
    def _parse_tweet(self, tweet: Dict) -> Dict:
        """解析推文数据"""
        author = tweet.get("author", {})
        return {
            "id": tweet.get("id"),
            "text": tweet.get("text", ""),
            "created_at": tweet.get("createdAt"),
            "url": tweet.get("url"),
            "likes": tweet.get("likeCount", 0),
            "retweets": tweet.get("retweetCount", 0),
            "views": tweet.get("viewCount", 0),
            "author": {
                "name": author.get("name"),
                "username": author.get("userName"),
                "followers": author.get("followers", 0),
                "verified": author.get("isBlueVerified", False),
            },
        }


class AISAModelClient:
    """AISA AI 模型调用客户端"""
    
    def __init__(self, api_key: str = AISA_API_KEY):
        self.api_key = api_key
        self.base_url = f"{AISA_BASE_URL}/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    
    def list_models(self) -> List[str]:
        """列出可用模型"""
        url = f"{self.base_url}/models"
        try:
            r = requests.get(url, headers=self.headers, timeout=30)
            r.raise_for_status()
            data = r.json()
            return [m["id"] for m in data.get("data", [])]
        except Exception as e:
            print(f"[AISA Models] 获取模型列表失败: {e}")
            return []
    
    def chat(
        self, 
        prompt: str, 
        model: str = "gpt-4.1-mini",
        system: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """
        调用 AI 模型
        
        Args:
            prompt: 用户提示
            model: 模型名称
            system: 系统提示
            max_tokens: 最大 token 数
            temperature: 温度
            
        Returns:
            模型回复
        """
        url = f"{self.base_url}/chat/completions"
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        try:
            r = requests.post(url, headers=self.headers, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[AISA Chat] 调用失败: {e}")
            return None
    
    def analyze_market_sentiment(self, market_question: str, tweets: List[Dict]) -> Dict:
        """
        分析市场情绪
        
        Args:
            market_question: 市场问题
            tweets: 相关推文
            
        Returns:
            情绪分析结果
        """
        tweets_text = "\n".join([
            f"- {t['text'][:200]}... (likes: {t['likes']}, views: {t['views']})"
            for t in tweets[:10]
        ])
        
        prompt = f"""分析以下 Polymarket 市场的 Twitter 情绪：

市场问题：{market_question}

相关推文：
{tweets_text}

请输出 JSON 格式：
{{
    "sentiment": "bullish" | "bearish" | "neutral",
    "confidence": 0-100,
    "key_signals": ["信号1", "信号2"],
    "recommended_action": "buy_yes" | "buy_no" | "hold",
    "reasoning": "分析理由"
}}"""
        
        response = self.chat(
            prompt=prompt,
            model="gpt-4.1",  # 用强模型做分析
            system="你是 Polymarket 情绪分析专家，根据 Twitter 数据判断市场走向。",
            temperature=0.3,
        )
        
        if response:
            try:
                import json
                # 提取 JSON
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
            except:
                pass
        
        return {
            "sentiment": "neutral",
            "confidence": 0,
            "key_signals": [],
            "recommended_action": "hold",
            "reasoning": "分析失败",
        }


# ============ 便捷函数 ============
def search_polymarket_tweets(query: str = "polymarket", limit: int = 10) -> List[Dict]:
    """搜索 Polymarket 相关推文"""
    client = AISATwitterClient()
    return client.search_tweets(query, query_type="Top", limit=limit)


def get_kol_latest_tweets(usernames: List[str]) -> Dict[str, List[Dict]]:
    """获取多个 KOL 的最新推文"""
    client = AISATwitterClient()
    results = {}
    for username in usernames:
        results[username] = client.get_user_tweets(username, limit=5)
    return results


def analyze_with_ai(prompt: str, model: str = "gpt-4.1") -> Optional[str]:
    """快速 AI 分析"""
    client = AISAModelClient()
    return client.chat(prompt, model=model)


# ============ 测试 ============
if __name__ == "__main__":
    print("=== 测试 AISA Twitter 客户端 ===")
    twitter = AISATwitterClient()
    
    # 搜索热门推文
    tweets = twitter.search_tweets("polymarket trading", query_type="Top", limit=3)
    for t in tweets:
        print(f"\n📌 {t['text'][:100]}...")
        print(f"   👍 {t['likes']} | 👀 {t['views']} | 🔗 {t['url']}")
    
    # 获取趋势
    print("\n=== Twitter 趋势 ===")
    trends = twitter.get_trends(woeid=1)
    for trend in trends[:5]:
        print(f"  - {trend.get('name')}")
    
    # 测试 AI 模型
    print("\n=== 测试 AI 模型 ===")
    model_client = AISAModelClient()
    models = model_client.list_models()
    print(f"可用模型数: {len(models)}")
    print(f"前 5 个: {models[:5]}")
