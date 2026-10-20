# LLM Provider Switching for Charon Bot

## Overview
Charon bot has **two separate LLM call sites** that must both be updated when switching providers:
1. `src/pipeline/llm.js` — candidate screening decisions
2. `src/learning/lessons.js` — learning from dry-run evidence

## Switching Workflow

### 1. Test New Provider Endpoint
```bash
# Discover available models
curl -s http://<new-base-url>/v1/models \
  -H "Authorization: Bearer <api-key>" | jq -r '.data[].id'

# Test with sample request
curl -s -X POST http://<new-base-url>/v1/chat/completions \
  -H "Authorization: Bearer <api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<provider/model-id>",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 50
  }' | jq '.choices[0].message.content // .error'
```

### 2. Update .env
```bash
# Three variables must match the provider's format
LLM_BASE_URL=http://43.159.56.39:1430/v1
LLM_API_KEY=enx-652efacd9a8d161549282e07d29e532cbac275423fee752f3eb27da1d1d9d2c3
LLM_MODEL=kiro/claude-haiku-4.5  # Use provider/model format from /v1/models
```

### 3. Verify Both Call Sites Use Fetch (Not Axios)
```bash
# Check for axios imports in LLM-related files
grep -n "import.*axios" src/pipeline/llm.js src/learning/lessons.js

# If found, remove them — both files should use native fetch()
```

### 4. Restart and Monitor
```bash
pm2 restart charon --update-env
sleep 15
pm2 logs charon --lines 50 --nostream | grep -E "llm|learn"
```

## Common Pitfalls

### Model Name Format Errors
**Symptom:** `invalid model 'claude-haiku-4.5': use provider/model_id format`

**Cause:** Provider requires `provider/model` format (e.g., `kiro/claude-haiku-4.5`), not bare model name.

**Fix:** Query `/v1/models` endpoint to get exact model IDs, then update `LLM_MODEL` in `.env`.

### Axios vs Fetch Confusion
**Symptom:** Error message `Request failed with status code 500` but logs from fetch code never appear.

**Cause:** Old axios imports still present, or cached module using axios.

**Fix:**
1. Remove `import axios from 'axios';` from both `llm.js` and `lessons.js`
2. Force restart: `pm2 delete charon && pm2 start src/app.js --name charon`

### Two LLM Call Sites
**Symptom:** Screening works but learning fails (or vice versa).

**Cause:** Only updated one of the two files that call LLM.

**Fix:** Always update both:
- `src/pipeline/llm.js` — `decideCandidateBatch()` function
- `src/learning/lessons.js` — `generateLessons()` function

## Provider-Specific Notes

### enowX Labs (http://43.159.56.39:1430/v1)
- Model format: `kiro/<model-name>`
- Available models: `kiro/claude-haiku-4.5`, `kiro/claude-sonnet-4.5`, `kiro/claude-opus-4.5`, etc.
- Auth: Bearer token with `enx-` prefix
- Supports standard OpenAI-compatible `/v1/chat/completions` endpoint

### 9router (local, http://localhost:20128/v1)
- Model format: `kr/<model-name>` (e.g., `kr/claude-haiku-4.5`)
- Runs locally, no external network required
- May have rate limiting or concurrent request limits

## Debugging LLM Errors

### Add Request Logging
```javascript
// In src/pipeline/llm.js, before fetch call:
const requestBody = JSON.stringify({...});
console.log(`[llm] request size: ${requestBody.length} bytes, ${user.candidates.length} candidates`);
```

### Add Function Entry Logging
```javascript
// At start of _decideCandidateBatch():
console.log(`[llm] _decideCandidateBatch called with ${rows.length} rows, trigger=${triggerCandidateId}`);

// At start of generateLessons():
console.log(`[learn] generateLessons called`);
```

### Check Which Function Is Failing
If logs never appear, the error is happening **before** the logged function is called — check:
1. Throttle queue (`throttledLlmCall` wrapper)
2. Data preparation (`compactCandidateForLlm`)
3. Early returns (ENABLE_LLM check, API key check)
