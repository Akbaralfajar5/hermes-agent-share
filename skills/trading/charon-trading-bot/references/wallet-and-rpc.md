# Charon Wallet & RPC Configuration

## Wallet

- **Address**: `5j37jsGxkB5Zs5Hgfr1UdubHeBGTqzwCUgaAjQWxq2aq`
- **Current balance** (as of 2026-05-16 06:04 UTC): **0.3097 SOL**
- **Reserve**: 0.1 SOL (locked)
- **Available for trading**: 0.2097 SOL
- **Entry size per position**: 0.05 SOL
- **Max concurrent positions**: 3

## Helius RPC

- **API Key** (from `.env`): `7b9774eb-e198-4d5d-8756-3bfaf03505a0`
- **Endpoint**: `https://mainnet.helius-rpc.com/?api-key=7b9774eb-e198-4d5d-8756-3bfaf03505a0`
- **Method**: `getBalance` (returns lamports, divide by 1e9 for SOL)

### Query Example

```python
import requests

helius_key = "7b9774eb-e198-4d5d-8756-3bfaf03505a0"
rpc_url = f"https://mainnet.helius-rpc.com/?api-key={helius_key}"
wallet = "5j37jsGxkB5Zs5Hgfr1UdubHeBGTqzwCUgaAjQWxq2aq"

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getBalance",
    "params": [wallet]
}

response = requests.post(rpc_url, json=payload, timeout=10)
balance_lamports = response.json()['result']['value']
balance_sol = balance_lamports / 1e9

print(f"Balance: {balance_sol:.4f} SOL")
```

## Database

- **Path**: `~/charon/charon.sqlite`
- **Settings table**: Stores `wallet_balance_sol`, `wallet_balance_updated_at_ms`
- **Positions table**: `dry_run_positions` (filter by `execution_mode='live'` for live trades only)

## Live Mode Performance (as of 2026-05-16)

| Metric | Value |
|--------|-------|
| Total trades | 17 |
| Open positions | 0/3 |
| Closed positions | 17 |
| Win rate | 23.5% (4W / 5L) |
| Total PnL | +0.1859 SOL |
| Manual swaps | +0.0829 SOL (3 trades: HANSA, NUTZ, ANALYST) |
| Bot-managed | +0.1030 SOL (14 trades) |
| Best trade | PUFF +322% (+0.1610 SOL) |
| Avg PnL per trade | +21.87% |

## Strategy Config (Locked)

- **TP**: 75% (LOCKED - LLM cannot override)
- **SL**: -75% (LOCKED - LLM cannot override)
- **Trailing**: Enabled (35%)
- **Position size**: 0.05 SOL
- **Max open**: 3
- **LLM confidence threshold**: 60%
