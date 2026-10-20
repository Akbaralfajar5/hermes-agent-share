# Token Age Filter Bug

**Discovered:** May 16, 2026  
**Symptom:** Bot entering tokens 24+ hours old despite `LLM_CANDIDATE_MAX_AGE_MS=3600000` (1h) in `.env`  
**Root cause:** Variable name mismatch between config and code

## The Bug

**Config uses:** `token_age_max_ms` (milliseconds) in strategy JSON  
**Code checks:** `strat.max_token_age_hours` (hours) in `candidateBuilder.js`  
**Result:** Condition `if (strat.max_token_age_hours > 0)` always false → filter never executes

### Code Location

`src/pipeline/candidateBuilder.js`, line 116:

```javascript
// Token age filter (avoid late entry)
if (strat.max_token_age_hours > 0 && candidate.graduation?.graduationDate) {
  const nowMs = Date.now();
  const ageMs = nowMs - candidate.graduation.graduationDate;
  const ageHours = ageMs / (1000 * 60 * 60);
  if (ageHours > strat.max_token_age_hours) {  // ← NEVER TRUE
    failures.push(`token age: ${ageHours.toFixed(1)}h > max ${strat.max_token_age_hours}h (late entry)`);
  }
}
```

### Strategy Config

`charon.sqlite` → `strategies` table → `config_json`:

```json
{
  "token_age_max_ms": 3600000,  // ← Config uses milliseconds
  "max_open_positions": 2,
  // ... other settings
}
```

### Confusion with LLM_CANDIDATE_MAX_AGE_MS

**Important:** `.env` has `LLM_CANDIDATE_MAX_AGE_MS=3600000` which controls **candidate freshness** (how old the DB record is), NOT token age since graduation. These are two separate filters:

1. **Candidate freshness** (`LLM_CANDIDATE_MAX_AGE_MS`) — How long ago was the candidate row created in DB? Prevents LLM from screening stale data.
2. **Token age** (`token_age_max_ms`) — How long ago did the token graduate on Pump.fun? Prevents late entry into old tokens.

User updated `.env` thinking it would filter token age, but it only affected candidate freshness.

## The Fix

Convert milliseconds to hours at runtime:

```javascript
// Token age filter (avoid late entry)
const maxTokenAgeHours = strat.token_age_max_ms > 0 ? strat.token_age_max_ms / (1000 * 60 * 60) : 0;
if (maxTokenAgeHours > 0 && candidate.graduation?.graduationDate) {
  const nowMs = Date.now();
  const ageMs = nowMs - candidate.graduation.graduationDate;
  const ageHours = ageMs / (1000 * 60 * 60);
  if (ageHours > maxTokenAgeHours) {
    failures.push(`token age: ${ageHours.toFixed(1)}h > max ${maxTokenAgeHours.toFixed(1)}h (late entry)`);
  }
}
```

**Applied:** `src/pipeline/candidateBuilder.js`, lines 115-123

## Verification

After fix + restart, check logs for rejection messages:

```bash
tail -f ~/.pm2/logs/charon-out.log | grep "token age"
```

Expected output:
```
[candidate] filtered ABC123... token age: 24.3h > max 1.0h (late entry)
[candidate] filtered DEF456... token age: 2.1h > max 1.0h (late entry)
```

If no logs appear, filter still not working. Check:
1. Strategy config has `token_age_max_ms > 0`
2. Candidates have `graduation.graduationDate` field (only graduated tokens)
3. Bot restarted after code change (`pm2 restart charon`)

## Session Context

**User complaint:** "bro lihat kamu masih entry token yg sudah berumur 1 hari" (you're still entering 1-day-old tokens)  
**Config at time:** `.env` had `LLM_CANDIDATE_MAX_AGE_MS=600000` (10 min), user updated to `3600000` (1h) thinking it would filter token age  
**Actual issue:** Code never checked `token_age_max_ms` from strategy config due to variable name mismatch  
**Fix applied:** May 16, 2026 14:05 UTC  
**Verification:** Logs now show "token age: X.Xh > max 1.0h (late entry)" rejections

## Related Settings

- **Strategy config:** `token_age_max_ms` (milliseconds) — Token age since graduation
- **`.env` config:** `LLM_CANDIDATE_MAX_AGE_MS` (milliseconds) — Candidate DB record freshness
- **Default strategy:** `src/db/settings.js` line 81 — `token_age_max_ms: 3600000` (1h default)

## Pitfall

Don't confuse these two age filters:
1. **Token age** — How old is the token since Pump.fun graduation? (prevents late entry)
2. **Candidate freshness** — How old is the candidate DB record? (prevents LLM from screening stale data)

Both use milliseconds in config, but serve different purposes. User updated the wrong one initially.: Variable Name Mismatch

**Discovered:** May 16, 2026  
**Severity:** Critical — filter never executed, allowing late entries on 1-day-old tokens

## Problem

Token age filter was **completely non-functional** due to variable name mismatch between strategy config and filter code:

- **Strategy config** (database): `token_age_max_ms` (milliseconds)
- **Filter code** (candidateBuilder.js): `max_token_age_hours` (hours)

Result: `strat.max_token_age_hours` was always `undefined`, so the filter condition never triggered.

## Symptoms

- User reports: "bro lihat kamu masih entry token yg sudah berumur 1 hari"
- No "token age" rejection logs in PM2 output
- Bot entering tokens 24+ hours old despite config showing 1-hour limit
- `.env` shows `LLM_CANDIDATE_MAX_AGE_MS=3600000` but this is **candidate freshness** (how old the DB row is), NOT token age since graduation

## Root Cause

**File:** `src/pipeline/candidateBuilder.js` (line 116)

```javascript
// BROKEN CODE (before fix):
if (strat.max_token_age_hours > 0 && candidate.graduation?.graduationDate) {
  const nowMs = Date.now();
  const ageMs = nowMs - candidate.graduation.graduationDate;
  const ageHours = ageMs / (1000 * 60 * 60);
  if (ageHours > strat.max_token_age_hours) {  // ← always undefined!
    failures.push(`token age: ${ageHours.toFixed(1)}h > max ${strat.max_token_age_hours}h (late entry)`);
  }
}
```

Strategy config uses `token_age_max_ms` (confirmed in `src/db/settings.js` line 81, `src/db/connection.js` default strategies).

## Fix

Convert `token_age_max_ms` (milliseconds) to hours at runtime:

```javascript
// FIXED CODE:
const maxTokenAgeHours = strat.token_age_max_ms > 0 ? strat.token_age_max_ms / (1000 * 60 * 60) : 0;
if (maxTokenAgeHours > 0 && candidate.graduation?.graduationDate) {
  const nowMs = Date.now();
  const ageMs = nowMs - candidate.graduation.graduationDate;
  const ageHours = ageMs / (1000 * 60 * 60);
  if (ageHours > maxTokenAgeHours) {
    failures.push(`token age: ${ageHours.toFixed(1)}h > max ${maxTokenAgeHours.toFixed(1)}h (late entry)`);
  }
}
```

**Patch applied:** `src/pipeline/candidateBuilder.js` line 115-122

## Verification

After fix + restart:

```bash
tail -f ~/.pm2/logs/charon-out.log | grep "token age"
# Expected output:
# [candidate] filtered ABC123... token age: 24.3h > max 1.0h (late entry)
```

If no logs appear, filter is still broken or no old tokens are being screened.

## Related Config

**Two separate age settings** (don't confuse):

1. **Token age since graduation** (what we fixed):
   - Config: `token_age_max_ms` in strategy table
   - Default: 3600000 ms (1 hour)
   - Purpose: Reject tokens that graduated >1h ago (late entry)
   - File: `src/pipeline/candidateBuilder.js`

2. **Candidate freshness** (unrelated):
   - Config: `LLM_CANDIDATE_MAX_AGE_MS` in `.env`
   - Default: 600000 ms (10 min)
   - Purpose: Reject stale DB rows (data older than 10 min)
   - File: `src/db/candidates.js` line 75

User wanted #1 (token age), not #2 (candidate freshness).

## Impact

Before fix:
- Bot entered tokens 24+ hours old
- No age-based filtering occurred
- Late entries = poor risk/reward (pump already happened)

After fix:
- Tokens >1h old rejected at candidate stage
- Logs show "token age: X.Xh > max 1.0h (late entry)"
- Only fresh tokens (<1h since graduation) pass filter

## Prevention

When adding new strategy filters:
1. **Use consistent variable names** between config and code
2. **Log filter rejections** to verify execution
3. **Test with known-old tokens** to confirm filter triggers
4. **Check both strategy table AND default strategy** in connection.js

## See Also

- `references/token-age-filter.md` — Original implementation guide (had the bug)
- `references/reserve-balance-diagnostic.md` — Separate issue discovered same session
