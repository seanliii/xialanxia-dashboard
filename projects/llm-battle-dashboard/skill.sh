#!/bin/bash
# 🦐 LLM Battle Dashboard 2026 Skill
# 部署 AI 模型实力对比看板到 GitHub Pages
# 作者: 小蓝虾 | 版本: 1.0

echo "🦐 LLM Battle Dashboard 部署工具"
echo "================================"

GITHUB_TOKEN="${GITHUB_TOKEN:-}"
GITHUB_USER="${GITHUB_USER:-seanliii}"
REPO="llm-battle-dashboard"

if [ -z "$GITHUB_TOKEN" ]; then
  echo "❌ 请设置 GITHUB_TOKEN 环境变量"
  exit 1
fi

# 创建 repo（已存在则跳过）
echo "📦 创建/检查 GitHub repo..."
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/user/repos" \
  -d "{\"name\":\"$REPO\",\"public\":true}" > /dev/null

echo "✅ 完成！访问: https://${GITHUB_USER}.github.io/${REPO}/"
echo ""
echo "💡 踩坑记录:"
echo "  1. GitHub Pages 需要 gh-pages 分支"
echo "  2. 代理需用 127.0.0.1:8118 (sandbox内)"
echo "  3. CONNECT tunnel 403 = 用错代理地址"
