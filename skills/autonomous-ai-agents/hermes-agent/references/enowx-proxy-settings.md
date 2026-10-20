# enowX Proxy Settings API

enowX is the local LLM proxy running on the user's VPS. It pools upstream accounts and exposes an OpenAI-compatible API.

## Endpoints

- **LLM API:** `http://localhost:1430/v1` (OpenAI-compatible chat completions)
- **Dashboard/Settings:** `http://localhost:1431/`

## Settings API

### Read current settings
```bash
curl -s http://localhost:1431/ | python3 -m json.tool
```

### Update settings
```bash
curl -s -X POST http://localhost:1431/api/settings \
  -H "Content-Type: application/json" \
  -d '{"setting_name": value}'
```

No auth required for the settings endpoint.

## Available Settings

| Setting | Type | Description |
|---------|------|-------------|
| `rtk_enabled` | bool | **Tool Result Compression** — compresses large tool outputs (git diff, grep, ls, tree, file reads) before sending to model. Saves tokens. |
| `dcp_enabled` | bool | **Dynamic Context Pruning** — prunes context dynamically to fit token limits. Does NOT affect image handling. |
| `caveman_enabled` | bool | Caveman mode — simplifies/compresses assistant responses. |
| `caveman_level` | string | Level of caveman compression: `full`, etc. |
| `auth_engine` | string | Browser engine for account auth: `camoufox` |
| `auto_delete_exhausted` | bool | Auto-delete accounts that hit rate limits |
| `account_add_concurrent` | int | Max concurrent account additions |
| `account_add_headless` | bool | Headless browser for account addition |
| `account_add_parallel` | int | Parallel account add workers |
| `account_add_priority` | string | Priority for new accounts: `standard` |
| `codex_use_system_browser` | bool | Use system browser for Codex auth |
| `discord_rpc_enabled` | bool | Discord Rich Presence |
| `discord_webhook_url` | string | Discord webhook for notifications |
| `discord_webhook_events` | list/null | Which events trigger Discord notifications |

## Common Operations

### Enable RTK (save tokens on tool-heavy sessions)
```bash
curl -s -X POST http://localhost:1431/api/settings \
  -H "Content-Type: application/json" \
  -d '{"rtk_enabled": true}'
```

### Disable DCP (if suspecting context issues)
```bash
curl -s -X POST http://localhost:1431/api/settings \
  -H "Content-Type: application/json" \
  -d '{"dcp_enabled": false}'
```

## Other API Endpoints

- `GET http://localhost:1431/api/accounts` — list pooled upstream accounts
- `GET http://localhost:1431/api/config` — full config (requires dashboard password)

## Notes

- RTK compresses tool results at the proxy level before they reach the model. Useful for coding sessions with lots of file reads/diffs.
- DCP does NOT cause image stripping — that's a fundamental limitation of upstream provider accounts (see vision troubleshooting in main skill).
- Settings changes take effect immediately for new requests (no restart needed).
- **Streaming:** The proxy **always returns SSE streaming responses** regardless of `stream: false` parameter. This breaks Hermes auxiliary vision when configured as `auxiliary.vision.provider: openai/custom` with `base_url: http://localhost:1430/v1`. **FIX:** Patch `_validate_llm_response()` in `auxiliary_client.py` to parse SSE responses via `_parse_sse_to_response()`. See `references/enowx-vision-streaming-incompatibility.md` for the patch details.

## Model Names and Provider-Prefix Routing

enowX exposes models with two naming styles in `GET /v1/models`:

1. **Bare names** — `claude-opus-4.6`, `claude-sonnet-4.6`, `gpt-5.5`, `gemini-3.1-pro`, etc. Routed by the proxy across whatever upstream pools support that model.
2. **Provider-prefixed names** — `kr/claude-opus-4.6`, `kiro/...`, `codex-gpt-5.5`, etc. Pin the request to a specific upstream account pool (e.g. `kr` = Kiro pool, `codex-` = OpenAI Codex pool).

The model list at `/v1/models` may list the same model twice (once bare, once prefixed) when multiple pools support it. Picking the prefixed form is **only correct if that pool currently has at least one active, non-exhausted account.**

### Error signatures when routing fails

| Symptom | Meaning | Fix |
|---------|---------|-----|
| `400 invalid_request` / `Request payload is malformed for upstream API` | The prefix is recognized but the upstream pool rejected the payload — usually because the pool has zero accounts of that provider type, or the model id format isn't accepted by the upstream. | Drop the prefix, or switch to a pool that has accounts (`auto`, or a different prefix). |
| `500 server_error` / `no active accounts for provider` | The bare-name pool is empty — every account that could serve this model is rate-limited / exhausted / removed. | Use `auto` (proxy picks any working pool) or wait for accounts to reset. Check dashboard at `:1431`. |
| Works on `auto`, fails on bare or prefixed | Confirms it's a pool-availability issue, not an API-key / endpoint issue. | Use `auto` until pool refills. |

### Diagnosing in one shot

```bash
BASE=http://localhost:1430/v1
KEY=$ENOWX_API_KEY

# 1. Confirm endpoint + auth work at all
curl -s -X POST $BASE/chat/completions -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"auto","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
# auto failing too → endpoint/auth/config issue, not pool issue

# 2. Try the bare name
curl ... -d '{"model":"claude-opus-4.6", ...}'
# "no active accounts for provider" → that pool is empty

# 3. Try a different prefix
curl ... -d '{"model":"kr/claude-opus-4.6", ...}'
# "malformed for upstream API" → kr pool can't serve this model id
```

### When the user says `model.default = <prefix>/<model>` and it errors

Don't silently swap to `auto` — that hides the user's intent. Instead:

1. Verify the prefixed model exists in `/v1/models`.
2. Run the curl test above to surface the exact error.
3. Report which case it is (empty pool vs payload rejection) and ask whether to (a) wait/refill, (b) drop the prefix, or (c) fall back to `auto`.

### Setting the model in Hermes config

```bash
hermes config set model.default <model_id>
# Active in NEW sessions. Current session keeps its model until /reset or relaunch.
```

The `/model` slash command changes the model for the current session only — does not write config.yaml. Use `hermes config set` for persistence.
