# CAPTCHA Solver Setup

## Critical: Provider-Type Matrix

Using the wrong provider wastes money and fails silently.

| CAPTCHA | CapSolver | 2Captcha | Anti-Captcha | SolveCaptcha |
|---------|-----------|----------|-------------|-------------|
| hCaptcha | ⚠️ PARTIAL | ❌ DROPPED | ⚠️ UNLISTED | ❌ NOT SUPPORTED |
| reCAPTCHA v2 | ✅ | ✅ | ✅ | ✅ |
| reCAPTCHA v3 | ✅ | ✅ | ✅ | ✅ |
| Turnstile | ✅ | ✅ | ✅ | ✅ |
| Image/text | ❌ | ✅ | ✅ | ✅ |

### hCaptcha: The Hard Truth (2026)

**No captcha solver service reliably solves hCaptcha for all sites.**

- **2Captcha** — removed hCaptcha entirely in late 2025. Returns `ERROR_METHOD_CALL`.
- **CapSolver** — has `HCaptchaTaskProxyLess` API but **silently blocks high-profile sites** (e.g., Discord). Returns `ERROR_INVALID_TASK_DATA: Request has been blocked due to a violation of our usage policies`. No public blocklist exists — you only discover blocks by testing. This is likely due to business agreements with hCaptcha.
- **Anti-Captcha** — documents `HCaptchaTaskProxyless` in their API but does NOT list hCaptcha on their pricing page. Untested for Discord specifically.
- **SolveCaptcha** — does not support hCaptcha at all. Returns `ERROR_METHOD_CALL`. Despite Reddit recommendations (likely outdated/astroturfed).

### hCaptcha Accessibility Mode: Does NOT Work

hCaptcha offers an "Accessibility Challenge" (text-based questions instead of visual puzzles) via the accessibility menu. While the text questions are trivially solvable by an LLM, **this approach fails in practice**:
- Sites like Discord detect accessibility mode usage and may reject the token
- hCaptcha may serve increasingly difficult challenges or block entirely
- The accessibility cookie approach requires a verified hCaptcha account

### What Actually Works for hCaptcha

1. **Human solves it** — VNC/remote desktop, 30 seconds, 100% success rate
2. **CapSolver** — works for sites NOT on their secret blocklist
3. **Custom solvers** — open-source GPT-4 vision-based solvers exist (e.g., `xtekky/Discord-Hcaptcha-Solver`) but are fragile and high-maintenance
4. **Browser fingerprint quality** — a clean enough browser fingerprint sometimes passes the checkbox click alone without a challenge

## CapSolver Setup

1. Sign up at capsolver.com
2. Dashboard → API Key
3. Fund account (minimum ~$1, accepts crypto + cards)

```bash
mkdir -p ~/.config/stealth
echo '{"provider":"capsolver","api_key":"CAP-xxx"}' > ~/.config/stealth/captcha.json
chmod 600 ~/.config/stealth/captcha.json
```

## 2Captcha Setup

1. Sign up at 2captcha.com
2. Dashboard → API Key
3. Fund account (minimum ~$1, accepts crypto + PayPal + cards)

```bash
echo '{"provider":"2captcha","api_key":"xxx"}' > ~/.config/stealth/captcha.json
chmod 600 ~/.config/stealth/captcha.json
```

## Solving Flow

### Step 1: Detect captcha type

Look in page source for:
- `hcaptcha.com/1/api.js` → hCaptcha
- `google.com/recaptcha/api.js` → reCAPTCHA
- `challenges.cloudflare.com` → Turnstile
- `<img>` with captcha-like src → Image captcha

Extract the `sitekey` (usually in a `data-sitekey` attribute or script config).

### Step 2: Submit to solver

**hCaptcha via CapSolver:**
```python
import requests, time

# Create task
resp = requests.post("https://api.capsolver.com/createTask", json={
    "clientKey": API_KEY,
    "task": {
        "type": "HCaptchaTaskProxyLess",
        "websiteURL": PAGE_URL,
        "websiteKey": SITEKEY
    }
}).json()
task_id = resp["taskId"]

# Poll for result
while True:
    time.sleep(3)
    result = requests.post("https://api.capsolver.com/getTaskResult", json={
        "clientKey": API_KEY, "taskId": task_id
    }).json()
    if result["status"] == "ready":
        token = result["solution"]["gRecaptchaResponse"]
        break
```

**reCAPTCHA v2 via 2Captcha:**
```python
import requests, time

# Submit
resp = requests.get(
    f"http://2captcha.com/in.php?key={API_KEY}&method=userrecaptcha"
    f"&googlekey={SITEKEY}&pageurl={PAGE_URL}&json=1"
).json()
captcha_id = resp["request"]

# Poll (wait 20s before first check)
time.sleep(20)
while True:
    result = requests.get(
        f"http://2captcha.com/res.php?key={API_KEY}&action=get&id={captcha_id}&json=1"
    ).json()
    if result["status"] == 1:
        token = result["request"]
        break
    time.sleep(5)
```

**Cloudflare Turnstile via CapSolver:**
```python
resp = requests.post("https://api.capsolver.com/createTask", json={
    "clientKey": API_KEY,
    "task": {
        "type": "AntiTurnstileTaskProxyLess",
        "websiteURL": PAGE_URL,
        "websiteKey": SITEKEY
    }
}).json()
# Same polling as above
```

### Step 3: Inject token

**hCaptcha / reCAPTCHA:**
```javascript
// In browser context (Playwright/Puppeteer)
document.querySelector('[name="h-captcha-response"]').value = token;
document.querySelector('[name="g-recaptcha-response"]').value = token;
// Trigger callback if needed
window.hcaptcha?.getResponse && hcaptcha.submit();
// Or for reCAPTCHA:
___grecaptcha_cfg?.clients?.[0]?.aa?.l?.callback?.(token);
```

**Turnstile:**
```javascript
document.querySelector('[name="cf-turnstile-response"]').value = token;
// Submit the form
document.querySelector('form').submit();
```

### Step 4: Verify

After injection, submit the form or trigger the next action. If the page reloads with another CAPTCHA, the token may have expired (they're time-limited, typically 60-120 seconds). Re-solve and inject faster.

## Key Rotation (Mass Operations)

When running mass operations (multiple accounts, batch processing), rotate through multiple API keys to avoid rate limits and distribute costs.

```python
import time
import requests
from pathlib import Path

class CaptchaSolver:
    """2Captcha API wrapper with key rotation."""
    
    def __init__(self, keys_file: str = None):
        self.keys = self._load_keys(keys_file) if keys_file else []
        self.key_index = 0
    
    def _load_keys(self, path: str) -> list:
        try:
            with open(path, 'r') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            return []
    
    def _next_key(self) -> str:
        if not self.keys:
            raise ValueError("No 2Captcha keys available")
        key = self.keys[self.key_index]
        self.key_index = (self.key_index + 1) % len(self.keys)
        return key
    
    def solve_turnstile(self, sitekey: str, page_url: str, max_wait: int = 120) -> str:
        """Solve Cloudflare Turnstile with automatic key rotation."""
        api_key = self._next_key()
        
        # Submit task
        resp = requests.post('http://2captcha.com/in.php', data={
            'key': api_key,
            'method': 'turnstile',
            'sitekey': sitekey,
            'pageurl': page_url,
            'json': 1,
        }, timeout=30).json()
        
        if resp.get('status') != 1:
            return None
        
        task_id = resp['request']
        
        # Poll for result
        start = time.time()
        while time.time() - start < max_wait:
            time.sleep(5)
            result = requests.get('http://2captcha.com/res.php', params={
                'key': api_key,
                'action': 'get',
                'id': task_id,
                'json': 1,
            }, timeout=30).json()
            
            if result.get('status') == 1:
                return result['request']
            elif result.get('request') != 'CAPCHA_NOT_READY':
                return None
        
        return None
    
    def solve_recaptcha_v2(self, sitekey: str, page_url: str, max_wait: int = 120) -> str:
        """Solve reCAPTCHA v2 with automatic key rotation."""
        api_key = self._next_key()
        
        resp = requests.post('http://2captcha.com/in.php', data={
            'key': api_key,
            'method': 'userrecaptcha',
            'googlekey': sitekey,
            'pageurl': page_url,
            'json': 1,
        }, timeout=30).json()
        
        if resp.get('status') != 1:
            return None
        
        task_id = resp['request']
        
        start = time.time()
        while time.time() - start < max_wait:
            time.sleep(10)
            result = requests.get('http://2captcha.com/res.php', params={
                'key': api_key,
                'action': 'get',
                'id': task_id,
                'json': 1,
            }, timeout=30).json()
            
            if result.get('status') == 1:
                return result['request']
            elif result.get('request') != 'CAPCHA_NOT_READY':
                return None
        
        return None
```

**Key storage format** (one key per line):
```
# ~/.hermes/credentials/2captcha_keys.txt
abc123def456ghi789
xyz987wvu654tsr321
...
```

**Benefits of rotation:**
- Avoids single-key rate limits
- Distributes costs across accounts
- If one key gets banned, others continue
- Parallel solving possible with multiple keys
