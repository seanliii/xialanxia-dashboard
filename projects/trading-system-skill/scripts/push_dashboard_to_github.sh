#!/bin/bash
# 把最新 dashboard.html 推送到 GitHub Pages
# 每次持仓更新后调用

GITHUB_TOKEN="<你的GitHub Token>"
GITHUB_USER="<你的GitHub用户名>"
REPO_NAME="<你的Dashboard仓库名>"
DASHBOARD_PATH="/root/.openclaw/workspace/dashboard/dashboard.html"
TMP_DIR="/tmp/gh-dashboard-push"

rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
cd "$TMP_DIR"

git init -q
git config user.email "bot@example.com"
git config user.name "Trading Bot"

cp "$DASHBOARD_PATH" index.html

git add index.html
git commit -q -m "📊 Dashboard update $(date '+%Y-%m-%d %H:%M')"

git remote add origin "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"
git fetch -q origin main 2>/dev/null || true
git branch -M main

# force push（每次用新 commit 覆盖，保持 repo 干净）
# 如果在沙箱中需要代理，取消下面注释：
# https_proxy="http://127.0.0.1:8118" git push -f origin main -q 2>&1
git push -f origin main -q 2>&1 && echo "✅ Dashboard pushed to GitHub Pages" || echo "❌ Push failed"
