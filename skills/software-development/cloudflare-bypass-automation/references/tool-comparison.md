# Cloudflare Bypass Tool Comparison

## Quick Reference Matrix

| Tool | JS Challenge | hCaptcha | reCAPTCHA | Bot Detection | Headless | Cost | Notes |
|------|--------------|----------|-----------|---------------|----------|------|-------|
| **Playwright** | ✗ | ✗ | ✗ | ✗ | ✓ | Free | Detected immediately; no stealth |
| **Puppeteer** | ✗ | ✗ | ✗ | ✗ | ✓ | Free | Same as Playwright |
| **Selenium** | ✗ | ✗ | ✗ | ⚠ | ✓ | Free | Slightly better; still detected |
| **cloakbrowser** | ⚠ | ⚠ | ⚠ | ⚠ | ✓ | Free | Best effort; unreliable on strict CF |
| **cloudscraper** | ✗ | ✗ | ✗ | ✗ | N/A | Free | Returns 403; outdated bypass |
| **2captcha** | N/A | ✓ | ✓ | N/A | N/A | $$ | Only for captcha solving |
| **Anti-Captcha** | N/A | ✓ | ✓ | N/A | N/A | $$ | Alternative to 2captcha |
| **Manual + Cookies** | ✓ | ✓ | ✓ | ✓ | N/A | Free | Most reliable fallback |

**Legend**: ✓ = Works, ⚠ = Unreliable/Partial, ✗ = Doesn't work, N/A = Not applicable, $$ = Paid service

## Cloudflare Protection Levels

### Level 1: Basic JS Challenge
- **Indicator**: "Just a moment..." page, no captcha
- **Bypass**: cloakbrowser (50% success), manual login
- **Example**: litensi.id (this session)

### Level 2: JS Challenge + Captcha
- **Indicator**: "Just a moment..." then hCaptcha/reCAPTCHA
- **Bypass**: cloakbrowser + 2captcha, manual login
- **Example**: Some banking sites

### Level 3: Advanced Bot Detection
- **Indicator**: Blocks even after JS challenge passes
- **Bypass**: Manual login + cookies, IP whitelisting
- **Example**: High-security sites, financial platforms

## When to Use Each Tool

### Use Playwright/Puppeteer if:
- Site has NO Cloudflare protection
- You control the site and can disable CF
- You need full browser automation (screenshots, interactions)

### Use cloakbrowser if:
- Site has Cloudflare JS challenge
- You have 45+ seconds to wait
- You're willing to accept 50% failure rate
- Manual login is not an option

### Use 2captcha if:
- Site presents hCaptcha or reCAPTCHA
- You have API credits
- You've confirmed captcha sitekey exists in page HTML

### Use Manual Login + Cookies if:
- Any automation fails
- You have user credentials
- You need reliable, repeatable access
- Speed is not critical

## Code Snippets

### Detect Challenge Type
```python
import asyncio
from playwright.async_api import async_playwright

async def detect_cf_challenge(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=10000)
        except:
            pass
        
        await asyncio.sleep(2)
        
        title = await page.title()
        content = await page.content()
        
        if "Just a moment" in title:
            return "JS_CHALLENGE"
        elif "hcaptcha" in content:
            return "HCAPTCHA"
        elif "g-recaptcha" in content:
            return "RECAPTCHA"
        else:
            return "NONE_OR_BOT_DETECTION"
        
        await browser.close()

# Usage
challenge_type = asyncio.run(detect_cf_challenge('https://example.com'))
print(f"Challenge type: {challenge_type}")
```

### Extract Cookies from Manual Login
```python
# In browser DevTools:
# 1. Open Application tab
# 2. Cookies → https://target.com
# 3. Copy all cookies as JSON

cookies = {
    'cf_clearance': 'YOUR_VALUE',
    '__cfruid': 'YOUR_VALUE',
    'other_session': 'YOUR_VALUE'
}

# Use in requests
import requests
response = requests.get('https://target.com/protected', cookies=cookies)
print(response.status_code)
```

### cloakbrowser with Timeout Fallback
```python
import asyncio
import cloakbrowser

async def try_cloakbrowser_with_fallback(url, timeout_sec=45):
    try:
        browser = await cloakbrowser.launch_async(headless=True)
        page = await browser.new_page()
        
        await page.goto(url, wait_until='load', timeout=timeout_sec * 1000)
        
        # Wait for challenge to resolve
        for i in range(timeout_sec):
            await asyncio.sleep(1)
            title = await page.title()
            if "Just a moment" not in title:
                print(f"✓ Challenge resolved at {i+1}s")
                return page
        
        print(f"✗ Challenge not resolved after {timeout_sec}s")
        await browser.close()
        return None
    
    except Exception as e:
        print(f"✗ cloakbrowser failed: {e}")
        return None

# Usage
page = asyncio.run(try_cloakbrowser_with_fallback('https://example.com', timeout_sec=45))
if page is None:
    print("→ Fall back to manual login + cookies")
```

## Known Issues & Workarounds

| Issue | Cause | Workaround |
|-------|-------|-----------|
| cloakbrowser hangs indefinitely | Strict CF config | Set hard timeout (45s), fall back to manual |
| 2captcha returns "ERROR_CAPTCHA_UNSOLVABLE" | No captcha on page | Check if it's a JS challenge instead |
| Cookies expire quickly | Session timeout | Re-extract cookies or use persistent login |
| Different IP gets different CF response | Geo-blocking or rate limiting | Use proxy or wait before retry |

## References
- Cloudflare Bot Management: https://www.cloudflare.com/products/bot-management/
- cloakbrowser GitHub: https://github.com/daijro/cloakbrowser
- 2captcha API: https://2captcha.com/api/docs
