# Charon .env Setup Checklist

Interactive step-by-step credential gathering for fresh Charon installs.

## Order of Setup (ask user one-by-one)

### 1. TELEGRAM_BOT_TOKEN
- Get from @BotFather → `/newbot` or `/token`
- Format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### 2. TELEGRAM_CHAT_ID
- Private chat: forward message to @userinfobot
- Group: add bot, send message, check ID
- Format: numeric (e.g., `<telegram_user_id>`)

### 3. TELEGRAM_TOPIC_ID (optional)
- Only needed for Forum groups with topics
- Skip for private chats or regular groups

### 4. SIGNAL_SERVER_KEY
- Contact @agentmeridian on Telegram
- Required for Pump.fun signal feed
- Format: 48-char hex string

### 5. HELIUS_API_KEY
- Get from https://helius.dev (free tier available)
- Required for Solana RPC
- Format: UUID `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### 6. SOLANA_PRIVATE_KEY
- ⚠️ Use dedicated trading wallet, NOT main wallet
- Format: Base58 (NOT hex like EVM)
- Get from Phantom export or `solana-keygen new`

### 7. JUPITER_API_KEY
- Get from https://portal.jup.ag
- Optional for dry_run, required for live trading
- Format: `jup_` prefix + hex

### 8. LLM Config (3 values)
Ask which provider:
- **enowX (local)**: `http://localhost:1430/v1` or `http://43.159.56.39:1430/v1`
- **MiniMax (default)**: `https://api.minimax.io/v1`
- **OpenAI**: `https://api.openai.com/v1`

Then set:
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL` (e.g., `claude-opus-4.5`, `MiniMax-M2.7`, `gpt-4o`)

### 9. TRADING_MODE
- `dry_run` — Simulation only (start here)
- `confirm` — Manual confirmation per trade
- `live` — Full auto execution

### 10. MAX_OPEN_POSITIONS
- Default: 3
- More = diversified but spread thin
- Less = focused but may miss opportunities

## After Setup

```bash
# Create .env from collected values
cat > /home/ubuntu/charon/.env << 'EOF'
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
# ... rest of values
EOF

# Start bot
cd ~/charon && pm2 start npm --name charon -- start
```

## Switching to Live Mode

When user is ready:
1. Ensure wallet has SOL for trading + gas
2. Update `.env`: `TRADING_MODE=live`
3. Restart: `pm2 restart charon`
