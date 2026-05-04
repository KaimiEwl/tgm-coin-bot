#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDDIR="${ROOT}/.pids"

require_env() {
  if [[ -z "${TG_BOT_TOKEN:-}" ]]; then
    echo "Missing TG_BOT_TOKEN."
    echo "Example: export TG_BOT_TOKEN='123:ABC'"
    exit 1
  fi
}

pidfile_admin_ui="${PIDDIR}/admin_ui.pid"
pidfile_bot="${PIDDIR}/bot.pid"

is_running() {
  local pid="$1"
  [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null
}

read_pid() {
  local file="$1"
  [[ -f "${file}" ]] && cat "${file}" || true
}

start_admin_ui() {
  mkdir -p "${PIDDIR}"
  local pid
  pid="$(read_pid "${pidfile_admin_ui}")"
  if is_running "${pid}"; then
    echo "admin_ui already running pid=${pid}"
    return
  fi
  nohup env \
    TG_BOT_TOKEN="${TG_BOT_TOKEN}" \
    DB_PATH="${DB_PATH:-${ROOT}/coins.db}" \
    WEBAPP_URL="${WEBAPP_URL:-http://127.0.0.1:8080/miniapp}" \
    ADMIN_UI_HOST="${ADMIN_UI_HOST:-127.0.0.1}" \
    ADMIN_UI_PORT="${ADMIN_UI_PORT:-8080}" \
    MINIAPP_BOT_USERNAME="${MINIAPP_BOT_USERNAME:-tgmcoinbot}" \
    PYTHONUNBUFFERED=1 \
    python3 -u "${ROOT}/admin_ui.py" > "${ROOT}/admin_ui.log" 2>&1 &
  echo $! > "${pidfile_admin_ui}"
  echo "admin_ui started pid=$(cat "${pidfile_admin_ui}")"
}

start_bot() {
  mkdir -p "${PIDDIR}"
  local pid
  pid="$(read_pid "${pidfile_bot}")"
  if is_running "${pid}"; then
    echo "bot already running pid=${pid}"
    return
  fi
  nohup env \
    TG_BOT_TOKEN="${TG_BOT_TOKEN}" \
    DB_PATH="${DB_PATH:-${ROOT}/coins.db}" \
    CHAT_REWARD_MIN="${CHAT_REWARD_MIN:-1}" \
    CHAT_REWARD_MAX="${CHAT_REWARD_MAX:-10}" \
    CHAT_DAILY_FIRST_MIN="${CHAT_DAILY_FIRST_MIN:-1}" \
    CHAT_DAILY_FIRST_MAX="${CHAT_DAILY_FIRST_MAX:-100}" \
    WEBAPP_URL="${WEBAPP_URL:-http://127.0.0.1:8080/miniapp}" \
    MINIAPP_BOT_USERNAME="${MINIAPP_BOT_USERNAME:-tgmcoinbot}" \
    PYTHONUNBUFFERED=1 \
    python3 -u "${ROOT}/bot.py" > "${ROOT}/bot.log" 2>&1 &
  echo $! > "${pidfile_bot}"
  echo "bot started pid=$(cat "${pidfile_bot}")"
}

stop_one() {
  local name="$1"
  local file="$2"
  local pid
  pid="$(read_pid "${file}")"
  if ! is_running "${pid}"; then
    echo "${name} not running"
    rm -f "${file}" >/dev/null 2>&1 || true
    return
  fi
  kill "${pid}" 2>/dev/null || true
  sleep 0.4
  if is_running "${pid}"; then
    kill -9 "${pid}" 2>/dev/null || true
  fi
  rm -f "${file}" >/dev/null 2>&1 || true
  echo "${name} stopped"
}

status() {
  local pida pidb
  pida="$(read_pid "${pidfile_admin_ui}")"
  pidb="$(read_pid "${pidfile_bot}")"
  if is_running "${pida}"; then
    echo "admin_ui: running pid=${pida} url=http://127.0.0.1:${ADMIN_UI_PORT:-8080}/"
  else
    echo "admin_ui: stopped"
  fi
  if is_running "${pidb}"; then
    echo "bot:      running pid=${pidb}"
  else
    echo "bot:      stopped"
  fi
}

logs() {
  echo "== admin_ui.log =="
  tail -n 80 "${ROOT}/admin_ui.log" 2>/dev/null || true
  echo
  echo "== bot.log =="
  tail -n 120 "${ROOT}/bot.log" 2>/dev/null || true
}

cmd="${1:-}"
case "${cmd}" in
  start)
    require_env
    start_admin_ui
    start_bot
    status
    ;;
  stop)
    stop_one "admin_ui" "${pidfile_admin_ui}"
    stop_one "bot" "${pidfile_bot}"
    ;;
  status)
    status
    ;;
  logs)
    logs
    ;;
  *)
    echo "Usage: ./devctl.sh start|stop|status|logs"
    exit 1
    ;;
esac
