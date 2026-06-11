#!/usr/bin/env python3
"""
cron_dashboard_update.py — cron 结束时统一调用的 Dashboard 更新入口

每次 cron 完成时，在 prompt 末尾加一句：
  python3 /root/.openclaw/workspace/scripts/cron_dashboard_update.py \
    --cron-name "小蓝虾10点-深度推送" \
    --module intel \
    --summary "今日OpenClaw热帖Top5: xxx / Perplexity深度分析: xxx"

也可以直接用 --auto 模式：自动从 positions.json 读取持仓快照，更新 stocks 模块
  python3 cron_dashboard_update.py --auto-stocks

使用方式：
  1. 情报 cron 结束时：--module intel --summary "..." --source "Twitter/Perplexity/etc"
  2. 股票扫描 cron 结束时：--auto-stocks （自动读 positions.json）
  3. 进化/记忆事件：--module evolution/memory --summary "..."
  4. 任意 cron 结束后追加日志 + 推送：--render-only

代理设置（适配沙盒环境）：
  HTTPS_PROXY=http://10.59.78.158:3128
"""

import json
import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import pytz

# 强制使用上游代理（跳过 Privoxy）
os.environ.setdefault("HTTPS_PROXY", "http://10.59.78.158:3128")
os.environ.setdefault("HTTP_PROXY", "http://10.59.78.158:3128")

WORKSPACE = "/root/.openclaw/workspace"
LOG_FILE = f"{WORKSPACE}/dashboard/dashboard_today.json"
POSITIONS_FILE = f"{WORKSPACE}/portfolio/positions.json"
SCRIPT_DIR = f"{WORKSPACE}/scripts"

def get_today():
    tz = pytz.timezone("Asia/Shanghai")
    return datetime.now(tz).strftime("%Y-%m-%d")

def get_now():
    tz = pytz.timezone("Asia/Shanghai")
    return datetime.now(tz).strftime("%H:%M")

def run_script(script, *args):
    cmd = [sys.executable, script] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"STDERR: {result.stderr[:300]}")
    return result.returncode == 0

def get_portfolio_snapshot():
    """从 positions.json 读取持仓快照"""
    try:
        with open(POSITIONS_FILE) as f:
            data = json.load(f)
        meta = data.get("meta", {})
        return {
            "total": meta.get("portfolio_value", 0),
            "pnl_pct": meta.get("total_return_pct", 0),
            "cash": meta.get("current_cash", 0),
            "positions": len(data.get("positions", [])),
            "price_time": meta.get("price_check_time", "unknown"),
            "time": get_now()
        }
    except Exception as e:
        print(f"⚠️  Could not read positions.json: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Dashboard cron update helper")
    parser.add_argument("--cron-name", default="", help="Cron job name for logging")
    parser.add_argument("--module", choices=["intel", "stocks", "evolution", "memory"], default="intel")
    parser.add_argument("--summary", default="", help="Summary content to log")
    parser.add_argument("--source", default="", help="Source (Twitter/Perplexity/Scholar/13F/AISA)")
    parser.add_argument("--ticker", default="", help="Ticker for stocks module")
    parser.add_argument("--action", default="", help="Action description for stocks module")
    parser.add_argument("--auto-stocks", action="store_true", help="Auto-read positions.json for stocks snapshot")
    parser.add_argument("--render-only", action="store_true", help="Skip log update, just render + push")
    args = parser.parse_args()

    print(f"\n🦐 Dashboard Update — {get_now()} | {args.cron_name or args.module}")
    print("─" * 50)

    if not args.render_only:
        if args.auto_stocks:
            # 自动读 positions.json
            snap = get_portfolio_snapshot()
            if snap:
                run_script(
                    f"{SCRIPT_DIR}/update_dashboard_log.py",
                    "--module", "snapshot",
                    "--snapshot-json", json.dumps(snap)
                )
        elif args.summary:
            run_script(
                f"{SCRIPT_DIR}/update_dashboard_log.py",
                "--module", args.module,
                "--content", args.summary,
                "--source", args.source,
                "--ticker", args.ticker,
                "--action", args.action
            )

    # 渲染 + 推送
    run_script(f"{SCRIPT_DIR}/render_daily_dashboard.py")

if __name__ == "__main__":
    main()
