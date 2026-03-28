#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT_DIR/.env"
EXAMPLE_FILE="$ROOT_DIR/.env.example"

if [ ! -f "$ENV_FILE" ]; then
  cp "$EXAMPLE_FILE" "$ENV_FILE"
fi

echo "Konfigurasi Discord untuk bot"
echo ""
read -r -p "Masukkan Discord webhook URL: " WEBHOOK_URL
read -r -p "Masukkan Discord channel ID (opsional, tekan Enter kalau tidak dipakai): " CHANNEL_ID

if [ -z "$WEBHOOK_URL" ]; then
  echo "DISCORD_WEBHOOK_URL wajib diisi."
  exit 1
fi

python3 - <<PY
from pathlib import Path

env_path = Path("$ENV_FILE")
content = env_path.read_text()

updates = {
    "DISCORD_WEBHOOK_URL": """$WEBHOOK_URL""".strip(),
    "DISCORD_CHANNEL_ID": """$CHANNEL_ID""".strip() or "0",
}

lines = []
seen = set()
for raw_line in content.splitlines():
    if "=" in raw_line and not raw_line.lstrip().startswith("#"):
        key, _, _ = raw_line.partition("=")
        key = key.strip()
        if key in updates:
            lines.append(f"{key}={updates[key]}")
            seen.add(key)
            continue
    lines.append(raw_line)

for key, value in updates.items():
    if key not in seen:
        lines.append(f"{key}={value}")

env_path.write_text("\\n".join(lines) + "\\n")
PY

echo ""
echo "Berhasil update .env"
echo "Webhook dan channel ID sekarang bisa dipakai user ini sendiri."
