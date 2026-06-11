#!/bin/bash
# 把最新 dashboard.html 推送到 GitHub Pages
# 每次持仓更新后调用

GITHUB_TOKEN="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"
GITHUB_USER="seanliii"
REPO_NAME="xialanxia-dashboard"
DASHBOARD_PATH="/root/.openclaw/workspace/dashboard/dashboard.html"
TMP_DIR="/tmp/gh-dashboard-push"

rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
cd "$TMP_DIR"

git init -q
git config user.email "bot@xialanxia.ai"
git config user.name "小蓝虾 Bot"

cp "$DASHBOARD_PATH" index.html

git add index.html
git commit -q -m "🦐 Dashboard update $(date '+%Y-%m-%d %H:%M')"

git remote add origin "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"
git fetch -q origin main 2>/dev/null || true
git branch -M main

# force push（每次用新 commit 覆盖，保持 repo 干净）
https_proxy="http://10.59.78.158:3128" git push -f origin main -q 2>&1 && echo "✅ Dashboard pushed to GitHub Pages" || echo "❌ Push failed"
