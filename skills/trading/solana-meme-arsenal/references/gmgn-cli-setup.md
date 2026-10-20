# GMGN CLI Setup Guide

## Full Setup Walkthrough

### Step 1: Install CLI
```bash
npm install -g gmgn-cli
```

### Step 2: Generate Ed25519 Key Pair
```bash
# Option A: OpenSSL (generates PEM directly)
openssl genpkey -algorithm Ed25519 -out ~/.config/gmgn/key.pem
chmod 600 ~/.config/gmgn/key.pem

# Option B: Convert existing Solana base58 key to PEM
```

### Step 3: Create GMGN API Key
1. Go to https://gmgn.ai/ai
2. Connect your Solana wallet (Phantom/Solflare)
3. Generate API Key
4. Copy the key

### Step 4: Configure .env
```bash
mkdir -p ~/.config/gmgn

# Write .env (PEM newlines must be escaped as \\n for single-line format)
# Use Node.js to do this correctly:
node -e "
const fs = require('fs');
const pem = fs.readFileSync('key.pem', 'utf-8').trim();
const escaped = pem.replace(/\n/g, '\\\\n');
const env = 'GMGN_API_KEY=<YOUR_KEY>\nGMGN_PRIVATE_KEY=' + escaped + '\n';
fs.writeFileSync(process.env.HOME + '/.config/gmgn/.env', env, {mode: 0o600});
"

chmod 600 ~/.config/gmgn/.env
```

### Step 5: Verify
```bash
# Test exist auth (should show bound wallets)
gmgn-cli portfolio info

# Test signed auth (should return holdings or empty list, NOT error)
gmgn-cli portfolio holdings --chain sol --wallet <YOUR_WALLET> --limit 3

# Test quote
gmgn-cli order quote --chain sol --from <YOUR_WALLET> \
  --input-token So11111111111111111111111111111111111111112 \
  --output-token <TOKEN_CA> \
  --amount 50000000 --slippage 10
```

### Step 6: Debug (if needed)
```bash
# Show actual curl command with signature
GMGN_DEBUG=1 gmgn-cli portfolio holdings --chain sol --wallet <WALLET> --limit 1

# Check .env contents
cat ~/.config/gmgn/.env | head -c 50  # API key
grep "BEGIN" ~/.config/gmgn/.env      # Has PEM?

# Verify PEM signs correctly
node -e "
const crypto = require('crypto');
require('dotenv').config({path: require('path').join(process.env.HOME, '.config/gmgn/.env')});
const pem = process.env.GMGN_PRIVATE_KEY.replace(/\\\\n/g, '\n');
const key = crypto.createPrivateKey(pem);
console.log('Type:', key.asymmetricKeyType);
const sig = crypto.sign(null, Buffer.from('test'), pem);
console.log('Sign OK:', sig.length, 'bytes');
"
```

## Swap Command Reference

```bash
# Buy token (SOL → Token)
gmgn-cli swap \
  --chain sol \
  --from <WALLET> \
  --input-token So11111111111111111111111111111111111111112 \
  --output-token <TOKEN_CA> \
  --amount <LAMPORTS> \
  --slippage 10 \
  --anti-mev \
  --priority-fee 0.001

# Sell token (Token → SOL)
gmgn-cli swap \
  --chain sol \
  --from <WALLET> \
  --input-token <TOKEN_CA> \
  --output-token So11111111111111111111111111111111111111112 \
  --percent 100 \
  --slippage 10

# Buy with auto TP/SL
gmgn-cli swap \
  --chain sol \
  --from <WALLET> \
  --input-token So11111111111111111111111111111111111111112 \
  --output-token <TOKEN_CA> \
  --amount 50000000 \
  --slippage 10 \
  --condition-orders '[{"order_type":"profit_stop","side":"sell","price_scale":"150","sell_ratio":"50"},{"order_type":"profit_stop","side":"sell","price_scale":"300","sell_ratio":"100"}]'

# Multi-wallet swap (up to 100 wallets)
gmgn-cli multi-swap --help
```

## condition-orders Format

```json
// Take profit at 150% price, sell 50% of position
{"order_type":"profit_stop","side":"sell","price_scale":"150","sell_ratio":"50"}

// Trailing stop with 50% drawdown
{"order_type":"profit_stop_trace","side":"sell","price_scale":"150","sell_ratio":"100","drawdown_rate":"50"}

// Stop loss (sell all at 50% of buy price)
{"order_type":"profit_stop","side":"sell","price_scale":"50","sell_ratio":"100"}
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `DECODER routines::unsupported` | Private key in base58, not PEM | Convert to PEM format |
| `AUTH_SIGNATURE_INVALID` | Wallet not bound to API key | Bind wallet on gmgn.ai or regenerate API key |
| `TRADE_WALLET_MISMATCH` | `--from` ≠ bound wallet | Use correct wallet address |
| Rate limit (429) | >20 req/min | Wait for X-RateLimit-Reset header |
