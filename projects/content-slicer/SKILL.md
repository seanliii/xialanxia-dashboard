---
name: content-slicer
description: "输入一段长文章/播客转录稿，自动切片成Twitter/小红书/LinkedIn/短视频脚本+7天内容日历。Mark Savant模式：5天获$700 MRR的内容自动化核心工具。"
triggers:
  - "内容自动化"
  - "内容切片"
  - "一键多平台"
  - "content repurpose"
  - "长文变短内容"
---
# Content Slicer — 内容自动切片分发器

输入长文本 → 自动提取核心观点 → 生成各平台适配内容。纯前端，无需 API。

## 使用步骤
1. 打开 https://seanliii.github.io/content-slicer/
2. 粘贴你的长文章/播客稿子（建议500字以上）
3. 点击「切片」按钮
4. 系统自动生成：Twitter/小红书/LinkedIn/短视频脚本 × N个观点
5. 一键复制每条内容，直接发布
6. 底部查看7天发布日历

## 技术实现（纯前端 NLP）
- 分句 → TF-IDF权重 → 提取Top观点
- 各平台模板格式化
- 零外部依赖，国内用户直接用

## 适合场景
- 播客/音频转录稿 → 社媒矩阵
- 长博客 → 短内容拆解
- 培训课程 → 知识卡片
