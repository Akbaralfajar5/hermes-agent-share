# Strategy Config Locking — TP/SL Override Prevention

## Problem

By default, Charon's LLM decision pipeline can suggest custom TP/SL percentages per trade via `decision.suggested_tp_percent` and `decision.suggested_sl_percent`. This allows LLM to override strategy-level TP/SL settings, which may not be desired for conservative or fixed-rule strategies.

## Solution

Lock TP/SL at the strategy level so LLM suggestions are ignored. All positions use the strategy's configured TP/SL regardless of LLM verdict.

## Implementation

### 1. Update Strategy Config

Set fixed TP/SL in the strategy's `config_json`:

```sql
UPDATE strategies
SET config_json = json_set(
  config_json,
  '$.tp_percent', 75,
  '$.sl_percent', -75
)
WHERE id='degen';
```

### 2. Lock in Position Creation Code

In `src/db/positions.js`, modify both `createDryRunPosition()` and `createLivePosition()`:

**Before (allows LLM override):**
```javascript
const tp = Number(strat.tp_percent ?? decision.suggested_tp_percent ?? numSetting('default_tp_percent', 50));
const sl = Number(strat.sl_percent ?? decision.suggested_sl_percent ?? numSetting('default_sl_percent', -25));
```

**After (locked):**
```javascript
// Lock TP/SL from LLM override - use strategy values only
const tp = Number(strat.tp_percent ?? numSetting('default_tp_percent', 50));
const sl = Number(strat.sl_percent ?? numSetting('default_sl_percent', -25));
```

The key change: remove `decision.suggested_tp_percent` and `decision.suggested_sl_percent` from the fallback chain. Strategy config is now the source of truth.

### 3. Restart Bot

```bash
pm2 restart charon
```

## Verification

After restart, all new positions should use the locked TP/SL:

```sql
SELECT id, symbol, tp_percent, sl_percent
FROM dry_run_positions
WHERE status='open' AND execution_mode='live'
ORDER BY opened_at_ms DESC
LIMIT 5;
```

Expected: all rows show `tp_percent=75, sl_percent=-75` (or whatever you set).

## Notes

- LLM still provides `suggested_tp_percent` and `suggested_sl_percent` in its decision output, but they are now ignored during position creation.
- If you want to allow LLM override again in the future, revert the code change to include `decision.suggested_tp_percent` in the fallback chain.
- This applies to both dry-run and live positions.
