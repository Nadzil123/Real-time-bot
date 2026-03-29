#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PID_FILE="$ROOT_DIR/bot.pid"
LOG_FILE="$ROOT_DIR/bot.log"

# --- Validasi ---
if [ ! -d "$VENV_DIR" ]; then
  echo "ERROR: .venv belum ada. Jalankan ./install.sh dulu."
  exit 1
fi

if [ ! -f "$ROOT_DIR/.env" ]; then
  echo "ERROR: .env belum ada. Jalankan ./configure.sh dulu."
  exit 1
fi

if grep -q "DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/replace_me" "$ROOT_DIR/.env"; then
  echo "ERROR: Webhook masih placeholder. Jalankan ./configure.sh dulu."
  exit 1
fi

# --- Cek apakah sudah jalan ---
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Bot sudah berjalan (PID: $OLD_PID)"
    echo "  Log   : tail -f $LOG_FILE"
    echo "  Stop  : ./stop.sh"
    exit 0
  else
    rm -f "$PID_FILE"
  fi
fi

# --- Jalankan di background dengan auto-restart ---
(
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot dimulai..."
    python "$ROOT_DIR/main.py"
    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot berhenti (exit code: $EXIT_CODE)."
    if [ "$EXIT_CODE" -eq 0 ]; then
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot berhenti normal. Tidak restart."
      break
    fi
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Crash terdeteksi. Restart dalam 10 detik..."
    sleep 10
  done
) >> "$LOG_FILE" 2>&1 &

BGPID=$!
echo "$BGPID" > "$PID_FILE"

echo "Bot berjalan di background!"
echo "  PID   : $BGPID"
echo "  Log   : tail -f $LOG_FILE"
echo "  Stop  : ./stop.sh"
echo "  Update: ./update.sh"
