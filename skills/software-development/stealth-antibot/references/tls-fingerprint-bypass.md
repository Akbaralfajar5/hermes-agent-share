# TLS Fingerprint Bypass (curl_cffi)

## Why TLS Fingerprinting Matters

Cloudflare, Akamai, and PerimeterX fingerprint the TLS handshake (JA3/JA4 hash) to detect bots. Standard HTTP libraries (requests, httpx, aiohttp) and even Playwright have known TLS fingerprints that are flagged.

**Key insight from testing (June 2026):**
- Playwright Chromium with 25 stealth patches: ❌ Cloudflare basic STILL BLOCKED
- curl_cffi with Chrome 124 profile: ✅ Cloudflare basic PASSED

The difference: curl_cffi impersonates real browser TLS fingerprints at the network level, before any JavaScript runs. Stealth patches only affect the JavaScript environment.

## When to Use curl_cffi vs Playwright

| Use Case | Tool | Why |
|----------|------|-----|
| Simple GET/POST requests | curl_cffi | Fast, lightweight, TLS bypassed |
| API calls | curl_cffi | No browser overhead |
| Cookie-based auth | curl_cffi | Cookies work in HTTP requests |
| Complex multi-step flows | Playwright | Need JavaScript execution |
| Form filling, clicking | Playwright | Need DOM interaction |
| Sites with JS challenges | Playwright | Need to execute challenge JS |

## Installation

```bash
pip install curl_cffi
```

## Quick Start

```python
from curl_cffi import requests

# GET with Chrome 124 TLS fingerprint
resp = requests.get(
    'https://www.example.com',
    impersonate='chrome124',  # JA3 = real Chrome 124
    headers={
        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    }
)
print(resp.status_code)
print(resp.text)

# POST with JSON
resp = requests.post(
    'https://api.example.com/data',
    json={'key': 'value'},
    impersonate='chrome124',
)

# Session with cookies
session = requests.Session(impersonate='chrome124')
session.cookies.set('token', 'xxx', domain='.example.com')
resp = session.get('https://www.example.com/protected')
```

## Available Browser Profiles

```python
# Chrome versions
'chrome120'  # Chrome 120
'chrome124'  # Chrome 124 (default, matches our UA)
'chrome119'  # Chrome 119
'chrome116'  # Chrome 116

# Other browsers
'edge101'    # Edge 101
'safari15_5' # Safari 15.5
'safari17_0' # Safari 17.0
```

## Proxy Support

```python
# With proxy
resp = requests.get(
    'https://www.example.com',
    impersonate='chrome124',
    proxy='http://user:pass@host:port',
)

# Session with proxy
session = requests.Session(
    impersonate='chrome124',
    proxies={
        'https': 'http://user:pass@host:port',
        'http': 'http://user:pass@host:port',
    }
)
```

## Test Results (June 2026)

```
============================================================
TLS FINGERPRINT TEST RESULTS
============================================================

1. JA3 Fingerprint:
   ✅ JA3 Hash: 29c6a9ee235d6b401641defb3a4dfc3b
   ✅ User-Agent: Chrome 124 (Windows)
   ✅ TLS fingerprint = Real browser

2. Cloudflare Basic (whatismybrowser.com):
   ✅ PASSED — Sebelumnya BLOCKED dengan Playwright

3. Cloudflare Advanced (nowsecure.nl):
   ❌ BLOCKED — Masih kena behavioral analysis

4. Netflix (with cookies):
   ✅ WORKING — Login berhasil via cookies

============================================================
```

## Netflix Cookie Injection (curl_cffi)

```python
from curl_cffi import requests

# Create session with Netflix cookies
session = requests.Session(impersonate='chrome124')
session.cookies.set('nfvdid', '...', domain='.netflix.com', path='/')
session.cookies.set('NetflixId', '...', domain='.netflix.com', path='/')
session.cookies.set('SecureNetflixId', '...', domain='.netflix.com', path='/')

# Access Netflix
resp = session.get('https://www.netflix.com/browse')
if 'login' not in resp.url:
    print("✅ Logged in!")
```

## Cookie Source

Netflix cookies can be found at:
- **shrestha.live** — Interactive map with 1096+ cookies across 50 countries
- Filter by region (Indonesia, India, etc.)
- Cookies expire when billing cycle ends
- Use the [CHECKER] feature to verify cookies before use

## TLS Client Module

A reusable TLS client module is available at:
```
/home/ubuntu/deposit_project/tls_client.py
```

Usage:
```python
from tls_client import safe_get, safe_post, safe_session, netflix_session

# Simple GET
resp = safe_get('https://target.com')

# Netflix session
session = netflix_session({'NetflixId': '...', 'SecureNetflixId': '...'})
resp = session.get('https://www.netflix.com/browse')
```

## Limitations

1. **No JavaScript execution** — curl_cffi is HTTP only, cannot execute JS challenges
2. **Cloudflare advanced still blocks** — Behavioral analysis (mouse, timing) requires Playwright + humanization
3. **Some sites check HTTP/2 settings** — curl_cffi's HTTP/2 may differ from real browser
4. **Cookies expire** — Need to refresh from source periodically

## Pitfalls

1. **Don't mix with requests/httpx** — curl_cffi has its own session/cookie management
2. **Proxy format** — Use `http://user:pass@host:port`, not socks5 unless supported
3. **Cookie domain** — Always set domain='.netflix.com' (with leading dot) for cross-subdomain cookies
4. **TLS profile must match UA** — If using chrome124 profile, UA should say Chrome 124
5. **Response object differs** — curl_cffi Response has .text, .json(), .status_code but implementation differs slightly from requests
