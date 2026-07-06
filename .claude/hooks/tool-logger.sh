#!/bin/bash
# Logs complete tool execution to tmp/tool-execution.jsonl (JSONL format).
# Receives full PostToolUse payload on stdin.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/tmp"
LOG_FILE="$LOG_DIR/tool-execution.jsonl"

mkdir -p "$LOG_DIR"

PAYLOAD=$(cat)

printf '%s\n' "$PAYLOAD" \
  | jq -c --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '. + {ts: $ts}' \
  >> "$LOG_FILE"

exit 0