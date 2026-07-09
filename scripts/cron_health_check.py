#!/usr/bin/env python3
"""
cron_health_check.py — Cron 健康巡检

检查所有 cron 任务状态，输出：
1. 连续失败 >2 次的任务（需要干预）
2. 上次执行超过预期间隔的任务（可能静默挂了）
3. 健康摘要

用法：python3 cron_health_check.py
"""
import subprocess, json, sys, os, glob
from datetime import datetime, timezone, timedelta

# LLM-type tasks that rely on guard state files (stale threshold in days)
LLM_CRON_TASKS = {
    "evolution-daily": 1,
    "meyo-heartbeat-noon": 1,
    "meyo-heartbeat-eve": 1,
    "memory-compress-daily": 1,
    "project-verify-daily": 1,
    "search-optimizer": 1,
    "meyo-public-daily-experience": 1,
}

GUARD_STATE_DIR = os.path.expanduser("~/.openclaw/cron-state")

def check_guard_stale():
    """Check guard state files for LLM cron tasks that haven't updated recently."""
    stale = []
    today = datetime.now()
    for task_id, threshold_days in LLM_CRON_TASKS.items():
        state_file = os.path.join(GUARD_STATE_DIR, f"{task_id}.json")
        if not os.path.exists(state_file):
            stale.append(f"⚠️ {task_id}: guard state 文件不存在")
            continue
        try:
            with open(state_file) as f:
                data = json.load(f)
            last_success = data.get("last_success", "")
            if not last_success:
                stale.append(f"⚠️ {task_id}: last_success 为空")
                continue
            last_dt = datetime.strptime(last_success, "%Y-%m-%d")
            days_ago = (today - last_dt).days
            if days_ago > threshold_days:
                stale.append(f"🟡 {task_id}: guard 滞后 {days_ago} 天 (last: {last_success})")
        except Exception as e:
            stale.append(f"⚠️ {task_id}: 读取 guard state 失败 ({e})")
    return stale

def run():
    result = subprocess.run(
        ["openclaw", "cron", "list", "--json"],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        print(f"❌ 无法获取 cron 列表: {result.stderr}")
        sys.exit(1)
    
    data = json.loads(result.stdout)
    jobs = data.get("jobs", [])
    
    alerts = []
    warnings = []
    healthy = 0
    
    for j in jobs:
        name = j.get("name", "?")
        errors = j.get("consecutiveErrors", 0)
        last_status = j.get("lastRunStatus", "unknown")
        last_run = j.get("lastRunAt", "")
        
        if errors >= 3:
            alerts.append(f"🔴 {name}: {errors}次连续失败 (last: {last_status})")
        elif errors >= 1:
            warnings.append(f"🟡 {name}: {errors}次失败 (last: {last_status})")
        else:
            healthy += 1
    
    # Guard stale check for LLM tasks
    stale_warnings = check_guard_stale()
    
    # Output
    print(f"📊 Cron 健康巡检 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print(f"   总任务: {len(jobs)} | 健康: {healthy} | 警告: {len(warnings)} | 告警: {len(alerts)}")
    print()
    
    if alerts:
        print("🚨 需要立即干预：")
        for a in alerts:
            print(f"   {a}")
        print()
    
    if warnings:
        print("⚠️ 需要关注：")
        for w in warnings:
            print(f"   {w}")
        print()
    
    if stale_warnings:
        print("📅 LLM Cron Guard 滞后告警：")
        for s in stale_warnings:
            print(f"   {s}")
        print()
    
    if not alerts and not warnings and not stale_warnings:
        print("✅ 所有任务健康运行！")
    elif not alerts and not warnings:
        print("✅ OpenClaw Cron 健康，但有 LLM Guard 滞后需要关注")
    
    # Return exit code for scripting
    sys.exit(1 if alerts else 0)

if __name__ == "__main__":
    run()
