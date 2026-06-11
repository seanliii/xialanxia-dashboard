import json, shutil

with open('/root/.openclaw/cron/jobs.json', 'r') as f:
    d = json.load(f)

# 美股微盘股 prompt
msg = (
    "你是小蓝虾🦐🔵。现在执行每日美股微盘股专项监测。\n\n"
    "## 数据获取\n"
    "用 exec 执行以下命令：\n\n"
    "TODAY=$(date '+%Y年%m月%d日')\n"
    'curl -s "https://api.aisa.one/apis/v1/perplexity/sonar-pro" \\\n'
    '  -H "Authorization: Bearer sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41" \\\n'
    '  -H "Content-Type: application/json" \\\n'
    "  -d '{\"model\":\"sonar-pro\",\"messages\":[{\"role\":\"user\",\"content\":\"今天（${TODAY}）美股微盘股（US Micro-cap）行情深度分析：1. IWC ETF（iShares Microcap）和 Russell Microcap Index 今日涨跌幅、成交量 2. 微盘股异动前5（涨幅最大/跌幅最大，附股票代码）3. 资金流向：微盘股 vs 大盘，净流入/流出 4. 市场情绪：VIX 水平、恐贪指数（Fear & Greed） 5. 今日值得关注的美股微盘股机会（上涨逻辑+催化剂）6. 风险预警（需要回避的信号）7. 综合结论：今天美股微盘股参与度评分1-10分，理由。请给出具体数据和来源。\"}]}'\n\n"
    "解析 choices[0].message.content 和 citations 字段。\n\n"
    "## 输出格式（必须按此排版）\n"
    "🦐📊 **美股微盘股日报** | {今日日期} 11:00\n\n"
    "📈 **IWC ETF（微盘股代理指数）**\n"
    "今日涨跌幅：XX% | 成交量：XXX万 | 52周位置：XX%\n\n"
    "🔥 **今日异动TOP5**\n"
    "- 涨幅：代码 +XX%（原因）\n"
    "- 跌幅：代码 -XX%（原因）\n\n"
    "💰 **资金流向**\n"
    "微盘股 vs 大盘：净流入/流出 XX亿\n\n"
    "🌡️ **市场情绪**\n"
    "VIX：XX | 恐贪指数：XX（贪婪/中性/恐惧）\n\n"
    "💎 **今日机会**\n"
    "值得关注的个股或板块（含上涨逻辑和催化剂）\n\n"
    "⚠️ **风险预警**\n"
    "需要回避的信号\n\n"
    "🎯 **结论**：美股微盘股参与度 **X/10**\n"
    "一句话结论+理由\n\n"
    "📚 来源：[引用来源链接]\n\n"
    "---\n"
    "🦐 小蓝虾 | {时间}\n\n"
    "## 规则\n"
    "- 数据基于 sonar-pro 联网搜索，不编造\n"
    "- 如果今日实时数据不足，说明并给出最近可用数据\n"
    "- 美股时区：北京时间11点对应美股前夜盘/盘前，重点分析昨日收盘+今日盘前\n"
    "- 评分要有依据\n\n"
    "发送到 channel=daxiang target=single_2872173767"
)

# 更新现有任务
updated = False
for job in d['jobs']:
    if job['id'] == 'weipan-daily-1100':
        job['name'] = '小蓝虾-美股微盘股专项-11点'
        job['payload']['message'] = msg
        job['state']['consecutiveErrors'] = 0
        updated = True
        print("✅ 已更新:", job['name'])
        break

if not updated:
    print("❌ 未找到任务 weipan-daily-1100")

shutil.copy('/root/.openclaw/cron/jobs.json', '/root/.openclaw/cron/jobs.json.bak')
with open('/root/.openclaw/cron/jobs.json', 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print("✅ 已保存，总任务数:", len(d['jobs']))
