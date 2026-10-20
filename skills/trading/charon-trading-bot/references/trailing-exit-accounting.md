# Trailing-exit accounting anomaly: `TRAILING_TP` stored as `-100%`

Use this when Charon learning output flags an impossible trailing take-profit result, especially a closed dry-run position with:
- `exit_reason = 'TRAILING_TP'`
- `exit_mcap > entry_mcap`
- but `pnl_percent <= -100` or `pnl_sol = -size_sol`

## Why this matters

This is not just a bad lesson label. It contaminates:
- win rate
- average PnL
- route-level performance summaries
- lesson generation from `/learn`

A single false `-100%` can mislead the LLM into recommending the wrong strategy changes.

## Proven symptom from session

Observed row pattern in `dry_run_positions`:
- symbol: `Doomscroll`
- `entry_mcap = 21238.87`
- `exit_mcap = 34964.32`
- `exit_reason = 'TRAILING_TP'`
- `pnl_percent = -100.0`
- `pnl_sol = -0.05`

Stored sell payload showed:
- `exitProceedsSol = 0`
- `priorRealizedProceedsSol = 0`

That forced final accounting to compute:
- `totalProceedsSol = 0`
- `finalPnlSol = 0 - size_sol`
- result: full loss despite profitable exit mcap

## Fast DB probes

List negative trailing exits:

```sql
select id, symbol, pnl_percent, pnl_sol, entry_mcap, exit_mcap, partial_tp_done
from dry_run_positions
where status='closed'
  and exit_reason='TRAILING_TP'
  and pnl_percent < 0
order by closed_at_ms desc;
```

Inspect a suspicious position and its trade legs:

```sql
select id, symbol, size_sol, entry_mcap, exit_mcap, pnl_percent, pnl_sol, exit_reason,
       partial_tp_done, high_water_mcap, trailing_armed
from dry_run_positions
where id = ?;

select id, side, at_ms, price, mcap, size_sol, token_amount_est, reason, payload_json
from dry_run_trades
where position_id = ?
order by id;
```

## Likely failure mode

`finalizePositionPnl()` trusts `exitReceivedSol` if it is finite, including zero:
- if caller passes `0`, accounting treats the final leg as worthless
- this can happen even when market-cap-derived `pnlPercent` is strongly positive

So the bug is usually **final proceeds recorded as zero**, not a wrong trailing trigger.

## Audit rule

When `/learn` reports a lesson like:
- "A -100% exit tagged TRAILING_TP signals a logic bug"

Treat it as a backend accounting bug until disproven. Verify DB rows before changing strategy thresholds.

## Recommended follow-up

1. Inspect the suspicious `dry_run_positions` row.
2. Inspect matching `dry_run_trades` sell payload.
3. Check whether `exitReceivedSol` or derived `exitProceedsSol` became `0`.
4. Patch accounting before trusting the learning summary.
5. Re-run `/learn <window>` after correction to refresh lessons.
