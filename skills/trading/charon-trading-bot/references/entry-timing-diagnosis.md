# Entry Timing Diagnosis

When dry run PnL is negative, diagnose entry timing quality before adjusting strategy parameters.

## Diagnostic Queries

### 1. Closed Positions Deep Analysis

```js
const Database = require('better-sqlite3');
const db = new Database('charon.sqlite');

const positions = db.prepare(`
  SELECT * FROM dry_run_positions 
  WHERE status='closed' AND exit_reason != 'manual_reset'
  ORDER BY id DESC
`).all();

positions.forEach(p => {
  const holdMin = ((p.closed_at_ms - p.opened_at_ms) / 60000).toFixed(1);
  const peakPct = ((p.high_water_mcap / p.entry_mcap) - 1) * 100;
  console.log(`--- ${p.symbol} (#${p.id}) ---`);
  console.log(`  Entry MCap: $${Math.round(p.entry_mcap)} | Exit: $${Math.round(p.exit_mcap)} | Peak: $${Math.round(p.high_water_mcap)}`);
  console.log(`  PnL: ${p.pnl_percent.toFixed(1)}% | Exit: ${p.exit_reason}`);
  console.log(`  Peak from entry: +${peakPct.toFixed(1)}% | Hold: ${holdMin} min`);
});
```

### 2. Entry Quality Assessment

Key metric: **peak from entry**. If peak = 0%, token NEVER went up after entry (entered at exact top).

| Peak from Entry | Quality | Meaning |
|----------------|---------|---------|
| +0% | ❌ TOPPED | Entered at exact peak, immediate dump |
| < +5% | ❌ TOPPED | Essentially entered at top |
| +5% to +20% | ⚠️ WEAK | Some upside but not enough |
| > +20% | ✅ HAD ROOM | Good entry, strategy issue if still lost |

### 3. Chart Context at Entry (from snapshot_json)

```js
positions.forEach(p => {
  const snap = JSON.parse(p.snapshot_json || '{}');
  const chart = snap.candidate?.chart || {};
  const m = snap.candidate?.metrics || {};
  console.log(`${p.symbol}: ATH dist ${chart.distanceFromAthPercent?.toFixed(1)}%, priceChange5m ${m.dexPriceChange5m}%, topBlastRisk ${chart.topBlastRisk}, vol5m $${Math.round(m.dexVolume5m||0)}`);
});
```

### 4. LLM Decision Quality

```js
const decisions = db.prepare(`
  SELECT d.confidence, d.reason, p.symbol, p.pnl_percent, p.exit_reason
  FROM dry_run_positions p
  LEFT JOIN decision_logs d ON d.selected_candidate_id = p.candidate_id
  WHERE p.status='closed' AND p.exit_reason != 'manual_reset'
  ORDER BY p.id DESC
`).all();
```

## Common Patterns & Fixes

### Pattern 1: Dead Cat Bounce Entry
- **Signal:** priceChange5m > +100%, distanceFromATH < -40%
- **What happens:** Token pumped briefly from deep dump, bot enters, token continues dumping
- **Fix:** Hard filter `priceChange5m > 100%` → reject

### Pattern 2: Zero Volume Entry
- **Signal:** dexVolume5m = 0, dexVolume1h = 0
- **What happens:** Token has no active buyers, bot enters based on narrative alone
- **Fix:** Hard filter `vol1h === 0 && age > 10min` → reject

### Pattern 3: ATH Entry (topBlastRisk)
- **Signal:** topBlastRisk = true, priceChange5m > +40%
- **What happens:** Token at/near all-time high, high probability of dump
- **Fix:** Hard filter `topBlastRisk === true` → reject

### Pattern 4: Narrative Trap
- **Signal:** LLM confidence 60-68%, strong narrative, weak price action
- **What happens:** LLM loves the story but ignores timing red flags
- **Fix:** Harden LLM prompt with explicit timing rules (JANGAN BUY if...)

## Hard Filters Implementation

Location: `src/pipeline/candidateBuilder.js`, inside `filterCandidate()`, after the Anti-ATH block and before the Trending filters block.

```js
// Hard filter: reject dead tokens (zero volume in last 1h = no buyers)
const vol1h = Number(candidate.metrics.dexVolume1h || 0);
if (vol1h === 0 && Number(candidate.metrics.dexAgeMs || 0) > 600000) {
  failures.push(`dead token: volume 1h=$0, age>${Math.round((candidate.metrics.dexAgeMs||0)/60000)}min`);
}

// Hard filter: reject parabolic pumps (likely to dump immediately)
const priceChange5m = Number(candidate.metrics.dexPriceChange5m || 0);
if (priceChange5m > 100) {
  failures.push(`parabolic pump: priceChange5m=${priceChange5m.toFixed(0)}% > 100%`);
}

// Hard filter: reject topBlastRisk = true (at or near ATH, high dump probability)
if (candidate.chart?.topBlastRisk === true) {
  failures.push(`topBlastRisk: token at/near ATH, high dump probability`);
}
```

**PITFALL:** These filters can get lost during file patches if the patch tool operates on a partial view of the file. After ANY patch to `candidateBuilder.js`, ALWAYS verify with:
```bash
grep -n "dead token\|parabolic\|topBlastRisk" src/pipeline/candidateBuilder.js
```
Should show 6 lines (2 per filter: comment + push). If missing, re-add them.

## Volume Filter Tuning

- `vol5m === 0 AND vol1h === 0` was TOO strict — many tokens from signal server show 0 volume in 5m window due to GMGN bridge data delay
- `vol1h === 0 AND age > 10min` is the correct threshold — if a token has been around 10+ minutes with zero 1h volume, it's truly dead
- Brand new tokens (age < 10min) are exempt because they haven't had time to accumulate volume data

## LLM Prompt Hardening

When LLM keeps buying bad entries despite having the data, the issue is prompt softness. The LLM prioritizes narrative over timing. Fix by adding explicit RULES (not suggestions) in the system prompt:

- Use imperative language: "JANGAN BUY" not "sebaiknya hindari"
- List specific numeric thresholds: ">50%" not "terlalu tinggi"
- State consequences: "ini parabolic pump yang akan dump"
- Define ideal entry: "pullback sehat -15% sampai -30% dari ATH"
- Bias toward PASS: "kamu lebih suka PASS daripada entry yang meragukan"

## Full Audit Checklist

After making filter/strategy changes, run this audit:

1. Strategy config values match intent (query `strategies.config_json`)
2. Settings table matches strategy config (no mismatches)
3. Hard filters present in `candidateBuilder.js` (grep check)
4. LLM prompt contains timing rules (grep "SANGAT SELEKTIF")
5. `bot_paused` = false (unless intentionally stopped)
6. Error log clean (`cat /home/ubuntu/.pm2/logs/charon-error.log`)
7. Syntax check all modified files (`node --check`)
8. GMGN bridge responding (curl localhost:9876)
9. LLM endpoint responding (curl with auth)
10. PM2 entry point is `index.js` (not `src/app.js`)
