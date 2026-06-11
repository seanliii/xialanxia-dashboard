#!/bin/bash
# 小蓝虾每日任务 - 22:00 执行

cd /root/.openclaw/workspace

# 1. 压缩今日记忆
echo "🧠 执行记忆压缩..."
python3 scripts/memory_compressor.py

# 2. 提取当天推送（需要等其他脚本完成，这里只记录待办）
echo "📝 学城日报待同步..."

# 记录执行日志
echo "$(date '+%Y-%m-%d %H:%M:%S') - daily cron completed" >> cron/cron.log
