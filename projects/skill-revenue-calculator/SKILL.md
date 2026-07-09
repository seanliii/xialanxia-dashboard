# Skill变现计算器 — 复刻方法

## 这是什么
一个帮 Skill 开发者快速计算变现收入的在线工具。输入定价、预估销量、变现方式，秒算月收入/年收入/时薪，内置5步变现SOP。

## 适合谁
- 做了 Skill 想知道能赚多少钱的开发者
- 正在考虑 Skill 定价策略的人
- 想评估副业收入潜力的 AI 从业者

## 复刻步骤

### Step 1：创建 GitHub 仓库
新建一个公开仓库，开启 GitHub Pages（Settings → Pages → Deploy from branch: main）

### Step 2：创建 index.html
单文件方案，包含以下模块：
- 输入区：定价（单次/订阅/按量）、预估月销量、变现方式选择
- 计算逻辑：月收入 = 定价 × 销量 × 平台抽成系数
- 年收入 = 月收入 × 12
- 时薪 = 年收入 / 预估投入小时数
- 5步SOP展示区：选赛道→做MVP→定价→推广→迭代

### Step 3：技术栈
- 纯前端 HTML + CSS + JavaScript
- 无需后端，GitHub Pages 免费部署
- 响应式设计，手机可用

### Step 4：部署
推送到 main 分支，等待 GitHub Actions 自动部署

## 关键 Prompt（让 AI 帮你生成）

```
帮我写一个单页面 Skill 变现计算器：
- 输入：Skill单价、月销量预估、变现方式（一次性/订阅/按量计费）
- 输出：月收入、年收入、折算时薪
- 包含一个5步变现SOP的可折叠展示区
- 样式要现代、深色主题、有渐变色
- 纯前端实现，部署到 GitHub Pages
```

## 踩坑记录
- GitHub Pages 部署后需要等1-2分钟生效
- 计算逻辑要考虑平台抽成（一般 10%-30%）
- 时薪计算需要用户输入每周投入小时数

## 成品地址
https://seanliii.github.io/skill-revenue-calculator/
