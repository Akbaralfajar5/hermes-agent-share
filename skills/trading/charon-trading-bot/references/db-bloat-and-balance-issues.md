# Charon: DB Bloat & Insufficient Funds Diagnosis

## Symptoms
- Log spam: `[position] NNN Jupiter order failed: Insufficient funds`
- Log spam: `[server] database or disk is full`
- Bot still running (PM2 online) but unable to open OR close positions

## Root Causes

### 1. signal_events table bloat
`signal_events` accumulates every trending/graduated/fee_claim signal tick.
At ~30K rows/day it hits 300K+ rows in 10 days → DB file grows to ~900MB.
When disk hits ~89% full, SQLite can no longer write → "database or disk is full".

**Diagnosis:**
```js
const Database = require('better-sqlite3');
const db = new Database('charon.sqlite', {readonly: true});
const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all();
tables.forEach(t => {
  const count = db.prepare('SELECT COUNT(*) as c FROM ' + t.name).get();
  console.log(t.name + ':', count.c, 'rows');
});
// Check signal_events date range
const range = db.prepare('SELECT MIN(at_ms) as oldest, MAX(at_ms) as newest, COUNT(*) as total FROM signal_events').get();
console.log('oldest:', new Date(range.oldest).toISOString(), 'total:', range.total);
db.close();
```

**Fix — prune signal_events older than 3 days:**
```js
const Database = require('better-sqlite3');
const db = new Database('charon.sqlite');
const cutoff = Date.now() - (3 * 24 * 60 * 60 * 1000);
const result = db.prepare('DELETE FROM signal_events WHERE at_ms < ?').run(cutoff);
console.log('Deleted:', result.changes, 'rows');
db.prepare('VACUUM').run();
db.close();
```

**Expected result:** DB shrinks from ~900MB to ~50-100MB, disk usage drops significantly.

### 2. Insufficient SOL balance for Jupiter sell orders
Jupiter Ultra API requires SOL for:
- Transaction signature fee (~5000 lamports)
- Prioritization fee (~5000 lamports)
- Rent for token accounts (~2,039,280 lamports = ~0.002 SOL)

With balance < ~0.01 SOL, even SELL orders (which should return SOL) fail because
Jupiter needs to pay fees upfront before receiving proceeds.

**Check balance:**
```js
const { Connection, PublicKey, LAMPORTS_PER_SOL } = require('@solana/web3.js');
const conn = new Connection(process.env.SOLANA_RPC_URL);
conn.getBalance(new PublicKey('WALLET_ADDRESS'))
  .then(b => console.log('Balance:', b/LAMPORTS_PER_SOL, 'SOL'));
```

**Minimum viable balance:** ~0.05 SOL to execute sells on open positions.
**Recommended operating balance:** 0.5+ SOL (covers 2 positions at 0.2 SOL each + reserve).

The code enforces `LIVE_MIN_SOL_RESERVE_LAMPORTS` (default 0.02 SOL) only on BUY orders
(`src/execution/router.js:49`). SELL orders have NO balance guard — they fail at Jupiter API level.

## DB Schema Quick Reference
```
signal_events: id, mint, kind, at_ms, source, payload_json
  kind values: 'trending', 'graduated', 'fee_claim'
  
dry_run_positions: id, candidate_id, mint, symbol, status, execution_mode, ...
  status: 'open' | 'closed'
  execution_mode: 'live' | 'dry_run'

charon.sqlite  — main DB (can grow to 900MB+)
charon.db      — empty placeholder file (0 bytes), ignore
```

## Stuck Open Positions
Positions stuck as `status='open'` with repeated sell failures:
- Check `token_amount_raw` — if non-null, tokens are still in wallet
- Bot retries sell every signal cycle — this is expected behavior, not a crash
- Fix: restore SOL balance → sells will succeed on next retry

## Preventive Measures
Add a cron or periodic cleanup to prune signal_events:
```js
// Add to app.js or a maintenance cron
setInterval(() => {
  const cutoff = Date.now() - (3 * 24 * 60 * 60 * 1000);
  db.prepare('DELETE FROM signal_events WHERE at_ms < ?').run(cutoff);
}, 6 * 60 * 60 * 1000); // every 6 hours
```

Or add a DB size check alert when disk > 80%.
