# Profit Lock Implementation Status (May 2026)

## CRITICAL: Profit Lock Config-Only, Not Implemented in Code

**Status:** `use_profit_lock`, `profit_lock_tiers` fields exist in strategy `config_json` but are **NOT read or used by the execution engine**.

### What Does NOT Work

- Setting `use_profit_lock: true` in strategy config does nothing
- `profit_lock_tiers` array is ignored
- No `PROFIT_LOCK` exit reason is ever generated
- No floor-based exit logic exists in `src/execution/positions.js`

### What Actually Happens

When you configure:
```json
{
  "use_profit_lock": true,
  "profit_lock_tiers": [
    { "threshold": 30, "floor": 10 },
    { "threshold": 80, "floor": 60 }
  ],
  "tp_percent": 9999,
  "sl_percent": -30
}
```

The bot **ignores profit lock entirely** and only uses:
- `partial_tp` + `partial_tp_at_percent` + `partial_tp_sell_percent` (works)
- `sl_percent` (works)
- `tp_percent` as trailing arm threshold (works if `trailing_enabled: true`)

### Exit Reasons That Actually Exist

- `SL` — pnl ≤ sl_percent
- `TP` — pnl ≥ tp_percent (only if trailing disabled)
- `TRAILING_TP` — trailing armed + drop from peak
- `PARTIAL_TP` — partial sell at threshold
- `MAX_HOLD` — time limit exceeded
- `STALE` — position >10min, high <10%

### Code Location

File: `src/execution/positions.js` lines 177–247

The exit logic checks:
```js
const tpHit = pnlPercent >= Number(position.tp_percent);
const slHit = pnlPercent <= Number(position.sl_percent);
const trailingArmed = position.trailing_armed || (position.trailing_enabled && tpHit);
const trailingHit = trailingArmed && position.trailing_enabled && trailDrop <= -Math.abs(Number(position.trailing_percent));

if (!exitReason) {
  if (slHit) exitReason = 'SL';
  else if (tpHit && !position.trailing_enabled) exitReason = 'TP';
  else if (trailingHit) exitReason = 'TRAILING_TP';
}
```

**No mention of `use_profit_lock` or `profit_lock_tiers`.**

### Workaround: Simulate Profit Lock with Trailing

To approximate profit lock behavior, use:
- `tp_percent: 80` (tier threshold)
- `trailing_enabled: true`
- `trailing_percent: 35` (floor = threshold - 35%)
- `trailing_arm_percent: 80` (arm at threshold)

This gives:
- Trailing arms at +80%
- Exits when price drops 35% from peak
- Effective floor: +45% (80 - 35)

Not identical to multi-tier profit lock, but similar risk/reward profile.

### To Implement Real Profit Lock

Would require:
1. Read `use_profit_lock` flag in `refreshPosition()`
2. If true, iterate `profit_lock_tiers` to find active tier
3. Compare current pnl to tier floor
4. Exit as `PROFIT_LOCK` if pnl < floor
5. Update high water mark to trigger next tier

Estimated effort: 30–50 lines of code + testing.

### Session Discovery (May 15, 2026)

User configured profit lock expecting it to work. After 12h dry-run, all exits were `TRAILING_TP` (not `PROFIT_LOCK`). Investigation revealed config was being set but never read. User reverted to trailing TP strategy (which works) and moved to live mode.

**Lesson:** Always verify that config fields are actually used in the execution path before relying on them.
