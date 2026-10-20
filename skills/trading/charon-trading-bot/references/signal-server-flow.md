# Signal Server → LLM Entry Flow

## Architecture

```
Signal Server (/api/signals)
    ↓
fetchServerSignals() [serverClient.js]
    ↓
triggerCandidate() → candidateHandler
    ↓
processCandidateFromSignals() [orchestrator.js]
    ↓
checkTokenAlreadyEntered() ← DEDUP CHECK
    ↓
buildCandidate() → filter checks
    ↓
decideCandidateBatch() [llm.js] ← LLM SCREENING
    ↓
handleApprovedBuy() → executeLiveBuy()
```

## Entry Points

### 1. Signal Server Polling
**File:** `src/signals/serverClient.js`

- Polls `/api/signals` endpoint every interval (configurable)
- Fetches up to 100 signals with `minSources=2`
- Deduplicates by `mint:sources` key (10-minute TTL)
- Updates `graduated` and `trending` maps in-memory

### 2. Candidate Handler Registration
**File:** `src/pipeline/orchestrator.js` (line 23)

```javascript
setCandidateHandler(processCandidateFromSignals);
```

When signal server finds a new pair, it calls `processCandidateFromSignals(signals)` with:
- `mint` — token address
- `fee` — fee claim object (if present)
- `signature` — transaction signature
- `graduatedCoin` — graduated coin metadata
- `trendingToken` — trending token metadata
- `route` — signal route (e.g., 'fee_graduated_trending')

### 3. Deduplication Gate
**File:** `src/db/positions.js`

```javascript
export function checkTokenAlreadyEntered(mint) {
  const result = db.prepare(`
    SELECT COUNT(*) AS count FROM dry_run_positions WHERE mint = ?
  `).get(mint);
  return result.count > 0;
}
```

**Scope:** Checks entire position history (all statuses: open, closed, partial).
- If token has ANY prior position → skip
- Prevents re-entry of tokens already traded

### 4. Filter Checks
**File:** `src/pipeline/candidateBuilder.js`

Candidate must pass:
- `min_source_count` — minimum signal sources (default: 1)
- `require_fee_claim` — fee claim requirement (default: false)
- `token_age_max_ms` — max token age in ms (default: 3600000 = 1 hour)
- Custom filters (liquidity, holder count, etc.)

### 5. LLM Batch Decision
**File:** `src/pipeline/orchestrator.js` (line 62-63)

If `strategy.use_llm = true`:
```javascript
rows = recentEligibleCandidates(numSetting('llm_candidate_pick_count', 10));
batchDecision = await decideCandidateBatch(rows, candidateId);
```

LLM compares up to 10 recent eligible candidates and picks best one.

**Confidence threshold:** `strategy.llm_min_confidence` (default: 75)
- If confidence < threshold → WATCH (no entry)
- If confidence >= threshold → BUY (execute)

### 6. Entry Execution
**File:** `src/execution/router.js`

If approved:
- `mode='dry_run'` → `createDryRunPosition()`
- `mode='confirm'` → create trade intent (pending user confirmation)
- `mode='live'` → `executeLiveBuy()` (immediate Solana swap)

## Strategy Gates

**Active Strategy:** Degen (as of May 16, 2026)

```
use_llm: true
min_source_count: 1
require_fee_claim: false
token_age_max_ms: 3600000 (1 hour)
max_open_positions: 5
entry_mode: 'immediate' (sniper mode)
```

**Entry modes:**
- `immediate` — enter on signal (sniper, smart_money, degen)
- `wait_for_dip` — store price alert, enter when price dips to target

## Signal Routes

Determined by signal attributes:

| Route | Condition |
|-------|-----------|
| `fee_graduated_trending` | fee + graduated + trending |
| `fee_graduated` | fee + graduated |
| `fee_trending` | fee + trending |
| `graduated_trending` | graduated + trending |
| `multi_source` | sourceCount >= 3 |
| `dual_source` | sourceCount >= 2 |
| `single_source` | sourceCount = 1 |

## Logging

Signal server flow logs to console:
```
[server] 100 signals, 5 triggered, 2 dip alerts, tracking 45
[candidate] filtered 8haahDqc... age_too_old; insufficient_liquidity
[agent] token BCaBbYYk... already entered before, skipping
[agent] BUY skipped: confidence 62 < threshold 75 (strategy degen)
```

## Troubleshooting

**Q: Signal server not triggering entries?**
- Check `SIGNAL_SERVER_URL` and `SIGNAL_SERVER_KEY` in `.env`
- Verify `fetchServerSignals()` is called in app startup
- Check console logs for `[server]` messages

**Q: Token entered multiple times?**
- Deduplication check may be disabled or scoped wrong
- Verify `checkTokenAlreadyEntered()` is called before LLM
- Check database for duplicate positions: `SELECT mint, COUNT(*) FROM dry_run_positions GROUP BY mint HAVING COUNT(*) > 1`

**Q: LLM not screening candidates?**
- Check `strategy.use_llm = true` in database
- Verify `decideCandidateBatch()` is being called
- Check `llm_min_confidence` threshold vs actual confidence scores

**Q: Entries skipped due to max positions?**
- Check `max_open_positions` in strategy config
- Query open positions: `SELECT COUNT(*) FROM dry_run_positions WHERE status='open'`
- Increase limit or close existing positions
