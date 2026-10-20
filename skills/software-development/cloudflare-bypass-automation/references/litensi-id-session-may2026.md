# Session: litensi.id Login Automation (May 16, 2026)

## Target
- **URL**: https://litensi.id
- **Credentials**: you@example.com / your-password78
- **Goal**: Automate login and access protected content

## Challenge Type
**Cloudflare JavaScript Challenge ("Just a moment...")**
- No captcha involved
- Pure JS computation challenge
- Page title stuck at "Just a moment..." for 20+ seconds
- Page content length: ~31,464 bytes (challenge page, not actual site)

## Tools Attempted

### 1. Playwright (vanilla)
```python
await page.goto('https://litensi.id', timeout=30000, wait_until='networkidle')
```
**Result**: ✗ Timeout after 30s, page never progresses past "Just a moment..."
**Reason**: Cloudflare detects automation; JS challenge never executes

### 2. Cloudscraper
```python
import cloudscraper
scraper = cloudscraper.create_scraper()
response = scraper.get('https://litensi.id', timeout=30)
```
**Result**: ✗ 403 Forbidden, returns challenge page HTML
**Reason**: Cloudscraper's Cloudflare bypass is outdated or ineffective for this protection level

### 3. Cloakbrowser
```python
import cloakbrowser
browser = await cloakbrowser.launch_async(headless=True)
page = await browser.new_page()
await page.goto('https://litensi.id', wait_until='load', timeout=45000)
```
**Result**: ✗ Page loads but stuck on "Just a moment..." for full 45s
- Title never changes from "Just a moment..."
- No form elements visible
- Page content remains challenge page HTML
- Waited 20 iterations of 1s checks; no progress

**Reason**: Even cloakbrowser's stealth measures insufficient for this Cloudflare config

### 4. 2captcha Integration
```python
from twocaptcha import TwoCaptcha
solver = TwoCaptcha(api_key)
result = solver.hcaptcha(sitekey=sitekey, pageurl='https://litensi.id')
```
**Result**: ✗ No captcha sitekey found in page HTML
**Reason**: This is a JS challenge, not a captcha challenge. 2captcha cannot solve JS challenges.

## Conclusion

**litensi.id uses Cloudflare protection that cannot be bypassed via headless browser automation.**

All tools (Playwright, cloakbrowser, cloudscraper) failed. The site's Cloudflare config:
- Detects headless browsers
- Blocks automation patterns
- Does not present a solvable captcha
- Requires real browser interaction or manual login

## Recommended Next Steps

1. **Manual Login + Cookie Extraction** (Most Reliable)
   - User logs in via desktop browser
   - Extract `cf_clearance` and session cookies
   - Pass cookies to requests/curl for subsequent API calls

2. **Check for API Endpoints**
   - Inspect Network tab in DevTools during manual login
   - Look for `/api/v1/...` or `/graphql` endpoints
   - These may have weaker Cloudflare protection

3. **IP Whitelisting**
   - If user has access to Cloudflare dashboard
   - Whitelist automation server IP
   - Allows direct access without challenge

4. **Contact litensi.id Support**
   - Request bot token or API access
   - Ask about automation-friendly endpoints

## Tools Tested
- Playwright 1.40+
- cloakbrowser (latest)
- cloudscraper (latest)
- 2captcha-python (latest)
- All with headless=True, various wait_until strategies

## Session Metadata
- Date: May 16, 2026
- API Key (2captcha): 227c1b6fe26a115607babe6224614181
- Status: **Automation not feasible; recommend manual login + cookies**
