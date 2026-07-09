# 待部署项目清单

## ⚠️ GitHub Token 已过期
需要更新 token 后才能推送。更新后修改：
- `/root/.openclaw/workspace/scripts/deploy_project_to_github.sh` 第7行
- `/root/.openclaw/workspace/scripts/push_dashboard_to_github.sh` 第5行

---

## 1. AI Landing Page Generator ✅ 已完成
- 路径：`projects/ai-landing-generator/`
- 部署命令：`bash scripts/deploy_project_to_github.sh projects/ai-landing-generator ai-landing-generator`
- 预计链接：https://seanliii.github.io/ai-landing-generator/
- 功能：输入产品描述 → 即时生成4种风格的 Landing Page HTML → 复制/下载
- 变现：免费引流工具 → 可加 Pro 版（自定义域名、更多模板）

## 待复刻队列
(每次 cron 发现好案例 → 加到这里 → 执行 → 部署)

## 2. LLM Battle Tracker 2026 ⏳ 待推送
- 路径：`projects/llm-battle-tracker/`
- 预计链接：https://seanliii.github.io/llm-battle-tracker/
- 功能：开源 vs 闭源大模型实力对决榜，含筛选、benchmark对比、Ticker行情栏
- 数据：Kimi K2.6、DeepSeek V4、Claude Opus 4.7、GPT-5.5、Qwen 3.5、GLM 5.1
- 状态：HTML完成，GitHub代理被封锁，需手动push
- 部署命令：`cd /tmp/gh-llm-tracker && https_proxy="http://10.59.78.158:3128" git push -f origin master`
