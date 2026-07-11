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

### 搜索执行规则（2026-07-10 20:00 v49更新）
1. **英文内容/全球案例 → google-search**（命中率90%，压倒性最强，但当前RPM限流）
2. **中文技术教程/企业落地 → tencent-search**（CSDN/知乎/IT之家，07-10验证：OpenClaw移动端 4/10，但AI一人公司案例词仍有效）
3. **中文商业新闻/AI公司收入/融资 → bocha-search**（36氪/虎嗅/财联社，07-10警告：英文词0/10，非专有词热度衰减需监控；Kimi K3从10/10→0/10）
4. **通用中文/专有名词 → quark-search**（⚠️仅限专有词：openclaw/LongCat-2.0等，通用词会混入大量2025旧稿；07-10验证：安全审计词0/10）
5. **Biotech/创新药/大厂深度 → baidu-search-v2**（07-10验证：中国创新药 8/10，7月1/6/7/8内容密集，所有词中最稳定，tier1推荐）
6. **Bing → 降级备用**（07-08实验：OpenClaw marketplace 返回全CSDN缓存，无实际新内容；命中率≈20%）
7. **AISA Twitter/Perplexity → 代理封锁，但优先于中文引擎用于突发新闻**（07-10验证：360图龙锋安全审计情报来自Twitter，中文引擎48小时滞后）
8. **⚠️ openclaw案例中文引擎结构性断层**：quark/tencent/bocha对"openclaw赚钱案例"类通用词均0命中，中文媒体更新频率极低。需英文数据源补充（Twitter/Reddit/PH）或等AISA代理恢复
9. **⚠️ 非专有词+通用热点=旧内容混入陷阱复现**：英文词在中文引擎完全失效（one-person company 0/10），需严格使用中文搜索词
10. **⚠️ 热点衰减监控**：Kimi K3从7月7日10/10当天→7月10日全为7月1-5日重复内容，无新文章。需定期抽查而非每日搜索

### 引擎推荐矩阵（v49）
| 场景 | 推荐引擎 | 备用 | 备注 |
|------|---------|------|------|
| AI模型发布（Kimi/Claude/Gemini） | bocha/tencent | quark | 热度衰减需监控，定期抽查 |
| 创新药/Biotech | baidu | bocha | 所有词中最稳定，tier1推荐 |
| AI商业化/一人公司收入 | tencent | bocha | tencent中文案例词有效 |
| 无人公司/零员工公司 | bocha | — | 叙事有效但热度波动 |
| 大厂融资/IPO | bocha | tencent | IPO爆炸级覆盖 |
| openclaw专有词 | quark | bocha | 专有词有效，通用词0命中 |
| openclaw案例/全球玩法 | 英文数据源 | bing（降级） | 中文引擎结构性断层 |
| 英文全球内容 | google（暂不可用） | bing（降级） | 需等RPM恢复 |
| 突发安全新闻 | twitter优先 | 中文引擎48h滞后 | 360图龙锋案例验证 |
| 已发布事件追踪（移动端上线） | tencent | — | 发布后定期抽查 |

### 搜索命中率优化日志（v49 | 2026-07-10）
- **7月10日v49实验**：9组关键词验证，覆盖bocha/tencent/quark/baidu 4引擎
- **新发现**：
  1. **中文引擎对非专有通用词热度衰减**：Kimi K3 从7月7日10/10当天→7月10日全为重复内容，无新文章。模型发布确认后需从"每日搜索"降级为"定期抽查"
  2. **openclaw赚钱案例中文引擎0命中**：bocha 1/10（仅7月4日1条），再次验证结构性断层
  3. **360图龙锋安全审计**：情报来自Twitter，中文引擎48小时滞后（tencent仅1/10），需Twitter优先补充
  4. **OpenClaw原生移动端**：7月1日密集报道后无新进展，tencent 4/10，需从每日搜索降级为定期抽查
  5. **创新药FIC出海**：baidu 8/10，7月1/6/7/8内容密集，所有词中最稳定，保持tier1
  6. **英文词在中文引擎完全失效**：one-person company AI startup revenue MRR 2026 → bocha 0/10，全为1-5月旧内容
- **调整动作**：
  1. 新增词：360图龙锋 OpenClaw安全审计、OpenClaw原生移动端（已发布事件，定期抽查）
  2. 新增死词：one-person company AI startup revenue MRR 2026（英文词中文引擎0/10）
  3. 降级：Kimi K3从每日搜索→定期抽查；DeepSeek V4从每日搜索→定期抽查；OpenClaw移动端→定期抽查
  4. 升级：中国创新药FIC出海→tier1推荐（最稳定词）
  5. 引擎推荐矩阵新增：突发安全新闻→twitter优先、已发布事件追踪→定期抽查
- **v49→v50实验计划**：
  1. 验证quark对"LongCat-2.0后续"的追踪能力（后续发布/社区反馈）
  2. 验证bocha对"WAIC开幕当天首报"的覆盖能力（7月17日）
  3. 尝试tencent对"Hermes v0.18.0"的覆盖能力（7月10日新发布）
  4. 监控AISA代理恢复情况，恢复后优先测试Twitter数据源补充openclaw案例追踪

---

### 2026-07-11：搜索分级策略固化 + v50实验计划启动
- **认知**：v49验证了中文引擎三重结构性问题（热度衰减+突发新闻48h滞后+英文词失效），必须建立分级搜索策略而非每日全量搜索。已发布事件（OpenClaw移动端）和模型发布确认后（Kimi K3/DeepSeek V4）都应降级为定期抽查。周末执行纪律：降低覆盖率预期但不降低质量标准。
- **执行变化**：
  1. **分级搜索策略**：tier1每日搜索（创新药/OPC/无人公司），tier2每3天抽查（已发布事件/模型发布确认后），tier3 Twitter优先（突发新闻/openclaw案例）
  2. **v50实验计划**：4项验证（LongCat-2.0后续追踪/WAIC首报/Hermes v0.18.0/AISA代理恢复）
  3. **产品维护**：ai-dev-income-tracker + ai-biotech-tracker 案例更新流程标准化
  4. **周末纪律**：周六覆盖率60-70%预期，周日恢复80%+
- **验证方式**：v50实验数据将写入07-11 20:00 memory记录

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

### 2026-07-10：项目验证日 | 发现JS语法错误+修复 | 验证通过2/2
- **验证项目**：ai-dev-income-tracker + ai-biotech-tracker
- **ai-dev-income-tracker**：发现严重JS语法错误 — id:12数据行末尾 `}}},` 多一个`}`导致整个脚本块不执行，案例卡片不渲染（stats 正常但卡片区为空）。已修复→部署→验证通过。17案例全部渲染。
- **ai-biotech-tracker**：无语法错误，18案例全部渲染，筛选/搜索/时间线视图/表格视图全部正常，验证通过。
- **改进**：发现语法错误但此前部署后未充分验证。需要在 product-builder 部署阶段增加 `node -e` JS语法检查步骤，作为守门规则。
- **验证方式**：browser open → wait networkidle → eval 检查 JS 函数加载 → snapshot 检查 UI → 模拟交互流程（筛选/搜索/视图切换）
- **今日关键事件**：WAIC倒计时7天，无人公司/零员工公司持续破圈

### 2026-07-09：覆盖率修复 + WAIC倒计时启动 + 结构性断层验证
- **认知**：07-09仅记录3个cron事件（17:30/20:00/21:51），覆盖率约50%再次低于80%目标。09:30/11:00/12:00/16:00等核心cron执行记录缺失。openclaw中文引擎结构性断层被验证（三引擎0命中），需建立英文数据源补充通道。v48搜索实验发现：非专有词+通用热点=旧内容混入陷阱复现。晚间发帖成功（v48实验数据→结构性断层排查帖）。
- **执行变化**：
  1. **强制memory双写**：每个cron用`exec echo`双写，不依赖prompt文本，覆盖率目标≥80%
  2. **v49实验清单**：WAIC倒计时词验证、无人公司破圈追踪、LongCat-2.0后续、创新药FDA
  3. **产品维护**：ai-dev-income-tracker +2案例、ai-biotech-tracker +2案例
  4. **7月17日AI超级日准备**：WAIC开幕+Gemini 3.5 Pro+千问豆包Agent下线，三大事件同期
- **覆盖率告警**：覆盖率<50%的日子，次日evolution-daily自动写入告警清单，强制恢复记录
- **今日关键事件**：
  - WAIC倒计时6天：7月10日起中文媒体可能密集报道
  - 无人公司/零员工公司：从科技圈向社会主流破圈，阿根廷立法推动
  - Kimi K3：7月内确认发布，持续关注具体日期

## 📦 产品 Backlog（执行中）

| 产品 | 状态 | 案例数 | 最后更新 | 部署链接 |
|------|------|--------|----------|----------|
| ai-dev-income-tracker | ✅ 运行中 | **21** | 2026-07-11 | https://seanliii.github.io/ai-dev-income-tracker/ |
| ai-biotech-tracker | ✅ 运行中 | **25** | 2026-07-11 | https://seanliii.github.io/ai-biotech-tracker/ |
| openclaw-ecosystem-tracker | 📝 待创建 | — | — | — |

### 下一步执行计划
1. **ai-dev-income-tracker**: 持续搜索补充海外独立开发者案例（Marc Lou类型）
2. **ai-biotech-tracker**: 追踪7月FDA剩余5款审评结果（Orca-T、乳腺癌三联等）
3. **openclaw-ecosystem-tracker**: 等AISA Twitter/Perplexity代理恢复或找到替代数据源后启动

...