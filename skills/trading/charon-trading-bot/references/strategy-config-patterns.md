# Charon Strategy Config Patterns

## Updating Strategy Config

Strategy config is stored in `strategies` table as JSON in `config_json` column.

```python
import sqlite3, json

con = sqlite3.connect('/home/ubuntu/charon/charon.sqlite')
con.row_factory = sqlite3.Row

# Read
row = con.execute("SELECT config_json FROM strategies WHERE id='ponyin_scalp'").fetchone()
cfg = json.loads(row['config_json'])

# Update
cfg['tp_percent'] = 0  # 0 = unlimited
cfg['sl_percent'] = -30
cfg['partial_tp'] = True
cfg['partial_tp_at_percent'] = 50
cfg['partial_tp_sell_percent'] = 50
cfg['trailing_enabled'] = True
cfg['trailing_percent'] = 35

con.execute("UPDATE strategies SET config_json=? WHERE id='ponyin_scalp'", (json.dumps(cfg),))
con.commit()
```

## Global Settings Sync

Strategy config and global settings can diverge. Always update both:

```python
# Global settings table
settings_updates = [
    ('default_tp_percent', '0'),
    ('default_sl_percent', '-30'),
    ('trailing_enabled', 'true'),
    ('trailing_percent', '35'),
    ('partial_tp', 'true'),
    ('partial_tp_at_percent', '50'),
    ('partial_tp_sell_percent', '50'),
]

for key, value in settings_updates:
    exists = con.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone()
    if exists:
        con.execute("UPDATE settings SET value=? WHERE key=?", (value, key))
    else:
        con.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
```

## Update Open Positions

Existing positions don't auto-inherit new strategy settings:

```python
con.execute("""
    UPDATE dry_run_positions 
    SET tp_percent = 0,
        sl_percent = -30,
        trailing_enabled = 1,
        trailing_percent = 35
    WHERE status = 'open'
""")
```

## Full Verification Check ("Cek Semuanya")

User often asks "cek semuanya" — run this comprehensive check:

```python
import sqlite3, json

con = sqlite3.connect('/home/ubuntu/charon/charon.sqlite')
con.row_factory = sqlite3.Row

print("=" * 50)
print("🔍 FULL CONFIG CHECK")
print("=" * 50)

# 1. Strategy Config
row = con.execute("SELECT config_json FROM strategies WHERE id='ponyin_scalp'").fetchone()
cfg = json.loads(row['config_json'])

checks = [
    ('partial_tp', True, cfg.get('partial_tp')),
    ('partial_tp_at_percent', 50, cfg.get('partial_tp_at_percent')),
    ('partial_tp_sell_percent', 50, cfg.get('partial_tp_sell_percent')),
    ('trailing_enabled', True, cfg.get('trailing_enabled')),
    ('trailing_percent', 35, cfg.get('trailing_percent')),
    ('tp_percent', 0, cfg.get('tp_percent')),  # 0 = unlimited
    ('sl_percent', -30, cfg.get('sl_percent')),
]

print("\n📋 STRATEGY CONFIG:")
for key, expected, actual in checks:
    status = "✅" if actual == expected else "❌"
    print(f"  {status} {key}: {actual} (expected: {expected})")

# 2. Global Settings
print("\n📋 GLOBAL SETTINGS:")
for key, expected, _ in checks:
    row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    actual = row['value'] if row else 'NOT SET'
    # Convert for comparison
    if expected is True:
        expected_str = 'true'
    elif expected is False:
        expected_str = 'false'
    else:
        expected_str = str(expected)
    status = "✅" if actual == expected_str else "❌"
    print(f"  {status} {key}: {actual} (expected: {expected_str})")

# 3. Open Positions
print("\n📋 OPEN POSITIONS:")
positions = con.execute("""
    SELECT id, symbol, tp_percent, sl_percent, trailing_enabled, trailing_percent
    FROM dry_run_positions WHERE status='open'
""").fetchall()

for p in positions:
    tp_ok = "✅" if p['tp_percent'] == 0 else "❌"
    sl_ok = "✅" if p['sl_percent'] == -30 else "❌"
    trail_ok = "✅" if p['trailing_enabled'] == 1 and p['trailing_percent'] == 35 else "❌"
    print(f"  {p['symbol']}: TP={tp_ok}{p['tp_percent']}% SL={sl_ok}{p['sl_percent']}% Trail={trail_ok}{p['trailing_percent']}%")
```

## Re-Entry Loop Issue

Bot may re-enter same token after position closes (SL/MAX_HOLD). This is NOT DCA — it's separate positions.

The duplicate check only prevents opening when position is OPEN:
```javascript
// src/db/positions.js line 47-50
const existing = db.prepare(`
  SELECT id FROM dry_run_positions WHERE mint = ? AND status = 'open' LIMIT 1
`).get(candidate.token.mint);
if (existing) return existing.id;
```

To prevent re-entry loops, implement cooldown in candidateBuilder.js:
```javascript
// Check if token had recent loss
const recentLoss = db.prepare(`
  SELECT id FROM dry_run_positions 
  WHERE mint = ? AND status = 'closed' 
  AND exit_reason IN ('SL', 'MAX_HOLD')
  AND closed_at_ms > ?
  LIMIT 1
`).get(mint, Date.now() - (4 * 60 * 60 * 1000)); // 4 hour cooldown

if (recentLoss) {
  return { passed: false, failures: ['cooldown: recent SL/loss within 4h'] };
}
```

## User Preferences (the user)

- Exit strategy: Partial TP +50% (sell 50%), trailing 35%, NO fixed TP (unlimited), SL -30%
- Priority: "amankan modal dulu" — partial TP should recover principal
- Wants cooldown/blacklist for tokens that hit SL to prevent re-entry loops
- Always restart PM2 after config changes: `pm2 restart charon --update-env`
