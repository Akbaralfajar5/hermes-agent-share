# Hermes Fallback Providers — Rate Limit Auto-Switch

## Overview

When the primary model returns 429 (rate limited), Hermes automatically tries fallback models in order. Configured via `fallback_providers` in `~/.hermes/config.yaml`.

## Config Format

```yaml
# Primary model
model:
  api_key: sk-xxxxx
  base_url: http://127.0.0.1:20128/v1
  default: kr/claude-opus-4.6
  provider: custom

# Fallback chain (tried in order on 429)
fallback_providers:
- provider: custom
  model: kr/claude-opus-4.7
  base_url: http://127.0.0.1:20128/v1
  api_key: sk-xxxxx
- provider: custom
  model: kr/claude-opus-4.8
  base_url: http://127.0.0.1:20128/v1
  api_key: sk-xxxxx
- provider: custom
  model: kr/claude-sonnet-4.6
  base_url: http://127.0.0.1:20128/v1
  api_key: sk-xxxxx
```

## Required Fields Per Entry

| Field | Required | Notes |
|-------|----------|-------|
| `provider` | ✅ | e.g. `custom`, `openrouter`, `anthropic` |
| `model` | ✅ | Full model name as the provider expects |
| `base_url` | Optional | Required for `custom` provider |
| `api_key` | Optional | Uses main model's key if omitted (but explicit is safer) |

## Implementation Details

- Source: `hermes_cli/fallback_config.py` → `get_fallback_chain(cfg)`
- Gateway loads at startup: `gateway/run.py` → `_load_fallback_model()`
- Also reads legacy `fallback_model` key (single dict or list), appended after `fallback_providers`
- Deduplication: entries with same (provider, model, base_url) are skipped

## Pitfalls

1. **api_key must be the FULL key** — don't truncate. If using same provider/base_url as primary, pull from `model.api_key` or copy exact value.
2. **YAML dump reorders keys** — if editing via Python `yaml.dump()`, use `sort_keys=False` to preserve order.
3. **`fallback_providers: []`** — empty list means no fallback. Gateway restart may reset to `[]` if config migration runs.
4. **Takes effect after gateway restart** — `systemctl --user restart hermes-gateway`
5. **Same custom provider, different models** — this is the common pattern for 9router/enowX where you switch model names but keep same base_url + api_key.

## Clearing / Disabling Fallback Providers

When you want NO auto-fallback (primary model fails → error, not silent switch):

```bash
hermes config set fallback_providers "[]"
```

Why `hermes config set` and not direct file edit? `~/.hermes/config.yaml` is a **protected system file** — the `patch` tool and `write_file` tool both deny writes to it. `hermes config set` is the sanctioned path.

Verify:
```bash
cat ~/.hermes/config.yaml | grep -A 3 "fallback_providers"
# Should show: fallback_providers: '[]'
```

To re-enable, run the same command with the full YAML list inline (JSON-safe format):
```bash
hermes config set fallback_providers '[{"provider":"custom","model":"kr/claude-opus-4.7","base_url":"http://127.0.0.1:20128/v1","api_key":"sk-xxxxx"}]'
```

## When to Use

- Primary model frequently rate-limited (kr/claude-opus-4.6 on shared proxy)
- Want graceful degradation (opus → opus newer → sonnet)
- Using credential pools with limited quotas per model
