# Hybrid Partial TP + Trailing Strategy

A risk-managed exit strategy that secures principal (modal) first, then lets remaining position ride for bigger gains.

## Concept

Instead of choosing between fixed TP or trailing stop, use both:
1. **Partial TP** at moderate gain → sell enough to recover entry (modal aman)
2. **Trailing stop** on remainder → free ride for potential moonshot

## Recommended Settings (User Preferred)

```python
# Strategy config — user's preferred "amankan modal" setup
cfg['partial_tp'] = True
cfg['partial_tp_at_percent'] = 50      # trigger at +50%
cfg['partial_tp_sell_percent'] = 50    # sell 50%
cfg['trailing_enabled'] = True
cfg['trailing_percent'] = 35           # trailing exit trigger
cfg['tp_percent'] = 0                  # UNLIMITED — no final TP cap
cfg['sl_percent'] = -30                # stop loss
```

**Key insight**: User prefers `tp_percent = 0` (unlimited) because trailing handles the exit. No need for fixed TP cap — let winners run.

## Alternative: Conservative 75% Sell

```python
# More conservative — secure more principal
cfg['partial_tp_at_percent'] = 35      # trigger earlier at +35%
cfg['partial_tp_sell_percent'] = 75    # sell 75% to fully secure modal
cfg['trailing_percent'] = 25           # tighter trailing
cfg['tp_percent'] = 100                # optional final TP cap
```

## Math Behind 50% Sell at +50%

At +50% gain:
- Entry: 0.05 SOL
- Value: 0.05 × 1.50 = 0.075 SOL
- Sell 50%: 0.075 × 0.50 = **0.0375 SOL** (75% of modal secured)
- Remaining: 0.075 × 0.50 = 0.0375 SOL (free ride)

Note: 50% sell at +50% secures 75% of modal. For full modal recovery, need 67% sell at +50%.

## Math Behind 75% Sell at +35%

At +35% gain:
- Entry: 0.05 SOL
- Value: 0.05 × 1.35 = 0.0675 SOL
- Sell 75%: 0.0675 × 0.75 = **0.0506 SOL** (modal + tiny profit)
- Remaining: 0.0675 × 0.25 = 0.0169 SOL (free ride)

## Flow Example

```
1. Entry 0.05 SOL at $20k mcap
2. Price pumps +35% → mcap $27k
3. Partial TP triggers:
   - Sell 75% → get ~0.05 SOL back (modal secured)
   - Keep 25% → ~0.017 SOL riding
4. Scenarios:
   a) Dumps 25% → trailing triggers → exit with modal + small profit
   b) Pumps to +100% → final TP or keep trailing → modal + 2x on remainder
   c) Moonshot 5x → trailing rides it → modal + massive bonus
```

## Why This Works for Meme Coins

- Meme coins are volatile — 50%+ dumps in minutes are common
- Fixed TP misses moonshots; pure trailing gets stopped on wicks
- Hybrid approach: **never lose principal** after +35%, but still catch runners

## Implementation

### Update Strategy Config
```python
import sqlite3, json

con = sqlite3.connect('/home/ubuntu/charon/charon.sqlite')
con.row_factory = sqlite3.Row
row = con.execute("SELECT config_json FROM strategies WHERE id='ponyin_scalp'").fetchone()
cfg = json.loads(row['config_json'])

# User's preferred settings
cfg['partial_tp'] = True
cfg['partial_tp_at_percent'] = 50      # +50% trigger
cfg['partial_tp_sell_percent'] = 50    # sell 50%
cfg['trailing_enabled'] = True
cfg['trailing_percent'] = 35           # 35% trailing exit
cfg['tp_percent'] = 0                  # UNLIMITED (no cap)
cfg['sl_percent'] = -30

con.execute("UPDATE strategies SET config_json=? WHERE id='ponyin_scalp'", (json.dumps(cfg),))
con.commit()
```

### Update Global Settings (for new positions)
```python
updates = [
    ('default_tp_percent', '0'),       # unlimited
    ('default_sl_percent', '-30'),
    ('trailing_enabled', 'true'),
    ('trailing_percent', '35'),
    ('partial_tp', 'true'),
    ('partial_tp_at_percent', '50'),
    ('partial_tp_sell_percent', '50'),
]

for key, value in updates:
    exists = con.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone()
    if exists:
        con.execute("UPDATE settings SET value=? WHERE key=?", (value, key))
    else:
        con.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
con.commit()
```

### Update Existing Open Positions
```python
con.execute("""
    UPDATE dry_run_positions 
    SET tp_percent = 0,
        sl_percent = -30,
        trailing_enabled = 1,
        trailing_percent = 35
    WHERE status = 'open'
""")
con.commit()
```

### Restart Bot
```bash
pm2 restart charon --update-env
```

## Verification Checklist

After setting, verify ALL three locations are synced:
1. **Strategy config** (`strategies.config_json`)
2. **Global settings** (`settings` table)
3. **Open positions** (`dry_run_positions` — update existing)

User often says "cek lagi semuanya biasanya belum ke setting" — always verify all three.

**Quick verification script**: `scripts/verify_settings.py`
```bash
python3 ~/.hermes/skills/trading/charon-trading-bot/scripts/verify_settings.py
```

## Variations

| Risk Level | Partial TP | Sell % | Trailing | Final TP | Notes |
|------------|------------|--------|----------|----------|-------|
| Conservative | +35% | 75% | 25% | 100% | Secure modal fully, capped upside |
| **User Default** | **+50%** | **50%** | **35%** | **∞** | Balanced risk, unlimited upside |
| Aggressive | +75% | 40% | 40% | ∞ | Max exposure, ride moonshots |

**User philosophy**: "amankan modal dulu" (secure principal first) — but with unlimited upside via trailing, no TP cap.

## Pitfall: Settings Not Applied

Common issue: strategy config updated but global settings or open positions not synced.

**Always update all three:**
1. `strategies.config_json` — affects new positions from strategy
2. `settings` table — affects manual buys and defaults
3. `dry_run_positions` — affects already-open positions
