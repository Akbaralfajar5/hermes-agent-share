# Manual Swap Sync Workflow

## Problem
When a user manually closes a position via Phantom wallet (outside the bot), the database marks it as `closed` but `exit_price` and `pnl_sol` remain NULL. This breaks audit reports and PnL calculations.

**Example (May 16, 2026):**
- Pos 126 (NUTZ): manual_swap @ 06:00:03 — exit_price NULL, pnl_sol NULL
- Pos 130 (HANSA): manual_swap @ 06:00:03 — exit_price NULL, pnl_sol NULL
- Pos 133 (ANALYST): manual_swap @ 06:00:03 — exit_price NULL, pnl_sol NULL

## Root Cause
Manual swaps via Phantom bypass the bot's exit logic. The bot detects the position is gone (via RPC balance check) and marks it closed, but has no exit price data.

## Solution: Manual Swap Sync

### Step 1: Identify NULL PnL Positions
```sql
SELECT id, symbol, exit_reason, closed_at_ms
FROM dry_run_positions
WHERE status='closed' AND execution_mode='live' 
  AND (pnl_sol IS NULL OR pnl_percent IS NULL)
ORDER BY closed_at_ms DESC;
```

### Step 2: Get Exit Amount from User or Phantom History
**Option A: User provides exit amount (SOL)**
```bash
python3 sync-manual-swaps.py <pos_id> <exit_sol>
# Example: python3 sync-manual-swaps.py 126 0.0776
```

**Option B: Query Phantom transaction history**
- Use Helius RPC `getSignaturesForAddress()` to find swap tx
- Parse tx details to extract exit token amount
- Calculate exit price: `exit_price = exit_sol / tokens_bought`

### Step 3: Calculate PnL
```python
entry_cost = 0.05  # SOL
exit_amount = 0.0776  # SOL (from swap)
pnl_sol = exit_amount - entry_cost  # +0.0276 SOL
pnl_percent = (pnl_sol / entry_cost) * 100  # +55.2%
```

### Step 4: Update Database
```sql
UPDATE dry_run_positions
SET exit_price = ?, pnl_sol = ?, pnl_percent = ?
WHERE id = ? AND execution_mode = 'live';
```

## Script: sync-manual-swaps.py
Located at `~/charon/sync-manual-swaps.py`. Usage:
```bash
python3 sync-manual-swaps.py 126 0.0776
# Output: ✅ Pos 126: NUTZ | Entry: 0.05 SOL @ $0.00001258 | Exit: 0.0776 SOL @ $0.00001953 | PnL: +0.0276 SOL (+55.2%)
```

## Audit Query (with COALESCE)
Always use COALESCE to handle NULL PnL in reports:
```sql
SELECT id, symbol, COALESCE(pnl_percent, 0), COALESCE(pnl_sol, 0), exit_reason
FROM dry_run_positions
WHERE status='closed' AND execution_mode='live'
ORDER BY closed_at_ms DESC;
```

## Prevention
- Monitor for manual exits: positions marked `closed` with `exit_reason='manual_swap'` but NULL PnL
- Alert user to provide exit prices immediately after manual swap
- Consider adding Phantom webhook listener to auto-capture exit prices in future
