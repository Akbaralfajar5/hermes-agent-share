# Entry/Exit Logic Notes

Session-derived implementation notes for auditing or patching Charon entry/exit behavior.

## Critical invariants

1. **Never compute live final PnL from market-cap ratio alone** for manual close or auto-exit.
   - Use realized `sell.outputAmount` / received SOL when available.
   - MCap-based PnL is only a fallback estimate for dry-run or missing execution receipts.

2. **Partial TP must only set `partial_tp_done` after the sell succeeds and is recorded.**
   - If the live partial sell fails, do not burn the flag.
   - Record a partial sell trade row so later accounting can reconstruct realized proceeds.

3. **Final exit accounting must include prior partial TP proceeds.**
   - Aggregate all prior `PARTIAL_TP` sell trades.
   - Compute final PnL from `realized partial proceeds + final exit proceeds - original size_sol`.
   - Do not treat the last sell leg as if it represents the entire position.

4. **Dry-run partial TP should simulate reduced exposure, not just flip a flag.**
   - Reduce estimated token amount / remaining size.
   - Insert a partial sell trade entry so dry-run accounting mirrors live behavior.

5. **Manual buy / confirmed intent execution must use a fresh execution check.**
   - Re-run candidate freshness and filters immediately before execution.
   - Reject stale candidates instead of trusting the older Telegram snapshot.

6. **Duplicate live buy guards belong before swap execution.**
   - Use an in-memory per-mint lock for concurrent requests.
   - Check DB for existing open position by mint before executing the buy.
   - After swap, avoid throwing in a way that loses the newly opened on-chain position; prefer warning/reconciliation because the swap already happened.

7. **Telegram intent size should match active strategy sizing.**
   - Confirmation messages and `trade_intents` should use `activeStrategy().position_size_sol` first.
   - Only fall back to `dry_run_buy_sol` if strategy size is absent.

8. **Live buy success must not be retroactively marked as failed just because Telegram notification failed.**
   - After swap + DB insert succeed, wrap `sendPositionOpen()` in its own try/catch.
   - Log a warning, but do not throw an execution failure that misrepresents live state.

9. **Manual close should re-read the position after `refreshPosition(..., { autoExit: false })`.**
   - `refreshPosition()` can mutate DB state such as partial-TP fields.
   - Re-query the row before calling `executeLiveSell()` or computing final accounting.
   - If refresh closed the position through another path, abort manual close safely.

10. **Treat impossible trailing exits as accounting bugs first.**
   - If `exit_reason = 'TRAILING_TP'` but `exit_mcap > entry_mcap` and stored PnL is `-100%`, the problem is usually final proceeds/accounting, not the trailing trigger.
   - Inspect `dry_run_trades.payload_json` for zeroed `exitProceedsSol` / `priorRealizedProceedsSol`.
   - Re-run `/learn <window>` after fixing accounting because one bogus full-loss row can distort route stats and lesson generation.

11. **`finalizePositionPnl(position, pnlPercent, exitReceivedSol = null)` must guard against `null` proceeds.**
   - PITFALL (May 2026): default param was `null`, but the validity check used `Number.isFinite(Number(exitReceivedSol))`. Because `Number(null) === 0`, a `null` proceeds value was silently treated as a valid `0 SOL` realized proceeds → final PnL stored as full loss `-size_sol` (`-100%`).
   - Symptom row: `exit_reason='TRAILING_TP'`, `exit_mcap > entry_mcap`, `pnl_percent=-100`, `pnl_sol=-size_sol`. `dry_run_trades.payload_json` shows `exitProceedsSol: 0, priorRealizedProceedsSol: 0`.
   - Fix in `src/execution/positions.js`: only honor `exitReceivedSol` when it is **non-null AND finite**. Otherwise fall back to mcap-ratio PnL math.
     ```js
     const hasExplicitProceeds = exitReceivedSol != null && Number.isFinite(Number(exitReceivedSol));
     const exitProceedsSol = hasExplicitProceeds ? Number(exitReceivedSol) : /* fallback from pnlPercent */;
     ```
   - After the fix, **always backfill** any historical `pnl_percent=-100` rows where `exit_mcap > entry_mcap`. Recompute `pnl_percent` from mcap ratio and `pnl_sol = size_sol * pnl_percent / 100`. One bogus -100% row severely skews `/learn` lessons.
   - Sanity probe (Python):
     ```sql
     select id, symbol, exit_reason, pnl_percent, exit_mcap, entry_mcap
     from dry_run_positions
     where status='closed' and pnl_percent <= -99 and exit_mcap > entry_mcap;
     ```

## Bug: finalizePositionPnl null-proceeds fallback (May 2026)

**Root cause:** In `src/execution/positions.js`, `finalizePositionPnl(position, pnlPercent, exitReceivedSol = null)` checked `Number.isFinite(Number(exitReceivedSol))` to decide whether to use explicit proceeds. But `Number(null) === 0`, so `null` was treated as "valid proceeds = 0 SOL", causing dry-run exits without explicit `receivedSol` to record `-100%` PnL.

**Symptom:** `/learn` shows a `TRAILING_TP` exit with `-100%` PnL even though `exit_mcap > entry_mcap`. The `dry_run_trades.payload_json` shows `exitProceedsSol: 0`.

**Fix:**
```js
// OLD (buggy):
if (Number.isFinite(Number(exitReceivedSol))) {
  exitProceedsSol = Number(exitReceivedSol);
}

// NEW (correct):
if (exitReceivedSol !== null && exitReceivedSol !== undefined && Number.isFinite(Number(exitReceivedSol))) {
  exitProceedsSol = Number(exitReceivedSol);
}
```

**Backfill query** (recalculate PnL from mcap ratio for affected rows):
```python
import sqlite3, math
conn = sqlite3.connect('charon.sqlite')
cur = conn.cursor()
for row in cur.execute('''
  select id, size_sol, entry_mcap, exit_mcap, pnl_percent
  from dry_run_positions
  where status='closed' and exit_mcap > 0 and entry_mcap > 0
    and abs(pnl_percent - ((exit_mcap / entry_mcap - 1) * 100)) > 10
'''):
    correct_pct = (row[3] / row[2] - 1) * 100
    correct_sol = row[1] * correct_pct / 100
    cur.execute('UPDATE dry_run_positions SET pnl_percent=?, pnl_sol=? WHERE id=?',
                (round(correct_pct, 4), round(correct_sol, 6), row[0]))
conn.commit()
```

## PITFALL: Configuring strategy fields that the code doesn't read

**Lesson (May 2026):** Setting `use_profit_lock: true` and `profit_lock_tiers: [...]` in `strategies.config_json` does **nothing** in the current Charon fork at `~/charon`. The exit logic in `src/execution/positions.js` only reads:
- `tp_percent` (TP exit)
- `sl_percent` (SL exit)
- `trailing_enabled` + `trailing_percent` + `trailing_armed` (trailing TP)
- `partial_tp` + `partial_tp_at_percent` + `partial_tp_sell_percent` (partial sell)
- `max_hold_ms` (time-based exit)

There is **no `PROFIT_LOCK` exit reason**, **no tier evaluator**, and no reference to `use_profit_lock` or `profit_lock_tiers` anywhere in the source. The `tuning-playbook.md` reference describes a profit-lock implementation from a different fork or older version — its presence in skill docs does NOT prove the feature exists in the running repo.

**Verification before configuring any exit feature:**
```bash
cd ~/charon
grep -rn "profit_lock\|use_profit_lock\|PROFIT_LOCK" src/
# zero matches → feature not implemented, do not promise it to the user
```

**If the user asks for profit lock and it's not implemented, options to surface:**
1. Implement profit lock in `src/execution/positions.js` (per-tier floor tracking + `PROFIT_LOCK` exit reason). Non-trivial patch.
2. Approximate with trailing: `trailing_arm_percent` ≈ first tier threshold, `trailing_percent` ≈ (threshold - floor). E.g., tier `+30 → floor +10` ≈ trailing arm 30, trailing 20.
3. Stay on plain trailing TP if it already has a winning track record in `/learn`.

**Do NOT** set `use_profit_lock: true` and tell the user "profit lock is active" without verifying the code path exists. That's a false-confidence regression — it leaves the user thinking they have downside protection they don't have.

**Related pitfall:** Same class of bug applies to any strategy field. Before claiming a config change took effect, grep `src/` for the field name. Strategy `config_json` is free-form JSON — the DB will accept fields the runtime ignores.

## PITFALL: Strategy config changes don't migrate open positions

When switching exit strategy (e.g., trailing → profit lock), **existing open positions keep their old TP/SL/trailing values**. These are copied into the position row at entry time.

**Symptom:** User changes strategy to profit lock, but open positions still show `trailing_enabled=1` and exit via `TRAILING_TP` instead of `PROFIT_LOCK`.

**Migration SQL (run after strategy config change):**
```js
// Update all open positions to new exit settings
db.prepare(`
  UPDATE dry_run_positions 
  SET 
    tp_percent = 9999,
    sl_percent = -30,
    trailing_enabled = 0,
    trailing_percent = 0,
    trailing_armed = 0
  WHERE status = 'open'
`).run();
```

**Rule:** Always offer to migrate open positions when user changes TP/SL/trailing/profit-lock settings mid-session.

## PITFALL: Configuring strategy fields that the code doesn't read

**Symptom:** You set `use_profit_lock: true` and `profit_lock_tiers: [...]` in `strategies.config_json`. The user thinks profit lock is active. Bot keeps exiting via `TRAILING_TP` / `SL` only. No `PROFIT_LOCK` events ever fire.

**Root cause:** The current Charon at `~/charon` (May 2026, 0.39.x line) has **no code that reads `use_profit_lock` or `profit_lock_tiers`**. The trading-skill playbook describes that feature from a different fork. The active exit logic in `src/execution/positions.js` only handles:

- `SL` (pnl ≤ sl_percent)
- `TP` (pnl ≥ tp_percent, only when trailing disabled)
- `TRAILING_TP` (trailing armed + drop ≥ trailing_percent from peak)
- `PARTIAL_TP` (partial sell at partial_tp_at_percent)
- `MAX_HOLD` (time-based)
- `STALE` (>10min, high <10%)

**Verify before configuring ANY feature flag:**

```bash
cd ~/charon
grep -rn "use_profit_lock\|profit_lock_tiers\|PROFIT_LOCK" src/
# zero hits → feature doesn't exist, don't promise it to the user
```

Apply the same check to any strategy field you're about to set for the first time:

```bash
grep -rn "<field_name>" src/
```

If the only hits are in `references/`, `node_modules/`, or default-config seed files — the field is dead config. Tell the user the feature isn't implemented in this fork and offer either (a) implement it, or (b) use the closest in-code feature instead.

**Preferred behavior:** when the user asks for an exit strategy, list the in-code options first (`SL`, `TP`, `TRAILING_TP`, `PARTIAL_TP`, `STALE`) and only mention profit lock if you've just verified the code path exists. Don't assume parity with the skill playbook — playbook tracks multiple Charon forks.

**Bulk migration when switching active exit strategy:**

After changing strategy `config_json`, existing open positions still have the old per-row `tp_percent` / `sl_percent` / `trailing_*` snapshot — they will exit via the old behaviour. Always migrate:

```js
db.prepare(`
  UPDATE dry_run_positions
  SET tp_percent = ?, sl_percent = ?, trailing_enabled = ?, trailing_percent = ?, trailing_armed = 0
  WHERE status = 'open'
`).run(newTp, newSl, newTrailingEnabled ? 1 : 0, newTrailingPct);
```

Run this in the same step as the strategy update, not as a separate "later" task.

## Recommended verification checklist

- Manual close (live): compare stored PnL vs actual received SOL
- Partial TP live success: flag flips only after success
- Partial TP live failure: flag stays false
- Partial TP dry-run: trade log inserted and remaining exposure reduced
- Final close after partial TP: total PnL includes earlier partial proceeds
- Manual buy stale candidate: rejected on fresh-check
- Confirmed intent: same fresh-check path as live buy
- Duplicate live buy race: second request blocked before swap
- Telegram intent size: matches active strategy config
