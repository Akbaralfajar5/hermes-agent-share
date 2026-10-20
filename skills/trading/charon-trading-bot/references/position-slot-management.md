# Position Slot Management & Dry-Run→Live Migration

## Problem: max_open Limit Blocking Live Entries

When bot has `max_open=3` configured but 6 positions are holding (3 live + 3 migrated dry-run), the bot will skip all new signals with:
```
[agent] max positions reached (3/3), skipping <mint>...
```

This happens because:
1. Dry-run positions from earlier sessions get migrated to live mode
2. They remain in `dry_run_positions` table with `status='open'`
3. Bot counts them against the `max_open` limit
4. Live mode entry attempts fail silently (logged as `execution_failed` in `trade_intents`)

## Diagnosis

### Check Current Position Count

```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect('/home/ubuntu/charon/charon.sqlite')
c = conn.cursor()

# Count open dry-run positions
c.execute("SELECT COUNT(*) FROM dry_run_positions WHERE status='open'")
dry_run_open = c.fetchone()[0]

# Count live entry executions (successful entries)
c.execute("""
SELECT COUNT(DISTINCT selected_mint) 
FROM decision_logs 
WHERE verdict='live_entry_executed'
""")
live_open = c.fetchone()[0]

print(f"Dry-run open: {dry_run_open}")
print(f"Live open: {live_open}")
print(f"Total: {dry_run_open + live_open}")

# List them
print("\n=== DRY-RUN POSITIONS ===")
c.execute("""
SELECT id, mint, symbol, entry_price, opened_at_ms 
FROM dry_run_positions 
WHERE status='open'
ORDER BY opened_at_ms DESC
""")
for row in c.fetchall():
    pos_id, mint, symbol, entry_price, opened_at = row
    ts = datetime.fromtimestamp(opened_at/1000).isoformat()
    print(f"Pos {pos_id}: {symbol} ({mint[:8]}...) @ ${entry_price:.8f} | {ts}")

conn.close()
```

### Check Failed Live Attempts

```python
c.execute("""
SELECT id, mint, status, created_at_ms 
FROM trade_intents 
WHERE mode='live' AND status='execution_failed'
ORDER BY created_at_ms DESC 
LIMIT 5
""")

for row in c.fetchall():
    intent_id, mint, status, created_at = row
    ts = datetime.fromtimestamp(created_at/1000).isoformat()
    print(f"Intent {intent_id}: {mint[:12]}... | {status} | {ts}")
```

## Solution: Close Migrated Dry-Run Positions

When dry-run positions are blocking live slots, close them to free capacity:

```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect('/home/ubuntu/charon/charon.sqlite')
c = conn.cursor()

# Close all open dry-run positions
now_ms = int(datetime.now().timestamp() * 1000)
c.execute("""
UPDATE dry_run_positions 
SET status='closed', closed_at_ms=?, exit_reason='manual_close_to_free_live_slots'
WHERE status='open'
""", (now_ms,))

affected = c.rowcount
conn.commit()

print(f"✓ Closed {affected} dry-run positions")
print(f"✓ Live mode slots now freed")

conn.close()
```

Then restart bot to pick up the change:
```bash
pm2 restart charon
```

## Prevention: Separate Dry-Run & Live Tracking

**Recommended approach for future sessions:**
- Use separate tables or a `mode` column to distinguish dry-run from live positions
- Only count `execution_mode='live'` positions against `max_open` limit
- Keep dry-run positions in a separate tracking table that doesn't block live entries

Current bot may not support this yet — check with maintainer or patch locally if needed.

## Pitfall: Wallet Balance vs. Slot Limit

Don't confuse two different failure modes:

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `execution_failed` + "Insufficient SOL balance" | Wallet too low | Top-up wallet |
| `execution_failed` + "max positions reached (3/3)" | Slot limit hit | Close dry-run positions OR increase `max_open` |

Check logs to distinguish:
```bash
pm2 logs charon --lines 50 | grep -E "(Insufficient|max positions)"
```

## User Preference

User prefers to **focus live mode only** — when dry-run positions block live entries, close them immediately rather than increasing `max_open` or running both modes in parallel.
