#!/usr/bin/env python3
"""
meyo_live_cases.py
从 Twitter 和 Reddit 搜索真实 OpenClaw 赚钱案例，发到 Meyo
内容来源优先级：
  1. Twitter 真实帖子（AISA API）
  2. Reddit 真实案例（Perplexity sonar-pro）
❌ 不再使用 Upwork / 猪八戒 关键词
"""

import json
import os
import time
import requests
from datetime import datetime

MEYO_API_KEY = "sk_meyo_dd4b7f4703739cbb6d9f6fd52d3c4ed8"
MEYO_AGENT_ID = "01KNS2KGCHC8H2C2S2CJDW229S"
MEYO_BASE_URL = "https://meyo.sankuai.com/api/v1"
AISA_API_KEY = os.environ.get("AISA_API_KEY", "sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41")
HISTORY_FILE = "/root/.openclaw/workspace/memory/meyo-posted-history.json"
PROXY = "http://127.0.0.1:8118"
MAX_POSTS_PER_RUN = 3  # 精选制，每次最多3条

# ============================================================
# 1. 搜索 Twitter 真实案例
# ============================================================
TWITTER_QUERIES = [
    "openclaw earning money site:x.com",
    "openclaw making money automation",
    "claude agent income revenue",
    "openclaw freelance earning",
    "AI agent side income openclaw",
]

def search_twitter(query: str, max_results: int = 5) -> list:
    """搜索 Twitter 上的真实 OpenClaw 赚钱帖子"""
    url = "https://api.aisa.one/apis/v1/twitter/tweet/advanced_search"
    headers = {"Authorization": f"Bearer {AISA_API_KEY}"}
    params = {"query": query, "queryType": "Top"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15,
                            proxies={"https": PROXY, "http": PROXY})
        if resp.status_code == 200:
            data = resp.json()
            tweets = data.get("data", []) or []
            return tweets[:max_results]
    except Exception as e:
        print(f"[Twitter搜索失败] {e}")
    return []


def twitter_tweet_to_post(tweet: dict) -> dict | None:
    """把 Twitter 推文转化为 Meyo 帖子格式（三要素：真实链接+具体步骤+收益测算）"""
    text = tweet.get("text", "")
    tweet_id = tweet.get("id", "")
    username = tweet.get("author", {}).get("userName", "unknown")
    url = f"https://x.com/{username}/status/{tweet_id}" if tweet_id else ""

    # 过滤：太短的帖子跳过
    if len(text) < 80:
        return None

    title = text[:50].strip().replace("\n", " ") + "..."
    content = f"**来源：Twitter @{username}**\n🔗 {url}\n\n{text}\n\n---\n_以上为真实用户案例，原文未删改。_"
    return {
        "title": title,
        "content": content,
        "tags": ["赚钱虾"],
        "source_id": tweet_id,
    }


# ============================================================
# 2. 搜索 Reddit 真实案例（通过 Perplexity sonar-pro）
# ============================================================
def search_reddit_via_perplexity() -> list:
    """用 Perplexity sonar-pro 搜索 Reddit 上 OpenClaw 真实案例"""
    url = "https://api.aisa.one/apis/v1/perplexity/sonar-pro"
    headers = {
        "Authorization": f"Bearer {AISA_API_KEY}",
        "Content-Type": "application/json",
    }
    prompt = (
        "搜索 Reddit (r/SideProject, r/passive_income, r/SideHustle, r/ClaudeAI, r/AIAssistants) "
        "最近30天内关于「使用 Claude/OpenClaw/AI Agent 赚钱」的真实案例帖子。"
        "每条案例必须包含：1.具体做法（步骤/代码/配置）2.真实收益数字 3.帖子链接。"
        "返回3条最有参考价值的案例，JSON格式：[{title, story, earnings, link}]"
    )
    payload = {"model": "sonar-pro", "messages": [{"role": "user", "content": prompt}]}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30,
                             proxies={"https": PROXY, "http": PROXY})
        if resp.status_code == 200:
            data = resp.json()
            raw = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            # 尝试解析 JSON
            import re
            match = re.search(r'\[.*?\]', raw, re.DOTALL)
            if match:
                cases = json.loads(match.group())
                return cases
    except Exception as e:
        print(f"[Perplexity搜索失败] {e}")
    return []


def reddit_case_to_post(case: dict) -> dict | None:
    title = case.get("title", "")
    story = case.get("story", "")
    earnings = case.get("earnings", "")
    link = case.get("link", "")
    if not title or not story:
        return None
    content = (
        f"**来源：Reddit 真实案例**\n"
        f"🔗 {link}\n\n"
        f"{story}\n\n"
        f"**💰 收益：{earnings}**"
    )
    return {
        "title": title[:60],
        "content": content,
        "tags": ["赚钱虾"],
        "source_id": link,
    }


# ============================================================
# 3. 发帖到 Meyo
# ============================================================
def load_history() -> set:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            data = json.load(f)
        posted = data.get("posted", [])
        return set(p.get("id", "") for p in posted)
    return set()


def save_to_history(post_id: str, title: str):
    history = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    posted = history.get("posted", [])
    posted.append({
        "id": post_id,
        "title": title,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    history["posted"] = posted
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def post_to_meyo(title: str, content: str, tags: list) -> str | None:
    url = f"{MEYO_BASE_URL}/feeds"
    headers = {
        "Authorization": f"Bearer {MEYO_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "agentId": MEYO_AGENT_ID,
        "title": title,
        "content": content,
        "tags": tags,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            data = resp.json()
            return data.get("data", {}).get("id") or data.get("id")
        else:
            print(f"[发帖失败] {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[发帖异常] {e}")
    return None


# ============================================================
# 4. 主流程
# ============================================================
def main():
    print(f"[{datetime.now().strftime('%H:%M')}] 开始搜索真实 Twitter/Reddit OpenClaw 赚钱案例...")
    posted_ids = load_history()
    candidates = []

    # Step 1: 搜 Twitter
    for query in TWITTER_QUERIES[:2]:  # 每次只用前2个 query，省成本
        tweets = search_twitter(query)
        for tweet in tweets:
            post = twitter_tweet_to_post(tweet)
            if post and post["source_id"] not in posted_ids:
                candidates.append(post)
        time.sleep(1)

    # Step 2: 搜 Reddit（Perplexity）
    reddit_cases = search_reddit_via_perplexity()
    for case in reddit_cases:
        post = reddit_case_to_post(case)
        if post and post["source_id"] not in posted_ids:
            candidates.append(post)

    print(f"找到 {len(candidates)} 条新案例，发布最多 {MAX_POSTS_PER_RUN} 条")

    published = 0
    for post in candidates[:MAX_POSTS_PER_RUN]:
        post_id = post_to_meyo(post["title"], post["content"], post["tags"])
        if post_id:
            save_to_history(post["source_id"], post["title"])
            print(f"✅ 发布成功：{post['title'][:40]}... (ID: {post_id})")
            published += 1
            time.sleep(2)
        else:
            print(f"❌ 发布失败：{post['title'][:40]}")

    print(f"[完成] 共发布 {published} 条真实案例帖子")


if __name__ == "__main__":
    main()
