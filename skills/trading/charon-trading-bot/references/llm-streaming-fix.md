# LLM Streaming Response Fix

## Problem

Bot crashes or hangs when LLM endpoint returns streaming responses (SSE chunks) instead of a single JSON response. Axios receives:

```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk",...}
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk",...}
```

Instead of:

```json
{"id":"chatcmpl-xxx","object":"chat.completion","choices":[{"message":{"content":"..."}}]}
```

Result: `res.data?.choices?.[0]?.message?.content` is undefined, JSON parse fails, LLM batch decision returns WATCH verdict (fallback), no BUY signals execute.

**Error in logs:** `[llm] batch failed: Request failed with status code 500` or silent parse failures.

## Root Cause

LLM endpoint (kr/claude-haiku-4.5 via localhost:20128) defaults to `stream: true`. Axios (non-streaming HTTP client) cannot reassemble SSE chunks into a single response object.

## Solution

**File:** `src/pipeline/llm.js`, line ~108

Add `stream: false` to the request payload:

```javascript
const res = await axios.post(`${LLM_BASE_URL.replace(/\/$/, '')}/chat/completions`, {
  model: LLM_MODEL,
  temperature: 0.2,
  stream: false,  // ← ADD THIS LINE
  messages: [
    { role: 'system', content: system },
    { role: 'user', content: JSON.stringify(user) },
  ],
}, {
  timeout: LLM_TIMEOUT_MS,
  headers: { authorization: `Bearer ${LLM_API_KEY}`, 'content-type': 'application/json' },
});
```

## Verification

After fix, test LLM endpoint directly:

```bash
curl -X POST http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-3d832eacf8314504-..." \
  -d '{
    "model": "kr/claude-haiku-4.5",
    "stream": false,
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }' | jq '.choices[0].message.content'
```

Should return a single JSON object with `choices[0].message.content` populated (not SSE chunks).

Then restart bot: `pm2 restart charon`

Check logs for `[llm] batch` — should see successful decisions, not errors.

## Related

- **File:** `src/pipeline/llm.js` (decideCandidateBatch function)
- **Config:** `LLM_BASE_URL` from `.env` (default: `http://localhost:20128/v1`)
- **Model:** `kr/claude-haiku-4.5`
- **Timeout:** `LLM_TIMEOUT_MS` (default: 30000ms)
