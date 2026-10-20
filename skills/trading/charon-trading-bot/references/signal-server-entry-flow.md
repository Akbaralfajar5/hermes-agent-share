# Signal Server Entry Flow & Deduplication

## Complete Pipeline

```
Signal Server (/api/signals)
    ↓
fetchServerSignals() [serverClient.js]
    ↓
triggerCandidate() → candidateHandler
    ↓
processCandidateFromSignals() [orchestrator.js]
    ↓
[1] checkTokenAlreadyEntered(mint) ← DEDUP GATE
    ↓ (if already entered, skip)
[2] canOpenMorePositions() ← MAX POSITIONS GATE
    ↓ (if max reached, skip)
[3] buildCandidate() → filter checks
    ↓ (if filters fail, skip)
[4] LLM batch decision (if use_llm: true)
    ↓
[5] handleApprovedBuy() → executeLiveBuy()
    ↓
Position opened (live mode)
```

## Deduplication Gate (Step 1)

**Function:** `checkTokenAlreadyEntered(mint)` in `src/db/positions.js`

```python
# Query checks entire position history
SELECT COUNT(*) FROM dry_run_positions WHERE mint = ?
```

**Returns:** `true` if mint has ANY prior position (open, closed, or partial)

**Placement:** Must be **first check** in `processCandidateFromSignals()` — before LLM, before max positions check.

**Why first?** Avoid wasting LLM calls and enrichment on known tokens.

## Strategy Gates (Step 2-3)

After dedup, signal passes through strategy filters:

- `min_source_count` — require N sources (default: 1)
- `require_fee_claim` — require fee claim signal (default: false)
- `token_age_max_ms` — reject if older than N ms (default: 3600000 = 1h)
- `min_mcap_usd` — reject if mcap < N USD (default: 0 for degen, 10000 for smart_money)
- `max_mcap_usd` — reject if mcap > N USD (default: 30000 for degen)
- `min_holders` — reject if holders < N (default: 1)
- `max_top20_holder_percent` — reject if top 20 > N% (default: 100)

**Critical:** Strategy config is database-first. Check `strategies.config_json` for active strategy, not code defaults.

```python
import sqlite3, json
conn = sqlite3.connect('charon.sqlite')
c = conn.cursor()
c.execute("SELECT config_json FROM strategies WHERE enabled=1")
config = json.loads(c.fetchone()[0])
print(f"min_mcap_usd: {config.get('min_mcap_usd', 0)}")
```

## LLM Batch Decision (Step 4)

If `use_llm: true`, signal enters batch screening:

1. Fetch 10 recent eligible candidates from database
2. Send batch to LLM with current signal as trigger
3. LLM ranks candidates, picks best
4. If current signal selected → BUY
5. If different candidate selected → WATCH current, BUY selected
6. If no candidate selected → WATCH current

**Confidence gate:** Only execute if `confidence >= llm_min_confidence` (default: 75%)

## Entry Execution (Step 5)

If verdict is BUY and confidence passes:

1. Refresh candidate (re-check filters with fresh data)
2. If filters still pass → create position
3. If filters fail on refresh → reject with reason

**Position creation:**
- Mode: `dry_run`, `confirm`, or `live`
- Size: `strategy.position_size_sol` (default: 0.05 SOL)
- TP/SL: Locked from LLM (use strategy values only)
- Trailing: Enabled if `strategy.trailing_enabled: true`

## Signal Server Response Format

Server returns array of signals with structure:

```json
{
  "mint": "5vrEa5bQMRFDw6upTuSVX3zFaKCjSffSsGDyLv89oeHq",
  "name": ":)",
  "symbol": ":)",
  "priceUsd": 0.00123,
  "marketCapUsd": 9500,
  "liquidityUsd": 8000,
  "volume5m": 1200,
  "volume24h": 9600,
  "holders": 192,
  "sources": ["trending", "fee_claim"],
  "sourceCount": 2,
  "graduated": {
    "distanceFromAthPercent": -88.2,
    "volume24h": 0
  },
  "trending": {
    "buys": 45,
    "sells": 12,
    "volume": 9600
  },
  "feeClaim": {
    "distributedSol": 18.8296,
    "shareholders": [...]
  }
}
```

## Deduplication Scope

Current implementation: `checkTokenAlreadyEntered()` checks **all statuses** (open, closed, partial).

**Variants:**
- Allow re-entry after close: `WHERE mint = ? AND status != 'closed'`
- Allow re-entry after timeout: `WHERE mint = ? AND opened_at_ms > (now - 24h)`
- Per-strategy dedup: Add `strategy_id` column to positions, check per-strategy

## Testing Deduplication

```python
import sqlite3

conn = sqlite3.connect('charon.sqlite')
c = conn.cursor()

# Check if token already entered
mint = "5vrEa5bQMRFDw6upTuSVX3zFaKCjSffSsGDyLv89oeHq"
c.execute("SELECT COUNT(*) FROM dry_run_positions WHERE mint = ?", (mint,))
count = c.fetchone()[0]
print(f"Token {mint[:8]}... entered {count} time(s)")

# List all unique mints with entry count
c.execute("""
SELECT mint, COUNT(*) as times_entered
FROM dry_run_positions
GROUP BY mint
ORDER BY times_entered DESC
LIMIT 20
""")

for row in c.fetchall():
    print(f"  {row[0][:8]}... : {row[1]} entries")

conn.close()
```

## Logs to Watch

When dedup is active, logs show:

```
[agent] token 5vrEa5bQ... already entered before, skipping
```

When max positions reached:

```
[agent] max positions reached (5/5), skipping 8haahDqc...
```

When filters reject:

```
[candidate] filtered 8haahDqc... market cap min: 9505.78 < 10000
```

When LLM confidence too low:

```
[agent] BUY skipped: confidence 42 < threshold 75 (strategy degen) 8haahDqc...
```
