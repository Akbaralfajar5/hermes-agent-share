# Charon LLM Provider Options

Charon's LLM is a thin OpenAI-compatible client driven by `.env`:

```
ENABLE_LLM=true
LLM_BASE_URL=<openai compatible base>
LLM_API_KEY=<token>
LLM_MODEL=<model id>
LLM_TIMEOUT_MS=60000
```

Switching providers = update those 4 vars + `pm2 restart charon --update-env`. No code change.

Used in `src/pipeline/llm.js` for screening verdicts (BUY / WATCH / PASS). Recommendation: pick a fast, cheap model — calls run frequently per signal batch, latency directly delays entries.

## Provider 1: enowX (default, was original)

```
LLM_BASE_URL=http://localhost:1430/v1
LLM_API_KEY=enx-...
LLM_MODEL=auto
```

- `auto` routes upstream provider automatically.
- Hit `GET /v1/models` with `Authorization: Bearer enx-...` to list models.
- Models prefixed by family name only: `claude-opus-4.7`, `claude-sonnet-4.6`, `deepseek-3.2`, `minimax-m2.5`, `glm-5`, `gpt-5.x`, `gemini-3.x`, etc.

## Provider 2: 9router (local LLM gateway, May 2026)

```
LLM_BASE_URL=http://localhost:20128/v1
LLM_API_KEY=sk-...                # see "API key location" below
LLM_MODEL=kr/claude-haiku-4.5
```

- Listening on `0.0.0.0:20128` (also exposed via nginx on port 80 of the VPS).
- OpenAI-compatible. `GET /v1/models` works **without auth** (model catalog is public). `POST /v1/chat/completions` requires the bearer token.
- `GET /api/v1/models` returns `{"error":"Unauthorized"}` — wrong path. Always use `/v1/...`.
- Returns SSE-style streamed `data:` chunks even for non-streaming calls; the client must accept either streamed or single-shot. Charon's OpenAI client handles both.

### API key location

Keys live in `~/.9router/db/data.sqlite` table `apiKeys` (column `key`, plus `isActive`). To grab the active key without opening the dashboard:

```python
import sqlite3
conn = sqlite3.connect('/home/ubuntu/.9router/db/data.sqlite')
print(conn.execute("select key from apiKeys where isActive=1 limit 1").fetchone()[0])
```

(Treat that key as a secret; do not echo it back to the user once captured.)

### Model namespace

9router prefixes every model with the routed provider:

| Prefix | Provider class | Examples |
|--------|----------------|----------|
| `kr/`  | Anthropic-side | `kr/claude-haiku-4.5`, `kr/claude-sonnet-4.5`, `kr/claude-opus-4.6`, `kr/claude-opus-4.7`, `kr/deepseek-3.2`, `kr/qwen3-coder-next`, `kr/glm-5`, `kr/MiniMax-M2.5` |
| `cx/`  | OpenAI/Codex   | `cx/gpt-5.5`, `cx/gpt-5.4`, `cx/gpt-5.3-codex`, `cx/gpt-5.2`, `cx/gpt-5.1`, plus `-review`, `-codex`, `-mini`, `-max` variants |

Default for Charon screening: `kr/claude-haiku-4.5` — cheap, fast, good enough for verdict-only JSON.
Upgrade picks: `kr/claude-sonnet-4.5` (balance), `kr/claude-opus-4.7` (max smarts, slowest), `cx/gpt-5.5` (cross-check).

### Sanity probe before switching

Always test the new endpoint **before** restarting Charon, otherwise you'll only find out via silent screening failures:

```bash
curl -s -X POST $LLM_BASE_URL/chat/completions \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"<MODEL>","messages":[{"role":"user","content":"reply OK"}],"max_tokens":10}'
```

Expect either a single JSON `chat.completion` or SSE `data:` chunks ending with `data: [DONE]`.

## Switching procedure

1. Pick provider, base URL, key, model.
2. Probe with the curl above. Fail-fast if it 401s or returns the wrong content-type.
3. Patch the `# LLM` block in `~/charon/.env`.
4. `pm2 restart charon --update-env` (the `--update-env` flag is **mandatory** — without it, the new env vars are ignored).
5. Tail logs and confirm `[bot] Charon started` plus a fresh screening verdict — that is the only proof the new provider actually works end-to-end.

## Pitfalls

- Forgetting `--update-env` on `pm2 restart` → bot keeps using the old key/URL silently.
- Choosing an Opus-tier model for screening → high per-batch latency, missed signals when LLM queue fills (`[agent] LLM queue full`).
- Provider returns SSE only and downstream code expects single JSON → not an issue with current `src/pipeline/llm.js`, but worth re-checking if the LLM client is ever swapped.
- `llm_min_confidence` lives in 3 places (settings table, strategy `config_json`, system prompt). Switching providers doesn't change those — keep them in sync as documented in `tuning-playbook.md`.
