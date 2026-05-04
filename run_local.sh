#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${TG_BOT_TOKEN:-}" ]]; then
  echo "Missing TG_BOT_TOKEN. Example:"
  echo "  export TG_BOT_TOKEN='123:ABC'"
  exit 1
fi

export CHAT_REWARD_MIN="${CHAT_REWARD_MIN:-1}"
export CHAT_REWARD_MAX="${CHAT_REWARD_MAX:-10}"
export CHAT_DAILY_FIRST_MIN="${CHAT_DAILY_FIRST_MIN:-1}"
export CHAT_DAILY_FIRST_MAX="${CHAT_DAILY_FIRST_MAX:-100}"
export WEBAPP_URL="${WEBAPP_URL:-http://127.0.0.1:8080/miniapp}"
export ADMIN_UI_HOST="${ADMIN_UI_HOST:-127.0.0.1}"
export ADMIN_UI_PORT="${ADMIN_UI_PORT:-8080}"
export MINIAPP_BOT_USERNAME="${MINIAPP_BOT_USERNAME:-tgmcoinbot}"
export PYTHONUNBUFFERED=1

cleanup() {
  [[ -n "${ADMIN_UI_PID:-}" ]] && kill "$ADMIN_UI_PID" 2>/dev/null || true
  [[ -n "${BOT_PID:-}" ]] && kill "$BOT_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

python3 -u admin_ui.py &
ADMIN_UI_PID=$!

python3 -u bot.py &
BOT_PID=$!

echo "Admin panel: http://${ADMIN_UI_HOST}:${ADMIN_UI_PORT}/"
echo "Mini app:    http://${ADMIN_UI_HOST}:${ADMIN_UI_PORT}/miniapp?lang=ru"
echo "Bot polling is running. Press Ctrl+C to stop."

wait
