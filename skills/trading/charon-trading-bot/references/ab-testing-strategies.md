# A/B Testing Strategies in Charon

## Approach

Run each strategy for 15 minutes, collect results, compare. Total test time: 1 hour for 4 strategies.

## Scripts

### `switch_strategy.js` — Switch active strategy + close open positions

```js
import { initDb, db } from './src/db/connection.js';
import { now } from './src/utils.js';
initDb();

const stratId = process.argv[2];
// Close all open positions
const open = db.prepare("SELECT id FROM dry_run_positions WHERE status = 'open'").all();
for (const p of open) {
  db.prepare("UPDATE dry_run_positions SET status = 'closed', exit_reason = 'strategy_switch', closed_at_ms = ?, pnl_percent = 0, pnl_sol = 0 WHERE id = ?").run(now(), p.id);
}
// Switch strategy
db.prepare('UPDATE strategies SET enabled = 0').run();
db.prepare('UPDATE strategies SET enabled = 1 WHERE id = ?').run(stratId);
console.log(`Switched to ${stratId}, closed ${open.length} positions`);
```

### `report_results.js` — Collect and compare results

Queries `dry_run_positions` grouped by `strategy_id`, calculates win rate and PnL per strategy. Excludes positions with `exit_reason IN ('test_reset', 'manual_reset', 'strategy_switch')`.

### `run_ab_test.sh` — Automated rotation

```bash
#!/bin/bash
cd /home/ubuntu/charon
# Sniper 15 min
sleep 900 && node switch_strategy.js dip_buy && pm2 restart charon --silent
# Dip Buy 15 min
sleep 900 && node switch_strategy.js smart_money && pm2 restart charon --silent
# Smart Money 15 min
sleep 900 && node switch_strategy.js degen && pm2 restart charon --silent
# Degen 15 min
sleep 900 && node report_results.js
```

Run as background process: `bash run_ab_test.sh &` or via Hermes background terminal.

## Strategy Configurations for Testing

### Sniper (no LLM, aggressive)
- mcap: $5K-$500K, holders: 20+, swaps: 5+
- TP: 80%, SL: -20%, partial TP: 40%@50%
- max_hold: 10 min, LLM: off
- Best for: high volume of trades, quick validation

### Dip Buy (LLM, established tokens)
- mcap: $50K-$2M, holders: 100+, swaps: 20+
- TP: 50%, SL: -15%, trailing: 15%
- max_ath_distance_pct: -30 (only buy dips)
- max_hold: 20 min, LLM: on (conf 60+)
- Best for: lower risk, buying pullbacks

### Smart Money (LLM strict, quality)
- mcap: $10K-$1M, holders: 50+, swaps: 15+
- TP: 100%, SL: -20%, trailing: 20%
- bundler: <0.25, rug: <0.1 (very strict)
- max_hold: 15 min, LLM: on (conf 70+)
- Best for: fewer but higher quality trades

### Degen (no LLM, wide net, quick flip)
- mcap: $5K-$200K, holders: 0+, swaps: 3+
- TP: 60%, SL: -20%, no trailing, no partial
- max_hold: 5 min, LLM: off
- Best for: maximum trade volume, pure rule-based

## Key Observations

- **Sniper without LLM** opens many positions quickly (5 in first minute) but win rate ~29%. After 5 min: 17 trades, 5W/12L, -0.0518 SOL. Too aggressive without LLM quality gate — consider enabling LLM or tightening safety filters for production use.
- **GMGN safety filter** rejects 33-53% of tokens before strategy filters — this is healthy
- **max_hold_ms** is critical for meme coins — tokens that don't move in 10-20 min rarely recover
- **Filters that commonly block candidates:**
  - `market cap max` — GMGN trending has many $1M+ tokens, need wide range
  - `trending swaps < X` — new tokens have few swaps, keep threshold low (5-10)
  - `holders < X` — very new tokens have <50 holders, set 20-30 for early entry
  - `bundler_rate` — many legit tokens have 0.3-0.5 bundler, don't set below 0.4
- **Strategy config is hot-read** — no PM2 restart needed after DB update
- **PM2 restart IS needed** after changing `app.js` imports or `.env` values
