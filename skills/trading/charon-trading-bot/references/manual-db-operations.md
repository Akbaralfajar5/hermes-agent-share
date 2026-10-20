# Manual Database Operations for Charon

When the normal execution path fails (e.g., module not found, bot not responding), positions can be created directly via SQLite.

## Database Location
```
/home/ubuntu/charon/charon.sqlite
```

## Key Tables

### dry_run_positions
```sql
-- Columns (as of May 2026):
id, candidate_id, mint, symbol, status, opened_at_ms, closed_at_ms, size_sol,
entry_price, entry_mcap, token_amount_est, high_water_price, high_water_mcap,
tp_percent, sl_percent, trailing_enabled, trailing_percent, trailing_armed,
exit_price, exit_mcap, exit_reason, pnl_percent, pnl_sol, llm_decision_id,
execution_mode, entry_signature, exit_signature, token_amount_raw, snapshot_json,
strategy_id, partial_tp_done, intended_full_size_sol, dca_done
```

### llm_decisions
```sql
-- Columns:
id, candidate_id, mint, created_at_ms, verdict, confidence, reason, risks_json, raw_json
```

### candidates
```sql
-- Columns:
id, mint, status, created_at_ms, updated_at_ms, signature, signal_key, candidate_json, filter_result_json
```

### strategies
```sql
-- config_json contains all filter settings
id, name, config_json
```

## Manual Position Creation

```python
import sqlite3, json, time

con = sqlite3.connect('/home/ubuntu/charon/charon.sqlite')
con.row_factory = sqlite3.Row

# 1. Get candidate by ID or mint
row = con.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)).fetchone()
cand = json.loads(row['candidate_json'])

# 2. Extract token info
token = cand.get('token', {})
metrics = cand.get('metrics', {})
price = metrics.get('priceUsd', 0)
mcap = metrics.get('marketCapUsd', 0)

# 3. Create decision record
now_ms = int(time.time() * 1000)
cur = con.execute("""
    INSERT INTO llm_decisions (candidate_id, mint, created_at_ms, verdict, confidence, reason, risks_json, raw_json)
    VALUES (?, ?, ?, 'BUY', 100, 'Manual buy', '[]', ?)
""", (candidate_id, row['mint'], now_ms, json.dumps({
    'verdict': 'BUY', 'confidence': 100, 'reason': 'Manual buy',
    'risks': [], 'suggested_tp_percent': 50, 'suggested_sl_percent': -25
})))
decision_id = cur.lastrowid

# 4. Create position
cur = con.execute("""
    INSERT INTO dry_run_positions (
        candidate_id, mint, symbol, status, opened_at_ms, size_sol,
        entry_price, entry_mcap, high_water_price, high_water_mcap,
        tp_percent, sl_percent, trailing_enabled, trailing_percent, trailing_armed,
        llm_decision_id, execution_mode, strategy_id, partial_tp_done, intended_full_size_sol, dca_done,
        snapshot_json
    ) VALUES (?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'dry_run', 'ponyin_scalp', 0, ?, 0, ?)
""", (
    candidate_id, row['mint'], token.get('symbol', 'UNKNOWN'), now_ms, 0.05,
    price, mcap, price, mcap,
    50, -25, 1, 35,  # tp, sl, trailing_enabled, trailing_percent
    decision_id, 0.05, row['candidate_json']
))
position_id = cur.lastrowid

con.commit()
print(f"Position {position_id} created")
```

## Finding Candidates

```python
# By mint prefix
rows = con.execute("""
    SELECT id, mint, candidate_json FROM candidates 
    WHERE mint LIKE 'AUaCHx%' ORDER BY created_at_ms DESC LIMIT 5
""").fetchall()

# Extract name from candidate_json
for r in rows:
    cand = json.loads(r['candidate_json'])
    name = cand.get('token', {}).get('name', 'N/A')
    print(f"ID: {r['id']}, Name: {name}")
```

## Pitfall: Similar Token Names

Multiple tokens can have similar/identical names but different mints. Always verify by mint address, not name:
- "Norovirus" (2SikwgSLXn5ztkUNXkuKSTZpjNQ9ZwbhxP5qhbmBpump) — different token
- "NORO" (AUaCHxCoJoPS3815hndnh5AG4Veu9pzX5S1kcTcUpump) — the one user wanted

## Pitfall: LLM Decision Without Position

Sometimes LLM creates a BUY decision but position is not created (bug in execution flow). Check for orphaned decisions:

```python
# Find BUY decisions without positions
decisions = con.execute("""
    SELECT d.id, d.mint, d.verdict, d.confidence 
    FROM llm_decisions d
    LEFT JOIN dry_run_positions p ON d.id = p.llm_decision_id
    WHERE d.verdict = 'BUY' AND p.id IS NULL
    ORDER BY d.id DESC LIMIT 10
""").fetchall()

for d in decisions:
    print(f"Orphan decision {d['id']}: {d['mint'][:12]}... ({d['confidence']}%)")
```

If found, manually create position using the decision ID.

## Updating Strategy Filters

### Via Node.js (preferred — sqlite3 CLI often not installed)

```bash
# Check which strategy is enabled and its mcap range
cd ~/charon && node -e "
const Database = require('better-sqlite3');
const db = new Database('charon.sqlite');
const rows = db.prepare('SELECT id, name, enabled, config_json FROM strategies').all();
rows.forEach(r => {
  const cfg = JSON.parse(r.config_json);
  console.log(r.id, '| enabled:', r.enabled, '| min_mcap:', cfg.min_mcap_usd, '| max_mcap:', cfg.max_mcap_usd);
});
"

# Update a specific strategy config field
cd ~/charon && node -e "
const Database = require('better-sqlite3');
const db = new Database('charon.sqlite');
const row = db.prepare('SELECT config_json FROM strategies WHERE id = ?').get('degen');
const cfg = JSON.parse(row.config_json);
cfg.min_mcap_usd = 10000;  // change this value
db.prepare('UPDATE strategies SET config_json = ? WHERE id = ?').run(JSON.stringify(cfg), 'degen');
console.log('Updated');
"
```

### Via Python (alternative)

```python
row = con.execute("SELECT config_json FROM strategies WHERE id='ponyin_scalp'").fetchone()
cfg = json.loads(row['config_json'])

# Modify filters
cfg['max_bundler_ratio'] = 1.0  # disable bundler filter
cfg['max_bot_degen_rate'] = 0.50  # 50%
cfg['min_holders'] = 30

con.execute("UPDATE strategies SET config_json=? WHERE id='ponyin_scalp'", (json.dumps(cfg),))
con.commit()
```

## Settings Sync Pitfall

When updating TP/SL/trailing settings, **update ALL THREE locations**:

1. **Strategy config** (`strategies.config_json`) — affects new auto-positions
2. **Global settings** (`settings` table) — affects manual buys and defaults  
3. **Open positions** (`dry_run_positions`) — affects already-open positions

User often says "cek lagi semuanya biasanya belum ke setting" — always verify all three are synced.

See `references/hybrid-partial-tp-strategy.md` for the recommended hybrid exit strategy.

## After DB Changes

Always restart the bot to pick up changes:
```bash
pm2 restart charon --update-env
```

## LLM Model Configuration

LLM settings are in `.env`, not the database:

```bash
# Check current LLM config
cd ~/charon && grep -i "llm" .env

# Key variables:
# LLM_MODEL=auto          # "auto" for enowX default routing, or specific model
# LLM_BASE_URL=http://localhost:1430/v1
# LLM_API_KEY=enx-...
# LLM_TIMEOUT_MS=60000
```

### Model Options for enowX
- `auto` — default routing (recommended)
- `claude-opus-4.5`, `claude-sonnet-4.6` — may hit content filters on trading prompts
- `deepseek-3.2`, `glm-5`, `minimax-m2.5` — more permissive for trading analysis

### Pitfall: Content Filter Errors
If logs show `"I can't help..."` JSON parse errors, the LLM is refusing trading-related prompts. Solutions:
1. Switch to `LLM_MODEL=auto` (lets enowX route to available model)
2. Use more permissive models like `deepseek-3.2` or `glm-5`
3. Simplify/compact the candidate data sent to LLM

After changing `.env`:
```bash
pm2 restart charon --update-env
```
