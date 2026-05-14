#!/bin/zsh
set -u

REPO="/Users/zhangfeng/openclaw-config-backup"
LOG_DIR="$REPO/logs"
LOG_FILE="$LOG_DIR/auto-update.log"
mkdir -p "$LOG_DIR"

exec >> "$LOG_FILE" 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S %z') OpenClaw config backup start ====="
cd "$REPO" || exit 1

# Keep commits attributable even when launchd runs without global git identity.
git config user.name "OpenClaw Config Backup" >/dev/null
git config user.email "openclaw-config-backup@local" >/dev/null

python3 scripts/export-sanitized.py

git add .
if git diff --cached --quiet; then
  echo "No sanitized config changes."
  echo "===== $(date '+%Y-%m-%d %H:%M:%S %z') done ====="
  exit 0
fi

COMMIT_MSG="Update OpenClaw config backup $(date '+%Y-%m-%d')"
git commit -m "$COMMIT_MSG"

if git remote get-url origin >/dev/null 2>&1; then
  git push
else
  echo "No git remote named origin; committed locally only."
fi

echo "===== $(date '+%Y-%m-%d %H:%M:%S %z') done ====="
