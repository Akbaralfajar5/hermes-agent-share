# Charon Step-by-Step Setup Guide

When user wants to set up Charon from scratch, guide them through each setting one at a time. This approach prevents errors and ensures user understands each configuration.

## Setup Order

### 1. Clone & Install
```bash
cd ~ && git clone https://github.com/yunus-0x/charon.git
cd charon && npm install
```

### 2. Environment Variables (ask one by one)

| Order | Variable | How to Get |
|-------|----------|------------|
| 1 | `TELEGRAM_BOT_TOKEN` | @BotFather → /newbot |
| 2 | `TELEGRAM_CHAT_ID` | Forward message to @userinfobot |
| 3 | `TELEGRAM_TOPIC_ID` | Optional, for forum groups |
| 4 | `SIGNAL_SERVER_KEY` | Contact @agentmeridian |
| 5 | `HELIUS_API_KEY` | https://helius.dev (free tier ok) |
| 6 | `SOLANA_PRIVATE_KEY` | Base58 format, dedicated trading wallet |
| 7 | `JUPITER_API_KEY` | https://portal.jup.ag |
| 8 | `LLM_API_KEY` | enowX, MiniMax, or OpenAI-compatible |

### 3. Trading Settings (ask preferences)

| Setting | Question | Options |
|---------|----------|---------|
| `TRADING_MODE` | Start with dry_run or live? | dry_run (recommended), confirm, live |
| `MAX_OPEN_POSITIONS` | How many positions max? | Default: 3, User chose: 10 |
| `GMGN_ENABLED` | Enable GMGN enrichment? | true/false |
| `BUY_AMOUNT_SOL` | SOL per trade? | 0.01-0.1 typical |
| `LIVE_MIN_SOL_RESERVE` | Min SOL to keep? | Default: 0.02 |

### 4. Exit Strategy

| Setting | Question | Example |
|---------|----------|---------|
| Partial TP % | At what profit trigger partial? | 30%, 50%, 100% |
| Partial Sell Ratio | Sell what % of position? | 30%, 50% |
| Trailing Stop % | Trailing from high? | 25%, 35% |
| Stop Loss % | Cut loss at? | -25%, -30% |
| Full TP | Fixed or unlimited? | null = unlimited |

### 5. Strategy Selection

Show user the 4 built-in strategies:
- **Sniper** — Fast entry, tight filters, 1h token age
- **Dip Buy** — Wait for -40% dip, 24h token age
- **Smart Money** — High holder requirements, 1000+ holders
- **Degen** — Loose filters, high risk/reward

User can switch via Telegram: `/strat` → select → enable

### 6. Start Bot

```bash
pm2 start npm --name "charon" -- start
pm2 logs charon --lines 30
```

### 7. Verify

- Check Telegram for startup message
- Send `/start` to bot
- Check `/status` and `/balance`

## Common Issues During Setup

1. **Terminal stuck after deleting charon folder** — Use `execute_code` with subprocess instead of terminal tool
2. **429 errors in logs** — Normal, auto-retry handles it
3. **LLM returns "I can't help"** — Prompt triggered safety filter, see `references/llm-prompt-pitfalls.md`

## Derived RPC URLs from Helius Key

```
SOLANA_RPC_URL=https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}
SOLANA_WS_URL=wss://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}
```

## Sample .env

```env
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
TELEGRAM_TOPIC_ID=

SIGNAL_SERVER_URL=https://api.thecharon.xyz/api
SIGNAL_SERVER_KEY=xxx
SIGNAL_POLL_MS=30000

HELIUS_API_KEY=xxx
SOLANA_RPC_URL=https://mainnet.helius-rpc.com/?api-key=xxx
SOLANA_WS_URL=wss://mainnet.helius-rpc.com/?api-key=xxx

GMGN_ENABLED=true
GMGN_API_KEY=xxx

DB_PATH=./charon.sqlite
TRADING_MODE=dry_run

SOLANA_PRIVATE_KEY=xxx
JUPITER_API_KEY=xxx
LIVE_MIN_SOL_RESERVE=0.1

ENABLE_LLM=true
LLM_BASE_URL=http://localhost:1430/v1
LLM_API_KEY=xxx
LLM_MODEL=claude-opus-4.5

MAX_OPEN_POSITIONS=10
BUY_AMOUNT_SOL=0.05
```
