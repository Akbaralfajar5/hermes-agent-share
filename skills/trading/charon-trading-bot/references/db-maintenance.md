# Charon SQLite Database Maintenance

## Key Facts

- **Active DB**: `~/charon/charon.sqlite` (NOT `charon.db` — that file is 0 bytes / empty)
- **DB engine**: better-sqlite3 (Node.js native binding)
- **sqlite3 CLI**: NOT installed on VPS — always use Node.js for DB operations
- **Disk**: VPS has 40G total, charon.sqlite can grow to 900MB+ if unmanaged

## Table Sizes (typical steady state)

| Table | Rows | Notes |
|---|---|---|
| signal_events | 300K+ | **Largest table** — grows ~80K/day |
| candidates | ~5K | Moderate growth |
| llm_decisions | ~2K | Moderate growth |
| llm_batches | ~1.7K | Moderate growth |
| decision_logs | ~1.7K | Moderate growth |
| dry_run_positions | varies | Stores BOTH dry-run AND live positions (misleading name) |
| dry_run_trades | varies | Trades linked to positions |
| trade_intents | ~86 | Slow growth |
| alerts | ~1.7K | Slow growth |
| learning_lessons | ~18 | Minimal |

## Pruning Script (Node.js)

Run via `node -e` in `~/charon` directory. Always use better-sqlite3, never sqlite3 CLI.

```js
const Database = require('better-sqlite3');
const db = new Database('./charon.sqlite');

// 1. Delete signal_events older than 3 days
const threeDaysAgo = Date.now() - (3 * 24 * 60 * 60 * 1000);
const del = db.prepare('DELETE FROM signal_events WHERE at_ms < ?').run(threeDaysAgo);
console.log('Deleted signal_events:', del.changes);

// 2. Delete dry-run data (if in live-only mode)
const dr1 = db.prepare('DELETE FROM dry_run_positions').run();
const dr2 = db.prepare('DELETE FROM dry_run_trades').run();
console.log('Deleted dry_run_positions:', dr1.changes, 'dry_run_trades:', dr2.changes);

// 3. Prune old candidates (keep last 1000)
const del2 = db.prepare("DELETE FROM candidates WHERE id NOT IN (SELECT id FROM candidates ORDER BY id DESC LIMIT 1000)").run();
console.log('Deleted old candidates:', del2.changes);

// 4. VACUUM to reclaim disk space (critical after large DELETEs)
console.log('Running VACUUM...');
db.pragma('wal_checkpoint(TRUNCATE)');
db.exec('VACUUM');
console.log('VACUUM done');

const pageCount = db.pragma('page_count')[0].page_count;
const pageSize = db.pragma('page_size')[0].page_size;
console.log('New DB size:', Math.round(pageCount*pageSize/1024/1024), 'MB');
db.close();
```

**Result from 2026-05-26 run**: 900MB → 374MB (freed 526MB)

## VACUUM is Critical

- `DELETE` does NOT reclaim disk space in SQLite — it only marks pages as free
- `VACUUM` rebuilds the entire DB file, reclaiming all free space
- Without VACUUM, the DB file stays at peak size forever
- VACUUM requires ~2x the DB size as temporary disk space
- Always run `PRAGMA wal_checkpoint(TRUNCATE)` before VACUUM

## Disk Space Monitoring

Check with `df -h /` — if >90%, prune immediately.

Other large dirs on VPS (as of 2026-05-26):
- `~/arc-agent`: 3.5G
- `~/SekaiDrama`: 847MB
- `~/my-app`: 657MB
- `~/my-site`: 582MB

Safe to delete if not in use: `base-airdrop-hunter`, `codebuddy-bot`, `giwa-testnet`, `backup-hermes`

## Common DB Queries

```js
const Database = require('better-sqlite3');
const db = new Database('./charon.sqlite');

// Count rows per table
const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all();
for (const {name} of tables) {
  const cnt = db.prepare('SELECT COUNT(*) as cnt FROM ' + name).get();
  if (cnt.cnt > 0) console.log(name + ':', cnt.cnt);
}

// Open positions (live or dry-run)
db.prepare("SELECT * FROM dry_run_positions WHERE status='open'").all();

// Recent trade intents
db.prepare('SELECT id, mint, status, side, size_sol FROM trade_intents ORDER BY id DESC LIMIT 10').all();

// DB size
const pageCount = db.pragma('page_count')[0].page_count;
const pageSize = db.pragma('page_size')[0].page_size;
console.log('DB size:', Math.round(pageCount*pageSize/1024/1024), 'MB');
```

## Stale Position Cleanup

If positions show "Insufficient funds" loop in logs:
1. The bot tries to sell but can't (wallet empty or token worthless)
2. These positions loop forever in `monitorPositions()`
3. Fix: either top up wallet or manually close positions in DB
4. After DB cleanup + restart, stale positions are cleared

## "database or disk is full" Error

- Symptom: charon logs show this error, bot may crash/restart
- Root cause: disk >95% full, usually from bloated signal_events
- Fix: prune + VACUUM + restart pm2
