# Grow a Garden Token Bot

Bot ini mengambil post `GaG value list` dari Fandom, lalu mengirim `nama pet`, `rarity`, dan `harga token` ke Discord webhook.

## Sebelum Dibagikan

- jangan upload file `.env`
- kalau pernah pakai webhook Discord asli saat testing, rotate webhook itu dulu sebelum repo dipublikasikan

## Fitur

- otomatis cari post value list yang relevan dengan `token value`
- parse nama pet dan harga token
- ambil rarity dari halaman wiki/API
- kirim hasil ke Discord dengan embed yang lebih rapi
- simpan cache rarity dan snapshot supaya run berikutnya lebih ringan

## Install

### Ubuntu / VPS Ubuntu

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-venv
git clone https://github.com/Nadzil123/Real-time-bot.git
cd Real-time-bot
chmod +x install.sh configure.sh run.sh
./install.sh
./configure.sh
./run.sh
```

### Termux

```bash
git clone https://github.com/Nadzil123/Real-time-bot.git
cd Real-time-bot
chmod +x termux.sh run.sh
./termux.sh
./run.sh
```

## Konfigurasi

Cara paling gampang:

```bash
./configure.sh
```

Script ini akan minta:
- `DISCORD_WEBHOOK_URL`
- `DISCORD_CHANNEL_ID` (opsional)

Kalau mau edit manual, file config ada di `.env`.

Script sekarang sudah bantu cegah error pemula seperti:
- webhook masih placeholder
- format webhook salah
- `python3` tidak ada tapi `python` ada
- install Chromium Playwright gagal tanpa pesan yang jelas

## Menjalankan Bot

### Test dulu tanpa kirim webhook

```bash
chmod +x preview.sh
./preview.sh
```

### Jalankan bot

```bash
./run.sh
```

### Cek environment kalau bingung

```bash
chmod +x doctor.sh
./doctor.sh
```

## Contoh Output

Discord akan menerima embed dengan isi seperti:

- `Grow a Garden Token Values`
- nama post sumber
- tanggal post
- link sumber
- daftar pet seperti:
  - `1. Kitsune`
  - `Rarity: Prismatic`
  - `Token: 825`

## File Penting

- [install.sh](/root/bot/install.sh): install dependency project
- [configure.sh](/root/bot/configure.sh): isi webhook dan channel ID
- [run.sh](/root/bot/run.sh): jalankan bot
- [preview.sh](/root/bot/preview.sh): test scraper dengan cepat
- [doctor.sh](/root/bot/doctor.sh): cek environment dan setup
- [termux.sh](/root/bot/termux.sh): setup Termux
- [scraper.py](/root/bot/scraper.py): logic scraping
- [notifier.py](/root/bot/notifier.py): format dan kirim webhook
- [LICENSE](/root/bot/LICENSE): lisensi project

## Catatan

- bot ini pakai Playwright + Chromium, jadi run pertama bisa agak berat
- di Termux, bagian yang paling rawan adalah install Chromium untuk Playwright
- kalau Fandom lagi agresif anti-bot, scraping bisa terasa lambat

## Troubleshooting

### Bot lambat

Normal untuk run pertama. Bot perlu:
- buka halaman search
- cek kandidat post
- parse data
- ambil rarity

Run berikutnya biasanya lebih cepat karena ada cache.

### Tidak kirim ke Discord

Cek:
- webhook benar
- internet aktif
- hasil `./preview.sh`
- hasil `./doctor.sh`

### Gagal install di Termux

Biasanya mentok di Playwright Chromium. Kalau itu terjadi, lebih aman jalankan bot di Linux biasa, VPS, atau proot distro.

### `./run.sh` langsung berhenti

Biasanya karena:
- `.env` belum ada
- webhook masih placeholder
- webhook belum diisi lewat `./configure.sh`
