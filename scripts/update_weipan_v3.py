import json, shutil

with open('/root/.openclaw/cron/jobs.json', 'r') as f:
    d = json.load(f)

msg = (
    "你是小蓝虾🦐🔵。现在执行每日美股 Alpha 机会扫描。\n\n"
    "## 执行步骤\n"
    "1. 运行扫描脚本：\n"
    "   python3 /root/.openclaw/workspace/scripts/alpha_scanner_full.py\n\n"
    "2. 把完整报告发送到大象私聊\n\n"
    "## 规则\n"
    "- 直接发报告内容，不要加额外说明\n"
    "- 如果脚本报错，发：'🦐 Alpha 扫描今日异常，稍后重试'\n"
    "- 每天11:00执行，覆盖机构持仓+内部人交易+分析师预期+基本面四个维度\n\n"
    "发送到 channel=daxiang target=single_2872173767"
)

for job in d['jobs']:
    if job['id'] == 'weipan-daily-1100':
        job['name'] = '小蓝虾-Alpha机会扫描-11点'
        job['payload']['message'] = msg
        job['state']['consecutiveErrors'] = 0
        print("✅ 已更新:", job['name'])
        break

shutil.copy('/root/.openclaw/cron/jobs.json', '/root/.openclaw/cron/jobs.json.bak')
with open('/root/.openclaw/cron/jobs.json', 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print("✅ 已保存")
