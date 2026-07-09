#!/bin/bash
# cron_llm_guard.sh — LLM型cron的幂等检查
# 
# 检查: bash cron_llm_guard.sh check <task-id>
#   → SKIP / CONTINUE
#
# 标记完成: bash cron_llm_guard.sh done <task-id>
#   → MARKED_DONE

STATE_DIR="$HOME/.openclaw/cron-state"
mkdir -p "$STATE_DIR"

ACTION="${1:-check}"
TASK_ID="${2:-unknown}"
TODAY=$(date +%Y-%m-%d)
STATE_FILE="$STATE_DIR/${TASK_ID}.json"

case "$ACTION" in
  check)
    if [ -f "$STATE_FILE" ]; then
      LAST_SUCCESS=$(grep -o '"last_success":"[^"]*"' "$STATE_FILE" | cut -d'"' -f4)
      if [ "$LAST_SUCCESS" = "$TODAY" ]; then
        echo "SKIP: $TASK_ID already ran today ($TODAY)"
        exit 0
      fi
    fi
    echo "CONTINUE: $TASK_ID has not run today, proceed"
    exit 0
    ;;
  done)
    echo "{\"task_id\":\"$TASK_ID\",\"last_success\":\"$TODAY\",\"timestamp\":\"$(date -Iseconds)\"}" > "$STATE_FILE"
    echo "MARKED_DONE: $TASK_ID @ $TODAY"
    exit 0
    ;;
  *)
    echo "Usage: cron_llm_guard.sh check|done <task-id>"
    exit 1
    ;;
esac
