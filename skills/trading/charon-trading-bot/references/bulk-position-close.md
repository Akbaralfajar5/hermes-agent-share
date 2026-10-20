# Bulk Position Close

## Problem

User has 17 open live positions and wants to close all at once. Individual manual closes via Telegram bot would take too long.

## Solution

Direct database update to mark all positions as `closed` with `exit_reason='manual_close_all'`. This is **fast** but does NOT:
- Execute actual swaps
- Calculate PnL
- Update wallet balance
- Remove tokens from wallet

Tokens remain in wallet after this operation. For actual liquidation, must swap manually via Phantom or Jupiter.

## Script Pattern

```javascript
const db = require('better-sqlite3')('/home/ubuntu/charon/charon.sqlite');

// Find all open live positions
const positions = db.prepare(`
  SELECT id, mint, symbol 
  FROM dry_run_positions 
  WHERE exit_price IS NULL 
  AND execution_mode = 'live'
`).all();

console.log(`Found ${positions.length} open positions to close`);

// Prepare update statement
const updateStmt = db.prepare(`
  UPDATE dry_run_positions 
  SET 
    status = 'closed',
    closed_at_ms = ?,
    exit_reason = 'manual_close_all',
    exit_price = NULL,
    exit_mcap = NULL,
    pnl_percent = NULL,
    pnl_sol = NULL
  WHERE id = ?
`);

// Close all
const now = Date.now();
let closed = 0;

for (const pos of positions) {
  updateStmt.run(now, pos.id);
  console.log(`✓ Closed position ${pos.id}: ${pos.symbol} (${pos.mint.slice(0, 8)}...)`);
  closed++;
}

console.log(`\n✅ Closed ${closed} positions`);
```

## Execution

Save script to `/tmp/close_all_positions.js`, then:

```bash
node /tmp/close_all_positions.js
```

**Note:** If running from `/tmp`, must use absolute path to `better-sqlite3`:
```javascript
const db = require('/home/ubuntu/charon/node_modules/better-sqlite3')('/home/ubuntu/charon/charon.sqlite');
```

## Verification

Check status field (not exit_price):

```bash
cd ~/charon && node -e "
const db = require('better-sqlite3')('charon.sqlite');
const open = db.prepare('SELECT COUNT(*) as count FROM dry_run_positions WHERE status = \\'open\\' AND execution_mode = \\'live\\'').get();
console.log('Open positions:', open.count);
"
```

Should return `0` after bulk close.

## When to Use

- User says "close all positions" or similar bulk action
- Bot has 10+ open positions and user wants to reset
- Emergency stop — close all positions immediately without waiting for exit conditions

## Limitations

1. **No actual swaps** — Tokens remain in wallet. User must manually swap via Phantom/Jupiter if they want SOL back.
2. **No PnL calculation** — `pnl_sol` and `pnl_percent` remain NULL. Cannot calculate profit/loss without exit prices.
3. **No wallet balance update** — Database `wallet_balance_sol` setting not updated. Must query Helius RPC separately.
4. **No transaction signatures** — `exit_signature` remains NULL. No on-chain record of close.

## Alternative: Actual Liquidation

For actual swaps with PnL tracking, must:
1. Query token balances from wallet
2. Build Jupiter swap for each token → SOL
3. Execute swaps via bot's swap router
4. Update database with actual exit prices and signatures

This is much slower (1-2 seconds per swap) but provides complete audit trail.

## Session Context

**Date:** May 16, 2026  
**User request:** "Close yg open posisi sekarang"  
**Positions closed:** 17 (IDs 77, 90, 102, 105, 108, 110, 115, 124, 126, 130, 133, 134, 135, 136, 137, 138, 139)  
**Entry sizes:** 16 positions @ 0.05 SOL, 1 position @ 0.2 SOL (total ~1.0 SOL locked)  
**Reason:** User wanted to reset bot state before applying new config (max_open_positions=1, entry_size=0.15 SOL, token_age_max=1h)
