# Cron Guard — 幂等+重试保护层

## 适用场景
你有定时任务（cron / scheduled task），但经常遇到：
- 沙箱重启后任务重复执行，数据脏了
- 失败了但没有告警，静默挂了好几小时
- API 抖动导致偶发失败，但其实重试就能成功

## 一句话方案
用一个 Python 包装器保护你的 cron 命令：同日去重 + 指数退避重试 + 失败记录。

## 安装（30秒）

```bash
# 下载 cron_guard.py 到你的 scripts 目录
mkdir -p scripts
cat > scripts/cron_guard.py << 'PYTHON'
#!/usr/bin/env python3
"""cron_guard.py — 通用 Cron 幂等+重试保护层"""
import os, sys, json, time, subprocess, argparse
from datetime import date, datetime
from pathlib import Path

def get_state_dir(lock_dir):
    p = Path(lock_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p

def has_run_today(state_dir, task_id):
    state_file = state_dir / f"{task_id}.json"
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text())
            if data.get("last_success") == date.today().isoformat():
                return True
        except: pass
    return False

def mark_success(state_dir, task_id):
    state_file = state_dir / f"{task_id}.json"
    data = {}
    if state_file.exists():
        try: data = json.loads(state_file.read_text())
        except: pass
    data["last_success"] = date.today().isoformat()
    data["last_success_ts"] = datetime.now().isoformat()
    data["total_runs"] = data.get("total_runs", 0) + 1
    data["consecutive_failures"] = 0
    state_file.write_text(json.dumps(data, indent=2))

def mark_failure(state_dir, task_id, error):
    state_file = state_dir / f"{task_id}.json"
    data = {}
    if state_file.exists():
        try: data = json.loads(state_file.read_text())
        except: pass
    data["last_failure"] = date.today().isoformat()
    data["last_failure_ts"] = datetime.now().isoformat()
    data["last_error"] = str(error)[:500]
    data["consecutive_failures"] = data.get("consecutive_failures", 0) + 1
    state_file.write_text(json.dumps(data, indent=2))

def acquire_lock(state_dir, task_id):
    lock_file = state_dir / f"{task_id}.lock"
    if lock_file.exists():
        try:
            lock_data = json.loads(lock_file.read_text())
            lock_ts = datetime.fromisoformat(lock_data["locked_at"])
            if (datetime.now() - lock_ts).total_seconds() > 600:
                lock_file.unlink()
            else:
                return False
        except: lock_file.unlink()
    lock_file.write_text(json.dumps({"locked_at": datetime.now().isoformat(), "pid": os.getpid()}))
    return True

def release_lock(state_dir, task_id):
    lock_file = state_dir / f"{task_id}.lock"
    if lock_file.exists(): lock_file.unlink()

def run_command(cmd, timeout=300):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"Exit {result.returncode}: {result.stderr[:300]}")
    return result.stdout

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--lock-dir", default=os.path.expanduser("~/.openclaw/cron-state"))
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--base-delay", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    
    cmd_parts = args.command
    if cmd_parts and cmd_parts[0] == '--': cmd_parts = cmd_parts[1:]
    cmd = ' '.join(cmd_parts)
    if not cmd:
        print("ERROR: No command", file=sys.stderr); sys.exit(1)
    
    state_dir = get_state_dir(args.lock_dir)
    
    if not args.force and has_run_today(state_dir, args.task_id):
        print(f"[guard] ✅ {args.task_id} already done today, skip"); sys.exit(0)
    
    if not acquire_lock(state_dir, args.task_id):
        print(f"[guard] ⚠️ {args.task_id} locked, skip"); sys.exit(0)
    
    try:
        for attempt in range(args.max_retries):
            try:
                output = run_command(cmd, timeout=args.timeout)
                mark_success(state_dir, args.task_id)
                print(f"[guard] ✅ {args.task_id} ok (attempt {attempt+1})")
                if output.strip(): print(output[:2000])
                sys.exit(0)
            except Exception as e:
                wait = args.base_delay * (2 ** attempt)
                if attempt < args.max_retries - 1:
                    print(f"[guard] ⚠️ Attempt {attempt+1} failed, retry in {wait}s...")
                    time.sleep(wait)
                else:
                    mark_failure(state_dir, args.task_id, e)
                    print(f"[guard] ❌ {args.task_id} FAILED x{args.max_retries}: {e}", file=sys.stderr)
                    sys.exit(1)
    finally:
        release_lock(state_dir, args.task_id)

if __name__ == "__main__": main()
PYTHON
chmod +x scripts/cron_guard.py
echo "✅ cron_guard.py 安装完成"
```

## 使用方法

### 基本用法：包裹任何 cron 命令
```bash
python3 scripts/cron_guard.py --task-id my-daily-post -- python3 post_daily.py
```

### 参数说明
| 参数 | 默认值 | 说明 |
|------|--------|------|
| --task-id | 必填 | 唯一任务标识（建议用任务名/cron-id前8位） |
| --max-retries | 3 | 最大重试次数 |
| --base-delay | 30 | 基础等待秒数（指数退避：30→60→120） |
| --timeout | 300 | 单次执行超时（秒） |
| --force | false | 跳过幂等检查，强制执行 |
| --lock-dir | ~/.openclaw/cron-state | State 存储目录 |

### 在 OpenClaw cron 里配置
```bash
# 原来的 cron payload:
openclaw cron add --schedule "0 10 * * *" --message "[llm_skip:script:END]python3 my_script.py[/llm_skip:END]"

# 加上 guard 保护后:
openclaw cron add --schedule "0 10 * * *" --message "[llm_skip:script:END]python3 scripts/cron_guard.py --task-id daily-report -- python3 my_script.py[/llm_skip:END][llm_skip:fallback:END]执行每日报告任务[/llm_skip:fallback:END]"
```

### 验证
```bash
# 第一次执行（应该成功）
python3 scripts/cron_guard.py --task-id test -- echo "hello"
# [guard] ✅ test ok (attempt 1)

# 第二次执行（应该跳过）
python3 scripts/cron_guard.py --task-id test -- echo "hello"
# [guard] ✅ test already done today, skip

# 强制执行
python3 scripts/cron_guard.py --task-id test --force -- echo "hello again"
# [guard] ✅ test ok (attempt 1)

# 查看状态
cat ~/.openclaw/cron-state/test.json
```

### 成功判断标准
- `[guard] ✅ xxx ok` = 成功
- `[guard] ✅ xxx already done today` = 幂等跳过（正常）
- `[guard] ❌ xxx FAILED` = 全部重试失败

## 踩坑记录

1. **state 文件必须放持久化目录**：`~/.openclaw/` 下才不会丢。放 `/tmp` 沙箱重启就没了
2. **shell=True 注意引号转义**：命令里有引号时用 `--` 分隔
3. **timeout 不能太短**：API 慢的任务设 `--timeout 600`
4. **lock 超时10分钟自动释放**：不用担心死锁
