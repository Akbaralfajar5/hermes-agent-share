# enowX + Hermes Quick Setup (One-Liner)

When someone has both enowX and Hermes installed on their VPS and needs to connect them quickly.

## Prerequisites

- Hermes Agent installed (`hermes --version` works)
- enowX running locally (`curl -s http://localhost:1430/v1/models -H "Authorization: Bearer API_KEY"` returns models)
- enowX API key in hand

## One-Liner Setup

Replace `API_KEY` with the actual enowX API key:

```bash
hermes config set model.provider custom && hermes config set model.base_url "http://localhost:1430/v1" && hermes config set model.api_key "API_KEY" && hermes config set model.default "auto" && hermes gateway restart
```

## Verification

```bash
# Test that Hermes can reach enowX
hermes chat -q "test, model apa yang kamu pakai?"

# Or curl directly
curl -s http://localhost:1430/v1/models \
  -H "Authorization: Bearer API_KEY" | head -20
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `missing Authorization header` | Forgot `-H "Authorization: Bearer ..."` in curl | Add the header |
| `connection refused` on :1430 | enowX not running | Start enowX service |
| Models list empty | No upstream accounts pooled | Add accounts via enowX dashboard (:1431) |

## Architecture (for explaining to others)

```
[User] → [Hermes Agent] → [enowX localhost:1430] → [Upstream LLM (Claude/GPT/Gemini)]
```

- **Hermes** = the agent (tools, memory, skills, gateway to Telegram/Discord)
- **enowX** = LLM proxy (pools upstream accounts into one OpenAI-compatible API)
- Connected via `model.base_url` pointing to enowX's `/v1` endpoint
- No special plugin needed — Hermes treats enowX as any OpenAI-compatible provider

## Remote Access (friend using YOUR enowX)

If someone wants to use enowX on a different VPS:
- Use the public IP instead of localhost: `http://PUBLIC_IP:1430/v1`
- Ensure port 1430 is open in firewall/security group
- enowX must listen on `0.0.0.0:1430` (check with `ss -tlnp | grep 1430`)

## Notes

- `model.default: "auto"` lets enowX pick the best available model
- Specific models: `claude-opus-4.6`, `gpt-5.5`, `gemini-3.1-pro`, etc.
- After config change, gateway needs restart but CLI picks it up on next invocation
- Vision does NOT work through enowX — set `auxiliary.vision.provider` to `google` or `openrouter` separately
