# Database-Blockchain Sync Workflow

## Problem

Positions can be closed in the bot/wallet but the database may not have complete exit data recorded. Symptoms:

- Position marked `status='closed'` but `exit_price=NULL`, `pnl_percent=NULL`, `pnl_sol=NULL`
- User reports position closed in bot UI but DB shows no SELL trades
- No exit records in `decision_logs` or `dry_run_trades`
- Manual swaps (user exits via Phantom) don't auto-sync to DB

## Diagnosis Sequence

**Do NOT ask the user for data.** Query autonomously in this order:

### 1. Check for exit trades in DB

```sql
SELECT * FROM dry_run_trades
WHERE position_id=? AND side='SELL'
ORDER BY at_ms DESC;
```

If rows exist → exit was recorded. Extract `price` and `mcap` for PnL calculation.

### 2. Check decision_logs for exit actions

```sql
SELECT id, action, verdict, at_ms, execution_json
FROM decision_logs
WHERE selected_mint=? AND (action='SELL' OR verdict LIKE '%exit%')
ORDER BY at_ms DESC
LIMIT 5;
```

Parse `execution_json` for `exit_price`, `exit_mcap`, `signature`.

### 3. Check TP/SL rules

```sql
SELECT tp_percent, sl_percent, trailing_enabled, trailing_percent
FROM tp_sl_rules
WHERE position_id=?;
```

This tells you what exit conditions were configured. If position hit SL or TP, it should have exited.

### 4. If no exit records found

User likely exited manually (via Phantom/Solscan). **Do NOT guess exit prices.** Instead:

- Mark position as `status='closed'` with `exit_reason='manual_swap'` or `'synced_from_bot_state'`
- Set `closed_at_ms=NOW()`
- Leave `exit_price=NULL`, `pnl_percent=NULL`, `pnl_sol=NULL` (or ask user for actual exit price if needed for audit)

## Fix Workflow

### For positions with no exit data but user confirms closed:

```sql
UPDATE dry_run_positions
SET status='closed', 
    closed_at_ms=?,
    exit_reason='manual_swap'
WHERE id=?;
```

### For positions with exit trades but missing PnL:

```sql
-- Get exit price from trades
SELECT price FROM dry_run_trades
WHERE position_id=? AND side='SELL'
ORDER BY at_ms DESC LIMIT 1;

-- Calculate PnL
-- pnl_percent = ((exit_price - entry_price) / entry_price) * 100
-- pnl_sol = size_sol * (exit_price - entry_price) / entry_price

UPDATE dry_run_positions
SET exit_price=?,
    exit_mcap=?,
    pnl_percent=?,
    pnl_sol=?
WHERE id=?;
```

### For manual swaps with known exit price (user provides):

```sql
UPDATE dry_run_positions
SET status='closed',
    closed_at_ms=?,
    exit_price=?,
    exit_mcap=?,
    pnl_percent=?,
    pnl_sol=?,
    exit_reason='manual_swap'
WHERE id=?;
```

## Wallet Balance Query (RPC)

When syncing, also update wallet balance from Helius RPC:

```python
import requests

helius_key = "7b9774eb-e198-4d5d-8756-3bfaf03505a0"  # from .env
rpc_url = f"https://mainnet.helius-rpc.com/?api-key={helius_key}"
wallet = "5j37jsGxkB5Zs5Hgfr1UdubHeBGTqzwCUgaAjQWxq2aq"

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getBalance",
    "params": [wallet]
}

response = requests.post(rpc_url, json=payload, timeout=10)
data = response.json()
balance_lamports = data['result']['value']
balance_sol = balance_lamports / 1e9

# Update DB
# INSERT OR REPLACE INTO settings (key, value) VALUES ('wallet_balance_sol', str(balance_sol))
```

## Key Rules

1. **Query first, ask never** — User preference: "Kamu harusnya bisa cek sendiri". Use DB and RPC queries before asking for data.
2. **Don't guess exit prices** — Only update `exit_price` if you have it from trades, decision_logs, or user provides it. NULL is acceptable for manual swaps.
3. **Mark sync source** — Use `exit_reason='synced_from_bot_state'` or `'manual_swap'` to indicate how the position was closed.
4. **Update wallet balance** — After syncing positions, query Helius RPC for current SOL balance and update settings table.
5. **Restart bot if needed** — If you modify strategy config or code, restart bot after DB updates.

## Example Session Flow

```
User: "Audit live mode"
→ Query open/closed positions
→ Find 3 closed positions with NULL exit_price
→ Query decision_logs for exit records → none found
→ Query dry_run_trades for SELL → none found
→ User confirms: "Sudah gw swap dulu bro" (I already swapped them)
→ Mark all 3 as closed with exit_reason='manual_swap'
→ Query Helius for wallet balance → 0.3097 SOL
→ Update settings table with balance
→ Report: "3 positions closed (manual swap), wallet 0.3097 SOL, ready for new entries"
```
