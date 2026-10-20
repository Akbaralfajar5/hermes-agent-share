# Panduan Install di VPS (dari nol sampai jalan)

Panduan lengkap buat teman yang mau pasang Hermes Agent + share pack ini di VPS.
Semua perintah copy-paste. Asumsi: VPS Ubuntu 22.04 / 24.04, akses root/sudo.

---

## 0. Spesifikasi VPS

| Komponen | Minimum | Rekomendasi |
|----------|---------|-------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 2 GB | 4 GB (browser automation butuh lebih) |
| Disk | 20 GB | 40 GB |
| OS | Ubuntu 22.04+ | Ubuntu 24.04 |

Cek disk dulu: `df -h` — Hermes + skills + browser ≈ 2–3 GB.

---

## 1. Install dependency sistem

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl wget build-essential sqlite3
```

Opsional — Node.js 22 (dibutuhkan sebagian skill, mis. x-twitter):

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## 2. Install Hermes Agent

### Cara A — script resmi (paling gampang)

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
source ~/.bashrc && hash -r
hermes --version
```

### Cara B — clone dari GitHub (kalau domain install diblokir)

```bash
git clone https://github.com/NousResearch/hermes-agent.git ~/.hermes/hermes-agent
cd ~/.hermes/hermes-agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

mkdir -p ~/.local/bin
ln -sf ~/.hermes/hermes-agent/venv/bin/hermes ~/.local/bin/hermes
source ~/.bashrc && hash -r
hermes --version
```

> Kalau `hermes: command not found`: `source ~/.bashrc && hash -r`, atau pakai
> path penuh `~/.hermes/hermes-agent/venv/bin/hermes`.

---

## 3. Ambil share pack (SOUL + skills)

```bash
git clone https://github.com/Akbaralfajar5/hermes-agent-share.git /tmp/hermes-share

cp /tmp/hermes-share/SOUL.md /tmp/hermes-share/IDENTITY.md ~/.hermes/
mkdir -p ~/.hermes/skills
cp -r /tmp/hermes-share/skills/* ~/.hermes/skills/
```

---

## 4. Isi environment (.env)

```bash
cp /tmp/hermes-share/.env.example ~/.hermes/.env
nano ~/.hermes/.env
```

Minimal yang wajib diisi:

| Variable | Isi |
|----------|-----|
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `OPENROUTER_API_KEY` | API key provider LLM (pilih salah satu) |
| `TELEGRAM_BOT_TOKEN` | Token bot dari @BotFather |
| `TELEGRAM_ALLOWED_USERS` | ID Telegram kamu (angka) |
| `TELEGRAM_HOME_CHANNEL` | ID chat tujuan notifikasi |

Kalau tidak pakai WhatsApp, pastikan:

```bash
WHATSAPP_ENABLED=false
```

(Kalau `true` tapi belum pairing, gateway bisa mati total saat startup.)

---

## 5. Setup model & cek kesehatan

```bash
hermes setup     # wizard interaktif: pilih provider + model + API key
# atau langsung:
hermes model

hermes doctor    # diagnosa instalasi
hermes status    # status komponen
```

---

## 6. Bikin bot Telegram

1. Chat **@BotFather** → `/newbot` → ikuti instruksi → simpan **token**.
2. Chat **@userinfobot** → catat **ID angka** kamu.
3. Masukkan keduanya ke `~/.hermes/.env` (langkah 4).

---

## 7. Jalankan gateway

```bash
hermes gateway setup     # pilih Telegram, tempel token
hermes gateway install   # pasang sebagai service systemd
hermes gateway start
hermes gateway status
```

Biar tetap hidup setelah SSH logout:

```bash
sudo loginctl enable-linger $USER
```

Alternatif untuk WSL/Docker (foreground): `hermes gateway run`.

---

## 8. Verifikasi

```bash
hermes --version
hermes doctor
hermes gateway status
```

Kirim pesan ke bot Telegram → harus dibalas.

---

## 9. Update Hermes

```bash
hermes update
```

Catatan: `hermes update` menimpa source Hermes, tapi **tidak** menyentuh
`~/.hermes/SOUL.md`, `~/.hermes/skills/`, dan `~/.hermes/.env`.

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `hermes: command not found` | `source ~/.bashrc && hash -r`, atau pakai `~/.hermes/hermes-agent/venv/bin/hermes` |
| `python3` versi < 3.10 | install python3.11/3.12 + `python3.12 -m venv` |
| Gateway mati setelah logout SSH | `sudo loginctl enable-linger $USER` |
| Gateway langsung exit saat start | cek `WHATSAPP_ENABLED=false` kalau WhatsApp belum dipairing |
| Disk penuh | `df -h`, bersihkan cache: `rm -rf ~/.cache/ms-playwright` (install ulang nanti) |
| Config nolak diedit manual | pakai `hermes config set <key> <value>` |
| `browser_navigate` gagal | `python3 -m playwright install chromium` lalu set `AGENT_BROWSER_EXECUTABLE_PATH` di `.env`, restart gateway dari shell luar |

---

## Struktur setelah install

```
~/.hermes/
├── SOUL.md          # persona
├── IDENTITY.md      # identitas agent
├── .env             # API keys & token (JANGAN di-commit)
├── config.yaml      # config Hermes
└── skills/          # koleksi skill dari share pack
```
