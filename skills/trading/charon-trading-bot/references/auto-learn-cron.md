# Hourly Auto-Learn Loop — Data-Driven Strategy Tuning

Pattern for closing the loop on a trading bot's strategy tuning: a script that pulls closed-trade data from SQLite every hour, an LLM-driven cron job that interprets the data and applies *bounded* mutations to the strategy config.

## When to use this

Symptoms that warrant the loop:
- User keeps pasting screenshots of `/menu` and asking "kenapa WR jelek"
- Closed-trade count is in the dozens+ per day (enough sample for stats)
- Strategy config has many knobs, manual tuning is slow
- User says some variant of "perbaiki sendiri tiap jam"

## Architecture

```
┌─────────────────────────────┐
│  charon_hourly_audit.py     │  pure-Python, reads charon.sqlite
│  (~/.hermes/scripts/)       │  outputs JSON report to stdout
└──────────────┬──────────────┘
               │  (script output piped into prompt)
               ▼
┌─────────────────────────────┐
│  Hermes cronjob (every 1h)  │  LLM agent w/ terminal+file tools
│  prompt: diagnose → tune    │  applies bounded changes to DB
│  → restart → report         │  delivers to origin chat
└─────────────────────────────┘
```

## The audit script

Location: `~/.hermes/scripts/charon_hourly_audit.py` (script names must be relative to that dir, no absolute paths in cronjob `script` field).

The script reads SQLite directly (no `sqlite3` CLI on this VPS — use `sqlite3` Python stdlib). It emits a JSON report with:

- `last_1h.overall` — n, wins, losses, WR, total PnL SOL, avg/median PnL pct
- `last_1h.by_route` — per-route n, WR, avg pct (route from `snapshot_json.candidate.signals.route`)
- `last_1h.by_mcap_bucket` — `<10k`, `10-30k`, `30-60k`, `60-100k`, `>100k`
- `last_1h.by_exit_reason` — `SL` / `MAX_HOLD` / `TRAILING_TP` / `MANUAL` distribution
- Same blocks for `last_24h` (more sample, used as the basis for irreversible changes)
- `worst_recent` — top 5 worst trades with hold time, exit reason, mcap

Full implementation lives in `~/.hermes/scripts/charon_hourly_audit.py`. Output is verbose JSON — that is intentional, the LLM in the cronjob needs all the breakdowns to make decisions.

## The cronjob prompt — bounded autonomy

The agent must NOT have free rein. Encode the allowed mutations explicitly:

```
1. DIAGNOSE last_1h:
   - Routes with WR <30%
   - MCAP bucket with worst avg
   - Exit reason dominance (>50% of trades)

2. AUTO-TUNE only if last_24h has clear pattern (n>=10):
   - Route WR<25% n>=4 → add to blocked_routes
   - MCAP bucket WR=0% n>=3 → raise min_mcap_usd to bucket upper bound
   - MAX_HOLD avg pnl positive but <10% → cut max_hold_ms by 30 min
   - SL hits >60% → trailing_percent -= 5 (NEVER widen SL itself)

3. REPORT max 15 lines, Indonesian, with before→after diff.

4. If last_1h.overall.n < 3, send "⏸ Sample <3, skip auto-tune" — DO NOT tune.
```

Key constraints:
- 24h window (not 1h) for actual changes — 1h sample is too noisy
- Numerical thresholds (n>=10, WR<25%, etc.) — prevents over-fitting on 2-3 trades
- "Never widen SL" — common LLM mistake is to relax stop-loss when SL hit rate is high; correct fix is tighten entry filters
- Always restart `charon` PM2 process after DB mutation

## Strategy config additions

The pattern requires `strategies.config_json` to support `blocked_routes` array:

```js
// In src/pipeline/candidateBuilder.js, near end of filterCandidate()
if (Array.isArray(strat.blocked_routes) && strat.blocked_routes.length) {
  const route = candidate.signals?.route || candidate.signals?.label || null;
  if (route && strat.blocked_routes.includes(route)) {
    failures.push(`route blocked by /learn: ${route} (historical WR < threshold)`);
  }
}
```

This is a soft-blacklist — the scanner still picks up the route, but it gets filtered before LLM. Cheaper than removing the source entirely (can be re-enabled by emptying the array).

## Mutation pattern (the agent runs this)

```bash
python3 -c "
import sqlite3, json
con = sqlite3.connect('/home/ubuntu/charon/charon.sqlite')
cfg = json.loads(con.execute(\"SELECT config_json FROM strategies WHERE enabled=1\").fetchone()[0])
cfg['blocked_routes'] = ['graduated_trending', 'fee_graduated_trending']
cfg['min_mcap_usd'] = 10000
con.execute('UPDATE strategies SET config_json=? WHERE enabled=1', (json.dumps(cfg),))
con.commit()
print('updated')
"
bash -c "source ~/.nvm/nvm.sh && pm2 restart charon"
```

## Cronjob setup (Hermes)

```
cronjob action=create
  name="Charon Auto-Learn Hourly"
  schedule="every 1h"
  script="charon_hourly_audit.py"          # relative to ~/.hermes/scripts/
  enabled_toolsets=["terminal", "file"]
  prompt="<the bounded-autonomy prompt above>"
```

After creation, `cronjob action=run job_id=<id>` triggers the first cycle immediately for verification.

## Pitfalls discovered

**1. Side-effect: tightening `max_hold_ms` retroactively closes old positions.**
Switching `max_hold_ms` from `0` (∞) to `5400000` (90 min) caused the next monitor pass to instantly close 12 positions whose age already exceeded 90m. This is correct behavior but startles the user — explain it. Net effect was *good* (cleared dead bags), but on a live wallet it would mean 12 simultaneous market sells.

**2. WR computed on `pnl_percent <= 0` includes wash trades / 0% exits as losses.**
Be careful — if the script counts wins as `pnl_percent > 0`, manual exits at exactly breakeven count as losses. Use `> 0` for wins, `< 0` for losses, `== 0` separate.

**3. Route name comes from `snapshot_json.candidate.signals.route`.**
Not from a top-level column. Need `JSON.parse(snapshot_json)` per row in the audit script. There's no index on it — fine for hundreds of rows, would need denormalizing for tens of thousands.

**4. `script` parameter in `cronjob action=create` must be a bare filename.**
The validator rejects absolute or `~/`-prefixed paths. Place the file in `~/.hermes/scripts/` and pass just `charon_hourly_audit.py`.

**5. The LLM will try to "be helpful" beyond the bounded mutations.**
If the prompt says "only blacklist routes, only raise mcap, only cut hold time", the agent might still propose changing TP or position size in the report. The prompt should explicitly say: *do not propose other mutations; if you see a pattern not covered, surface it as `🎯 Saran manual review` — do not act.*

## Why this works for Charon specifically

- Charon already exposes a `/learn` workflow with `learning_runs` and `learning_lessons` tables — but those are *advisory* lessons stored as text. The hourly cron is the *enforcement* layer that turns advisory into config-applied.
- Strategy config is hot-reloaded each candidate eval (no restart strictly needed, but restart-on-change is safer and clears any in-memory caches).
- The data is already there in `dry_run_positions` — no new instrumentation needed.

## Generalizing

Same pattern works for any bot with: (a) a closed-trade table with PnL columns, (b) a config table whose values can be JSON-mutated, (c) a hot-reload or quick-restart mechanism. The script + cronjob + bounded-prompt triad is the reusable shape.
