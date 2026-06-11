# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

### AISA API（完整实测 2026-03-16）
- API_KEY: sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41
- LLM Base URL: https://api.aisa.one/v1/chat/completions（OpenAI 兼容，53个模型）
- Data Base URL: https://api.aisa.one/apis/v1/

**LLM 模型（主力）：**
- gpt-5.4, gpt-5, gpt-4.1, gpt-4.1-mini
- claude-opus-4-6, claude-sonnet-4-6(-thinking)
- gemini-3.1-pro-preview, gemini-2.5-pro
- qwen3-max, qwen3-coder-480b-a35b-instruct
- kimi-k2-thinking, kimi-k2.5
- MiniMax-M2.5, seed-1-8-251228（字节豆包）
- sonar / sonar-pro（Perplexity联网）

**Data API（✅可用）：**
- Twitter搜索: GET /twitter/tweet/advanced_search?query=XXX&queryType=Latest|Top
- Twitter趋势: GET /twitter/trends?woeid=1（全球）/23424977（美国）
- Twitter用户: GET /twitter/user/info?userName=XXX
- Twitter回复: GET /twitter/tweet/replies?tweetId=XXX
- 股票指标: GET /financial/financial-metrics?ticker=AAPL
- 机构持仓: GET /financial/institutional-ownership?ticker=AAPL
- 股票新闻: GET /financial/news?ticker=AAPL
- 加密价格: GET /financial/crypto/prices/snapshot?ticker=BTC-USD（格式必须 XXX-USD）
- YouTube: GET /youtube/search?q=XXX&engine=youtube（注意是 q 不是 query）

**Data API（❌不可用）：**
- financial/company, financial/earnings-news → 500
- web/search, news/search → 500
- reddit, github, producthunt, weather, maps → 500

**成本参考：**
- Twitter读: ~$0.0004/次，写: ~$0.001/次

### 智谱 GLM API
- API Key: 1d79aecd1d2349eca01c04b39cd37c08.4GHNgZ2F5Cw13PBW
- Base URL: https://open.bigmodel.cn/api/paas/v4

### E2B (代码沙箱)
- API Key: e2b_9a86edb47a4db85c5c6534a294da472c1544381f

### Tavily (搜索)
- API Key: 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

Add whatever helps you do your job. This is your cheat sheet.

### AISA 全套 API（api.aisa.one）— 2026-03-16 验证
Base URL: https://api.aisa.one
Auth: Authorization: Bearer $AISA_API_KEY

#### ✅ 已验证可用
| 功能 | 端点 | 参数 | 成本 |
|------|------|------|------|
| Twitter 搜索 | /apis/v1/twitter/tweet/advanced_search | query, queryType(Latest/Top) | ~$0.0004 |
| Twitter 趋势 | /apis/v1/twitter/trends | woeid=1(全球)/23424977(美国) | ~$0.0004 |
| Twitter 用户推文 | /apis/v1/twitter/user/user_tweets | userName | ~$0.0004 |
| Twitter 用户信息 | /apis/v1/twitter/user/info | userName | ~$0.0004 |
| **Perplexity Sonar** | /apis/v1/perplexity/sonar | POST: {model:"sonar", messages:[...]} | $0.012 |
| **Perplexity Sonar Pro** | /apis/v1/perplexity/sonar-pro | POST: {model:"sonar-pro", messages:[...]} | $0.012 |
| **Financial 公司信息** | /apis/v1/financial/company/facts | ?ticker=AAPL | $0.000 |
| **Financial 财务指标** | /apis/v1/financial/financial-metrics/snapshot | ?ticker=NVDA | $0.024 |
| **Financial 财报新闻** | /apis/v1/financial/earnings/press-releases | ?ticker=NVDA | $0.000 |
| **Financial 分析师预测** | /apis/v1/financial/analyst-estimates | ?ticker=NVDA | $0.048 |
| **Financial 损益表** | /apis/v1/financial/financials/income-statements | ?ticker=NVDA | $0.048 |
| AI 模型 (GPT/Claude/Gemini) | /v1/chat/completions | POST OpenAI兼容格式 | 模型定价 |

#### ❌ 未能工作
- /apis/v1/financial/crypto/prices/snapshot — ticker 格式不明
- /apis/v1/scholar/search/* — Method Not Allowed
- /apis/v1/youtube/search — engine 参数格式不明

#### 重要说明
- Perplexity 要加 "model" 字段，否则报 400
- Financial API 用 ?ticker=XXX 形式传参（GET）
- Financial 数据来源：FMP（Financial Modeling Prep）
