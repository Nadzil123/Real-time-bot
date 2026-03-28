#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT_DIR/.env"
VENV_DIR="$ROOT_DIR/.venv"

ok() {
  echo "[OK] $1"
}

warn() {
  echo "[WARN] $1"
}

fail() {
  echo "[FAIL] $1"
}

echo "Checking Grow a Garden Token Bot environment..."
echo ""

if command -v python3 >/dev/null 2>&1; then
  ok "python3 ditemukan"
elif command -v python >/dev/null 2>&1; then
  ok "python ditemukan"
else
  fail "Python belum terinstall"
fi

if [ -d "$VENV_DIR" ]; then
  ok ".venv tersedia"
else
  fail ".venv belum ada. Jalankan ./install.sh dulu"
fi

if [ -f "$ENV_FILE" ]; then
  ok ".env tersedia"
else
  fail ".env belum ada. Jalankan ./configure.sh dulu"
fi

if [ -f "$ENV_FILE" ]; then
  if grep -q "DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/replace_me" "$ENV_FILE"; then
    fail "Webhook masih placeholder. Jalankan ./configure.sh"
  elif grep -q "^DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/" "$ENV_FILE"; then
    ok "Webhook Discord terlihat valid"
  else
    warn "Webhook Discord belum terdeteksi dalam format standar"
  fi
fi

if [ -d "$VENV_DIR" ]; then
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  if python -c "import requests, bs4, dotenv, playwright" >/dev/null 2>&1; then
    ok "Dependency Python utama tersedia"
  else
    fail "Masih ada dependency Python yang belum terinstall"
  fi

  if python -m playwright install --dry-run chromium >/dev/null 2>&1; then
    ok "Playwright Chromium siap"
  else
    warn "Chromium Playwright belum siap atau tidak bisa dicek dengan aman"
  fi
fi

echo ""
echo "Saran command:"
echo "- Install : ./install.sh"
echo "- Config  : ./configure.sh"
echo "- Preview : ./preview.sh"
echo "- Run bot : ./run.sh"
