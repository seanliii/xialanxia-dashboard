# MVP 设计 — ListingBridge

> 创始人：老张 | 日期：2026-05-18  
> 主利基：跨境电商多平台 Listing 本地化工具

---

## 1. 最优先验证的假设

**核心假设：多平台跨境卖家愿意为 AI Listing 本地化工具付费 $49-99/月**

拆解为三个子假设：
1. 多平台卖家确实在手动做 listing 翻译/适配（问题存在性）
2. 现有方案（Google Translate + 手动调格式）让他们足够痛（痛点强度）
3. 他们愿意为自动化工具付 $49+/月（付费意愿）

---

## 2. 最小验证形式

### 选定方案：Landing Page + Manual-Behind-the-Curtain

**不写代码。** 先用 landing page 验证需求，首批用户手动 + 半自动交付。

| 阶段 | 做什么 | 工具 |
|------|--------|------|
| Week 1 | Landing page + waitlist | Carrd/Framer + Mailchimp |
| Week 2 | Product Hunt "Coming Soon" 页 | PH |
| Week 3-4 | 首批5-10个用户，手动交付（Python脚本半自动） | GPT API + 自己的脚本 |
| Week 5-6 | 根据反馈决定是否值得做 SaaS | — |

---

## 3. MVP 边界

### 做什么（V0.1）
- Amazon listing → Shopify/eBay 格式转换
- 支持英→德/法/西 3个语种
- AI 翻译 + 格式适配
- CSV 上传/下载
- 手动触发（非实时）

### 不做什么
- ❌ 不做 API 直接同步上架
- ❌ 不做实时自动监控
- ❌ 不做图片/A+ Content
- ❌ 不做定价优化
- ❌ 不做多用户并发

---

## 4. 成功标准

| 指标 | 目标 | 时间窗口 |
|------|------|---------|
| Waitlist 注册数 | ≥ 100 | 2周内 |
| 首批付费用户 | ≥ 5 | 4周内 |
| 用户留存（第2月续费） | ≥ 60% | 8周内 |
| NPS 评分 | ≥ 8/10 | 首批用户反馈 |

**决策规则**：
- 100 waitlist + 5 付费 = ✅ 值得做 SaaS
- 50 waitlist + 2 付费 = ⚠️ 调整定位/定价后再试
- < 30 waitlist = ❌ Pivot

---

## 5. 人机分工

| 环节 | 人工（老张） | AI/自动化 |
|------|------------|-----------|
| Landing page | 设计+文案 | Framer 模板 |
| Listing 翻译 | 质检+调优 | GPT-4 API |
| 格式适配 | 规则定义 | Python 脚本自动执行 |
| SEO 关键词 | 最终选词 | AI 候选词生成 |
| 客户沟通 | 全部人工（5-10人量级可控） | — |
| 数据分析 | 解读+决策 | 自动汇总 |

---

## 6. 验证周期

```
Week 1:   Landing page 上线 + PH Coming Soon
Week 2:   Reddit/Facebook 跨境卖家群推广 + 收集 waitlist
Week 3:   联系 waitlist 前10名，半价($25)试用
Week 4:   手动交付，收集反馈
Week 5:   评估数据，决定 Go / Pivot
Week 6:   Go → 开始写 SaaS 代码 | Pivot → 调整方向
```

总验证时间：**6周，$0 开发成本**
