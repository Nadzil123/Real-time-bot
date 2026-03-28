#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-}"

if [ -z "$PYTHON_BIN" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    PYTHON_BIN="python3"
  fi
fi

echo "[1/5] Checking Python"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
  echo "Python tidak ditemukan. Install python3 dulu."
  exit 1
}

echo "[2/5] Creating virtualenv if needed"
if [ ! -d "$VENV_DIR" ]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "[3/5] Upgrading pip"
python -m pip install --upgrade pip

echo "[4/5] Installing Python dependencies"
pip install -r "$ROOT_DIR/requirements.txt"

echo "[5/5] Installing Playwright Chromium"
if ! python -m playwright install chromium; then
  echo ""
  echo "Gagal install Chromium untuk Playwright."
  echo "Kalau kamu di Termux, ini memang titik yang paling sering gagal."
  echo "Coba jalankan di Ubuntu/VPS kalau tetap mentok."
  exit 1
fi

if [ ! -f "$ROOT_DIR/.env" ]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  echo ""
  echo "File .env berhasil dibuat dari .env.example"
fi

echo ""
read -r -p "Mau isi webhook Discord sekarang? [y/N]: " CONFIGURE_NOW
if [[ "${CONFIGURE_NOW,,}" == "y" ]]; then
  chmod +x "$ROOT_DIR/configure.sh"
  "$ROOT_DIR/configure.sh"
else
  echo "Lewati konfigurasi interaktif. Nanti bisa jalankan ./configure.sh"
fi

echo ""
echo "Selesai."
echo "Config   : chmod +x configure.sh && ./configure.sh"
echo "Preview  : source .venv/bin/activate && python preview.py"
echo "Run bot  : source .venv/bin/activate && python main.py"
