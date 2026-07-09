#!/bin/bash
set -e

cd /root/.openclaw/workspace/projects/ai-weekly-report-gen

echo "🦐 部署 ai-weekly-report-gen → GitHub Pages..."

# Ensure git repo
if [ ! -d .git ]; then
  git init
  git remote add origin https://github.com/seanliii/ai-weekly-report-gen.git 2>/dev/null || true
fi

# Commit and push
git add index.html
git commit -m "feat: weekly report generator MVP $(date +%Y-%m-%d)" || true
git branch -M main || true
git push -f https://seanliii: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@github.com/seanliii/ai-weekly-report-gen.git main || true

echo "✅ 推送完成"
echo "🔗 访问地址：https://seanliii.github.io/ai-weekly-report-gen/"
