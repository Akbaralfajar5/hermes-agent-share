# Gateway Display Config — Telegram Tool Progress & Empty Responses

## Tool Progress Still Showing on Telegram

**Symptom:** User sees `💻 terminal: "..."` in Telegram chat despite `tool_progress: false` in config.

**Root cause:** `gateway/display_config.py` has hardcoded per-platform defaults. Telegram's default is `"new"`. The resolution order is:

1. `display.platforms.<platform>.<key>` — explicit per-platform override (WINS)
2. `display.tool_progress_overrides.<platform>` — legacy compat
3. `display.<key>` — global user setting
4. Built-in platform default (`_PLATFORM_DEFAULTS`) — Telegram = `"new"`
5. Built-in global default (`_GLOBAL_DEFAULTS`)

Global `display.tool_progress: none` or top-level `tool_progress: false` is checked at step 3, but Telegram's hardcoded default at step 4 takes priority if step 3 isn't recognized properly.

**Fix:** Explicit per-platform override in `~/.hermes/config.yaml`:

```yaml
display:
  platforms:
    telegram:
      tool_progress: off
```

**Related settings (all under `display:`):**
- `tool_progress_command: false` — suppresses command-style progress
- `tool_preview_length: 0` — no preview of tool args
- `interim_assistant_messages: false` — no partial assistant messages

## Empty Responses Sent to Chat

**Symptom:** Agent sends "(empty)" or blank messages to Telegram.

**Root cause:** In `gateway/run.py`, function `_normalize_empty_agent_response()` (line ~1528):
- If `response` is empty AND `api_calls == 0` AND not `failed` → returns empty string as-is
- Gateway then delivers this empty string to chat

**Scenarios that trigger this:**
- Model returns empty content without making any tool calls
- Streaming produces empty final chunk
- `interim_assistant_messages: true` sends partial empty messages

**Fixes (in order of preference):**

1. **Config-level** — ensure `interim_assistant_messages: false`
2. **System prompt** — add "Always provide a final text response, never return empty"
3. **Source patch** — in `gateway/run.py` around line 1571, change `return response` to `return None` so gateway skips delivery (base platform adapter already skips None)

**Relevant source locations:**
- `gateway/display_config.py` — `_PLATFORM_DEFAULTS`, `resolve_display_setting()`
- `gateway/run.py:1528` — `_normalize_empty_agent_response()`
- `gateway/run.py:8686` — caller that invokes normalize then delivers
- `gateway/platforms/base.py:3458` — logs empty/None response skip
