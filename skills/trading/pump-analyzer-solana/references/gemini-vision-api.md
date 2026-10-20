# Gemini Vision API — Direct Call Pattern

How to call Google Gemini Vision API directly from Python when the built-in `vision_analyze` tool fails (e.g., non-vision model active, provider overloaded).

## Prerequisites

Gemini API key in `~/.hermes/.env`:
```
GOOGLE_API_KEY=AQ.xxx...
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
```

The key (`GOOGLE_API_KEY`) is used both as env var and as query param.

## Basic call pattern

```python
import base64, json, urllib.request, ssl

# Read key from .env
with open("/home/ubuntu/.hermes/.env") as f:
    for line in f:
        if line.startswith("GOOGLE_API_KEY="):
            api_key = line.split("=", 1)[1].strip()
            break

# Encode image
with open("/path/to/image.jpg", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

# Call Gemini
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

body = json.dumps({
    "contents": [{
        "parts": [
            {"text": "Describe this image in detail."},
            {"inlineData": {"mimeType": "image/jpeg", "data": img_b64}}
        ]
    }]
}).encode()

ctx = ssl.create_default_context()
req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
    result = json.loads(resp.read())

# Extract text
for candidate in result.get("candidates", []):
    for part in candidate.get("content", {}).get("parts", []):
        if "text" in part:
            print(part["text"])
```

## Model fallback strategy

Gemini models have different availability. Try in order:

| Priority | Model | Notes |
|----------|-------|-------|
| 1st | `gemini-2.5-flash` | Best, but often 503 (overloaded) |
| 2nd | `gemini-2.0-flash-exp` | Good fallback |
| 3rd | `gemini-2.5-flash-lite` | Lighter, less overloaded |

If all return 503 → wait 5-10 seconds and retry (transient overload).
If quota exceeded → key needs credit/topup.

## Common use cases

### 1. Analyze trading bot screenshots (Trojan, Photon, BullX)
```
Prompt: "Jelaskan isi gambar ini dalam Bahasa Indonesia secara detail dan ringkas. 
Apa yang ditampilkan? Sebutkan semua angka, metrik, dan status yang terlihat."
```

### 2. Read chart screenshots
```
Prompt: "Read this chart. What's the current price, trend direction, 
and key support/resistance levels visible?"
```

### 3. Extract text from mobile screenshots
```
Prompt: "Extract ALL text visible in this screenshot. Include numbers, 
percentages, wallet addresses, and labels."
```

## Why not use built-in vision_analyze?

- `vision_analyze` depends on the configured `vision` provider in `config.yaml`
- If active model is non-vision (e.g., DeepSeek), vision_analyze may fail
- Gemini API direct call bypasses the configured provider and works standalone
- Useful when user explicitly says "pake api gemini"

## Pitfalls

- Gemini API has rate limits per key — don't call in tight loops
- Image must be <20MB for base64 encoding to be practical
- `ssl.create_default_context()` needed for some environments
- 503 errors are common on gemini-2.5-flash during peak hours — always have fallback models ready
