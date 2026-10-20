# Strategy Optimization via Data Analysis

When the user asks to optimize strategy or asks "gimana profit?", run this analysis workflow.

## Step 1: Query Performance by Exit Reason

```js
const db = require('better-sqlite3')('charon.sqlite');
const byExit = db.prepare(`
  SELECT exit_reason, COUNT(*) as cnt, 
    ROUND(AVG(pnl_percent),1) as avg_pnl, 
    ROUND(SUM(pnl_sol),4) as total_sol 
  FROM dry_run_positions WHERE status='closed' 
  GROUP BY exit_reason
`).all();
```

**What to look for:**
- MAX_HOLD with high avg_pnl → max_hold_ms too short, tokens still climbing
- SL with avg worse than sl_percent → slippage or delayed exit
- TP count low → tp_percent too high, tokens don't reach it

## Step 2: Query Performance by Entry Mcap

```js
const byMcap = db.prepare(`
  SELECT CASE 
    WHEN entry_mcap < 10000 THEN '<10K' 
    WHEN entry_mcap < 25000 THEN '10-25K' 
    WHEN entry_mcap < 50000 THEN '25-50K' 
    WHEN entry_mcap < 100000 THEN '50-100K' 
    ELSE '>100K' END as mcap_range, 
  COUNT(*) as cnt, ROUND(AVG(pnl_percent),1) as avg_pnl, 
  ROUND(SUM(pnl_sol),4) as total_sol 
  FROM dry_run_positions WHERE status='closed' 
  GROUP BY mcap_range ORDER BY avg_pnl DESC
`).all();
```

**What to look for:**
- Which mcap range has best avg_pnl → tighten min/max_mcap_usd to that range
- Ranges with negative avg → exclude or reduce exposure

## Step 3: TP Trades Hold Time

```js
const tpTrades = db.prepare(`
  SELECT symbol, pnl_percent, 
    (closed_at_ms - opened_at_ms)/1000/60 as hold_min 
  FROM dry_run_positions WHERE exit_reason='TP' 
  ORDER BY pnl_percent DESC
`).all();
```

**What to look for:**
- If TP trades close in <5 min → winners pump fast, max_hold can be shorter
- If TP trades take 15-30 min → need longer max_hold

## Step 4: MAX_HOLD Positive Trades (Missed Gains)

```js
const maxHoldPos = db.prepare(`
  SELECT symbol, pnl_percent FROM dry_run_positions 
  WHERE exit_reason='MAX_HOLD' AND pnl_percent > 10 
  ORDER BY pnl_percent DESC LIMIT 10
`).all();
```

**What to look for:**
- Many trades at +30-60% closed by MAX_HOLD → increase max_hold_ms
- Enable trailing stop to capture these runners

## Decision Framework

| Signal | Action |
|--------|--------|
| MAX_HOLD avg > +10% | Increase max_hold_ms (e.g., 10min → 30min) |
| MAX_HOLD trades at +30-60% | Enable trailing (15-20%) |
| Best mcap range identified | Tighten min/max_mcap_usd |
| SL avg worse than -25% | Tighten sl_percent (e.g., -25 → -20) |
| TP rarely hit | Lower tp_percent |
| Many signals skipped (max pos) | Increase max_open_positions |
| Low win rate but high avg win | Strategy is fine, just needs volume |

## Applying Changes

Strategy config is hot-read from SQLite — no restart needed:

```js
const newConfig = { /* ... */ };
db.prepare("UPDATE strategies SET config_json=? WHERE enabled=1")
  .run(JSON.stringify(newConfig));
```

But always restart after to confirm no errors:
```bash
pm2 restart charon && sleep 3 && pm2 logs charon --lines 10 --nostream
```

## Benchmark (2026-05-12, 80 trades)

After optimization:
- MAX_HOLD: 29 trades, avg +11.9%, total +0.1718 SOL
- SL: 21 trades, avg -29.6%, total -0.3108 SOL  
- TP: 3 trades, avg +132.7%, total +0.199 SOL
- TRAILING_TP: 2 trades, avg +31.3%, total +0.0313 SOL
- **Net: +0.0914 SOL** across 80 closed positions

Best mcap range: 10-25K (+9.2% avg), then 25-50K (+7.1%), then >100K (+4.2%)
Worst: 50-100K (-6.9%), <10K (-8.6%)
