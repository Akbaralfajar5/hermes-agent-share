# CloakBrowser X Login Flow

When twitter-cli env vars are NOT available and browser login is required.

## Prerequisites
- `pip install cloakbrowser` (v0.3.26+)
- Account credentials (username + password)
- CloakBrowser passes Cloudflare JS challenges but NOT interactive Turnstile

## Key Findings (May 2026)

### Auth Token Expiry
- All auth_tokens from bulk-purchased accounts expire within days/weeks
- X actively invalidates tokens for suspicious accounts
- Tokens from spreadsheets are almost always dead — check with curl first:
```bash
curl -s -D - "https://x.com/home" -H "Cookie: auth_token=TOKEN" -o /dev/null | grep "ct0="
# If response has "Max-Age=-" → EXPIRED
# If response has a real ct0 value → VALID
```

### X Login Flow Steps (CloakBrowser)
```python
from cloakbrowser import launch
import time

browser = launch(headless=True)  # humanize=True breaks fill() on hidden elements
page = browser.new_page()
page.goto('https://x.com/i/flow/login', timeout=30000)
time.sleep(7)  # Must wait for React to hydrate
```

### Critical: React Input Handling
X uses React — standard `page.fill()` and `page.click("Next")` often FAIL silently.

**Working approach for username step:**
```python
# Set value via React-compatible native setter
page.evaluate(f'''() => {{
    const input = document.querySelector('input[autocomplete="username"]');
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(input, '{USERNAME}');
    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
}}''')

# Navigate via Tab+Enter (clicking "Next" button often doesn't work)
page.evaluate('() => document.querySelector("input[autocomplete=\\"username\\"]").focus()')
page.keyboard.press('Tab')
time.sleep(0.3)
page.keyboard.press('Tab')
time.sleep(0.3)
page.keyboard.press('Enter')
time.sleep(5)
```

### Password Step
```python
# Password input works with standard click+type
pw = page.wait_for_selector('input[type="password"]', timeout=5000)
pw.click()
time.sleep(0.3)
page.keyboard.type(PASSWORD, delay=60)
time.sleep(1)
page.keyboard.press('Enter')
time.sleep(8)
```

### Common Verification Steps
X may insert these between username and password:
1. **"Find your X account"** → Enter email address
2. **"Confirm your username"** → Re-enter username
3. **"Where should we send a confirmation code?"** → Need email access (see below)

All use `input[data-testid="ocfEnterTextTextInput"]` or `input[name="text"]`.

### Email Confirmation Code Flow
If X requires email verification:
1. Click "Send an email to..." option
2. Login to email provider (rambler.ru for bulk accounts)
3. Extract 6-8 digit code from email
4. Enter code back in X

**Problem:** Rambler.ru requires captcha ("Пройдите верификацию") — cannot be automated.

### Extracting Cookies After Login
```python
cookies = page.context.cookies()
auth = [c for c in cookies if c['name'] == 'auth_token']
ct0 = [c for c in cookies if c['name'] == 'ct0']
```

## Pitfalls
- `humanize=True` breaks `fill()` on elements not in viewport — use `headless=True` without humanize for form filling
- X Cloudflare blocks API calls from VPS IPs (returns "Sorry, you have been blocked")
- `page.click('button:has-text("Next")')` often doesn't navigate — use Tab+Enter instead
- `networkidle` wait causes timeout — use default `load` event
- Bulk account tokens expire fast; X forces password reset flow for flagged accounts
- Rambler.ru email login requires captcha — manual intervention needed for email codes
