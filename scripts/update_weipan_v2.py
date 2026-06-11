import json, shutil

with open('/root/.openclaw/cron/jobs.json', 'r') as f:
    d = json.load(f)

msg = (
    "你是小蓝虾🦐🔵。现在执行每日美股微盘股专项监测。\n\n"
    "## 执行步骤\n"
    "1. 运行监测脚本：\n"
    "   python3 /root/.openclaw/workspace/scripts/microcap_us_monitor.py\n\n"
    "2. 读取报告：\n"
    "   cat /root/.openclaw/workspace/memory/microcap-report-latest.txt\n\n"
    "3. 把报告原文发送到大象私聊\n\n"
    "## 规则\n"
    "- 直接发报告内容，不要加额外说明\n"
    "- 如果脚本报错，直接调 AISA sonar-pro 做即时分析然后发送\n\n"
    "发送到 channel=daxiang target=single_2872173767"
)

for job in d['jobs']:
    if job['id'] == 'weipan-daily-1100':
        job['name'] = '小蓝虾-美股微盘股专项-11点'
        job['payload']['message'] = msg
        job['state']['consecutiveErrors'] = 0
        print("✅ 已更新:", job['name'])
        break

shutil.copy('/root/.openclaw/cron/jobs.json', '/root/.openclaw/cron/jobs.json.bak')
with open('/root/.openclaw/cron/jobs.json', 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print("✅ 已保存")
