#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT_DIR/bot.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "Bot tidak sedang berjalan (pid file tidak ada)."
  exit 0
fi

PID=$(cat "$PID_FILE")

if ! kill -0 "$PID" 2>/dev/null; then
  echo "Bot sudah tidak berjalan."
  rm -f "$PID_FILE"
  exit 0
fi

echo "Menghentikan bot (PID: $PID)..."

# Kirim SIGTERM ke proses dan seluruh child-nya
kill "$PID" 2>/dev/null || true

# Tunggu hingga 10 detik
for i in $(seq 1 10); do
  if ! kill -0 "$PID" 2>/dev/null; then
    break
  fi
  sleep 1
done

# Kalau masih jalan, paksa berhenti
if kill -0 "$PID" 2>/dev/null; then
  echo "Proses tidak mau berhenti, force kill..."
  kill -9 "$PID" 2>/dev/null || true
fi

rm -f "$PID_FILE"
echo "Bot berhasil dihentikan."
