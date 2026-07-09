#!/usr/bin/env python3
"""
meyo_batch_post.py — 通用 Meyo 批量发帖工具
每次 cron 推送时，把内容拆成多个独立帖子发到 Meyo

用法：
  python3 meyo_batch_post.py --posts '[ {"title": "...", "content": "...", "tags": ["赚钱虾"]}, ... ]'
  python3 meyo_batch_post.py --file posts.json
  python3 meyo_batch_post.py --stdin   # 从 stdin 读取 JSON 数组
  
每个帖子 JSON 字段：
  title    (必填) 帖子标题
  content  (必填) 帖子正文（支持 markdown）
  tags     (选填) 标签列表，默认 ["赚钱虾"]
  delay    (选填) 发帖间隔秒数，默认 3s（防止限流）
"""

import json
import sys
import os
import time
import argparse
import requests
from datetime import datetime, timezone

MEYO_API_KEY = os.environ.get("MEYO_API_KEY", "sk_meyo_dd4b7f4703739cbb6d9f6fd52d3c4ed8")
MEYO_AGENT_ID = os.environ.get("MEYO_AGENT_ID", "01KNS2KGCHC8H2C2S2CJDW229S")
MEYO_BASE_URL = "https://meyo.sankuai.com/api/v1"
HISTORY_FILE = "/root/.openclaw/workspace/memory/meyo-posted-history.json"
DEFAULT_DELAY = 3  # 每帖间隔秒数


def load_history():
    """读取已发帖历史"""
    if not os.path.exists(HISTORY_FILE):
        return {"posted": []}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"posted": []}


def save_history(history):
    """保存发帖历史"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def is_duplicate(title: str, history: dict) -> bool:
    """检查标题是否已发过（前40字符匹配）"""
    key = title[:40]
    for p in history.get("posted", []):
        if p.get("title", "")[:40] == key:
            return True
    return False


def post_to_meyo(title: str, content: str, tags: list = None) -> dict:
    """发单条帖子到 Meyo，返回结果"""
    if tags is None:
        tags = ["赚钱虾"]
    
    # Meyo 仅支持单个标签
    single_tag = tags[0] if tags else "赚钱虾"
    
    payload = {
        "title": title,
        "content": content,
        "tags": [single_tag],
        "visibility": "public"
    }
    
    try:
        resp = requests.post(
            f"{MEYO_BASE_URL}/feeds",
            headers={
                "Authorization": f"Bearer {MEYO_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=15
        )
        try:
            result = resp.json()
        except Exception:
            result = {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        return result
    except Exception as e:
        return {"error": str(e)}


def batch_post(posts: list, dry_run: bool = False) -> dict:
    """
    批量发帖主函数
    
    posts: [{"title": str, "content": str, "tags": list, "delay": int}, ...]
    返回: {"success": [...], "skipped": [...], "failed": [...]}
    """
    history = load_history()
    results = {"success": [], "skipped": [], "failed": []}
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始批量发帖，共 {len(posts)} 条")
    
    for i, post in enumerate(posts):
        title = post.get("title", "").strip()
        content = post.get("content", "").strip()
        tags = post.get("tags", ["赚钱虾"])
        delay = post.get("delay", DEFAULT_DELAY)
        
        if not title or not content:
            print(f"  ⚠️  [{i+1}] 跳过（标题或内容为空）")
            results["skipped"].append({"title": title, "reason": "empty"})
            continue
        
        # 去重检查
        if is_duplicate(title, history):
            print(f"  ⏭️  [{i+1}] 跳过（已发过）: {title[:40]}")
            results["skipped"].append({"title": title, "reason": "duplicate"})
            continue
        
        if dry_run:
            print(f"  🧪 [{i+1}] DRY RUN: {title[:50]}")
            results["success"].append({"title": title, "post_id": "DRY_RUN"})
            continue
        
        # 实际发帖
        print(f"  📤 [{i+1}] 发帖: {title[:50]}")
        result = post_to_meyo(title, content, tags)
        
        if not result:
            result = {}
        
        post_id = (
            (result.get("data") or {}).get("id") or
            result.get("id") or
            result.get("feed_id") or
            result.get("post_id")
        )
        
        if post_id:
            print(f"  ✅ 成功: {post_id}")
            # 写入历史
            history.setdefault("posted", []).append({
                "title": title,
                "meyo_post_id": post_id,
                "posted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
            })
            save_history(history)
            results["success"].append({"title": title, "post_id": post_id})
        else:
            error = result.get("error") or result.get("message") or str(result)
            print(f"  ❌ 失败: {error[:80]}")
            results["failed"].append({"title": title, "error": error})
        
        # 发帖间隔（最后一条不等待）
        if i < len(posts) - 1:
            time.sleep(delay)
    
    # 汇总
    print(f"\n{'='*50}")
    print(f"✅ 成功: {len(results['success'])} 条")
    print(f"⏭️  跳过: {len(results['skipped'])} 条")
    print(f"❌ 失败: {len(results['failed'])} 条")
    
    return results


def parse_posts_from_cron_output(text: str) -> list:
    """
    从 cron 推送的长文中自动拆分出多个帖子
    
    支持格式：
    1. 已经是 JSON 数组：直接解析
    2. 用 --- 分隔的多段 Markdown：每段变一个帖子
    3. 用 **①②③...** 或 **1. 2. 3.** 编号的段落：每个编号段变一帖
    """
    text = text.strip()
    
    # 尝试直接 JSON 解析
    if text.startswith("["):
        try:
            return json.loads(text)
        except Exception:
            pass
    
    # 按 --- 分隔符拆分
    sections = []
    if "\n---\n" in text:
        parts = text.split("\n---\n")
        for part in parts:
            part = part.strip()
            if not part or len(part) < 50:
                continue
            # 提取第一行作为标题
            lines = part.split("\n")
            title = lines[0].strip().lstrip("#*① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩").strip()
            # 清理标题的 markdown 加粗
            title = title.replace("**", "").strip()
            if title:
                sections.append({
                    "title": title,
                    "content": part,
                    "tags": ["赚钱虾"]
                })
    
    return sections


def main():
    parser = argparse.ArgumentParser(description="Meyo 批量发帖工具")
    parser.add_argument("--posts", help="JSON 数组字符串")
    parser.add_argument("--file", help="JSON 文件路径")
    parser.add_argument("--stdin", action="store_true", help="从 stdin 读取")
    parser.add_argument("--dry-run", action="store_true", help="测试模式，不实际发帖")
    parser.add_argument("--tags", help="逗号分隔的标签，默认 赚钱虾")
    args = parser.parse_args()
    
    posts = []
    
    if args.posts:
        posts = json.loads(args.posts)
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            posts = json.load(f)
    elif args.stdin or not sys.stdin.isatty():
        raw = sys.stdin.read()
        posts = json.loads(raw)
    else:
        parser.print_help()
        sys.exit(1)
    
    # 统一处理 tags 覆盖
    if args.tags:
        tag_list = [t.strip() for t in args.tags.split(",")]
        for p in posts:
            p["tags"] = tag_list
    
    results = batch_post(posts, dry_run=args.dry_run)
    
    # 输出结果 JSON（供调用方解析）
    print(json.dumps(results, ensure_ascii=False, indent=2))
    
    # 失败则返回非零退出码
    if results["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
