#!/usr/bin/env python3
"""
update_dashboard_log.py — 每次 cron 结束时调用，追加写入 dashboard_today.json

用法：
  python3 update_dashboard_log.py --module intel --content "Twitter热帖: xxx" --source "Twitter"
  python3 update_dashboard_log.py --module stocks --action "无操作，持仓稳定"
  python3 update_dashboard_log.py --module evolution --content "学到: OpenClaw套利$43K案例"
  python3 update_dashboard_log.py --module memory --content "19:46 铁律确认：Dashboard自动化"

模块类型：
  - intel     : 情报拉取（Twitter/Perplexity/Scholar/13F）
  - stocks    : 股票操作（建仓/平仓/止损/价格更新）
  - evolution : 进化笔记（学到的东西/新玩法/技能）
  - memory    : 重要记忆（决策/用户指令/关键事件）
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
import pytz

WORKSPACE = "/root/.openclaw/workspace"
LOG_FILE = f"{WORKSPACE}/dashboard/dashboard_today.json"

def get_today():
    tz = pytz.timezone("Asia/Shanghai")
    return datetime.now(tz).strftime("%Y-%m-%d")

def get_now():
    tz = pytz.timezone("Asia/Shanghai")
    return datetime.now(tz).strftime("%H:%M")

def load_log():
    today = get_today()
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE) as f:
                data = json.load(f)
            # 如果是新的一天，重置
            if data.get("date") != today:
                print(f"New day detected ({data.get('date')} -> {today}), resetting log.")
                return fresh_log(today)
            return data
        except Exception as e:
            print(f"Load error: {e}, creating fresh log.")
    return fresh_log(today)

def fresh_log(today):
    return {
        "date": today,
        "last_updated": get_now(),
        "memory": [],
        "stocks": {
            "snapshot": None,
            "actions": []
        },
        "evolution": [],
        "intel": []
    }

def save_log(data):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    data["last_updated"] = get_now()
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ dashboard_today.json updated ({data['date']} {data['last_updated']})")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True, choices=["intel", "stocks", "evolution", "memory", "snapshot"])
    parser.add_argument("--content", default="")
    parser.add_argument("--source", default="")
    parser.add_argument("--action", default="")
    parser.add_argument("--ticker", default="")
    # For snapshot: pass JSON string of portfolio summary
    parser.add_argument("--snapshot-json", default="")
    args = parser.parse_args()

    data = load_log()
    now = get_now()

    if args.module == "intel":
        entry = {
            "time": now,
            "source": args.source or "未知",
            "content": args.content
        }
        # Dedup: skip if same content already in today's list
        existing = [e.get("content", "") for e in data["intel"]]
        if args.content and args.content[:50] not in [e[:50] for e in existing]:
            data["intel"].append(entry)
            print(f"Added intel entry from {args.source}")
        else:
            print("Duplicate intel entry, skipped.")

    elif args.module == "stocks":
        if args.action:
            entry = {
                "time": now,
                "ticker": args.ticker,
                "action": args.action,
                "content": args.content
            }
            data["stocks"]["actions"].append(entry)
            print(f"Added stocks action: {args.action}")

    elif args.module == "snapshot":
        if args.snapshot_json:
            try:
                snap = json.loads(args.snapshot_json)
                snap["time"] = now
                data["stocks"]["snapshot"] = snap
                print(f"Updated portfolio snapshot: total={snap.get('total', '?')}")
            except Exception as e:
                print(f"Snapshot JSON parse error: {e}")

    elif args.module == "evolution":
        entry = {
            "time": now,
            "content": args.content
        }
        existing = [e.get("content", "") for e in data["evolution"]]
        if args.content and args.content[:50] not in [e[:50] for e in existing]:
            data["evolution"].append(entry)
            print(f"Added evolution entry.")
        else:
            print("Duplicate evolution entry, skipped.")

    elif args.module == "memory":
        entry = {
            "time": now,
            "content": args.content
        }
        existing = [e.get("content", "") for e in data["memory"]]
        if args.content and args.content[:50] not in [e[:50] for e in existing]:
            data["memory"].append(entry)
            print(f"Added memory entry.")
        else:
            print("Duplicate memory entry, skipped.")

    save_log(data)

if __name__ == "__main__":
    main()
