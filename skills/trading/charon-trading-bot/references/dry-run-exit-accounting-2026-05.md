# Dry-run exit accounting bug (May 2026)

## Symptom

`/learn 12h` surfaced a false lesson: a `TRAILING_TP` exit (`Doomscroll`) was recorded as `-100%` / `-0.05 SOL` even though `exit_mcap > entry_mcap`.

A second bad historical row existed for `SL` (`FINDER`) with the same `-100%` symptom.

## Root cause

In `src/execution/positions.js`, `finalizePositionPnl(position, pnlPercent, exitReceivedSol = null)` treated `null` as a real proceeds value because it used:

```js
Number.isFinite(Number(exitReceivedSol))
```

`Number(null) === 0`, so dry-run exits without explicit realized proceeds were finalized with `exitProceedsSol = 0` instead of falling back to `remainingSizeSol * (1 + pnlPercent / 100)`.

## Correct fix

Gate the explicit override on non-null input first:

```js
const explicitExitReceivedSol = exitReceivedSol == null ? null : Number(exitReceivedSol);
const exitProceedsSol = Number.isFinite(explicitExitReceivedSol)
  ? explicitExitReceivedSol
  : fallbackExitProceedsSol;
```

This preserves live/manual-close behavior while restoring correct fallback accounting for dry-run exits.

## Verification pattern

1. Syntax check:
   - `node --check src/execution/positions.js`
2. Diff hygiene:
   - `git diff --check -- src/execution/positions.js`
3. Query suspicious impossible losses:

```sql
select id, symbol, exit_reason, pnl_percent, pnl_sol, entry_mcap, exit_mcap
from dry_run_positions
where status='closed'
  and round(coalesce(pnl_percent,0), 6) <= -99.999999;
```

4. Cross-check expected dry-run PnL for non-partial exits:
   - compare stored `pnl_percent` / `pnl_sol` against `(exit_mcap / entry_mcap - 1) * 100`

## Historical backfill used

For rows with:
- `status='closed'`
- stored PnL near `-100%`
- no `PARTIAL_TP` sell trades
- valid `entry_mcap`, `exit_mcap`, `size_sol`

recompute:

- `expected_pct = (exit_mcap / entry_mcap - 1) * 100`
- `expected_sol = size_sol * expected_pct / 100`

Then update both:
- `dry_run_positions.pnl_percent`, `dry_run_positions.pnl_sol`
- latest sell trade `payload_json` fields `pnlPercent`, `pnlSol`, `exitProceedsSol`

## Known corrected rows from session

- `id 61` `FINDER`: `-100% -> -17.03%`
- `id 75` `Doomscroll`: `-100% -> +64.62%`

## Pitfall

Do **not** import runtime modules with `node --input-type=module ...` while PM2 `charon` is live unless you know the import tree avoids bot polling startup. In this repo, ad-hoc imports can trigger `ETELEGRAM 409 Conflict` against the running poller. Prefer `node --check`, direct file inspection, or isolated scripts that do not boot the bot.