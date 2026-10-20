# LLM Concurrency Queue & Prompt Engineering

## Concurrency System (src/pipeline/orchestrator.js)

The old debounce system (single LLM call, 15s cooldown) dropped tokens that arrived while LLM was busy. Replaced with proper concurrent queue:

```js
// LLM concurrency: 3 parallel slots + queue max 10
const LLM_MAX_CONCURRENT = 3;
const LLM_QUEUE_MAX = 10;
let llmActiveCount = 0;
const llmQueue = []; // { candidate, candidateId, strat, resolve }
```

### How it works:
1. If `llmActiveCount < 3` → immediately process (increment counter)
2. If all 3 slots busy → push to queue (max 10 items)
3. If queue full (10) → drop with log message
4. When a slot frees up → `drainLlmQueue()` pops next item and processes it
5. Queued items get **re-checked** before LLM call (positions, cooldown, filters may have changed)

### Key function: `drainLlmQueue()`
```js
function drainLlmQueue() {
  while (llmQueue.length > 0 && llmActiveCount < LLM_MAX_CONCURRENT) {
    const item = llmQueue.shift();
    llmActiveCount++;
    processQueuedCandidate(item).finally(() => {
      llmActiveCount--;
      drainLlmQueue();
    });
    item.resolve();
  }
}
```

### `processQueuedCandidate()` re-checks:
- `canOpenMorePositions()` — may have filled while queued
- `hasMintPosition(mint)` — may have entered via another path
- `isMintOnSlCooldown(mint)` — may have been SL'd while queued

### Log messages:
- `[agent] LLM busy (3/3), queued XXX... (queue: N)` — queued successfully
- `[agent] LLM queue full (10), dropping XXX...` — dropped (queue overflow)
- `[agent] queued LLM error for XXX...: message` — queued item failed

### Pitfalls:
- The queue stores `{ candidate, candidateId, strat, resolve }` — all from the closure at queue time
- `resolve()` is called immediately when dequeued (unblocks the original Promise)
- If LLM endpoint is slow (>30s per call), queue fills fast. Monitor queue depth.
- Increasing `LLM_MAX_CONCURRENT` beyond 3 risks 503s from enowX endpoint

---

## Position Check Interval (src/config.js)

```js
export const POSITION_CHECK_MS = Number(process.env.POSITION_CHECK_MS || 5_000);
```

Changed from 10s to 5s. Reason: SL at -20% was exiting at -42% because token dumped between checks. 5s reduces worst-case slip but doesn't eliminate it (meme coins can dump 20%+ in 5s).

**Trade-off:** More API calls to Jupiter for price checks. If rate-limited, can bump back to 7-8s.

---

## LLM System Prompt (src/pipeline/llm.js)

### Entry Signals (current):
1. **DIP BUY** — token turun >20% dari ATH, fundamentals kuat (holders, liquidity >$10K, volume)
2. **MOMENTUM BUY** — token naik, belum peak (distance from ATH <15%), volume tinggi, holders naik
3. **EARLY ENTRY** — token baru mcap $7K-$50K, holders naik cepat, narrative/catalyst
4. **KOL SIGNAL** — renowned_count >= 3 = very strong signal, prioritaskan

### Signal Strength Hierarchy:
- renowned_count (KOL) >= 3: VERY STRONG
- smart_degen_count >= 5: strong
- Token in multiple sources (dual_source): strong
- Kombinasi KOL + smart wallet + volume = highest conviction

### AVOID rules:
- Token at ATH + volume turun + holders flat = late entry
- Token tanpa liquidity (<$5K) = rug risk
- Token dump >50% tanpa recovery = dead cat

### Removed: `topBlastRisk`
Was blocking momentum entries. Removed from both:
- `compactCandidateForLlm()` — no longer sends topBlastRisk field
- System prompt — no longer references "top-blast risk"

Reason: contradicts MOMENTUM BUY signal. Token near ATH is fine if volume/holders support it.

### Prompt format:
- Joined with `\n` (not space) for readability
- Sections use `##` headers
- Indonesian language enforced for reason/risks fields

---

## Route Blacklisting (src/pipeline/candidateBuilder.js)

Added at top of `filterCandidate()`:
```js
const BLOCKED_ROUTES = ['smart_copy'];
const route = candidate.signals?.route;
if (route && BLOCKED_ROUTES.includes(route)) {
  failures.push(`route blacklisted: ${route}`);
  return { passed: false, failures, strategy: strat.id };
}
```

Returns early (before enrichment/mcap checks) to save resources. The scanner still runs but tokens are blocked at filter stage.

To re-enable a route: remove from `BLOCKED_ROUTES` array and restart.

---

## KOL Integration (src/signals/newPairs.js)

### Data flow:
1. Scanner polls GMGN `/defi/quotation/v1/rank/sol/swaps/5m?orderby=renowned_count&direction=desc&limit=30`
2. Pre-filter: `renowned_count < 3` → skip (don't waste LLM call on weak KOL signal)
3. `renowned_count` passed as `trendingToken.renowned_count` to pipeline
4. `candidateBuilder.js` stores as `metrics.trendingKolCount`
5. LLM sees it in candidate data and prompt tells it to prioritize

### Threshold rationale:
- 1 KOL = noise (could be random)
- 2 KOL = interesting but not strong enough alone
- 3+ KOL = strong consensus signal, worth entry even without other confirmation
