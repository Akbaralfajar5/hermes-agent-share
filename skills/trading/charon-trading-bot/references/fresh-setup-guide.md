# Charon Fresh Setup Guide

Step-by-step setup untuk Charon dari nol. Tanyakan user satu-satu, jangan sekaligus.

## Pre-requisites

```bash
# Node.js v20+
node -v

# Clone repo
cd ~ && git clone https://github.com/yunus-0x/charon.git
cd charon && npm install
```

## Setup Flow (Step by Step)

### 1. TELEGRAM_BOT_TOKEN
- Buka @BotFather di Telegram
- `/newbot` → kasih nama → kasih username
- Copy token format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### 2. TELEGRAM_CHAT_ID
- Chat ID tujuan notifikasi
- Private chat: forward pesan ke @userinfobot
- Group: tambah bot ke group, kirim pesan, cek ID

### 3. TELEGRAM_TOPIC_ID (optional)
- Hanya untuk Forum/Group dengan Topics
- Kosongkan jika private chat

### 4. SIGNAL_SERVER_KEY
- API key dari https://api.thecharon.xyz
- Contact @agentmeridian di Telegram

### 5. HELIUS_API_KEY
- Dari https://helius.dev (gratis tier available)
- Buat project → copy API key

### 6. SOLANA_PRIVATE_KEY
- Private key wallet Solana untuk trading
- Format Base58 (bukan hex)
- ⚠️ Pakai wallet khusus, bukan wallet utama!

### 7. JUPITER_API_KEY
- Dari https://portal.jup.ag
- Optional untuk dry_run, wajib untuk live

### 8. LLM Config
Options:
- **enowX (lokal)**: `http://localhost:1430/v1` + key
- **MiniMax**: Default Charon, model M2.7
- **OpenAI/Anthropic**: Direct API

### 9. TRADING_MODE
- `dry_run` — Simulasi (recommended untuk testing)
- `confirm` — Perlu konfirmasi manual
- `live` — Full otomatis

### 10. MAX_OPEN_POSITIONS
- Default: 3
- Lebih banyak = modal tersebar
- Lebih sedikit = lebih fokus

### 11. GMGN Config
- `GMGN_ENABLED=true/false`
- `GMGN_API_KEY=gmgn_...`
- Note: GMGN API sering blocked Cloudflare

### 12. Exit Strategy
- `PARTIAL_TP_PERCENT` — Trigger partial TP di +X%
- `PARTIAL_TP_SELL_RATIO` — Jual X% posisi
- `TRAILING_STOP_PERCENT` — Trailing dari high
- `STOP_LOSS_PERCENT` — Cut loss di -X%

### 13. BUY_AMOUNT_SOL
- SOL per trade
- 0.01-0.05 untuk testing
- 0.1+ untuk live

### 14. LIVE_MIN_SOL_RESERVE
- Minimum SOL tetap di wallet
- Default: 0.02 SOL
- Untuk fee transaksi

## .env Template

```bash
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TELEGRAM_TOPIC_ID=

SIGNAL_SERVER_URL=https://api.thecharon.xyz/api
SIGNAL_SERVER_KEY=
SIGNAL_POLL_MS=30000

HELIUS_API_KEY=
SOLANA_RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_KEY
SOLANA_WS_URL=wss://mainnet.helius-rpc.com/?api-key=YOUR_KEY

GMGN_ENABLED=true
GMGN_API_KEY=
GMGN_REQUEST_DELAY_MS=2500
GMGN_MAX_RETRIES=2
GMGN_CACHE_TTL_MS=300000

DB_PATH=./charon.sqlite
TRADING_MODE=dry_run

SOLANA_PRIVATE_KEY=
JUPITER_API_KEY=
JUPITER_SWAP_BASE_URL=https://api.jup.ag/swap/v2
LIVE_MIN_SOL_RESERVE=0.1

ENABLE_LLM=true
LLM_BASE_URL=http://localhost:1430/v1
LLM_API_KEY=
LLM_MODEL=claude-opus-4.5
LLM_TIMEOUT_MS=60000
LLM_CANDIDATE_PICK_COUNT=10
LLM_CANDIDATE_MAX_AGE_MS=600000

MAX_OPEN_POSITIONS=10
BUY_AMOUNT_SOL=0.05

PARTIAL_TP_PERCENT=30
PARTIAL_TP_SELL_RATIO=0.3
TRAILING_STOP_PERCENT=35
STOP_LOSS_PERCENT=30

MIN_FEE_CLAIM_SOL=2
GRADUATED_POLL_MS=30000
GRADUATED_LOOKBACK_MS=7200000
TRENDING_POLL_MS=60000
TRENDING_LOOKBACK_MS=600000
TRENDING_ENABLED=true
TRENDING_SOURCE=jupiter
TRENDING_ALLOW_DEGEN=false
TRENDING_INTERVAL=5m
TRENDING_LIMIT=100
TRENDING_ORDER_BY=volume
TRENDING_MIN_VOLUME_USD=0
TRENDING_MIN_SWAPS=0
TRENDING_MAX_RUG_RATIO=0.3
TRENDING_MAX_BUNDLER_RATE=0.5
POSITION_CHECK_MS=10000
```

## Start Bot

```bash
# Direct
npm start

# PM2 (recommended)
pm2 start npm --name "charon" -- start
pm2 save

# Check logs
pm2 logs charon --lines 50
```

## Post-Setup

1. Kirim `/start` ke bot Telegram
2. Cek `/status` dan `/balance`
3. Pilih strategy via `/strat`
4. Monitor candidates di log

## Troubleshooting

**429 Too Many Requests:**
- Normal, auto-retry
- Increase `GMGN_REQUEST_DELAY_MS` if persistent

**Wallet not loaded:**
- Check `SOLANA_PRIVATE_KEY` format (Base58)
- Verify key is valid

**No candidates passing:**
- Filters terlalu ketat
- Adjust strategy settings via Telegram
