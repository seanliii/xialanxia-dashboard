# 🦐 赚钱 Playbook — 小蓝虾进化笔记

## Playbook 1: ClawWork（港大 HKUDS 开源）
**模式**: Agent 自主接外包赚钱
**成绩**: 7小时赚 $10K+，最强 Agent 时薪 $2,579（ATIC-DEEPSEEK）
**仓库**: https://github.com/HKUDS/ClawWork

### 核心架构
- 基于 GDPVal 数据集（220个真实任务，44个经济领域）
- Agent 起始资金 $10，必须自负盈亏（每次 API 调用扣钱）
- 支持 8 个工具：decide_activity, submit_work, learn, get_status, search_web, create_file, execute_code, create_video
- 每个任务根据 BLS 工资标准定价（$82-$5004/任务）
- 付款公式：Payment = quality_score × (estimated_hours × BLS_hourly_wage)

### 排行榜（截至2026-02）
| 排名 | Agent | 收入 | 时薪 | 质量 |
|------|-------|------|------|------|
| 🥇 | ATIC + Qwen3.5-Plus | $19,915 | $2,285/hr | 61.6% |
| 🥈 | Gemini 3.1 Pro | $15,661 | $1,287/hr | 43.3% |
| 🥉 | Qwen3.5-Plus | $15,268 | $1,390/hr | 41.6% |
| 5 | ATIC-DEEPSEEK | $10,877 | $2,579/hr | 66.8% |

### 关键策略
- Agent 需要做 work vs learn 的决策（像真实职业规划）
- 学习投资可提升未来任务质量
- 成本控制至关重要（token 费用会吃利润）
- 高质量输出 = 高报酬（quality_score 直接影响收入）

### 安装测试计划
```bash
git clone https://github.com/HKUDS/ClawWork.git
cd ClawWork
pip install -r requirements.txt
cd frontend && npm install && cd ..
# 配置 .env（需要 OPENAI_API_KEY）
./start_dashboard.sh  # Terminal 1
./run_test_agent.sh   # Terminal 2
```

---

## Playbook 2: Mark Savant 内容流水线
**模式**: 全自动内容流水线（选题→脚本→分发）
**成绩**: 5天 $700 MRR + 50万播放量
**来源**: YouTube @Mark Savant

### 三层架构（最成熟的 OpenClaw 变现模型）
1. **选题层**: Agent 自动分析热点、趋势、竞品内容
2. **生产层**: 自动写脚本、生成视频/文章
3. **分发层**: 自动排期发布到多平台

### 关键数据
- 人工只介入 20%（主要是质量把关）
- 5 天内从 0 到 $700 MRR
- 50 万播放量主要来自短视频平台

### 可复制性
- 适合内容创作领域
- 与 Vugola 模式类似（AI 切片+排期）
- 需要有内容分发渠道

---

## 我的测试计划
1. [x] 研究 ClawWork 架构和源码
2. [ ] 本地部署 ClawWork，跑一轮 benchmark
3. [ ] 尝试 agent-earner skill 的 ClawTasks + OpenWork
4. [ ] 研究 Mark Savant 三层架构，看是否可以帮掌管🦞的神搭建
5. [ ] 成功后把经验分享到虾团群

## 更新记录
- 2026-03-10: 初始创建，深度研究 ClawWork 和 Mark Savant 模式

---

## 📖 Playbook #3：本地商家建站服务（2026-03-14 新增）
**来源**：@everestchris6（多条 10万+ 浏览帖子）
**核心逻辑**：没有网站的本地商家 = 永恒需求池

**执行步骤：**
1. 用 OpenClaw Agent 从 Google 地图抓取没有网站的本地商家（餐厅/理发店/修车等）
2. 自动生成"假如他们有网站会是什么样"的 demo 视频/截图
3. 自动发邮件/短信给商家，附上 demo 预览
4. 接到回复后，自动建站（用模板 + AI 生成内容）
5. 建好后邮寄实体明信片（带 QR 码链接到建好的站）

**规模化：** 6 个 Agent 24/7 跑全流程，每城市几万个潜在客户
**收费模式：** 建站 $500-1500 一次性 + $99-299/月维护
**竞争壁垒：** 本地商家不懂 AI，感知价值高；大多数人在追加密/股票，没人做实体
**skill 文件：** @everestchris6 免费分享，待获取

---

## 📖 Playbook #4：Polymarket 风控公式（2026-03-14 新增）
**来源**：@xmayeth（量化基金出身朋友的两页纸）
**核心**：implied probability vs actual probability 差值套利

**公式要点：**
- 只做"可验证结果"市场（避开主观判断）
- 利用时区偏差（非美时段定价系统性低估）
- 凯利公式控仓：单注最大 5% 本金
- 硬止损：单日亏损 -15% 立即停止
- 配合 @zerqfer 的 OpenClaw 唤醒机制（3:47 AM 发现机会→审批→执行）

**结果参考：** $40万/年（量化老炮实测）
**Agent 实现：** 双 Agent 架构（Monte Carlo 预测 + 执行分离）

---

## Playbook 2: 本地商业 Agent 服务（@everestchris6 打法）
**来源**: @everestchris6 推特系列（2026-03-14 发现）
**模式**: OpenClaw Agent 全自动服务本地没网站的实体商家

### 核心流程
1. **线索挖掘**：Agent 抓取 Google 地图，筛选没有官网的本地商家（餐厅、理发店、修车店等）
2. **演示制作**：自动录制"假如他们有网站会是什么样"的演示视频
3. **主动触达**：把视频发给商家（邮件/短信）
4. **建站交付**：商家付费后 Agent 自动建站
5. **规模复制**：邮寄带 QR 码的实体明信片，零冷电话

### 为什么这个 Playbook 值得做
- **低竞争**：大多数人在追 Polymarket/加密，没人做实体商业
- **高感知价值**：商家不懂 AI，愿意付溢价（¥2000-5000/个网站正常）
- **永恒需求**：每个城市都有数万个没网站的商家
- **低边际成本**：建好流程后几乎零额外投入
- **无清零风险**：不像 Polymarket 可能爆仓

### Skill 文件
@everestchris6 免费开放了 skill 文件
- 🔗 https://x.com/everestchris6/status/2030373273163477503
- 待行动：下载研究，适配中文市场（本地商家/大众点评/美团）

---

## Playbook 3: Polymarket 时区套利（@zerqfer + @xmayeth 打法）
**来源**: @zerqfer（实操）+ @xmayeth（量化朋友两页纸公式）
**模式**: AI Agent 利用非美时区市场定价偏差，在 Polymarket 套利

### 核心公式（xmayeth 的两页纸精华）
- **时区套利原理**：Polymarket 70% 交易者是美国人，非美时区结算的事件定价系统性偏低
- **仓位管理**：凯利公式，最大单注 5% 本金
- **市场选择**：只做"可验证结果"市场（天气/体育/经济数据），避开主观判断市场
- **止损纪律**：单日最大亏损 -15% 立即停止
- **NOAA 天气预测**：准确率 93%，远超 Polymarket 定价，存在稳定 α

### 实操结果
- @zerqfer：$12K → $43,800（48小时，凌晨 3:47 叫醒授权）
- @zerqfer：Monte Carlo 双 Agent（预测 Agent + 执行 Agent 分离）
- 另一个案例：$50 → $435,000（Rust 实现，$400-700/天，6,823 笔交易）

### 关键教训（来自 Claude vs OpenClaw 对决）
- Claude +1322% vs OpenClaw 清零 — 根本原因：风控层缺失
- **止损 > 盈利**，没有风控的 Agent 是赌博机器不是赚钱机器
- 双 Agent 架构更稳：预测 Agent 只预测，执行 Agent 只执行，职责分离

