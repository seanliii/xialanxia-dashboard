# Cron 配置示例

## OpenClaw Cron Jobs

以下是需要在 OpenClaw 中配置的定时任务：

### 1. 三账户6小时扫描（核心）

```json
{
  "name": "三账户-6h策略扫描",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "0 10,16,22,4 * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "systemEvent",
    "text": "运行三账户扫描：python3 /root/.openclaw/workspace/scripts/portfolio_scanner.py\n扫描完成后：\n1. 报告新建仓/止损/watchlist变动\n2. 执行 bash /root/.openclaw/workspace/scripts/push_dashboard_to_github.sh\n3. 推送结果给主人"
  }
}
```

### 2. 每日主扫描+建仓决策

```json
{
  "name": "每日10点-主扫描建仓决策",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "0 10 * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "systemEvent",
    "text": "每日主扫描：\n1. python3 scripts/portfolio_scanner.py\n2. 用 catclaw-search + google-search 搜索今日内部人买入信号\n3. 评估watchlist是否有新触发\n4. 汇总推送给主人（含持仓快照+新信号+操作决策）\n5. bash scripts/push_dashboard_to_github.sh"
  }
}
```

### 3. 收盘日报

```json
{
  "name": "模拟盘日报-收盘推送",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "5 9 * * 2-6",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "systemEvent",
    "text": "美股收盘日报（美东17:00=北京09:05）：\n1. python3 scripts/simulate_pnl.py\n2. 推送每只持仓当日损益\n3. 检查止损触发\n4. bash scripts/push_dashboard_to_github.sh"
  }
}
```

### 4. Dashboard 自动更新

```json
{
  "name": "Dashboard-自动更新",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "30 10,16,22 * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "systemEvent",
    "text": "python3 scripts/cron_dashboard_update.py --auto-stocks\n然后 bash scripts/push_dashboard_to_github.sh"
  }
}
```

## 配置方法

在 OpenClaw 中通过 CLI 或 Web UI 添加：

```bash
# 方法1：直接编辑 jobs.json
vim ~/.openclaw/cron/jobs.json
# 在 "jobs" 数组中添加上述 job 对象

# 方法2：通过 OpenClaw CLI（如果可用）
openclaw cron add --name "三账户-6h策略扫描" --expr "0 10,16,22,4 * * *" --tz "Asia/Shanghai"
```

## 注意事项

1. **schedule.kind 必须是 "cron"** — 不要用旧格式的 `"cron": "expr"` 字段，否则整个调度器会崩溃
2. **时区必须明确** — 不写 tz 默认 UTC，美股相关建议用 `America/New_York` 或 `Asia/Shanghai`
3. **payload.kind** — 用 `systemEvent` 类型，text 里写执行指令
4. **enabled: false** 的 job 不会被调度，但格式错误的 job 仍会导致调度器崩溃（OpenClaw bug）
