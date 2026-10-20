# enowX Proxy Streaming Incompatibility with Auxiliary Vision

**Discovered:** May 26, 2026
**Status:** Unresolved — requires separate vision API key

## Problem

The enowX proxy at `localhost:1430` **always returns SSE streaming responses** regardless of the `stream` parameter. When `auxiliary.vision.provider` is set to `openai` or `custom` pointing at enowX, the OpenAI Python SDK's `client.chat.completions.create()` receives a raw SSE string (`data: {"choices":[{"delta":{"content":"Green"}...]}\n\n`) instead of a parsed response object with `.choices[0].message`.

This is **different from the image-stripping issue** documented in the main skill. The proxy correctly processes images (returns accurate vision results), but the response format is incompatible with Hermes's `_validate_llm_response()` which expects `response.choices[0].message`.

## Test Results

| Config | Result |
|--------|--------|
| `provider: openai`, `base_url: http://localhost:1430/v1` | ❌ Streaming parse error |
| `provider: custom`, `base_url: http://localhost:1430/v1` | ❌ Streaming parse error |
# enowX Proxy Streaming Incompatibility with Auxiliary Vision

**Discovered:** May 26, 2026
**Fixed:** May 26, 2026 — patched `_validate_llm_response()` in `auxiliary_client.py`

## Problem

The enowX proxy at `localhost:1430` **always returns SSE streaming responses** regardless of the `stream` parameter. When `auxiliary.vision.provider` is set to `openai` or `custom` pointing at enowX, the OpenAI Python SDK's `client.chat.completions.create()` receives a raw SSE string (`data: {"choices":[{"delta":{"content":"Green"...

## Fix Applied

Patched `~/.hermes/hermes-agent/agent/auxiliary_client.py`:

1. Added `_parse_sse_to_response()` function that:
   - Parses SSE `data:` lines from streaming response
   - Accumulates delta content into a single message
   - Returns a `SimpleNamespace` object with `.choices[0].message` structure

2. Modified `_validate_llm_response()` to:
   - Check if response is a string starting with `data:`
   - If so, call `_parse_sse_to_response()` to convert to proper response object
   - If parsing succeeds, return the parsed response (skip normal validation)

**⚠️ This patch may need reapplication after `hermes update`** since it modifies the Hermes source code.

## Working Config (after patch)

```bash
hermes config set auxiliary.vision.provider openai
hermes config set auxiliary.vision.model kiro/claude-sonnet-4.6
hermes config set auxiliary.vision.base_url http://localhost:1430/v1
hermes config set auxiliary.vision.api_key "$ENOWXLABS_API_KEY"
```

No separate vision API key needed — uses the same enowX proxy as the main model.
