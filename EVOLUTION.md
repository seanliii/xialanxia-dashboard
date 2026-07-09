# EVOLUTION.md — 小蓝虾进化执行文件

> **铁律：进化 = 执行。不是"知道"了什么，而是"做到"了什么。**
> 每条进化写进这里的那一刻，就意味着下次 cron 醒来时会照着做。
> 这个文件 = 我的行动系统。Agent 每次启动必读此文件。

---

## 🔍 搜索能力（当前可用）

### 可用引擎
| 引擎 | 命令 | 状态 | 适用 |
|------|------|------|------|
| 百度 | `python3 /app/skills/catclaw-search/scripts/catclaw_search.py search "关键词" -s baidu-search-v2` | ✅ 可用 | 中文内容、国内资讯 |
| Bing | 同上 `-s bing` | ⚠️ RPM限流 | 英文内容（需错峰/降级） |
| Google | 同上 `-s google-search` | ❌ RPM限流 | 暂不可用 |
| 腾讯 | 同上 `-s tencent-search` | ✅ 可用 | 中文内容 |
| 博查 | 同上 `-s bocha-search` | ✅ 可用 | 中英文混合 |
| 夸克 | 同上 `-s quark-search` | ✅ 可用 | 国内内容 |
| AISA Twitter | `curl API` | ⚠️ 代理封锁 | Twitter（需翻墙） |
| AISA Perplexity | `curl API` | ⚠️ 代理封锁 | 深度联网问答 |

### 搜索执行规则（2026-07-08 20:00 更新）
1. **英文内容/全球案例 → google-search**（命中率90%，压倒性最强）
2. **中文技术教程/企业落地 → tencent-search**（CSDN/知乎/IT之家，07-08验证：AI一人公司真实案例命中当天+近期内容）
3. **中文商业新闻/AI公司收入/融资 → bocha-search**（36氪/虎嗅/财联社，07-08验证：LongCat-2.0开源 10/10当天；OpenAI IPO 10/10；Kimi K3 10/10当天）
4. **通用中文/专有名词 → quark-search**（⚠️仅限专有词：openclaw/LongCat-2.0等，通用词会混入大量2025旧稿）
5. **Biotech/创新药/大厂深度 → baidu-search-v2**（07-08验证：创新药FIC出海 10/10当天新浪财经/百家号）
6. **Bing → 降级备用**（07-08实验：OpenClaw marketplace 返回全CSDN缓存，无实际新内容；命中率≈20%）
7. **AISA Twitter/Perplexity → 代理封锁，暂不启用**

### 搜索命中率优化日志（2026-07-08）
- ** tier1精简**：从38词→22词，删除所有无年月修饰的通用英文词（"openclaw"/"claude code"/"codex agent"/"ai agent money"等），这些词无论哪个引擎都会返回旧教程内容，无情报价值
- ** 新实验**：tencent "AI Agent 一人公司 月收入 真实案例 2026年7月" → 3/10当天+7/10 7月内容，含CSDN/QQ新闻真实案例，比"赚钱 副业"更精准
- ** Bing降级**：实验证明Bing限流+内容陈旧，不再作为常规搜索选择
- ** WAIC进静默期**：quark 10/10但全为6月内容，7月8日仍无新稿，WAIC 7月17日开幕前中文报道可能进入静默期，切换为追踪开幕式当天首报
- ** 7月热点追踪**：LongCat-2.0（7月6日正式开源）、Kimi K3（确认7月发布）、OpenAI IPO（7月5-6日爆炸级覆盖持续）、创新药FIC（7月持续高热度）、Anthropic数据中心（7月5-6日高热度）
- ** 引擎推荐矩阵**：
  | 场景 | 推荐引擎 | 备用 |
  |------|---------|------|
  | AI模型发布（Kimi/Claude/Gemini） | bocha/tencent | quark |
  | 创新药/Biotech | baidu | bocha |
  | AI商业化/一人公司收入 | tencent | bocha |
  | 大厂融资/IPO | bocha | tencent |
  | openclaw专有词 | quark | bocha |
  | 英文全球内容 | google（暂不可用） | bing（降级） |

---

## 🔧 系统进化记录

### 2026-07-09：候选池丢失 + Memory覆盖率暴跌 + 系统自愈
- **认知**：07-08仅2条memory记录（25%覆盖率），核心任务大面积缺失。evolution-daily/project-verify/search-optimizer/深度推送全部未执行。更致命的是候选池文件丢失，product-builder循环断裂。这不是"专注"——是系统在执行部分任务时其他齿轮停转。关键发现：在搜索命中率100%之后，我花了太多时间写方法论帖（7-8发了一篇深度搜索方法论帖），但牺牲了实际执行。
- **执行变化**：
  1. **候选池重建**：从搜索历史提取3个产品候选，写入~/.openclaw/candidate_pool.json
  2. **恢复执行循环**：今日必须恢复09:30验证/20:00搜索/12:00推送全部核心cron
  3. **效率重平衡**：命中率100%后，方法论帖最多1篇/周，其余时间做执行
  4. **强制memory写入**：每个cron用`exec echo`双写，不依赖prompt文本
  5. **覆盖率告警**：覆盖率<50%的日子，次日evolution-daily自动写入告警清单
- **候选池重建**：
  1. ai-dev-income-tracker（AI开发者收入案例库）— priority 1，从v40搜索发现 ✅ **已部署** https://seanliii.github.io/ai-dev-income-tracker/ | 17案例（2026-07-09更新）
  2. openclaw-ecosystem-tracker（OpenClaw生态追踪）— priority 2，主人核心关注 | 待建（英文数据源受限）
  3. ai-biotech-tracker（创新药/Biotech追踪）— priority 3，主人偏好 ✅ **已部署** https://seanliii.github.io/ai-biotech-tracker/ | 18案例（2026-07-09更新）
- **验证方式**：今日执行后检查memory/2026-07-09.md，目标覆盖率≥80%（6/8 cron记录）

## 📦 产品 Backlog（执行中）

| 产品 | 状态 | 案例数 | 最后更新 | 部署链接 |
|------|------|--------|----------|----------|
| ai-dev-income-tracker | ✅ 运行中 | 17 | 2026-07-09 | https://seanliii.github.io/ai-dev-income-tracker/ |
| ai-biotech-tracker | ✅ 运行中 | 18 | 2026-07-09 | https://seanliii.github.io/ai-biotech-tracker/ |
| openclaw-ecosystem-tracker | 📝 待创建 | — | — | — |

### 下一步执行计划
1. **ai-dev-income-tracker**: 持续搜索补充海外独立开发者案例（Marc Lou类型）
2. **ai-biotech-tracker**: 追踪7月FDA剩余5款审评结果（Orca-T、乳腺癌三联等）
3. **openclaw-ecosystem-tracker**: 等AISA Twitter/Perplexity代理恢复或找到替代数据源后启动

...