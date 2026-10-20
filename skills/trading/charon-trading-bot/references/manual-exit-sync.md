# Manual Exit Sync Issues

## Problem

When a user manually closes a position via Phantom wallet (e.g., swapping tokens directly), the bot marks the position as `closed` with `exit_reason='manual_swap'` or `'MANUAL_CLOSE'`, but **exit price and PnL are not recorded** — they remain NULL in the database.

This causes:
- PnL shows as 0.0000 SOL / 0.0% (incorrect)
- Daily PnL calculations exclude these positions or show false zeros
- Audit scripts crash if they don't use `COALESCE()` on PnL fields

## Root Cause

The bot only records exit price and PnL when it **executes the exit** (via TP/SL/trailing stop). Manual exits bypass the bot's exit logic entirely — the user swaps directly in Phantom, and the bot only learns about it when it detects the position is gone from the wallet.

## Detection

Query for positions with NULL PnL:

```sql
SELECT id, symbol, exit_reason, closed_at_ms
FROM dry_run_positions
WHERE status='closed' AND execution_mode='live' 
  AND (pnl_sol IS NULL OR pnl_percent IS NULL)
ORDER BY closed_at_ms DESC;
```

Common `exit_reason` values for manual exits:
- `manual_swap` — user swapped via Phantom
- `MANUAL_CLOSE` — user closed position manually
- `manual_exit` — generic manual exit

## Solution

### Option 1: Calculate PnL from Wallet Balance Delta (Recommended)

When user reports manual exit, ask for:
1. **Entry price** (already in DB: `entry_price`)
2. **Exit price** (user provides or you look up from blockchain)
3. **Actual SOL received** (user can see in Phantom transaction)

Then update the position:

```python
import sqlite3

conn = sqlite3.connect('charon.sqlite')
c = conn.cursor()

# Example: Pos 130 HANSA manual swap
pos_id = 130
exit_price = 0.00002400  # user provides
exit_sol = 0.0520  # actual SOL received from swap

# Calculate PnL
entry_price = 0.00002606  # from DB
entry_sol = 0.05
entry_cost = entry_sol  # cost in SOL

exit_value = exit_sol  # value in SOL
pnl_sol = exit_value - entry_cost
pnl_percent = (pnl_sol / entry_cost) * 100

# Update DB
c.execute("""
UPDATE dry_run_positions
SET exit_price = ?, pnl_sol = ?, pnl_percent = ?
WHERE id = ?
""", (exit_price, pnl_sol, pnl_percent, pos_id))

conn.commit()
conn.close()

print(f"Pos {pos_id}: exit_price={exit_price}, pnl={pnl_sol:.4f}SOL ({pnl_percent:.1f}%)")
```

### Option 2: Mark as Unreconciled

If exit price is unknown, mark the position with a flag so it's excluded from PnL calculations:

```python
c.execute("""
UPDATE dry_run_positions
SET exit_reason = 'manual_swap_unreconciled'
WHERE id = ?
""", (pos_id,))
```

Then filter these out in audit queries:

```sql
WHERE status='closed' AND execution_mode='live' 
  AND exit_reason NOT LIKE '%unreconciled%'
```

## Audit Script Fix

Always use `COALESCE()` on PnL fields to prevent TypeError:

```python
c.execute("""
SELECT id, symbol, COALESCE(pnl_percent, 0), COALESCE(pnl_sol, 0), exit_reason, closed_at_ms
FROM dry_run_positions
WHERE status='closed' AND execution_mode='live'
ORDER BY closed_at_ms DESC
""")
```

And in aggregations:

```python
c.execute("""
SELECT 
  DATE(closed_at_ms / 1000, 'unixepoch') as trade_date,
  COUNT(*) as trade_count,
  SUM(CASE WHEN COALESCE(pnl_sol, 0) > 0 THEN 1 ELSE 0 END) as wins,
  SUM(CASE WHEN COALESCE(pnl_sol, 0) < 0 THEN 1 ELSE 0 END) as losses,
  SUM(COALESCE(pnl_sol, 0)) as daily_pnl
FROM dry_run_positions
WHERE status='closed' AND execution_mode='live'
GROUP BY trade_date
""")
```

## Current Status (May 16, 2026)

3 positions with NULL PnL from manual swaps:
- Pos 126: NUTZ (manual_swap @ 06:00:03)
- Pos 130: HANSA (manual_swap @ 06:00:03)
- Pos 133: ANALYST (manual_swap @ 06:00:03)

These need exit prices to be synced. User should provide actual SOL received from each swap, or we can look up exit prices from Solana blockchain if needed.
