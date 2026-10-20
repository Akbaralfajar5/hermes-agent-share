# TanStack Start Server Function Reverse Engineering

Discovered June 2026 during GachaSlabz.com API analysis.

## Detection

TanStack Start apps use **Seroval** serialization for server functions. Telltale signs:

1. **URL pattern**: `/_serverFn/SHA256_HASH?createServerFn`
2. **Response header**: `x-tss-serialized: true`
3. **Error format**: `{"t":25,"i":0,"s":{"message":{...}},"c":"$TSR/Error"}`
4. **CSP header reveals API origin**: Look for `connect-src` directive — often contains separate API subdomain (e.g., `api.gachaslabz.com`)

## Seroval Serialization Format

Request body uses typed JSON objects:

```
t=1  → string  {t:1, s:"value"}
t=10 → object  {t:10, i:ID, p:{k:[keys], v:[values], s:count}, o:0}
t=0  → null    {t:0}
```

Example request to send email OTP:
```json
{
  "t": {
    "t": 10, "i": 0,
    "p": {
      "k": ["data"],
      "v": [{
        "t": 10, "i": 1,
        "p": {
          "k": ["email", "turnstileToken", "fingerprint"],
          "v": [
            {"t": 1, "s": "user@email.com"},
            {"t": 1, "s": "turnstile-response-token"},
            {"t": 1, "s": "client-fingerprint-hash"}
          ],
          "s": 3
        },
        "o": 0
      }],
      "s": 1
    },
    "o": 0
  },
  "f": 31,
  "m": []
}
```

## Required Headers

```
Content-Type: application/json
Accept: application/x-ndjson, application/json
x-tsr-redirect: manual
```

## Finding Server Function Hashes

Server function hashes are embedded in the JavaScript bundle. Search the main bundle for `lt({method:"POST"` or `lt({method:"GET"` patterns — each is preceded by a hash definition:

```javascript
const r_ = it("0a4bb50b2f3e8be675a1fd0ac78237f4c70e0adcbdb39be9f37b0bfd36f9439e"),
    XE = lt({method: "POST"}).handler(r_);
```

The hash becomes the URL segment: `/_serverFn/0a4bb50b...?createServerFn`

## Extraction Workflow

1. Load the page in browser
2. Use `browser_console` to fetch JS bundles: `fetch('/assets/main-XXX.js').then(r => r.text())`
3. Search for `handler(` pattern
4. Extract hash + method pairs
5. Test with `curl` using Seroval serialization format

## Pitfalls

- **Direct API calls usually fail without valid Turnstile/captcha token** — the server function validates the token server-side
- **Seroval format is strict** — wrong type codes cause deserialization errors
- **`f` field** (function ID) may vary between bundles/deployments
- **The `m` array** at top level is always `[]` for requests
