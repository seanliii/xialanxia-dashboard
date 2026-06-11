"""
AISA 全套 API 客户端 — 2026-03-16 验证版
整合: Twitter + Perplexity + Financial + AI 模型
"""
import os
os.environ["https_proxy"] = "http://10.59.78.158:3128"
os.environ["http_proxy"] = "http://10.59.78.158:3128"
os.environ["HTTPS_PROXY"] = "http://10.59.78.158:3128"
os.environ["HTTP_PROXY"] = "http://10.59.78.158:3128"
import requests
from typing import List, Dict, Optional
import os

AISA_KEY = os.getenv("AISA_API_KEY", "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41")
BASE = "https://api.aisa.one"
HEADERS = {"Authorization": f"Bearer {AISA_KEY}"}
JSON_HEADERS = {**HEADERS, "Content-Type": "application/json"}


# ============ Twitter ============
def twitter_search(query: str, query_type: str = "Top", limit: int = 10) -> List[Dict]:
    r = requests.get(f"{BASE}/apis/v1/twitter/tweet/advanced_search",
                     headers=HEADERS, params={"query": query, "queryType": query_type}, timeout=20)
    tweets = r.json().get("tweets", [])[:limit]
    return [{"text": t.get("text",""), "likes": t.get("likeCount",0),
             "views": t.get("viewCount",0), "url": t.get("url",""),
             "author": t.get("author",{}).get("userName","")} for t in tweets]

def twitter_trends(woeid: int = 1) -> List[str]:
    r = requests.get(f"{BASE}/apis/v1/twitter/trends", headers=HEADERS, params={"woeid": woeid}, timeout=15)
    data = r.json()
    if data and "trends" in data[0]:
        return [t["name"] for t in data[0]["trends"][:20]]
    return []

def twitter_user_tweets(username: str, limit: int = 5) -> List[Dict]:
    r = requests.get(f"{BASE}/apis/v1/twitter/user/user_tweets",
                     headers=HEADERS, params={"userName": username, "limit": limit}, timeout=20)
    return r.json().get("tweets", [])[:limit]


# ============ Perplexity (实时搜索 + AI分析) ============
def perplexity_search(question: str, model: str = "sonar") -> Dict:
    """
    Perplexity 实时搜索（带引用链接）
    model: sonar | sonar-pro | sonar-reasoning-pro | sonar-deep-research
    """
    r = requests.post(f"{BASE}/apis/v1/perplexity/{model}",
                      headers=JSON_HEADERS,
                      json={"model": model, "messages": [{"role": "user", "content": question}],
                            "max_tokens": 600},
                      timeout=30)
    data = r.json()
    return {
        "answer": data.get("choices", [{}])[0].get("message", {}).get("content", ""),
        "citations": data.get("citations", []),
        "model": model,
    }

def perplexity_deep_research(question: str) -> Dict:
    """Perplexity Deep Research — 深度调研"""
    return perplexity_search(question, model="sonar-deep-research")


# ============ Financial API ============
def financial_company(ticker: str) -> Dict:
    """公司基本信息"""
    r = requests.get(f"{BASE}/apis/v1/financial/company/facts",
                     headers=HEADERS, params={"ticker": ticker}, timeout=15)
    facts = r.json().get("company_facts", {})
    return {"name": facts.get("name"), "sector": facts.get("sector"),
            "industry": facts.get("industry"), "exchange": facts.get("exchange")}

def financial_metrics(ticker: str) -> Dict:
    """财务指标快照（PE、ROE、成长率等）"""
    r = requests.get(f"{BASE}/apis/v1/financial/financial-metrics/snapshot",
                     headers=HEADERS, params={"ticker": ticker}, timeout=15)
    snap = r.json().get("snapshot", {})
    return {
        "ticker": ticker,
        "pe_ratio": snap.get("price_to_earnings_ratio"),
        "pb_ratio": snap.get("price_to_book_ratio"),
        "roe": snap.get("return_on_equity"),
        "net_margin": snap.get("net_margin"),
        "revenue_growth": snap.get("revenue_growth"),
        "earnings_growth": snap.get("earnings_growth"),
        "market_cap": snap.get("market_cap"),
        "eps": snap.get("earnings_per_share"),
    }

def financial_earnings_news(ticker: str) -> List[Dict]:
    """财报新闻/press releases"""
    r = requests.get(f"{BASE}/apis/v1/financial/earnings/press-releases",
                     headers=HEADERS, params={"ticker": ticker}, timeout=15)
    releases = r.json().get("press_releases", [])
    return [{"date": x.get("date"), "title": x.get("title"),
             "url": x.get("url"), "summary": x.get("text","")[:300]} for x in releases[:3]]

def financial_analyst_estimates(ticker: str) -> Dict:
    """分析师预测（EPS、营收）"""
    r = requests.get(f"{BASE}/apis/v1/financial/analyst-estimates",
                     headers=HEADERS, params={"ticker": ticker}, timeout=15)
    data = r.json()
    estimates = data if isinstance(data, list) else data.get("estimates", [])
    if estimates:
        latest = estimates[0]
        return {"ticker": ticker,
                "est_eps": latest.get("estimatedEpsAvg"),
                "est_revenue": latest.get("estimatedRevenueAvg"),
                "date": latest.get("date")}
    return {}

def financial_income_statement(ticker: str) -> Dict:
    """损益表（最新季度）"""
    r = requests.get(f"{BASE}/apis/v1/financial/financials/income-statements",
                     headers=HEADERS, params={"ticker": ticker, "period": "quarter"}, timeout=15)
    data = r.json()
    stmts = data if isinstance(data, list) else data.get("income_statements", [])
    if stmts:
        latest = stmts[0]
        return {"ticker": ticker, "date": latest.get("date"),
                "revenue": latest.get("revenue"), "net_income": latest.get("netIncome"),
                "eps": latest.get("eps"), "gross_profit": latest.get("grossProfit")}
    return {}


# ============ AI 模型 ============
def ai_chat(prompt: str, model: str = "gpt-4.1", system: str = "", max_tokens: int = 800) -> str:
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    r = requests.post(f"{BASE}/v1/chat/completions", headers=JSON_HEADERS,
                      json={"model": model, "messages": msgs, "max_tokens": max_tokens, "temperature": 0.3},
                      timeout=60)
    return r.json().get("choices", [{}])[0].get("message", {}).get("content", "")


# ============ 综合情报函数 ============
def get_stock_intelligence(ticker: str) -> Dict:
    """
    综合股票情报：公司信息 + 财务指标 + Twitter 情绪 + Perplexity 实时新闻
    """
    company = financial_company(ticker)
    metrics = financial_metrics(ticker)
    
    # Twitter 情绪
    tweets = twitter_search(f"${ticker} stock", query_type="Top", limit=5)
    
    # Perplexity 实时新闻
    news = perplexity_search(f"Latest news about {ticker} stock today", model="sonar")
    
    return {
        "ticker": ticker,
        "company": company,
        "metrics": metrics,
        "tweets": tweets,
        "latest_news": news["answer"][:400],
        "citations": news["citations"][:3],
    }

def get_market_intelligence(topic: str) -> Dict:
    """
    市场情报：Twitter 热帖 + Perplexity 实时搜索 + AI 综合判断
    """
    tweets = twitter_search(topic, query_type="Top", limit=8)
    perp = perplexity_search(f"Latest news and analysis: {topic}", model="sonar")
    
    tweet_summary = "\n".join([f"- {t['text'][:120]} (👍{t['likes']})" for t in tweets[:5]])
    
    analysis = ai_chat(
        f"基于以下信息，用2-3句话总结最重要的信号：\n\nPerplexity: {perp['answer'][:300]}\n\nTwitter热帖:\n{tweet_summary}",
        model="gpt-4.1-mini"
    )
    
    return {
        "topic": topic,
        "perplexity_answer": perp["answer"],
        "citations": perp["citations"][:3],
        "top_tweets": tweets[:3],
        "ai_summary": analysis,
    }


# ============ 测试 ============
if __name__ == "__main__":
    print("=== 测试 AISA 全套 API ===\n")
    
    print("1. Perplexity Sonar:")
    result = perplexity_search("What are the hottest AI agent news today March 16 2026?")
    print(f"   {result['answer'][:200]}...")
    print(f"   引用: {result['citations'][:2]}")
    
    print("\n2. Financial NVDA 指标:")
    m = financial_metrics("NVDA")
    print(f"   PE={m['pe_ratio']:.1f}, ROE={m['roe']:.1%}, 营收增长={m['revenue_growth']:.1%}")
    
    print("\n3. Twitter BTC 热帖:")
    tweets = twitter_search("bitcoin BTC price today", limit=3)
    for t in tweets:
        print(f"   👍{t['likes']} - {t['text'][:80]}...")

