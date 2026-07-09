# Solo收入仪表板 — 复刻方法

## 这是什么
独立开发者专属的收入追踪仪表板。月度 Revenue vs AI 支出对比，自动计算 ROI，用 Chart.js 做数据可视化。

## 适合谁
- 用 AI 工具做产品但不知道投入产出比的独立开发者
- 想量化「AI 到底帮我赚了多少」的人
- 需要一个轻量级财务追踪工具的 Solo Founder

## 复刻步骤

### Step 1：创建 GitHub 仓库
新建公开仓库 solo-revenue-dashboard，开启 Pages

### Step 2：核心功能设计
- 月度收入录入（多来源：产品销售、咨询、订阅等）
- AI 支出录入（API 费用、工具订阅等）
- ROI 自动计算：(收入 - AI支出) / AI支出 x 100%
- Chart.js 折线图/柱状图可视化

### Step 3：技术实现
- HTML + CSS + JavaScript 单文件
- Chart.js CDN 引入
- LocalStorage 存储历史数据
- 响应式布局

### Step 4：关键 Prompt

```
帮我做一个独立开发者收入仪表板：
- 左侧录入区：月份选择、收入明细（来源+金额）、AI支出明细
- 右侧展示区：Chart.js 双轴图（收入柱状+AI支出折线）
- 底部：ROI 计算结果、累计收入、累计支出
- 数据用 LocalStorage 持久化
- 深色科技风主题
```

## 踩坑记录
- Chart.js 版本用 4.x，API 和 3.x 有区别
- LocalStorage 存 JSON 时记得 stringify/parse
- 移动端 Chart.js 图表需要设置 responsive: true

## 成品地址
https://seanliii.github.io/solo-revenue-dashboard/
