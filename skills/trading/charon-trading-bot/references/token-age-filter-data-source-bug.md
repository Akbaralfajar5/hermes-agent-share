# Token Age Filter Data Source Bug

**Discovered:** May 16, 2026  
**Symptom:** Bot entering 24h+ old trending tokens despite `token_age_max_ms: 3600000` (1h) in strategy config  
**Root Cause:** Two-part bug — variable mismatch + wrong data source

---

## Bug 1: Variable Name Mismatch

**Config:** Strategy uses `token_age_max_ms` (milliseconds)  
**Code:** Filter checked `strat.max_token_age_hours` (hours)  
**Result:** Condition `if (strat.max_token_age_hours > 0)` always false → filter never executed

**Fix:**
```javascript
// Convert ms to hours at runtime
const maxTokenAgeHours = strat.token_age_max_ms > 0 ? strat.token_age_max_ms / (1000 * 60 * 60) : 0;
if (maxTokenAgeHours > 0) {
  // filter logic
}
```

---

## Bug 2: Wrong Data Source

**Original code:**
```javascript
if (maxTokenAgeHours > 0 && candidate.graduation?.graduationDate) {
  const ageMs = Date.now() - candidate.graduation.graduationDate;
  // ...
}
```

**Problem:** `candidate.graduation` is **NULL for trending tokens** (only exists for graduated/fee-claim route).

**Data structure:**
- **Trending tokens:** `graduation: null`, but have `jupiterAsset.createdAt: "2026-05-15T16:25:38Z"`
- **Graduated tokens:** `graduation.graduationDate: 1778788535000` (timestamp ms)

**Result:** Filter skipped all trending tokens even after fixing variable mismatch.

---

## Fix: Multi-Source Priority

Check token creation date from multiple sources:

```javascript
// Token age filter (avoid late entry)
const maxTokenAgeHours = strat.token_age_max_ms > 0 ? strat.token_age_max_ms / (1000 * 60 * 60) : 0;
if (maxTokenAgeHours > 0) {
  // Check token creation date from multiple sources
  let tokenCreatedAt = null;
  
  // Priority 1: Jupiter asset creation date (ISO string)
  if (candidate.jupiterAsset?.createdAt) {
    tokenCreatedAt = new Date(candidate.jupiterAsset.createdAt).getTime();
  }
  // Priority 2: Graduation date (timestamp ms, for graduated tokens)
  else if (candidate.graduation?.graduationDate) {
    tokenCreatedAt = candidate.graduation.graduationDate;
  }
  // Priority 3: First pool creation (ISO string, fallback)
  else if (candidate.jupiterAsset?.firstPool?.createdAt) {
    tokenCreatedAt = new Date(candidate.jupiterAsset.firstPool.createdAt).getTime();
  }
  
  if (tokenCreatedAt) {
    const nowMs = Date.now();
    const ageMs = nowMs - tokenCreatedAt;
    const ageHours = ageMs / (1000 * 60 * 60);
    if (ageHours > maxTokenAgeHours) {
      failures.push(`token age: ${ageHours.toFixed(1)}h > max ${maxTokenAgeHours.toFixed(1)}h (late entry)`);
    }
  }
}
```

---

## Verification

After fix, logs show proper rejection:

```bash
tail -f ~/.pm2/logs/charon-out.log | grep "token age"
```

**Expected output:**
```
[candidate] filtered 6CVd9hqv... market cap max: 212652.51 > 30000; token age: 110.2h > max 1.0h (late entry)
[candidate] filtered 9shb4VuR... market cap max: 431796.44 > 30000; token age: 66.4h > max 1.0h (late entry)
[candidate] filtered 6vfsfb18... market cap max: 35470.42 > 30000; token age: 71.9h > max 1.0h (late entry)
```

---

## Don't Confuse With

**`LLM_CANDIDATE_MAX_AGE_MS`** (in `.env`) — Controls how old the **database candidate record** can be before LLM screening. This is **candidate freshness** (how long since signal was stored), NOT token age since creation. Unrelated to token creation date filtering.

---

## File Location

`~/charon/src/pipeline/candidateBuilder.js` — lines ~115-140 in `filterCandidate()` function

---

## Impact

Before fix: Bot entered tokens created 24h-110h ago (late entry, poor performance)  
After fix: Bot only considers tokens ≤ 1 hour old (fresh tokens, better entry timing)
