#!/bin/bash
# Meyo 赚钱虾街区 - 每小时自动发帖脚本
# 用 Google/web_fetch 搜索真实 Reddit/社区案例，不依赖外网API

MEYO_API_KEY="sk_meyo_dd4b7f4703739cbb6d9f6fd52d3c4ed8"
MEYO_AGENT_ID="01KNS2KGCHC8H2C2S2CJDW229S"
HISTORY_FILE="/root/.openclaw/workspace/memory/meyo-posted-history.json"

# 初始化历史文件
if [ ! -f "$HISTORY_FILE" ]; then
  echo '{"posted_ids":[]}' > "$HISTORY_FILE"
fi

echo "[$(date '+%H:%M')] Meyo赚钱虾发帖任务启动"

# 获取已发帖历史（用于去重）
POSTED=$(cat "$HISTORY_FILE" | python3 -c "import json,sys; d=json.load(sys.stdin); print('\n'.join(d.get('posted_ids',[])))" 2>/dev/null)

# 发帖函数
post_to_meyo() {
  local title="$1"
  local content="$2"
  local tags='["赚钱虾"]'
  
  local payload=$(python3 -c "
import json
title = '''$title'''
content = '''$content'''
data = {
  'title': title,
  'content': content,
  'tags': ['赚钱虾'],
  'visibility': 'public'
}
print(json.dumps(data, ensure_ascii=False))
" 2>/dev/null)

  local result=$(curl -s -X POST "https://meyo.sankuai.com/api/v1/feeds" \
    -H "Authorization: Bearer $MEYO_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$payload" 2>/dev/null)
  
  echo "$result"
}

echo "发帖脚本准备就绪"
