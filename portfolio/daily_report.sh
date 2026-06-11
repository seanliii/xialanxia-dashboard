#!/bin/bash
# 每天 17:00（美股收盘后）运行，推送模拟盘日报
cd /root/.openclaw/workspace
python3 portfolio/simulate_pnl.py > /tmp/pnl_today.txt 2>&1
cat /tmp/pnl_today.txt
