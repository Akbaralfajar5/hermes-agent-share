# Wallet Balance Query via Helius RPC

## Quick Reference

**Source of truth:** Helius RPC endpoint (configured in `.env`)

**Query method:** `getBalance` RPC call

**Conversion:** `balance_lamports / 1e9 = balance_sol`

## Implementation

### 1. Get Helius API Key from .env

```python
import os
from dotenv import load_dotenv

load_dotenv('/home/ubuntu/charon/.env')
helius_key = os.getenv('HELIUS_API_KEY')
rpc_url = f"https://mainnet.helius-rpc.com/?api-key={helius_key}"
```

### 2. Query Balance

```python
import requests

wallet = "5j37jsGxkB5Zs5Hgfr1UdubHeBGTqzwCUgaAjQWxq2aq"

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getBalance",
    "params": [wallet]
}

response = requests.post(rpc_url, json=payload, timeout=10)
data = response.json()

if 'result' in data:
    balance_lamports = data['result']['value']
    balance_sol = balance_lamports / 1e9
    print(f"Balance: {balance_sol:.4f} SOL")
else:
    print(f"Error: {data}")
```

### 3. Update Database

```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect('/home/ubuntu/charon/charon.sqlite')
c = conn.cursor()

now_ms = int(datetime.now().timestamp() * 1000)

c.execute("""
INSERT OR REPLACE INTO settings (key, value)
VALUES ('wallet_balance_sol', ?)
""", (str(balance_sol),))

c.execute("""
INSERT OR REPLACE INTO settings (key, value)
VALUES ('wallet_balance_updated_at_ms', ?)
""", (str(now_ms),))

conn.commit()
conn.close()
```

## Error Handling

### 401 Unauthorized
- **Cause:** Invalid or expired API key
- **Fix:** Check `.env` file for correct `HELIUS_API_KEY`
- **Fallback:** Ask user to provide balance manually

### Network Timeout
- **Cause:** RPC endpoint unreachable
- **Fix:** Retry with longer timeout (up to 30s)
- **Fallback:** Use last known balance from settings table

### Connection Error (Name Resolution)
- **Cause:** Network restricted (e.g., VPS without outbound HTTPS)
- **Fix:** Check if external API calls are allowed
- **Fallback:** Ask user to check wallet via Phantom/Solscan and provide balance

## Session Example (May 16, 2026)

**Pre-swap balance:** 0.2268 SOL  
**Post-swap balance:** 0.3097 SOL (after manual exit of HANSA, NUTZ, ANALYST)  
**Gain:** +0.0829 SOL (+36.55%)

Query executed at 06:03:55 UTC via Helius RPC successfully.
