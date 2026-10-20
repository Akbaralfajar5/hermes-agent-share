# Gemini Vision Model Compatibility (Google AI Studio)

**Last verified:** June 2026

## Model Vision Support Matrix

| Model | Vision (image input) | Notes |
|-------|---------------------|-------|
| `gemini-2.5-flash` | ✅ Yes | Best cost/speed for vision tasks |
| `gemini-2.5-pro` | ✅ Yes | Higher quality, slower |
| `gemini-3.1-pro-preview` | ❌ No | Returns `404: No endpoints found that support image input` |
| `gemini-3-pro-image` | ❌ (generates images) | Image generation, not vision input |
| `gemini-3-pro-image-preview` | ❌ (generates images) | Image generation, not vision input |

**Key finding (June 2026):** `gemini-3.1-pro-preview` does NOT support vision/image input despite being a "pro" model. Use `gemini-2.5-flash` or `gemini-2.5-pro` for vision tasks.

## Listing Available Models via API

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GOOGLE_API_KEY" \
  | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]"
```

Filter for vision-capable models (look for `supportedGenerationMethods` containing image input).

## Direct API Fallback When vision_analyze Fails Mid-Session

If `auxiliary.vision.model` was just changed via `hermes config set` but the session hasn't been reset, `vision_analyze` still uses the old model. Workaround — call Gemini API directly:

```python
import base64, json, urllib.request, os

api_key = ""
with open(os.path.expanduser("~/.hermes/.env")) as f:
    for line in f:
        if line.startswith("GOOGLE_API_KEY="):
            api_key = line.strip().split("=", 1)[1]
            break

with open("IMAGE_PATH.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

payload = {
    "contents": [{
        "parts": [
            {"text": "Describe this image in detail."},
            {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}}
        ]
    }],
    "generationConfig": {"maxOutputTokens": 2048}
}

req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}
)

resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
print(result["candidates"][0]["content"]["parts"][0]["text"])
```

Pitfalls:
- `maxOutputTokens` may truncate long responses — increase if needed
- Image must be base64-encoded; URL-based images require different payload format
- Model name goes in the URL path, not the payload
- Session reset (`/reset`) is required after `hermes config set auxiliary.vision.model` for `vision_analyze` to pick up the change
