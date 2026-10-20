# Profit Lock Implementation

## Code Location
`src/execution/positions.js` — inside `refreshPosition()` function, between MAX_HOLD check and partial TP check.

## In-Memory Timer (top of file, after `sellInProgress`)
```js
const profitLockBreaches = new Map(); // positionId → first breach timestamp (ms)
```

## Core Logic (inside refreshPosition, after MAX_HOLD check)
```js
// ─── Profit Lock Tiers ───
// Tiers: [[threshold%, floor%], ...] e.g. [[20,5],[40,15],[80,40],[150,90]]
// When pnl reaches threshold, lock a floor. If pnl drops below floor → exit.
// Uses high water PnL (from high_water_mcap) to determine highest tier reached.
if (!exitReason && strat?.use_profit_lock && strat.profit_lock_tiers?.length) {
  const highWaterPnl = (highWaterMcap / Number(position.entry_mcap) - 1) * 100;
  let lockedFloor = null;
  // Find highest tier reached based on high water mark
  for (const [threshold, floor] of strat.profit_lock_tiers) {
    if (highWaterPnl >= threshold) {
      lockedFloor = floor;
    }
  }
  if (lockedFloor !== null && pnlPercent <= lockedFloor) {
    // Confirm delay: only exit if below floor for confirm_s seconds
    const confirmMs = (strat.profit_lock_confirm_s || 0) * 1000;
    if (confirmMs <= 0) {
      exitReason = 'PROFIT_LOCK';
      console.log(`[profit_lock] pos ${position.id} exit: pnl ${pnlPercent.toFixed(1)}% below locked floor +${lockedFloor}% (high was +${highWaterPnl.toFixed(1)}%)`);
    } else {
      // Use in-memory tracker for confirm delay
      if (!profitLockBreaches.has(position.id)) {
        profitLockBreaches.set(position.id, now());
        console.log(`[profit_lock] pos ${position.id} breach started: pnl ${pnlPercent.toFixed(1)}% < floor +${lockedFloor}% (confirming ${strat.profit_lock_confirm_s}s)`);
      } else {
        const breachStart = profitLockBreaches.get(position.id);
        if (now() - breachStart >= confirmMs) {
          exitReason = 'PROFIT_LOCK';
          profitLockBreaches.delete(position.id);
          console.log(`[profit_lock] pos ${position.id} confirmed exit: pnl ${pnlPercent.toFixed(1)}% below floor +${lockedFloor}% for ${strat.profit_lock_confirm_s}s`);
        }
      }
    }
  } else {
    // Above floor or no tier reached — clear any breach timer
    profitLockBreaches.delete(position.id);
  }
}
```

## Strategy Config Fields (in `config_json`)
```json
{
  "use_profit_lock": true,
  "profit_lock_tiers": [[20, 5], [40, 15], [80, 40], [150, 90]],
  "profit_lock_trail_pct": 40,
  "profit_lock_confirm_s": 45
}
```

## Required: `use_profit_lock: true`
The code checks `strat?.use_profit_lock && strat.profit_lock_tiers?.length`. Both must be truthy. If `use_profit_lock` is missing or false, tiers are ignored even if defined.

## Position Creation Override (src/db/positions.js)
When profit_lock tiers exist, position creation IGNORES LLM suggested TP/SL:
```js
const tp = strat.profit_lock_tiers?.length ? 9999 : Number(decision.suggested_tp_percent || strat.tp_percent || ...);
const sl = strat.profit_lock_tiers?.length ? Number(strat.sl_percent || -20) : Number(decision.suggested_sl_percent || strat.sl_percent || ...);
const trailingEnabled = strat.profit_lock_tiers?.length ? 0 : ((strat.trailing_enabled ?? ...) ? 1 : 0);
```

## Telegram Display (src/telegram/format.js)
Shows dynamic profit lock info instead of fixed TP/SL:
```js
(() => {
  const strat = strategyById(position.strategy_id);
  if (strat?.use_profit_lock && strat.profit_lock_tiers?.length) {
    const highPnl = position.high_water_mcap && position.entry_mcap
      ? (Number(position.high_water_mcap) / Number(position.entry_mcap) - 1) * 100 : 0;
    let lockedFloor = null;
    for (const [threshold, floor] of strat.profit_lock_tiers) {
      if (highPnl >= threshold) lockedFloor = floor;
    }
    const tierStr = strat.profit_lock_tiers.map(([t,f]) => `${t}%→${f}%`).join(', ');
    const floorStr = lockedFloor !== null ? `+${lockedFloor}%` : 'none';
    return `├ 🔒 Profit Lock: floor ${floorStr}\n├ Tiers: ${tierStr}\n├ SL: ${fmtPct(position.sl_percent)}`;
  }
  return `├ TP: ${fmtPct(position.tp_percent)} · SL: ${fmtPct(position.sl_percent)}`;
})()
```

## Key Behaviors
- `profit_lock_tiers` is read from strategy config at check time (not stored per-position)
- Changing tiers applies to ALL open positions immediately (no restart needed, strategy is hot-read with 5s cache)
- `tp_percent`, `sl_percent`, `trailing_enabled` ARE stored per-position at entry time
- The confirm timer (`profitLockBreaches` Map) is in-memory only — restarting bot resets pending confirms
- If `use_profit_lock` is false or `profit_lock_tiers` is empty, the block is skipped entirely
- Exit reason is `'PROFIT_LOCK'` — distinct from `'SL'`, `'TP'`, `'TRAILING_TP'`
- Base SL (-20%) still works as absolute floor — if token never reaches +20%, SL handles exit
- Profit lock takes priority over standard exit checks (runs before SL/TP/trailing check)

## Example Scenario
1. Token enters at $10K mcap, position opened (TP: 9999, SL: -20%)
2. Token pumps to $12K (+20%) → tier 1 reached, floor locked at +5%
3. Token pumps to $15K (+50%) → tier 2 reached, floor locked at +15%
4. Token dumps to $11.5K (+15%) → at floor exactly, no breach
5. Token dumps to $10.4K (+4%) → below floor (+15%), breach timer starts (45s)
6. 45 seconds pass, still below +15% → PROFIT_LOCK exit confirmed
7. Without profit lock: would have hit base SL at -20% = bigger loss

## Bug History
- **2026-05-13:** Discovered profit lock tiers were configured in DB but NOT implemented in exit logic code. Only base SL was active. Fixed by adding the tier check block to `refreshPosition()`.
- **2026-05-13:** LLM `suggested_tp_percent` was overriding strategy TP (9999) with values like 45%. Fixed in `createDryRunPosition()` — when `profit_lock_tiers` exist, always use 9999/strategy-SL.
- **2026-05-13:** Telegram display showed "TP: 9999%" which confused user. Fixed to show dynamic profit lock info (current floor, tier list, SL).

## Pitfalls
- **`use_profit_lock` must be true** — just having `profit_lock_tiers` in config is NOT enough. The code checks both `strat?.use_profit_lock` AND `strat.profit_lock_tiers?.length`.
- **High water mcap must be tracked** — the `high_water_mcap` column in `dry_run_positions` is updated every refresh cycle. If this is 0 or null, `highWaterPnl` calculation breaks. The UPDATE statement runs AFTER profit lock check, so first check uses the previously-stored high water.
- **Confirm delay resets on restart** — `profitLockBreaches` is in-memory Map. If bot restarts during a 45s confirm window, the timer resets. Token must breach again for 45s after restart.
- **Floor is based on HIGH WATER, not current PnL** — once a tier is reached (based on highest-ever mcap), the floor is permanent for that position's lifetime. Even if price dumps and recovers, the floor stays.
