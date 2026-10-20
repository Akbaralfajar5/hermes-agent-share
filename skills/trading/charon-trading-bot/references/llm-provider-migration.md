# LLM Provider Migration

**Context:** Switching Charon bot from one LLM provider to another (e.g., 9router local → enowX Labs, OpenRouter, Anthropic direct).

## Migration Steps

### 1. Test Provider Manually First

```bash
curl -s -X POST <BASE_URL>/v1/chat/completions \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<MODEL_ID>",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 50
  }' | jq
```

**Common issues:**
- **Model format:** Some providers require `provider/model` (e.g., `kiro/claude-haiku-4.5`), others just `model-name`
- **List available models:** `curl <BASE_URL>/v1/models -H "Authorization: Bearer <API_KEY>" | jq -r '.data[].id'`

### 2. Update `.env`

```bash
cd ~/charon
# Backup current config
cp .env .env.backup

# Update LLM config
sed -i 's|^LLM_BASE_URL=.*|LLM_BASE_URL=<NEW_BASE_URL>|' .env
sed -i 's|^LLM_API_KEY=.*|LLM_API_KEY=<NEW_API_KEY>|' .env
sed -i 's|^LLM_MODEL=.*|LLM_MODEL=<NEW_MODEL_ID>|' .env
```

### 3. Verify Code Uses Fetch (Not Axios)

**Files to check:**
- `src/pipeline/llm.js` — main LLM client
- `src/learning/lessons.js` — learning system LLM calls

**Pattern:** Ensure all LLM calls use native `fetch()`, not `axios`. Axios error messages (`Request failed with status code 500`) can be misleading during debugging.

```javascript
// ✅ Correct (fetch)
const httpRes = await fetch(`${LLM_BASE_URL}/chat/completions`, {
  method: 'POST',
  headers: {
    'authorization': `Bearer ${LLM_API_KEY}`,
    'content-type': 'application/json'
  },
  body: JSON.stringify(payload)
});

// ❌ Avoid (axios)
const httpRes = await axios.post(`${LLM_BASE_URL}/chat/completions`, payload, {
  headers: { 'authorization': `Bearer ${LLM_API_KEY}` }
});
```

### 4. Restart Bot

```bash
cd ~/charon
pm2 restart charon --update-env
sleep 10
pm2 logs charon --lines 50 | grep -E "llm|LLM|Starting"
```

### 5. Verify LLM Calls

**Check logs for:**
- `[llm] _decideCandidateBatch called` — function invoked
- `[llm] request size: X bytes` — request sent
- No `[llm] batch failed` errors

**Check database:**
```python
import sqlite3
conn = sqlite3.connect('~/charon/charon.sqlite')
cursor = conn.cursor()
cursor.execute("SELECT id, verdict, confidence FROM llm_decisions ORDER BY id DESC LIMIT 5")
print(cursor.fetchall())
```

## Common Pitfalls

### Provider-Specific Model Names

| Provider | Format | Example |
|----------|--------|---------|
| enowX Labs | `kiro/<model>` | `kiro/claude-haiku-4.5` |
| OpenRouter | `provider/model` | `anthropic/claude-3.5-sonnet` |
| Anthropic Direct | `model-version` | `claude-3-5-sonnet-20241022` |
| 9router Local | `kr/<model>` | `kr/claude-haiku-4.5` |

### Cached Modules

If errors persist after config update:
```bash
cd ~/charon
pm2 delete charon
rm -rf node_modules/.cache 2>/dev/null
pm2 start src/app.js --name charon
```

### Confidence Threshold

After provider switch, LLM confidence scores may differ. Check `llm_min_confidence` in strategy config:

```python
import sqlite3, json
conn = sqlite3.connect('~/charon/charon.sqlite')
cursor = conn.cursor()
cursor.execute("SELECT config_json FROM strategies WHERE enabled=1")
config = json.loads(cursor.fetchone()[0])
print(f"Confidence threshold: {config.get('llm_min_confidence', 75)}%")
```

Adjust if needed:
```python
config['llm_min_confidence'] = 60  # Lower threshold
cursor.execute("UPDATE strategies SET config_json=? WHERE enabled=1", (json.dumps(config),))
conn.commit()
```

## Verification Checklist

- [ ] Manual curl test succeeds
- [ ] Model ID format correct for provider
- [ ] `.env` updated with new credentials
- [ ] Bot restarted with `--update-env`
- [ ] `[llm] _decideCandidateBatch called` appears in logs
- [ ] No `batch failed` errors
- [ ] `llm_decisions` table has new entries
- [ ] Confidence threshold appropriate for new provider
