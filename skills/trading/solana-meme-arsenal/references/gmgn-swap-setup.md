# GMGN CLI Swap Setup Guide

## Problem: Private Key Format

GMGN CLI v1.4.x uses Node.js `crypto.createPrivateKey()` which requires PEM or DER format.
Solana wallets use base58-encoded 64-byte keypairs — these MUST be converted to PEM.

**Error if wrong format:** `[gmgn-cli] error:1E08010C:DECODER routines::unsupported`

## Step 1: Convert base58 → PEM (PKCS8 Ed25519)

```python
import base58, base64, os

priv_b58 = "YOUR_BASE58_PRIVATE_KEY"
raw = base58.b58decode(priv_b58)
assert len(raw) == 64, f"Expected 64 bytes, got {len(raw)}"

# Verify wallet address
pubkey = base58.b58encode(raw[32:]).decode()
print(f"Wallet: {pubkey}")

# Build PKCS8 DER for Ed25519
secret = raw[:32]
pkcs8_prefix = bytes.fromhex("302e020100300506032b657004220420")
der = pkcs8_prefix + secret

# Convert to PEM
der_b64 = base64.b64encode(der).decode()
pem = "[REDACTED PRIVATE KEY]\n"

# Save
pem_path = os.path.expanduser("~/.config/gmgn/key.pem")
with open(pem_path, "w") as f:
    f.write(pem)
os.chmod(pem_path, 0o600)
```

## Step 2: Configure .env

```bash
mkdir -p ~/.config/gmgn
# Write .env with escaped newlines for PEM
python3 -c "
import os
pem_path = os.path.expanduser('~/.config/gmgn/key.pem')
with open(pem_path) as f:
    pem = f.read().strip()
api_key = 'YOUR_GMGN_API_KEY'
pem_escaped = pem.replace('\n', '\\\\n')
env_path = os.path.expanduser('~/.config/gmgn/.env')
with open(env_path, 'w') as f:
    f.write(f'GMGN_API_KEY=...)\n')
os.chmod(env_path, 0o600)
"
```

## Step 3: Verify Wallet Binding

```bash
# Check which wallets are bound to your API key
gmgn-cli portfolio info

# Output shows wallet per chain:
# sol: C3rCBouP47UVN7yEh9AJQgtpqzZ7enejRWqGD4PYrE9y
# If this doesn't match your wallet, rebind at https://gmgn.ai/ai
```

**Error if mismatch:** `HTTP 401 AUTH_SIGNATURE_INVALID`

## Step 4: Test Quote

```bash
gmgn-cli order quote \
  --chain sol \
  --from YOUR_WALLET \
  --input-token So11111111111111111111111111111111111111112 \
  --output-token TOKEN_CA \
  --amount 50000000 \
  --slippage 10
```

## Step 5: Execute Swap with TP/SL

```bash
gmgn-cli swap \
  --chain sol \
  --from YOUR_WALLET \
  --input-token SOL \
  --output-token TOKEN_CA \
  --amount 100000000 \
  --slippage 10 \
  --anti-mev \
  --priority-fee 0.001 \
  --condition-orders '[{"order_type":"profit_stop","side":"sell","price_scale":"150","sell_ratio":"50"},{"order_type":"profit_stop","side":"sell","price_scale":"300","sell_ratio":"100"}]'
```

## Condition Orders Reference

| Field | Description |
|-------|-------------|
| order_type | `profit_stop` (fixed TP) or `profit_stop_trace` (trailing) |
| side | `sell` |
| price_scale | % of entry price (150 = +50%, 200 = +100%) |
| sell_ratio | % of position to sell at this level |
| drawdown_rate | (trace only) % drawdown from peak to trigger |

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `DECODER routines::unsupported` | Private key not PEM format | Convert base58 → PEM |
| `AUTH_SIGNATURE_INVALID` | Wallet not bound to API key | Rebind at gmgn.ai/ai |
| `required option '--slippage'` | Missing slippage on quote | Add `--slippage N` |
| `RATE_LIMIT_BANNED` | Too many requests | Wait for reset_at timestamp |
