# LLM Error Debugging

## Problem
Axios throws generic "Request failed with status code 500" without revealing actual error from LLM server. Makes debugging impossible.

## Root Cause
- Axios throws on non-2xx status by default
- Error object doesn't include response body details
- Nested try-catch needed to capture both network errors and response errors

## Solution: Enhanced Error Handling

**File:** `src/pipeline/llm.js`, function `decideCandidateBatch()`

### Pattern: Nested Try-Catch with validateStatus

```javascript
try {
  let res;
  try {
    res = await axios.post(`${LLM_BASE_URL.replace(/\/$/, '')}/chat/completions`, {
      model: LLM_MODEL,
      temperature: 0.2,
      stream: false,  // CRITICAL: disable streaming
      messages: [
        { role: 'system', content: system },
        { role: 'user', content: JSON.stringify(user) },
      ],
    }, {
      timeout: LLM_TIMEOUT_MS,
      headers: { authorization: `Bearer ${LLM_API_KEY}`, 'content-type': 'application/json' },
      validateStatus: () => true,  // Don't throw on any status
    });
  } catch (axiosErr) {
    // Network error, timeout, or other axios-level error
    console.log(`[llm] axios error: ${axiosErr.code} ${axiosErr.message}`);
    if (axiosErr.response) {
      console.log(`[llm] response status: ${axiosErr.response.status}`);
      console.log(`[llm] response data: ${JSON.stringify(axiosErr.response.data).slice(0, 300)}`);
    }
    throw axiosErr;
  }
  
  // Now check response status manually
  if (res.status !== 200) {
    const errMsg = res.data?.error?.message || res.statusText || `HTTP ${res.status}`;
    console.log(`[llm] batch failed (${res.status}): ${errMsg}`);
    throw new Error(errMsg);
  }
  
  // Process successful response
  const content = res.data?.choices?.[0]?.message?.content || '';
  if (!content) {
    console.log(`[llm] empty response from LLM`);
    throw new Error('Empty LLM response');
  }
  
  const parsed = strictJsonFromText(content);
  if (!parsed) {
    console.log(`[llm] failed to parse JSON from: ${content.slice(0, 200)}`);
    throw new Error('Failed to parse LLM JSON response');
  }
  
  // ... rest of success path
  
} catch (err) {
  const errMsg = err.message || 'Unknown error';
  console.log(`[llm] batch failed: ${errMsg}`);
  return {
    verdict: 'WATCH',
    confidence: 0,
    selected_candidate_id: null,
    selected_mint: null,
    reason: `LLM failed: ${errMsg}`,
    risks: ['llm_error'],
    suggested_tp_percent: numSetting('default_tp_percent', 50),
    suggested_sl_percent: numSetting('default_sl_percent', -25),
    raw: { error: errMsg },
  };
}
```

## Key Points

1. **Outer try-catch** — catches all errors (network, parsing, logic)
2. **Inner try-catch** — wraps axios call to capture response body before throwing
3. **validateStatus: () => true** — prevents axios from throwing on 500, lets us inspect response
4. **Manual status check** — after axios returns, check `res.status !== 200` and log `res.data?.error?.message`
5. **Fallback to WATCH** — on any LLM error, return WATCH verdict (don't block entry, just skip LLM screening)

## Common Errors & Meanings

| Error | Cause | Fix |
|-------|-------|-----|
| `HTTP 500` | Server error, payload too large, or invalid request | Reduce payload size (see `llm-payload-optimization.md`), check `stream: false` |
| `HTTP 401` | Invalid API key | Check `LLM_API_KEY` in `.env` |
| `HTTP 400` | Invalid request format | Check message structure, ensure `stream: false` |
| `Empty LLM response` | LLM returned no content | Check model availability, retry |
| `Failed to parse JSON` | LLM response not valid JSON | Check `strictJsonFromText()` function, may need to adjust prompt |
| `ECONNREFUSED` | LLM server not running | Check `curl http://localhost:20128/v1/models` |
| `ETIMEDOUT` | Request took too long | Increase `LLM_TIMEOUT_MS` or reduce payload |

## Testing

```bash
# Test LLM endpoint directly
curl -X POST http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-3d832eacf8314504-..." \
  -d '{
    "model": "kr/claude-haiku-4.5",
    "temperature": 0.2,
    "stream": false,
    "messages": [
      {"role": "system", "content": "test"},
      {"role": "user", "content": "respond with JSON: {\"test\": true}"}
    ]
  }'
```

Expected: 200 status with JSON response (not streaming chunks).

## Fallback Strategy

When LLM fails repeatedly:
1. **Disable LLM** — Set `use_llm: false` in strategy config
2. **Use rule-based screening** — Filter passed = auto BUY
3. **Debug offline** — Test LLM endpoint separately, check payload size, verify API key
4. **Re-enable** — Once fixed, set `use_llm: true` and restart bot

Example:
```python
import sqlite3, json
conn = sqlite3.connect('charon.sqlite')
c = conn.cursor()
c.execute("SELECT config_json FROM strategies WHERE id='degen'")
config = json.loads(c.fetchone()[0])
config['use_llm'] = False  # Disable LLM
c.execute("UPDATE strategies SET config_json=? WHERE id='degen'", (json.dumps(config),))
conn.commit()
conn.close()
```

Then: `pm2 restart charon`
