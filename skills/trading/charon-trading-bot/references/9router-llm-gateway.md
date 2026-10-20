# 9router LLM Gateway for Charon

How to point Charon's LLM at the locally-running 9router gateway instead of enowX.

## Why

User runs **9router** (npm `9router`, dashboard at `http://43.159.56.39`) as their AI infrastructure router. It exposes an OpenAI-compatible endpoint that fans out to providers behind the scenes (Anthropic via `kr/`, OpenAI codex via `cx/`).

Charon's screening pipeline only needs a chat-completions endpoint, so it works as a drop-in for `LLM_BASE_URL`.

## Endpoint shape

| Item | Value |
|------|-------|
| Base URL | `http://localhost:20128/v1` |
| Models endpoint | `GET /v1/models` (NOT `/api/v1/models` — that returns Unauthorized) |
| Auth | Bearer token, model **must** include provider prefix (`kr/...`, `cx/...`) |

`/v1/models` is publicly readable for listing — no auth needed for discovery. Chat completions require a real API key.

## Where the API key lives

9router stores keys in its own SQLite DB:

```bash
sqlite3 ~/.9router/db/data.sqlite 'select key from apiKeys where isActive=1 limit 1'
```

Or, since `sqlite3` CLI is not installed, use Python:

```py
python3 - <<'PY'
import sqlite3
conn = sqlite3.connect('/home/ubuntu/.9router/db/data.sqlite')
print(conn.execute("select key from apiKeys where isActive=1 limit 1").fetchone()[0])
PY
```

Format: `sk-<machineId-prefix>-<random>-<random>` (e.g. `sk-3d832eacf8314504-4gzloj-38ddd6d1`).

## Available model families (May 2026 snapshot)

```
kr/claude-haiku-4.5      # cheap + fast, GOOD for screening
kr/claude-sonnet-4.5
kr/claude-opus-4.6
kr/claude-opus-4.7       # most capable, slowest
kr/deepseek-3.2
kr/qwen3-coder-next
kr/glm-5
kr/MiniMax-M2.5
cx/gpt-5.5
cx/gpt-5.5-review
cx/gpt-5.4
cx/gpt-5.3-codex (and codex-high/xhigh/spark/none/review variants)
cx/gpt-5.1, cx/gpt-5.2 ...
```

Always include the prefix. `claude-haiku-4.5` (no prefix) returns 400.

## User preference (the user, May 2026)

For Charon screening: **`kr/claude-haiku-4.5`**. Reason: every signal batch hits the LLM, so latency and cost matter more than peak reasoning. Opus is overkill here.

If the user wants to reason about strategy/lessons specifically (not screening), bump to `kr/claude-sonnet-4.5` or `kr/claude-opus-4.7` — but only for the relevant call site, not the whole pipeline.

## .env block to use

```env
# LLM - 9router (local LLM gateway)
ENABLE_LLM=true
LLM_BASE_URL=http://localhost:20128/v1
LLM_API_KEY=sk-...   # from ~/.9router/db/data.sqlite apiKeys
LLM_MODEL=kr/claude-haiku-4.5
LLM_TIMEOUT_MS=60000
```

After editing `.env`, restart with env reload:

```bash
pm2 restart charon --update-env
```

`--update-env` is **required** — without it PM2 keeps the old `LLM_BASE_URL` and the model switch silently does nothing.

## Verification (run before trusting the switch)

```bash
# 1) Models endpoint reachable & lists kr/ models
curl -s http://localhost:20128/v1/models | head -c 300

# 2) Auth + completion works end-to-end
curl -s -X POST http://localhost:20128/v1/chat/completions \
  -H "Authorization: Bearer $LLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"kr/claude-haiku-4.5","messages":[{"role":"user","content":"reply with just OK"}],"max_tokens":10}' \
  | head -c 300
```

Expected: streaming chunks with `"content":"OK"`. Response is **SSE-style** (`data: {...}` per chunk + `data: [DONE]`), not a single JSON object — Charon's OpenAI client handles both, so this is fine.

## Pitfalls

- **`/api/v1/models` → Unauthorized**. The dashboard UI uses `/api/...` paths but the OpenAI-compatible surface is `/v1/...`. Wrong path is the most common false alarm.
- **Restarting without `--update-env`** keeps stale env. The bot will appear healthy and still hit the old endpoint.
- **Model name without prefix** returns 400 from 9router. Always `kr/...` or `cx/...`.
- The 9router process binds to `127.0.0.1` even with `-H 0.0.0.0`. From inside the VPS that's fine (Charon talks to localhost). For phone access the user already has nginx + Cloudflare tunnel set up.
- API keys in `apiKeys` table can be rotated via dashboard. If a swap suddenly 401s, re-read the active key from SQLite.

## Switching back to enowX (for reference)

```env
LLM_BASE_URL=http://localhost:1430/v1
LLM_API_KEY=enx-...
LLM_MODEL=auto
```

enowX uses the literal model id `auto` for default routing; 9router does not — pick an explicit `kr/...` model instead.
