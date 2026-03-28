#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Updating Termux packages"
pkg update -y
pkg upgrade -y

echo "[2/4] Installing required Termux packages"
pkg install -y python git clang rust nodejs-lts

echo "[3/4] Making install script executable"
chmod +x install.sh

echo "[4/4] Running project installer"
./install.sh

echo ""
echo "Selesai."
echo "Edit .env lalu jalankan: ./run.sh"
