# Hermes Agent — Share Pack

Setup **Hermes Agent** (persona + koleksi skills) yang sudah dibersihkan.
Tidak ada data pribadi, kredensial, database session, atau project pribadi di repo ini.

## Isi

| Path | Keterangan |
|------|------------|
| `SOUL.md` | Persona / operating instructions agent |
| `IDENTITY.md` | Identitas ringkas agent |
| `skills/` | Koleksi skills (siap pakai) |
| `config.example.yaml` | Contoh config minimal |
| `.env.example` | Daftar environment variable — isi sendiri |

## Cara pakai

> Panduan langkah-demi-langkah untuk VPS baru: **[INSTALL-VPS.md](INSTALL-VPS.md)**


1. **Install Hermes Agent** (official):
   ```bash
   git clone https://github.com/NousResearch/hermes-agent.git ~/.hermes/hermes-agent
   cd ~/.hermes/hermes-agent
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Copy persona + skills:**
   ```bash
   cp SOUL.md IDENTITY.md ~/.hermes/
   cp -r skills/* ~/.hermes/skills/
   ```

3. **Isi environment:**
   ```bash
   cp .env.example ~/.hermes/.env
   # edit ~/.hermes/.env — API keys, Telegram bot token, dll
   ```

4. **Config:** jalankan `hermes` sekali untuk wizard, atau contek
   `config.example.yaml` lalu `hermes config set <key> <value>`.

5. **Jalankan:**
   ```bash
   hermes chat          # CLI
   hermes gateway start # Telegram / platform lain
   ```

## Catatan sanitasi

- Tidak ada `.env`, API key, token, kredensial proxy, memory (`MEMORY.md`/`USER.md`),
  session DB, atau file project pribadi.
- Skills yang spesifik ke project pribadi dan tooling bypass tidak disertakan.
- Sebagian skill masih menyebut file referensi yang tidak ikut dibagikan —
  itu normal; skill tetap bisa dibaca dan dipakai.
