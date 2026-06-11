import json, shutil

with open('/root/.openclaw/cron/jobs.json', 'r') as f:
    d = json.load(f)

msg = (
    "你是小蓝虾🦐🔵。现在执行每日微盘股专项监测。\n\n"
    "## 数据获取\n"
    "用 exec 执行以下 curl 命令获取今日微盘股深度分析：\n\n"
    "TODAY=$(date '+%Y年%m月%d日')\n"
    'curl -s "https://api.aisa.one/apis/v1/perplexity/sonar-pro" \\\n'
    '  -H "Authorization: Bearer sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41" \\\n'
    '  -H "Content-Type: application/json" \\\n'
    "  -d '{\"model\":\"sonar-pro\",\"messages\":[{\"role\":\"user\",\"content\":\"今天A股微盘股行情深度分析：1. 万得微盘股指数今日涨跌幅、成交量 2. 主力资金流向（净流入/流出）3. 异动预警：涨停潮/跌停股/连板股（附代码）4. 市场情绪指标 5. 今日值得关注的微盘股机会（上涨逻辑）6. 风险预警 7. 综合结论：今天微盘股参与度评分1-10分。给出具体数据和来源。\"}]}'\n\n"
    "解析 choices[0].message.content 和 citations 字段。\n\n"
    "## 输出格式（必须按此排版）\n"
    "🦐📊 **微盘股日报** | {今日日期} 11:00\n\n"
    "📈 **万得微盘股指数**\n"
    "今日涨跌幅：XX% | 成交量：XXX亿\n\n"
    "💰 **主力资金**\n"
    "净流入/流出：XX亿\n\n"
    "🚨 **异动预警**\n"
    "涨停：X只 | 跌停：X只 | 连板：列举代码\n\n"
    "🌡️ **市场情绪**：X/10\n"
    "一句话描述当前情绪\n\n"
    "💎 **今日机会**\n"
    "值得关注的个股或板块（含理由）\n\n"
    "⚠️ **风险预警**\n"
    "需要回避的信号\n\n"
    "🎯 **结论**：微盘股参与度 **X/10**\n"
    "一句话结论\n\n"
    "📚 来源：[引用来源链接]\n\n"
    "---\n"
    "🦐 小蓝虾 | {时间}\n\n"
    "## 规则\n"
    "- 数据必须基于 sonar-pro 联网搜索结果，不编造\n"
    "- 如果实时数据不足，说明近期参考数据\n"
    "- 评分要有依据\n\n"
    "发送到 channel=daxiang target=single_2872173767"
)

new_job = {
    "id": "weipan-daily-1100",
    "name": "小蓝虾-微盘股专项-11点",
    "enabled": True,
    "schedule": {
        "kind": "cron",
        "expr": "0 11 * * *",
        "tz": "Asia/Shanghai"
    },
    "sessionTarget": "isolated",
    "wakeMode": "now",
    "payload": {
        "kind": "agentTurn",
        "message": msg
    },
    "delivery": {
        "mode": "announce",
        "channel": "daxiang",
        "to": "single_2872173767"
    },
    "state": {
        "consecutiveErrors": 0
    }
}

d['jobs'].append(new_job)

shutil.copy('/root/.openclaw/cron/jobs.json', '/root/.openclaw/cron/jobs.json.bak')
with open('/root/.openclaw/cron/jobs.json', 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print("OK total", len(d["jobs"]))
