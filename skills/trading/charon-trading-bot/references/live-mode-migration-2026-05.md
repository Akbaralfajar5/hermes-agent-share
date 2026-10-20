# Live Mode Migration & Exit Strategy Tuning (May 2026)

## Profit Lock Implementation Status

**CRITICAL PITFALL:** The `charon-trading-bot` skill documents profit lock tiers as if they are implemented in the codebase. **They are not.**

Current state (May 2026):
- Strategy config accepts `use_profit_lock`, `profit_lock_tiers` fields
- **No code in `src/execution/positions.js` reads or acts on these fields**
- Exit logic only recognizes: `SL`, `TP`, `TRAILING_TP`, `PARTIAL_TP`, `MAX_HOLD`
- Profit lock tiers are **dead config** — setting them has no effect

**Workaround:** Use trailing stop with high `trailing_arm_percent` to simulate profit lock behavior. Example: arm at +80%, trail 35% drop = similar to profit lock tier at +80% with floor ~+45%.

**Future fix:** Implement profit lock tier logic in `src/execution/positions.js` around line 200, after partial TP check. Requires:
1. Per-tier floor tracking in position row
2. Check current PnL against active tier floor
3. Exit as `PROFIT_LOCK` if PnL drops below floor

## Dry-Run to Live Mode Workflow

### Step 1: Update Settings & Strategy Config

```js
// Settings table
db.prepare("UPDATE settings SET value = 'live' WHERE key = 'trading_mode'").run();
db.prepare("UPDATE settings SET value = '3' WHERE key = 'max_open_positions'").run();

// Strategy config
const row = db.prepare("SELECT config_json FROM strategies WHERE id = 'degen'").get();
const config = JSON.parse(row.config_json);
config.position_size_sol = 0.05;      // or 0.2, user choice
config.max_open_positions = 3;
db.prepare("UPDATE strategies SET config_json = ? WHERE id = 'degen'").run(JSON.stringify(config));
```

### Step 2: Migrate Existing Open Positions

**CRITICAL:** Positions created in dry-run mode have `execution_mode = 'dry_run'` stored in the DB row. When switching to live mode, these positions will NOT execute real swaps on exit unless migrated.

```js
// Migrate all open dry_run positions to live
db.prepare(`
  UPDATE dry_run_positions 
  SET execution_mode = 'live'
  WHERE status = 'open' AND execution_mode = 'dry_run'
`).run();
```

**Why this matters:** 
- Dry-run positions exit via simulation (no actual swap)
- Live positions exit via Jupiter swap (real SOL transferred)
- If you forget this step, old positions will close silently without executing swaps

### Step 3: Verify Wallet Balance

```js
import { Keypair, Connection } from '@solana/web3.js';
import bs58 from 'bs58';

const privKeyStr = process.env.SOLANA_PRIVATE_KEY;
const keypair = Keypair.fromSecretKey(bs58.decode(privKeyStr));
const conn = new Connection(process.env.SOLANA_RPC_URL, 'confirmed');
const balance = await conn.getBalance(keypair.publicKey);
const balanceSol = balance / 1_000_000_000;

console.log('Balance:', balanceSol.toFixed(4), 'SOL');
// Minimum: (max_open_positions × position_size_sol) + 0.05 SOL reserve
```

### Step 4: Add Wallet to Bot (Optional)

```js
db.prepare(`
  INSERT INTO saved_wallets (label, address, created_at_ms) 
  VALUES (?, ?, ?)
  ON CONFLICT(label) DO UPDATE SET address = excluded.address
`).run('main', keypair.publicKey.toString(), Date.now());
```

Then use `/wallets` or `/wallet main` to track PnL.

### Step 5: Restart Bot

```bash
pm2 restart charon --update-env
```

Bot now reads `trading_mode: live` and will execute real swaps on exit triggers.

## Exit Strategy Tuning (May 2026 Session)

User-confirmed exit config for live mode:

```json
{
  "partial_tp": true,
  "partial_tp_at_percent": 50,
  "partial_tp_sell_percent": 30,
  "trailing_enabled": true,
  "trailing_arm_percent": 80,
  "trailing_percent": 35,
  "tp_percent": 80,
  "sl_percent": -20,
  "max_hold_ms": 0
}
```

**Flow:**
1. Token pumps +50% → partial TP fires, sell 30% of position
2. Remaining 70% continues with trailing stop armed
3. Token pumps to +80% → trailing armed (if not already)
4. Token drops 35% from peak → exit remaining 70% as `TRAILING_TP`
5. Token drops to -20% from entry → exit as `SL` (any time)

**Rationale:**
- Partial TP at +50% locks in early profit (~0.0075 SOL per 0.05 SOL position)
- Trailing arm at +80% lets winners run further before protecting
- Trailing drop 35% gives room for meme coin volatility (normal pullbacks 20-25%)
- SL -20% is tight but acceptable with fast price watcher (1s polling)

**Dry-run validation (12h window):**
- 24 closed trades, 50% WR, +0.195 SOL realized
- Trailing exits: 12/12 wins, avg +50.2%
- SL exits: 12/12 losses, avg -17.7%
- Reward/risk ratio: 2.84x (profitable)

## Position Migration Gotchas

### Gotcha 1: Old Positions May Exit Immediately

When you migrate dry_run positions to live, they retain their old `high_water_mcap` and `trailing_armed` state. If a position already reached +80% during dry-run, it will have `trailing_armed = 1` in the DB. On the next check cycle, if price has dropped 35% from peak, it will exit immediately as `TRAILING_TP`.

**Mitigation:** Review open positions before migration. If any are at high unrealized profit and you want to keep them, either:
1. Close them manually in dry-run first
2. Reset `trailing_armed = 0` before migrating to live
3. Accept the immediate exit and let live mode start fresh

### Gotcha 2: Slippage Reality

Dry-run exit PnL is calculated from mcap ratio. Live exit PnL includes real slippage:
- Entry slippage: 2-5% on tokens <$30K mcap
- Exit slippage: 3-5% normal, 10-30% during dumps
- Net effect: avg loss -17% in dry-run becomes -22% to -35% in live

**Mitigation:** Expect 5-10% worse PnL on live exits. If dry-run WR is 50%, live WR may drop to 40-45% due to slippage.

### Gotcha 3: Wallet Balance Depletion

Each live position ties up `position_size_sol` in the wallet. With 3 open positions at 0.05 SOL each = 0.15 SOL locked. If wallet only has 0.2 SOL total, you have 0.05 SOL left for gas + buffer. One failed swap or unexpected fee can cause subsequent entries to fail.

**Mitigation:** Keep wallet balance at least 2x the max exposure. For 3 × 0.05 = 0.15 SOL exposure, keep 0.3 SOL minimum.

## Verification Queries

### Check Current Mode & Config

```sql
SELECT key, value FROM settings WHERE key IN ('trading_mode', 'max_open_positions');

SELECT id, position_size_sol, max_open_positions, partial_tp_at_percent, trailing_arm_percent, trailing_percent
FROM strategies WHERE id = 'degen';
```

### Check Open Positions Execution Mode

```sql
SELECT id, symbol, execution_mode, status, 
       ROUND(entry_mcap, 0) as entry,
       ROUND(high_water_mcap, 0) as high,
       ROUND((high_water_mcap / entry_mcap - 1) * 100, 1) as high_pct
FROM dry_run_positions
WHERE status = 'open'
ORDER BY id DESC;
```

### Check Recent Live Exits

```sql
SELECT id, symbol, exit_reason, 
       ROUND(pnl_percent, 1) as pnl_pct,
       ROUND(pnl_sol, 4) as pnl_sol,
       execution_mode
FROM dry_run_positions
WHERE status = 'closed' AND execution_mode = 'live'
ORDER BY closed_at_ms DESC
LIMIT 10;
```

## Dry-Run to Live Profitability Expectations

**All-time dry-run stats (102 trades, 36 hours):**
- Win rate: 36.3%
- Realized PnL: +0.0997 SOL
- Unrealized peak: +0.1324 SOL
- Combined: +0.2321 SOL

**Realistic live expectations (after slippage):**
- Win rate: 30-35% (5-10% worse due to slippage)
- Avg win: +40% (vs +50% dry-run)
- Avg loss: -22% (vs -17% dry-run)
- Reward/risk: still ~2x (profitable but tighter)

**Sample size:** Dry-run had 102 trades in 36 hours. Live mode with 3 max positions will be slower (fewer concurrent entries). Expect 50-70 trades per 36 hours. Need at least 30-50 live trades before drawing conclusions.

## LLM Model for Live Mode

Current: `kr/claude-haiku-4.5` via 9router (localhost:20128)

Haiku is fast and cheap for high-frequency screening. If you want higher-quality entry decisions, switch to:
- `kr/claude-sonnet-4.5` — better reasoning, slower
- `kr/claude-opus-4.7` — best quality, slowest

Change via `.env`:
```
LLM_MODEL=kr/claude-sonnet-4.5
```

Then `pm2 restart charon --update-env`.

## Troubleshooting Live Mode

### Bot not entering positions

Check:
1. `trading_mode` is `live` (not `dry_run`)
2. Wallet has balance >= max_exposure + 0.05 SOL
3. Open positions < max_open_positions
4. LLM is returning BUY verdicts (check logs for `[agent] BUY` lines)

### Positions exiting at worse PnL than expected

Normal — slippage. Check:
1. Token mcap at exit (lower = higher slippage)
2. Liquidity at exit (lower = higher slippage)
3. Compare `pnl_percent` (mcap-based estimate) vs actual received SOL

### Wallet balance dropping unexpectedly

Check:
1. Gas fees per swap (~0.001-0.002 SOL)
2. Failed swaps (still consume gas)
3. Slippage on exits (can be 10-30% on dumps)

Run query:
```sql
SELECT COUNT(*), SUM(pnl_sol) FROM dry_run_positions 
WHERE status = 'closed' AND execution_mode = 'live';
```

Compare to wallet balance change.
