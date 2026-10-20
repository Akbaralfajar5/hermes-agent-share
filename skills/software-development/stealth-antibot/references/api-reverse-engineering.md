# API Reverse Engineering Methodology

## Overview

When a site has complex browser automation (multi-step flows, CAPTCHAs, popups), it's often faster to reverse engineer the API and make direct HTTP calls instead.

## Methodology

### Step 1: Identify API Endpoints

**From JavaScript bundles:**
```python
from tls_client import safe_get
import re

# Get main page
resp = safe_get('https://target.com')

# Find JS chunks
js_files = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', resp.text)

# Analyze each chunk for API patterns
for js_url in js_files:
    if js_url.startswith('/'):
        js_url = f'https://target.com{js_url}'
    
    js_resp = safe_get(js_url)
    
    # Find API endpoints
    apis = re.findall(r'["\']([^"\']*(?:/api/|/v1/|/v2/|/h5/|/oauth/)[^"\']*)["\']', js_resp.text, re.I)
    
    # Find base URLs
    bases = re.findall(r'baseURL["\s:=]+["\']([^"\']+)["\']', js_resp.text)
    
    # Find fetch/axios patterns
    fetches = re.findall(r'(?:axios|fetch|request|post|get)\s*\(\s*["\']([^"\']+)["\']', js_resp.text)
```

**Common API patterns:**
- `/oauth/token` — OAuth login
- `/user/login` — User authentication
- `/api/v1/...` — Versioned API
- `/h5/...` — Mobile/H5 API endpoints
- `/verify-code/...` — Verification flows

### Step 2: Capture Live Requests

**Browser DevTools method:**
1. Open Chrome DevTools → Network tab
2. Perform the action manually
3. Right-click request → Copy as cURL
4. Convert to Python requests

**Playwright intercept method:**
```python
async def capture_requests(page, url, action):
    requests = []
    
    page.on('request', lambda req: requests.append({
        'url': req.url,
        'method': req.method,
        'headers': dict(req.headers),
        'body': req.post_data,
    }))
    
    await page.goto(url)
    await action(page)  # Perform the action
    
    return requests
```

### Step 3: Replicate with curl_cffi

```python
from tls_client import safe_session

session = safe_session(mobile=True)

# Replicate captured request
resp = session.post(
    'https://target.com/api/login',
    json={
        'phone': '081234567890',
        'password': 'your-password',
        'captcha': captcha_token,  # If needed
    },
    headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    },
)
```

### Step 4: Handle CAPTCHAs

Most sites with login flows require CAPTCHA solving. See `captcha-setup.md` for integration.

**Flow:**
1. GET page → extract CAPTCHA sitekey
2. Solve via 2Captcha/CapSolver
3. Include token in login request

## Case Study: example-target.com

**Site:** Indonesian gambling/deposit platform
**Tech stack:** Vue.js + Vant UI + Cloudflare Turnstile + Google reCAPTCHA

**API endpoints discovered:**
```
POST /oauth/token          — OAuth login (grant_type=password)
POST /user/login           — Alternative login
POST /verify-code/v1/centralized/phone — Phone verification
POST /h5/v3/aggregates/startup-data/index — Account data
POST /playerAccountChange/playerRechargeData/v1/get — Deposit methods
POST /playerAccountChange/playerRechargeData/update — Submit deposit
POST /game/login-game      — Game login
POST /withdraw-app/v2/addWithdrawOrder — Withdrawal
```

**Challenges:**
- Cloudflare Turnstile sitekey loaded dynamically via JS (not in HTML)
- API endpoints return 405 if wrong Content-Type or method
- OAuth token required for authenticated endpoints
- Both Turnstile AND reCAPTCHA may be required

**Solution approach:**
1. Browser automation for initial CAPTCHA solving + token capture
2. API calls for subsequent operations (faster, no browser overhead)
3. Token refresh via API when expired

## Pitfalls

1. **405 Method Not Allowed** — Wrong HTTP method or Content-Type. Try both JSON and form-data.

2. **Missing CORS headers** — API may reject browser requests but accept direct HTTP calls.

3. **Dynamic sitekeys** — CAPTCHA sitekeys may be loaded via JS, not in HTML. Need to execute JS to extract.

4. **Token expiration** — OAuth tokens expire. Implement refresh logic.

5. **Rate limiting** — API endpoints may have stricter rate limits than browser. Add delays.

6. **Fingerprint requirements** — Some APIs check TLS fingerprint. Use curl_cffi with browser profile.
