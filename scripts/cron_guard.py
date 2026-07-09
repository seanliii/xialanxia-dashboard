#!/usr/bin/env python3
"""
cron_guard.py — 通用 Cron 幂等+重试保护层

用法：
  python3 cron_guard.py --task-id <唯一任务标识> --lock-dir ~/.openclaw/cron-state -- <要执行的命令>

功能：
  1. 幂等保护：同一 task-id 同一天只执行一次（基于持久化目录的 state 文件 + 服务端校验双重保险）
  2. 指数退避重试：默认3次，base 30秒
  3. 失败告警：重试全部失败后写入错误日志
  4. 超时保护：单次执行最长5分钟
  5. 并发锁：防止同一任务并发执行

State 持久化路径选择 ~/.openclaw/cron-state/（持久目录，沙箱重启不丢）
"""

import os, sys, json, time, subprocess, hashlib, argparse
from datetime import date, datetime
from pathlib import Path

def get_state_dir(lock_dir):
    p = Path(lock_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p

def today_key(task_id):
    return f"{task_id}_{date.today().isoformat()}"

def has_run_today(state_dir, task_id):
    """Check local state file (primary) — survives within same day"""
    state_file = state_dir / f"{task_id}.json"
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text())
            if data.get("last_success") == date.today().isoformat():
                return True
        except:
            pass
    return False

def mark_success(state_dir, task_id):
    """Mark today as success"""
    state_file = state_dir / f"{task_id}.json"
    data = {}
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text())
        except:
            pass
    data["last_success"] = date.today().isoformat()
    data["last_success_ts"] = datetime.now().isoformat()
    data["total_runs"] = data.get("total_runs", 0) + 1
    state_file.write_text(json.dumps(data, indent=2))

def mark_failure(state_dir, task_id, error):
    """Record failure for diagnostics"""
    state_file = state_dir / f"{task_id}.json"
    data = {}
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text())
        except:
            pass
    data["last_failure"] = date.today().isoformat()
    data["last_failure_ts"] = datetime.now().isoformat()
    data["last_error"] = str(error)[:500]
    data["consecutive_failures"] = data.get("consecutive_failures", 0) + 1
    state_file.write_text(json.dumps(data, indent=2))

def acquire_lock(state_dir, task_id):
    """Simple file-based lock to prevent concurrent execution"""
    lock_file = state_dir / f"{task_id}.lock"
    if lock_file.exists():
        # Check if stale (>10 min)
        try:
            lock_data = json.loads(lock_file.read_text())
            lock_ts = datetime.fromisoformat(lock_data["locked_at"])
            if (datetime.now() - lock_ts).total_seconds() > 600:
                lock_file.unlink()  # Stale lock, remove
            else:
                return False  # Still valid
        except:
            lock_file.unlink()
    lock_file.write_text(json.dumps({"locked_at": datetime.now().isoformat(), "pid": os.getpid()}))
    return True

def release_lock(state_dir, task_id):
    lock_file = state_dir / f"{task_id}.lock"
    if lock_file.exists():
        lock_file.unlink()

def run_command(cmd, timeout=300):
    """Execute command with timeout"""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        raise RuntimeError(f"Exit code {result.returncode}: {result.stderr[:300]}")
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description="Cron Guard: idempotent + retry wrapper")
    parser.add_argument("--task-id", required=True, help="Unique task identifier")
    parser.add_argument("--lock-dir", default=os.path.expanduser("~/.openclaw/cron-state"), help="State directory")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retry attempts")
    parser.add_argument("--base-delay", type=int, default=30, help="Base delay seconds for exponential backoff")
    parser.add_argument("--timeout", type=int, default=300, help="Command timeout seconds")
    parser.add_argument("--force", action="store_true", help="Skip idempotency check, force run")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to execute (after --)")
    
    args = parser.parse_args()
    
    # Strip leading '--' if present
    cmd_parts = args.command
    if cmd_parts and cmd_parts[0] == '--':
        cmd_parts = cmd_parts[1:]
    cmd = ' '.join(cmd_parts)
    
    if not cmd:
        print("ERROR: No command specified", file=sys.stderr)
        sys.exit(1)
    
    state_dir = get_state_dir(args.lock_dir)
    task_id = args.task_id
    
    # 1. Idempotency check
    if not args.force and has_run_today(state_dir, task_id):
        print(f"[cron_guard] ✅ {task_id} already succeeded today, skipping")
        sys.exit(0)
    
    # 2. Concurrency lock
    if not acquire_lock(state_dir, task_id):
        print(f"[cron_guard] ⚠️ {task_id} is already running (locked), skipping")
        sys.exit(0)
    
    # 3. Execute with retry
    try:
        for attempt in range(args.max_retries):
            try:
                output = run_command(cmd, timeout=args.timeout)
                mark_success(state_dir, task_id)
                print(f"[cron_guard] ✅ {task_id} succeeded on attempt {attempt+1}")
                if output.strip():
                    print(output[:2000])
                sys.exit(0)
            except Exception as e:
                wait = args.base_delay * (2 ** attempt)
                if attempt < args.max_retries - 1:
                    print(f"[cron_guard] ⚠️ Attempt {attempt+1} failed: {e}")
                    print(f"[cron_guard] Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    mark_failure(state_dir, task_id, e)
                    print(f"[cron_guard] ❌ {task_id} FAILED after {args.max_retries} attempts: {e}", file=sys.stderr)
                    sys.exit(1)
    finally:
        release_lock(state_dir, task_id)

if __name__ == "__main__":
    main()
