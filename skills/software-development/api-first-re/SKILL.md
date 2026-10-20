---
name: api-first-re
description: "API-First Reverse Engineering — extract REST/GraphQL endpoints from web apps and build pure-API automation scripts. No browser, no Playwright, no Puppeteer. Full interaction via HTTP requests."
tags: ["reverse-engineering", "api", "automation", "airdrop", "testnet", "web3"]
embedding_hint: "reverse engineer web app API endpoints REST GraphQL extract JS bundle automation no browser pure API curl requests login claim mint farm tools"
---

# API-First Reverse Engineering

## Purpose
When given any web app (airdrop, testnet, farming platform, WL site), reverse-engineer ALL API endpoints first, then build pure-API scripts. Zero browser dependency. Everything via HTTP requests (curl/requests/fetch).

## When to Use
- User says "garap", "farm", "automate" any web platform
- User shares a URL and wants tools/scripts built
- User wants to interact with a web3 dApp programmatically
- User wants mass automation (multi-account, multi-wallet)
- ANY task where browser automation would normally be considered
- Keywords: RE, reverse engineer, API, automate, garap, tools, script

## Golden Rule
**NEVER reach for browser automation first.** Always RE the API. Browser is LAST RESORT only when:
- OAuth popup is truly un-automatable (Google GIS with consent)
- CAPTCHA with no solver available
- WebSocket-only realtime that has no REST fallback

## Workflow (Sequential, Never Skip)

### Phase 1: Reconnaissance (5 min)
```bash
# 1. Get page source, find JS bundles
curl -s 'https://target.com/' | grep -oP 'src="[^"]*\.js[^"]*"'

# 2. For Next.js apps — find _next/static chunks
curl -s 'https://target.com/' | grep -oP '/_next/static/chunks/[^"]+\.js'

# 3. For Vite/React SPAs — find assets/*.js  
curl -s 'https://target.com/' | grep -oP '/assets/[^"]+\.js'

# 4. Check common API paths
curl -s 'https://target.com/api' 
curl -s 'https://target.com/api/health'
curl -s 'https://target.com/api/graphql' -X POST -H 'Content-Type: application/json' -d '{"query":"{ __typename }"}'
```

### Phase 2: JS Bundle Analysis (10 min)
```bash
# Download main bundle(s)
curl -s 'https://target.com/assets/index-HASH.js' > bundle.js

# Extract API URLs
grep -oP 'https://[^"'\''`,\s]+' bundle.js | sort -u

# Extract API route paths
grep -oP '"/[a-z][^"]*"' bundle.js | sort -u

# Find auth patterns
grep -oP '.{0,100}(auth|token|session|cookie|bearer|apikey).{0,100}' bundle.js

# Find function names / endpoints
grep -oP '.{0,50}(fetch|axios|post|get|put|delete).{0,100}' bundle.js

# Find contract addresses (web3 apps)
grep -oP '0x[0-9a-fA-F]{40}' bundle.js | sort -u

# Find GraphQL mutations/queries
grep -oP '(mutation|query)\s+\w+' bundle.js
```

### Phase 3: API Mapping (10 min)
Document all endpoints found:
```
BASE_URL: https://api.target.com
AUTH: Bearer token via /auth/login
ENDPOINTS:
  POST /auth/login          → {email, password} → {token}
  GET  /user/me             → user profile
  POST /claim               → {wallet, proof} → {txHash}
  GET  /leaderboard         → [{rank, address, points}]
  POST /tasks/complete      → {taskId} → {points}
```

### Phase 4: Auth Flow RE
Common patterns to identify:
1. **JWT Bearer** — login endpoint returns token, use in Authorization header
2. **Session Cookie** — login sets httpOnly cookie, send with credentials
3. **API Key** — static key in headers (X-API-Key, Authorization)
4. **OAuth2** — /auth/callback with code exchange
5. **Wallet Signature** — SIWE (Sign In With Ethereum): get nonce → sign → verify
6. **Magic Link** — email verification, extract token from URL

```bash
# Test auth flow
curl -s -X POST 'https://api.target.com/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@test.com","password":"pass"}' \
  -D - 2>/dev/null | grep -i 'set-cookie\|token\|bearer'
```

### Phase 5: Build Script (Pure API)
```python
#!/usr/bin/env python3
"""target.com automation — pure API, no browser"""
import requests, time, json

BASE = "https://api.target.com"
session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://target.com",
    "Referer": "https://target.com/"
})

def login(email, password):
    r = session.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    data = r.json()
    token = data.get("token")
    session.headers["Authorization"] = f"Bearer {token}"
    return data

def claim(wallet_address):
    r = session.post(f"{BASE}/claim", json={"wallet": wallet_address})
    return r.json()

# Multi-account loop
for account in accounts:
    login(account["email"], account["password"])
    result = claim(account["wallet"])
    print(f"{account['email']}: {result}")
    time.sleep(2)  # rate limit respect
```

### Phase 6: Verification
```bash
# Test single account manually
curl -s -X POST 'https://api.target.com/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@test.com","password":"pass"}'

# Verify claim works
curl -s -X POST 'https://api.target.com/claim' \
  -H 'Authorization: Bearer TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"wallet":"0x..."}'
```

## Advanced Patterns

### tRPC Apps (Next.js)
```bash
# tRPC endpoints follow pattern: /trpc/router.procedure
# Query (GET): /trpc/user.getProfile?batch=1&input={"0":{"json":null}}
# Mutation (POST): /trpc/user.claim?batch=1 with body {"0":{"json":{...}}}

# Discover procedures from JS bundles:
grep -oP '\w+\.\w+\.(query|mutate|useQuery|useMutation)' bundle.js
```

### GraphQL Apps
```bash
# Introspection (if enabled)
curl -s -X POST 'https://api.target.com/graphql' \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ __schema { queryType { fields { name } } mutationType { fields { name } } } }"}'

# Find mutations from bundle
grep -oP 'mutation \w+\([^)]+\)' bundle.js
```

### Wallet Auth (SIWE)
```python
from eth_account import Account
from eth_account.messages import encode_defunct

# 1. Get nonce
nonce = session.get(f"{BASE}/auth/nonce?address={wallet}").json()["nonce"]

# 2. Construct SIWE message
message = f"""target.com wants you to sign in with your Ethereum account:
{wallet}

Sign in to target.com

URI: https://target.com
Version: 1
Chain ID: 1
Nonce: {nonce}
Issued At: {datetime.utcnow().isoformat()}Z"""

# 3. Sign
signed = Account.from_key(private_key).sign_message(encode_defunct(text=message))

# 4. Verify
session.post(f"{BASE}/auth/verify", json={
    "message": message,
    "signature": signed.signature.hex()
})
```

### Encrypted/Obfuscated Payloads
When API requires encrypted tokens (like b.ai's `encryptedToken`):
```python
# 1. Find encryption in JS bundle
grep -oP '.{0,200}encrypt.{0,200}' bundle.js

# 2. Identify algorithm (usually CryptoJS AES or SubtleCrypto)
# 3. Find key (hardcoded in bundle or derived)
# 4. Replicate in Python
from Crypto.Cipher import AES  # or use cryptography library
```

### Rate Limiting & Anti-Detection
```python
# Between requests: 2-5 seconds random
time.sleep(2 + random.random() * 3)

# Rotate User-Agents for multi-account
UAs = ["Mozilla/5.0 (Windows...", "Mozilla/5.0 (Mac..."]

# If IP-based rate limit: use proxy rotation
proxies = {"https": f"http://user:pass@proxy:port"}
session.proxies = proxies
```

## When Browser IS Required (last resort)

Only after confirming ALL of these:
- [ ] No REST/GraphQL API found for the action
- [ ] Auth requires browser popup (Google OAuth GIS, Twitter OAuth)
- [ ] CAPTCHA with no API solver available
- [ ] WebSocket-only with no HTTP fallback

If browser needed, use **minimal browser** approach:
- Login only → extract cookie/token → close browser → continue with API
- Never use browser for data fetching or form submission if API exists

### Browser Fallback Pitfalls
1. **Turnstile won't solve from VPS/datacenter IPs** — Cloudflare detects ASN and silent-fails. Script must run from residential IP. See `captcha-self-solve` skill.
2. **Google OAuth consent screen** — after password, there's a "Continue" button. Handle: email → password → consent → popup closes → page.reload().
3. **Session cookie names vary** — NextAuth: `next-auth.session-token`. AuthJS v5: `__Secure-authjs.*`. Always check actual cookie names.
4. **React buttons need Playwright .click()** — JS `el.click()` may not trigger React synthetic events. Use `page.locator().click()`.
5. **Modal flows** — some claim flows: click banner → modal opens → Turnstile solves → inner button enables → click inner button. Don't skip steps.

## When Browser IS Required (exceptions to API-first)
Despite best efforts, some flows genuinely need a browser:
- **Cloudflare Turnstile (managed mode):** Server validates token. **BUT always test empty string first** (`turnstile=`) — some sites accept it (unimodel.ai confirmed). If empty fails, must render widget in real browser from residential IP.
- **Google OAuth popup (GIS):** Uses postMessage between popup and parent. Can't replicate via pure HTTP.
- **Interactive CAPTCHA (hCaptcha image grid):** Needs visual solver.

**2-Phase Architecture** (minimize browser usage):
1. Phase 1 (API/headless): Login, extract cookies, do everything possible without visible browser
2. Phase 2 (non-headless, residential IP): ONLY for the Turnstile/CAPTCHA-gated action, using saved cookies from Phase 1

This keeps browser usage to the absolute minimum while handling hard blocks.

## Key Principles (from reverse-api-engineer methodology)
1. **Generated scripts must work immediately** — hardcode all credentials, cookies, tokens found during RE. No env vars needed for single-use scripts. Config file only for multi-account.
2. **Auto re-auth** — if token refresh or login flow is discovered, implement automatic re-authentication so script doesn't go stale.
3. **Prefer httpx/requests over browser** — match headers exactly as seen in network traffic. Only use browser as absolute last resort.
4. **Test immediately** — after generating script, run against 1 account to verify before scaling.
5. **Narrate findings** — document APIs discovered, auth method, limitations before writing code.

## Google Forms Auto-Submit (No Login Required)

Google Forms can be RE'd and mass-submitted via pure API — no browser needed.

### Phase 1: Extract Form Structure
```javascript
// In browser console on the viewform URL:
(() => {
  const scripts = document.querySelectorAll('script');
  for (const script of scripts) {
    if (script.textContent.includes('FB_PUBLIC_LOAD_DATA_')) {
      return script.textContent.substring(
        script.textContent.indexOf('FB_PUBLIC_LOAD_DATA_')
      );
    }
  }
})();
```

The `FB_PUBLIC_LOAD_DATA_` array contains ALL questions, entry IDs, field types, and options — even for multi-page forms. Parse it to extract:
- **Entry IDs** (numeric, e.g., `1851559330`) — the `entry.XXXXX` POST param names
- **Field types**: `0`=text, `1`=paragraph, `2`=radio, `3`=dropdown, `4`=checkbox, `5`=linear scale
- **Required fields** (3rd element in field options array = `1` means required)
- **Scale options** for Likert (e.g., `[["1"],["2"],["3"],["4"],["5"]]`)

### Phase 2: Submit via curl
```bash
# POST to /formResponse (not /viewform)
# Public form URL: .../d/e/LONG_ID/viewform
# Submit URL:      .../d/e/LONG_ID/formResponse

curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://docs.google.com/forms/d/e/FORM_ID/formResponse" \
  -d "entry.111111=Answer1&entry.222222=3&entry.333333=Option+A"

# HTTP 200 = success
```

### Phase 3: Mass Submit Script
```bash
#!/bin/bash
FORM_URL="https://docs.google.com/forms/d/e/FORM_ID/formResponse"

# Loop with random delay to look natural
for i in $(seq 1 30); do
  curl -s -o /dev/null -w "%{http_code}" -X POST "$FORM_URL" \
    -d "entry.111=Name${i}&entry.222=${RANDOM:0:1}&entry.333=4"
  echo " - [$i/30] submitted"
  sleep $((RANDOM % 4 + 2))
done
```

### Key Notes
- **No auth needed** if form doesn't require Google login (check for "Sign in to Google" being optional vs mandatory)
- **Multi-page forms require `pageHistory` + `fbzx`** — a bare POST with just entry fields returns HTTP 200 but data is EMPTY in responses. You MUST include:
  - `fvv=1`
  - `pageHistory=0,1,2,3,...,N` (comma-separated page indices, 0-based, covering all pages)
  - `fbzx=TOKEN` (anti-CSRF token extracted from the form page)
  - `partialResponse=[null,null,"FBZX_TOKEN"]`
  - `submissionTimestamp=EPOCH_MS`
- **Extract fbzx**: load the viewform URL first, then regex `"fbzx":"([^"]+)"` or `name="fbzx" value="([^"]+)"` from HTML
- **Determine page count**: count section headers (type=8) in `FB_PUBLIC_LOAD_DATA_` array, or inspect hidden input `pageHistory` value on last page
- **Linear scale** values are just the number as string ("1", "2", etc.)
- **Checkbox** fields use repeated params: `entry.XXX=A&entry.XXX=B`
- **For realistic Likert data**: vary scores with weighted random (not uniform) to pass statistical scrutiny (N-Gain, normality tests)
- **Fresh session per submission**: create a new `requests.Session()` + GET the form page for each respondent to get a unique `fbzx` token. Reusing tokens may cause silent drops.

### Multi-Page Form Complete Example (Python)
```python
import requests, re, random, time

FORM_URL = "https://docs.google.com/forms/d/e/FORM_ID/viewform"
SUBMIT_URL = "https://docs.google.com/forms/d/e/FORM_ID/formResponse"

def submit_one(entries_dict):
    """Submit one response to a multi-page Google Form."""
    session = requests.Session()
    r = session.get(FORM_URL)
    
    # Extract fbzx token
    fbzx_m = re.search(r'"fbzx":"([^"]+)"', r.text)
    if not fbzx_m:
        fbzx_m = re.search(r'name="fbzx" value="([^"]+)"', r.text)
    fbzx = fbzx_m.group(1) if fbzx_m else ""
    
    data = {
        **{f"entry.{k}": v for k, v in entries_dict.items()},
        "fvv": "1",
        "partialResponse": f'[null,null,"{fbzx}"]',
        "pageHistory": "0,1,2,3,4,5",  # adjust to actual page count
        "fbzx": fbzx,
        "submissionTimestamp": str(int(time.time() * 1000)),
    }
    
    r = session.post(SUBMIT_URL, data=data)
    return r.status_code == 200 and "recorded" in r.text.lower()
```

## Output Structure
```
~/project-name/
├── README.md           # API map, auth flow, endpoints
├── config.json         # accounts, wallets, credentials
├── main.py             # main automation script
├── auth.py             # login/token refresh logic
├── api.py              # API client with all endpoints
└── results.json        # execution logs
```

## When Pure API Hits a Wall

Some endpoints have **server-side validation** that can't be bypassed:

- **Turnstile/CAPTCHA token validation** — server calls Cloudflare verify API. Empty/dummy tokens return `missing-input-response` / `invalid-input-response`. Must solve in browser from residential IP.
- **Google OAuth (GIS)** — uses `postMessage` popup. Headless misses callback. Need real browser with popup handling (email → password → consent → popup closes).
- **"Button disabled until token" pattern** — modal opens → CAPTCHA renders → button enables only after callback. `removeAttribute('disabled')` doesn't help — React state blocks the fetch.

**Hybrid approach:** Login/auth via browser → extract session cookie → continue all other operations via pure API.

## Pitfalls
1. **CORS doesn't apply to server-side requests** — browser CORS errors don't exist in curl/Python. Just call the API directly.
2. **HttpOnly cookies** — Can't read from JS but curl receives them fine. Use `-c cookies.txt` to capture.
3. **CSRF tokens** — Fetch from page/API first, include in subsequent requests.
4. **Cloudflare WAF** — If API is behind CF managed challenge, need to solve or use cookie from browser session.
5. **WebSocket endpoints** — Some apps use WS for realtime. Use `websocket-client` Python lib, not browser.
6. **Minified/obfuscated bundles** — Use `js-beautify` or online deobfuscator before grepping.
7. **Dynamic imports/chunks** — Main bundle may lazy-load routes. Check network tab patterns or find chunk manifest.
8. **API versioning** — Check for /v1/, /v2/ in URLs. Older versions might have less security.
9. **Turnstile-gated endpoints: always test empty string first** — Some implementations accept empty `turnstile=` parameter (e.g., unimodel.ai). Before assuming Turnstile is a hard gate, try: `curl -s "https://target/api/endpoint?email=test@test.com&turnstile="`. If it returns success, you saved yourself 2captcha costs. If it returns `missing-input-response` / `invalid-input-response`, THEN you need browser/2captcha. **Never assume — always test.**
10. **File sharing for delivery** — transfer.sh is dead, 0x0.st blocks uploads. For Telegram: MEDIA: tag only works for images/audio/video. Use Bot API `send_document()` for .zip/.py/.txt files.
11. **SPA APIs require browser headers** — Vue/React SPAs (especially those behind Nginx gateways) return 404 or 403 if `User-Agent`, `Referer`, and `Origin` headers are missing. Always include them: `User-Agent: Mozilla/5.0 ...`, `Referer: https://site.com/`, `Origin: https://site.com`. Test with `curl` including these headers before assuming the API path is wrong.
12. **When SPA APIs use obfuscated field names, fall back to browser** — Some sites (e.g., example-target.com) use minified JS that maps human-readable form fields to obfuscated API params (`pfi`, `ui`, `du`, etc.) with custom signing mechanisms. If you can't reverse the mapping within 15 min, use browser automation (Camoufox/Playwright) to interact with the UI instead. Document the API endpoints you DID find in a reference file for future use.
