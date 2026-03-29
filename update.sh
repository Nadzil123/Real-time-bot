#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PID_FILE="$ROOT_DIR/bot.pid"

echo "=== Update Bot ==="

# --- Stop bot kalau sedang jalan ---
BOT_WAS_RUNNING=false
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "[1/4] Menghentikan bot..."
  bash "$ROOT_DIR/stop.sh"
  BOT_WAS_RUNNING=true
else
  echo "[1/4] Bot tidak sedang jalan, skip stop."
fi

# --- Pull dari git ---
echo "[2/4] Mengambil update terbaru dari git..."
cd "$ROOT_DIR"
git pull

# --- Update dependencies ---
echo "[3/4] Update Python dependencies..."
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
pip install -q --upgrade pip
pip install -q -r "$ROOT_DIR/requirements.txt"

# --- Restart kalau sebelumnya jalan ---
echo "[4/4] Selesai update."
if [ "$BOT_WAS_RUNNING" = true ]; then
  echo "Memulai ulang bot..."
  bash "$ROOT_DIR/start.sh"
else
  echo "Bot tidak dijalankan ulang (sebelumnya memang tidak jalan)."
  echo "Untuk menjalankan: ./start.sh"
fi
