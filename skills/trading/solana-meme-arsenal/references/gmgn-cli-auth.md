# GMGN CLI Auth & Trading Setup

## Auth Modes

| Mode | Endpoints | Headers |
|------|-----------|---------|
| **Exist** | token/*, market/*, portfolio info/activity/stats | `X-APIKEY` + `timestamp` + `client_id` |
| **Signed** | swap, order/*, portfolio holdings, follow_wallet | + `X-Signature` (Ed25519) |

## PEM Key Setup (Ed25519)

GMGN CLI uses `crypto.createPrivateKey(pem)` which requires PEM-encoded PKCS8 format.

### Generate fresh Ed25519 keypair:
```bash
openssl genpkey -algorithm Ed25519 -out ~/.config/gmgn/key.pem
chmod 600 ~/.config/gmgn/key.pem
```

### Convert Solana base58 key → PEM:
```javascript
const crypto = require('crypto');
const fs = require('fs');
const b58 = '<BASE58_PRIVATE_KEY>';

// Base58 decode
const ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
let num = BigInt(0);
for (const c of b58) num = num * BigInt(58) + BigInt(ALPHABET.indexOf(c));
const hex = num.toString(16).padStart(128, '0');
const raw = Buffer.from(hex, 'hex');
const seed = raw.slice(0, 32);

// PKCS8 DER for Ed25519
const prefix = Buffer.from('302e020100300506032b657004220420', 'hex');
const der = Buffer.concat([prefix, seed]);
const b64 = der.toString('base64');
const pem = `[REDACTED PRIVATE KEY]\n`;

fs.writeFileSync(process.env.HOME + '/.config/gmgn/key.pem', pem, {mode: 0o600});
```

### Derive Solana wallet from PEM:
```javascript
const key = crypto.createPrivateKey(pem);
const pub = crypto.createPublicKey(key);
const pubDer = pub.export({type: 'spki', format: 'der'});
const pubBytes = pubDer.subarray(pubDer.length - 32);
// Convert to base58 for Solana address
```

## .env Format (~/.config/gmgn/.env)

```
GMGN_API_KEY=<your_api_key>
GMGN_PRIVATE_KEY=<PEM content with \n escaped as \\n>
```

The CLI calls `replace(/\\n/g, "\n")` to restore newlines.

## Debugging

Set `GMGN_DEBUG=1` to see actual curl commands + signatures:
```bash
GMGN_DEBUG=1 gmgn-cli portfolio holdings --chain sol --wallet <ADDR> --limit 3
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `DECODER routines::unsupported` | Private key not PEM format | Convert base58 → PEM |
| `AUTH_SIGNATURE_INVALID` | Wallet not bound to API key | Check `portfolio info`, regenerate API key |
| `TRADE_WALLET_MISMATCH` | `--from` doesn't match binding | Use correct wallet address |
| `tip_fee is required` | Missing `--tip-fee` with `--condition-orders` | Add `--tip-fee 0.0001` |

## Wallet Binding

API keys are bound to specific wallets per chain. Check with:
```bash
gmgn-cli portfolio info
```

If binding is wrong:
1. Delete old API key at gmgn.ai/ai
2. Connect correct wallet
3. Generate new API key
4. Update ~/.config/gmgn/.env

Changing binding on existing key may NOT work — regenerate instead.

## Swap Command

```bash
gmgn-cli swap \
  --chain sol \
  --from <WALLET> \
  --input-token So11111111111111111111111111111111111111112 \
  --output-token <TOKEN_CA> \
  --amount <LAMPORTS> \
  --slippage 10 \
  --anti-mev \
  --priority-fee 0.001 \
  --tip-fee 0.0001 \
  --condition-orders '[{"order_type":"profit_stop","side":"sell","price_scale":"150","sell_ratio":"33"}]' \
  --raw
```

### condition-orders format:
- `price_scale`: percentage of entry price (150 = +50%, 50 = -50%)
- `sell_ratio`: percentage of position to sell
- `order_type`: `profit_stop` (fixed) or `profit_stop_trace` (trailing with `drawdown_rate`)
