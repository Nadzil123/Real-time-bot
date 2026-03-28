#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  echo ".venv belum ada. Jalankan ./install.sh dulu."
  exit 1
fi

if [ ! -f "$ROOT_DIR/.env" ]; then
  echo ".env belum ada. Copy dari .env.example lalu isi DISCORD_WEBHOOK_URL."
  exit 1
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Menjalankan bot..."
python "$ROOT_DIR/main.py"
