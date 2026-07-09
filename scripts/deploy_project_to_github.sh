#!/bin/bash
# deploy_project_to_github.sh — Deploy local project to GitHub Pages
# Usage: bash deploy_project_to_github.sh projects/<project-dir> <repo-name>

PROJECT_DIR=$1
REPO_NAME=$2
GH_USER="seanliii"
GH_TOKEN="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"

if [ -z "$PROJECT_DIR" ] || [ -z "$REPO_NAME" ]; then
  echo "Usage: $0 <project-dir> <repo-name>"
  exit 1
fi

FULL_PATH="/root/.openclaw/workspace/$PROJECT_DIR"
if [ ! -d "$FULL_PATH" ]; then
  echo "Error: $FULL_PATH not found"
  exit 1
fi

echo "🚀 Deploying $PROJECT_DIR to https://seanliii.github.io/$REPO_NAME/"

# Create repo if doesn't exist
gh_api() {
  curl -H 'X-Catclaw-Request: true' -H 'X-Request-Source: CatClaw' -s -H "Authorization: token $GH_TOKEN" -H "Accept: application/vnd.github.v3+json" "$@"
}

REPO_CHECK=$(gh_api "https://api.github.com/repos/$GH_USER/$REPO_NAME" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('name','NOT_FOUND'))" 2>/dev/null)
if [ "$REPO_CHECK" = "NOT_FOUND" ]; then
  echo "📦 Creating repo $REPO_NAME..."
  gh_api -X POST "https://api.github.com/user/repos" \
    -d "{\"name\":\"$REPO_NAME\",\"description\":\"AI tool by 小蓝虾\",\"private\":false,\"auto_init\":true}" > /dev/null
  sleep 2
fi

# Push files
cd "$FULL_PATH"
git init -q
git config user.email "bot@xialanxia.ai"
git config user.name "小蓝虾"
git remote remove origin 2>/dev/null || true
git remote add origin "https://$GH_TOKEN@github.com/$GH_USER/$REPO_NAME.git"
git checkout -b main 2>/dev/null || git checkout main
git add -A
git commit -m "deploy: $(date '+%Y-%m-%d %H:%M')" -q
git push -f origin main -q

# Enable Pages (main branch)
gh_api -X POST "https://api.github.com/repos/$GH_USER/$REPO_NAME/pages" \
  -d '{"source":{"branch":"main","path":"/"}}' > /dev/null 2>&1 || true

echo "✅ Deployed! URL: https://$GH_USER.github.io/$REPO_NAME/"
