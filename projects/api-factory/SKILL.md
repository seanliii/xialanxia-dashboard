# API工厂 — 复刻方法

## 这是什么
一个引导你在30分钟内把自己的能力打包成可售卖 API 的工具。自动生成 API 文档、定价页、上架流程指引。

## 适合谁
- 有技术能力但不知道怎么变现的开发者
- 想把 AI 能力封装成 API 出售的人
- 希望建立被动收入管道的程序员

## 复刻步骤

### Step 1：创建仓库
新建 GitHub 仓库 api-factory，开启 Pages

### Step 2：核心模块设计
- API 描述生成器：输入功能描述 → 自动生成 OpenAPI 格式文档
- 定价计算器：根据调用量/复杂度推荐定价方案
- 上架清单：RapidAPI / Mashape / 自建 等平台的步骤指引
- 示例代码生成：Python / Node.js / cURL 调用示例

### Step 3：关键 Prompt

```
做一个API工厂引导页面：
- 第一步：输入API功能描述，自动生成endpoint路径和参数说明
- 第二步：选择定价模式（免费增值/按量计费/包月），自动计算建议价格
- 第三步：生成上架到 RapidAPI 的完整步骤清单
- 第四步：生成多语言调用示例代码
- 深色主题，分步骤卡片式布局
```

### Step 4：部署
推送到 main 分支，GitHub Pages 自动部署

## 踩坑记录
- API 定价要参考同类产品，不能拍脑袋
- RapidAPI 上架需要真实可调用的 endpoint
- 示例代码要保证语法正确可复制

## 成品地址
https://seanliii.github.io/api-factory/
