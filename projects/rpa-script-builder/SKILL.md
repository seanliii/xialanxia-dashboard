---
name: rpa-script-builder
description: "可视化RPA脚本生成器——添加操作步骤（打开URL/点击/输入/截图/提取文本），实时生成可直接运行的Playwright Python脚本。零token永久回放，告别重复烧API成本。"
triggers:
  - "RPA"
  - "录制回放"
  - "playwright脚本"
  - "浏览器自动化"
  - "零token回放"
---
# RPA Script Builder — 可视化 Playwright 脚本生成器

## 使用步骤
1. 打开 https://seanliii.github.io/rpa-script-builder/
2. 添加操作步骤（打开URL / 点击 / 输入文字 / 等待 / 截图 / 提取文本）
3. 右侧实时预览生成的 Python 代码
4. 点击「复制代码」
5. 本地运行：
   ```bash
   pip install playwright
   playwright install
   python script.py
   ```

## 5个内置模板
- 登录签到 / 批量下载 / 表单填写 / 价格监控 / 社媒发帖

## 核心价值
- 录制一次 → 永久回放
- 完全不消耗 LLM token
- 生成标准 Playwright 代码，可独立运行
