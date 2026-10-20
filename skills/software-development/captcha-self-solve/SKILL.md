---
name: captcha-self-solve
description: "Solve CAPTCHAs locally without paid services — Turnstile auto-solve via browser, reCAPTCHA v3 score bypass, image/text OCR (Tesseract), audio transcription (Whisper). Zero cost."
tags: ["captcha", "turnstile", "recaptcha", "ocr", "whisper", "free", "self-solve"]
embedding_hint: "solve captcha free no service turnstile auto browser recaptcha v3 score OCR tesseract audio whisper bypass local"
---

# Captcha Self-Solve (Free, No Service)

## Purpose
Solve CAPTCHAs locally without paying third-party services. Covers all types that can be solved programmatically without human intervention.

## When to Use
- Target has Cloudflare Turnstile (invisible or managed)
- Target uses reCAPTCHA v3 (score-based, no challenge)
- Target has simple image/text CAPTCHA (OCR-able)
- Target offers audio CAPTCHA alternative
- User doesn't want to pay for captcha solver services

## What CAN vs CANNOT Be Self-Solved

| Type | Self-Solvable | Method |
|------|:---:|--------|
| Turnstile (invisible) | ✅ | Browser render + wait for callback |
| Turnstile (managed) | ✅ | Browser with stealth + auto-solve |
| Turnstile (interactive) | ⚠️ | Needs visible browser + click |
| reCAPTCHA v3 | ✅ | Stealth browser = high score auto |
| reCAPTCHA v2 audio | ✅ | Download audio → Whisper STT |
| Image/text CAPTCHA | ✅ | Tesseract OCR or PIL |
| reCAPTCHA v2 image grid | ❌ | Need paid service |
| hCaptcha image | ❌ | Need paid service |

---

## Method 1: Turnstile Auto-Solve (Browser)

Turnstile in invisible/managed mode auto-solves when rendered in a legitimate browser environment.

```python
#!/usr/bin/env python3
"""Turnstile self-solver — render widget, wait for token"""
from playwright.sync_api import sync_playwright
import time

def solve_turnstile(page, sitekey, target_url):
    """
    Inject Turnstile widget into page and wait for auto-solve.
    Returns token string or None.
    """
    # Inject Turnstile script + container
    page.evaluate(f'''() => {{
        window.__cf_token = null;
        const script = document.createElement('script');
        script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=__onTurnstileLoad';
        
        window.__onTurnstileLoad = function() {{
            const div = document.createElement('div');
            div.id = 'cf-self-solve';
            div.style.position = 'fixed';
            div.style.bottom = '10px';
            div.style.right = '10px';
            div.style.zIndex = '99999';
            document.body.appendChild(div);
            
            turnstile.render('#cf-self-solve', {{
                sitekey: '{sitekey}',
                callback: function(token) {{
                    window.__cf_token = token;
                }},
                'error-callback': function(e) {{
                    window.__cf_error = e;
                }}
            }});
        }};
        document.head.appendChild(script);
    }}''')
    
    # Poll for token (max 60s)
    for i in range(30):
        time.sleep(2)
        result = page.evaluate('() => ({token: window.__cf_token, error: window.__cf_error})')
        if result.get('token'):
            return result['token']
        if result.get('error'):
            return None
    
    return None


def solve_turnstile_stealth(sitekey, target_url):
    """Full stealth solve — launch browser, navigate, solve, return token"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # Turnstile needs non-headless for some sitekeys
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # Remove webdriver flag
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            delete navigator.__proto__.webdriver;
        """)
        
        page = context.new_page()
        page.goto(target_url, wait_until='load')
        time.sleep(3)
        
        token = solve_turnstile(page, sitekey, target_url)
        browser.close()
        return token
```

### Headless VPS: Use xvfb
```bash
# Install virtual display
sudo apt install -y xvfb

# Run with virtual display (Turnstile thinks it's real browser)
xvfb-run -a python3 solve_turnstile.py
```

### CloakBrowser variant
```python
from cloakbrowser import launch_context

def solve_turnstile_cloak(sitekey, target_url):
    """CloakBrowser stealth — better anti-detection"""
    ctx = launch_context(
        headless=False,  # or True with xvfb
        stealth_args=True,
        humanize=True,
        locale='en-US',
        timezone='America/New_York'
    )
    page = ctx.new_page()
    page.goto(target_url, timeout=60000, wait_until='load')
    time.sleep(3)
    
    token = solve_turnstile(page, sitekey, target_url)
    ctx.close()
    return token
```

---

## Method 2: reCAPTCHA v3 Score Bypass

reCAPTCHA v3 has NO challenge — it just assigns a score (0.0-1.0) based on browser behavior. Stealth browser with human-like behavior gets 0.7-0.9 automatically.

```python
def get_recaptcha_v3_token(page, sitekey, action='submit'):
    """
    Get reCAPTCHA v3 token — just execute, no challenge.
    Stealth browser gets high score automatically.
    """
    # Load reCAPTCHA script
    page.evaluate(f'''() => {{
        return new Promise((resolve) => {{
            const script = document.createElement('script');
            script.src = 'https://www.google.com/recaptcha/api.js?render={sitekey}';
            script.onload = () => resolve();
            document.head.appendChild(script);
        }});
    }}''')
    time.sleep(2)
    
    # Execute and get token
    token = page.evaluate(f'''() => {{
        return new Promise((resolve, reject) => {{
            grecaptcha.ready(function() {{
                grecaptcha.execute('{sitekey}', {{action: '{action}'}})
                    .then(resolve)
                    .catch(reject);
            }});
        }});
    }}''')
    
    return token  # Always returns token, score is server-side
```

**Key insight:** v3 ALWAYS returns a token. The score is evaluated server-side. With stealth browser, score is typically 0.7+. No need for solver service.

---

## Method 3: Audio reCAPTCHA v2 (Whisper)

reCAPTCHA v2 offers audio challenge as accessibility alternative. Transcribe with Whisper (free, local).

```python
import requests, tempfile, subprocess, os

def solve_recaptcha_v2_audio(page):
    """
    Solve reCAPTCHA v2 via audio challenge + Whisper transcription.
    Requires: pip install openai-whisper (or use whisper CLI)
    """
    # Click "I'm not a robot" checkbox
    frame = page.frame_locator('iframe[src*="recaptcha"]').first
    frame.locator('.recaptcha-checkbox-border').click()
    time.sleep(3)
    
    # Switch to audio challenge
    challenge_frame = page.frame_locator('iframe[src*="recaptcha/api2/bframe"]').first
    challenge_frame.locator('#recaptcha-audio-button').click()
    time.sleep(2)
    
    # Get audio URL
    audio_src = challenge_frame.locator('#audio-source').get_attribute('src')
    if not audio_src:
        return None, "no_audio_source"
    
    # Download audio
    audio_data = requests.get(audio_src).content
    tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
    tmp.write(audio_data)
    tmp.close()
    
    # Transcribe with Whisper
    try:
        result = subprocess.run(
            ['whisper', tmp.name, '--model', 'base', '--language', 'en', '--output_format', 'txt'],
            capture_output=True, text=True, timeout=30
        )
        # Read transcription
        txt_file = tmp.name.replace('.mp3', '.txt')
        if os.path.exists(txt_file):
            with open(txt_file) as f:
                text = f.read().strip()
        else:
            text = result.stdout.strip()
    finally:
        os.unlink(tmp.name)
    
    if not text:
        return None, "transcription_empty"
    
    # Type answer
    challenge_frame.locator('#audio-response').fill(text)
    challenge_frame.locator('#recaptcha-verify-button').click()
    time.sleep(3)
    
    # Extract token
    token = page.evaluate('''() => {
        const el = document.querySelector('[name="g-recaptcha-response"]');
        return el ? el.value : null;
    }''')
    
    return token, "ok" if token else "verify_failed"
```

### Setup Whisper
```bash
pip install openai-whisper
# Or faster: pip install faster-whisper

# Test
whisper test.mp3 --model base --language en
```

---

## Method 4: Image/Text OCR (Tesseract)

For simple text/number CAPTCHAs (not grid selection).

```python
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import requests, io

def solve_image_captcha(image_url_or_path):
    """
    OCR simple text/number CAPTCHA image.
    Works for: distorted text, colored backgrounds, simple noise.
    Does NOT work for: image grids, object selection.
    """
    # Load image
    if image_url_or_path.startswith('http'):
        img_data = requests.get(image_url_or_path).content
        img = Image.open(io.BytesIO(img_data))
    else:
        img = Image.open(image_url_or_path)
    
    # Preprocessing pipeline
    img = img.convert('L')  # Grayscale
    img = img.filter(ImageFilter.MedianFilter(3))  # Remove noise
    img = ImageEnhance.Contrast(img).enhance(2.0)  # Boost contrast
    img = img.point(lambda x: 0 if x < 128 else 255)  # Binarize
    
    # OCR with different configs
    configs = [
        '--psm 7 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
        '--psm 8 --oem 3',
        '--psm 13 --oem 1',
    ]
    
    results = []
    for config in configs:
        text = pytesseract.image_to_string(img, config=config).strip()
        if text:
            results.append(text)
    
    # Return most common result or longest
    if results:
        from collections import Counter
        return Counter(results).most_common(1)[0][0]
    return None
```

### Setup Tesseract
```bash
sudo apt install -y tesseract-ocr
pip install pytesseract Pillow
```

---

## Method 5: Slide CAPTCHA (Template Matching)

For slider/puzzle CAPTCHAs (drag piece to fit).

```python
import cv2
import numpy as np

def solve_slide_captcha(background_img, puzzle_piece_img):
    """
    Find X offset where puzzle piece fits in background.
    Returns pixel offset for the slider drag.
    """
    # Load images
    bg = cv2.imread(background_img, 0)  # grayscale
    piece = cv2.imread(puzzle_piece_img, 0)
    
    # Edge detection
    bg_edges = cv2.Canny(bg, 100, 200)
    piece_edges = cv2.Canny(piece, 100, 200)
    
    # Template matching
    result = cv2.matchTemplate(bg_edges, piece_edges, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(result)
    
    return max_loc[0]  # X offset in pixels
```

---

## Method 5: Aliyun Slider CAPTCHA (Jigsaw Puzzle)

Z.ai (GLM 5.2) and other Chinese platforms use **Aliyun CAPTCHA** (Alibaba Cloud) — a jigsaw slider puzzle. NOT Cloudflare Turnstile.

### Identification
- CSS class: `aliyun-captcha`
- Elements: `#aliyunCaptcha-img` (background, 296×200 natural), `#aliyunCaptcha-puzzle` (piece, 52×200)
- Slider: `[class*="slider"]` or `#aliyunCaptcha-slider`
- Trigger: "Click to start verification" widget → modal with puzzle appears

### Solve with OpenCV (confirmed working)
```python
import cv2, numpy as np, base64

def solve_aliyun_slider(bg_b64, piece_b64):
    bg = cv2.imdecode(np.frombuffer(base64.b64decode(bg_b64), np.uint8), cv2.IMREAD_COLOR)
    piece = cv2.imdecode(np.frombuffer(base64.b64decode(piece_b64), np.uint8), cv2.IMREAD_COLOR)
    bg_gray = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    piece_gray = cv2.cvtColor(piece, cv2.COLOR_BGR2GRAY)
    
    # Grayscale template matching = best for Aliyun (conf 0.5-0.85)
    result = cv2.matchTemplate(bg_gray, piece_gray, cv2.TM_CCOEFF_NORMED)
    _, val, _, loc = cv2.minMaxLoc(result)
    return loc[0]  # X offset in natural pixels (296px wide)
```

**Method ranking (tested):** Grayscale > Color > HSV > Edge. Use `TM_CCOEFF_NORMED`.

### Slider drag
- Get slider bounding box, start at `box.x + 15` (button on left)
- Scale: `drag_px = x_offset * (display_width / 296)`
- Human-like: 15-25 steps with ease-out curve + Y jitter
- After drag: `wait_for_selector('#aliyunCaptcha-img', state='hidden', timeout=5000)`

### Extract images (Playwright JS)
```js
const bg = document.querySelector('#aliyunCaptcha-img');
const piece = document.querySelector('#aliyunCaptcha-puzzle');
return {
    bg: bg.src.replace('data:image/png;base64,', ''),
    piece: piece.src.replace('data:image/png;base64,', '')
};
```

### Pitfalls
- Images sometimes load from Aliyun CDN (`static-captcha-sgp.aliyuncs.com`) — the src is still base64 data URI in DOM
- Modal z-index blocks "Create Account" button until captcha closes — must wait for `#aliyunCaptcha-img` to become hidden before clicking submit
- Low confidence (<0.3) = wrong match, try again with fresh captcha
- Headless Chromium works — no stealth needed for Aliyun (unlike Cloudflare)
- **2captcha does NOT support Aliyun slider captcha.** Task types like `AleeGnTask` or `GeeTestTask` won't work. Aliyun slider must be self-solved via OpenCV or browser automation — no paid solver shortcut exists for this captcha type.
- Aliyun DOM selectors: `#aliyunCaptcha-img` (BG), `#aliyunCaptcha-puzzle` (piece), `#aliyunCaptcha-start-icon` (trigger icon), `[class*="aliyunCaptcha"]` (container). BG natural size is 296×200 (not 300).
- If confidence is 0.4-0.6 and captcha doesn't close after drag, the X offset may be slightly off — try refreshing the captcha (click the refresh icon inside the modal) and re-solving rather than adjusting offset manually.

## Dependencies

```bash
# Core (choose what you need)
pip install playwright Pillow

# For audio solve
pip install openai-whisper

# For image OCR
sudo apt install -y tesseract-ocr
pip install pytesseract

# For slide captcha
pip install opencv-python-headless numpy

# For stealth browser (VPS headless)
sudo apt install -y xvfb
```

## Critical Pitfalls

### ⚠️ #1: Turnstile Token is IP-BOUND (CONFIRMED June 2025, re-confirmed June 2026)
**Paid solvers (sctg.xyz, 2captcha, capsolver) DO NOT WORK for IP-binding sites.**
- Solver solves from their IP → token invalid when used from your IP
- Error from b.ai: `"Invalid token: Token verification failed or expired"` = IP mismatch
- Solver successfully returns token (status=1, 800+ chars) but server rejects it
- This is NOT a solvability issue — it's architectural. Don't waste credits retrying.
- Cost wasted: ~$0.003/attempt × N attempts = money burned for nothing

Cloudflare Turnstile tokens are **bound to the IP that solved them**. Server-side verification checks:
1. Token validity (not expired, ~5 min TTL)
2. Token-IP match: IP that generated token MUST match IP sending the API request

**Third-party solver (sctg.xyz, 2captcha) tokens WILL be rejected** — solver solves from THEIR IP → token tied to solver IP → your request from YOUR IP = "Invalid token". NOT bypassable.

**Only working approaches for IP-protected Turnstile:**
1. Real browser on residential IP (user's PC) — auto-solves + claim from same IP
2. Residential proxy routing ALL traffic through same residential exit IP
3. Multi-account pattern: login parallel (headless OK) → browsers stay open → user claims manually from residential

### ⚠️ #1b: Turnstile WILL NOT render from datacenter/VPS IPs (CONFIRMED)
Cloudflare Turnstile uses **IP reputation**. From datacenter IPs (AWS, GCP, Hetzner, OVH, DigitalOcean, etc.), the widget loads (`typeof turnstile !== 'undefined'` is true) but **silently refuses to spawn an iframe or generate a token**. No error, no callback, just nothing.

**Symptoms:**
- `turnstile.render()` returns a widget ID (looks successful)
- No iframe ever spawns (`document.querySelectorAll('iframe').length === 0`)
- `turnstile.getResponse()` returns null forever
- Button stays `disabled` — no error, no timeout signal
- xvfb + non-headless + stealth browser does NOT fix it

**Diagnosis:** If after 15s of `turnstile.render()` there are 0 iframes and null token, you're hitting datacenter detection. Don't keep retrying.

**Solutions:**
1. **Run script on user's local PC** — residential IP = Turnstile auto-solves in <3s
2. **Residential proxy** — route browser traffic through residential IP
3. **Paid solver service** (2Captcha/CapSolver) — they use residential worker farms
4. **Mobile tethering** — share phone's mobile data to VPS via VPN/tunnel

See `references/turnstile-vps-failure-pattern.md` for full debugging transcript.

### #2: Turnstile managed mode (button gating pattern)
Some sites (e.g. b.ai) use Turnstile in managed mode inside a modal. The submit button stays `disabled` until Turnstile callback fires. Don't force-enable — server validates the token. Poll `button.disabled` every 2s to detect solve.

### #3: Third-party solvers may fail specific sitekeys
sctg.xyz/2Captcha can return `ERROR_CAPTCHA_UNSOLVABLE` for certain Turnstile managed-mode sitekeys even with valid balance. This is a solver limitation, not a config issue. Browser self-solve from residential IP is the reliable fallback.

### #4: Turnstile needs non-headless or xvfb
`headless=True` won't spawn iframe for many sitekeys. Use `xvfb-run -s "-screen 0 1280x720x24"` on VPS. But this is necessary, NOT sufficient — residential IP is still the hard requirement.

### #6: 2-Phase Architecture for Mass Ops with Turnstile
When mass-processing accounts that gate actions behind Turnstile:
1. **Phase 1 (Login):** headless, parallel, works from ANY IP → save session cookies to `cookies/<email>.json`
2. **Phase 2 (Claim/Action):** non-headless on RESIDENTIAL IP → load cookies (skip login), Turnstile auto-solves in 2-10s
This separates the slow auth step from the Turnstile-gated step. Login can be 15+ workers headless; claim needs non-headless but skips the login wait.

### #7: Turnstile silent-fail detection
After `turnstile.render()`, poll `document.querySelectorAll('iframe').length`. If 0 iframes after 10s = datacenter IP block. No error callback fires. Widget ID returns success but nothing renders. The ONLY fix is residential IP.

### #8: Turnstile in modals (React apps)
Some apps (b.ai, etc.) render Turnstile inside a modal. The Claim/Submit button is `disabled` until Turnstile token arrives. Detection: check `btn.disabled` in a poll loop. When `false` → Turnstile solved → click button. Use Playwright `.evaluate()` to check, not `.click()` (React buttons need JS click after disabled state change).

### #5: Turnstile fails with parallel browser instances
When running 10-15+ browsers from same residential IP, Turnstile may silently fail to render (no iframe). Causes: Cloudflare rate limits per IP, site-isolation blocking iframe. Fixes:
- Reduce parallel count to 5-8
- Add Chrome args: `--disable-features=IsolateOrigins,site-per-process --disable-site-isolation-trials --disable-web-security`
- Override Playwright default UA with real Chrome UA string
- User can try: refresh page (F5), close modal → reopen, restart router for new IP
- Use `channel="chrome"` (real Chrome) instead of default Chromium — better Turnstile render rate
- Add `context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")` 
- Keep parallel browsers to 5-8 max per IP — 15+ triggers Cloudflare rate limiting on Turnstile render
- Solver services (sctg.xyz, 2captcha) confirmed CANNOT bypass IP binding even when token solves successfully — server rejects with "Token verification failed or expired"

### #6: General pitfalls
- **reCAPTCHA v2 audio rate limit** — Google blocks audio after ~3-5 attempts from same IP. Rotate proxy or wait.
- **Whisper model size** — `base` is fast but less accurate. Use `small` for better accuracy.

## Method 6: waguriagentic/captcha-solver HTTP Sidecar

Local HTTP sidecar built on CloakBrowser — solves 11 captcha types natively. Zero per-solve cost for browser-based paths.

### Installation (already done)

```bash
# Service: captcha-solver (systemd)
# Endpoint: http://localhost:8877
# Logs: journalctl -u captcha-solver -f
```

### Supported Types

`turnstile`, `recaptcha`, `hcaptcha`, `cloudflare`, `awswaf`, `botguard`, `datadome`, `perimeterx`, `akamai`, `aliyun`, `arkose`

### Usage

```python
import requests

solver = "http://localhost:8877"

# Check status
r = requests.get(f"{solver}/health")
print(r.json())
# → {"status":"ok","supported_types":["turnstile","recaptcha",...]}

# Solve Turnstile
r = requests.post(f"{solver}/solve", json={
    "type": "turnstile",
    "sitekey": "0x4AAAAAAAx1wCHumK2rWgRU",
    "url": "https://target.com",
    "timeout_s": 30,
})
token = r.json().get("token")

# Solve reCAPTCHA v2
r = requests.post(f"{solver}/solve", json={
    "type": "recaptcha",
    "sitekey": "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
    "url": "https://target.com",
    "version": "v2",
})

# Solve reCAPTCHA v3 (get score + token)
r = requests.post(f"{solver}/solve", json={
    "type": "recaptcha",
    "sitekey": "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
    "url": "https://target.com",
    "version": "v3",
    "action": "submit",
})

# Solve Cloudflare clearance
r = requests.post(f"{solver}/solve", json={
    "type": "cloudflare",
    "url": "https://target.com",
    "timeout_s": 45,
})

# Solve on real page (navigate + interact)
r = requests.post(f"{solver}/solve", json={
    "type": "turnstile",
    "sitekey": "0x4AAAAAAA...",
    "url": "https://target.com",
    "real_page": True,
    "pre_actions": [
        {"action": "click", "selector": "#login-btn"},
        {"action": "type", "selector": "#email", "value": "user@email.com"},
    ],
})
```

### Response format

```json
{
  "token": "0.xxxxxxxx...",
  "method": "route_intercept",
  "elapsed_s": 3.2
}
```

On failure: HTTP 408 (timeout) or 400 (unsupported type).

### Architecture

```
┌─────────────┐    POST /solve     ┌──────────────────┐
│ Hermes/Your │ ──────────────────→ │ captcha-solver    │
│ Automation  │ ←────────────────── │ (CloakBrowser)    │
│ Script      │    token/error      │ Port 8877         │
└─────────────┘                    └──────────────────┘
                                         │
                                    ┌────▼────┐
                                    │ Chromium │
                                    │ Stealth  │
                                    └─────────┘
```

*Note: Turnstile/Cloudflare from VPS/datacenter IP still has rendering limitations (see Pitfall #1b). Use residential proxy if needed.*

---

## Paid Solver Fallback

When self-solve isn't possible (VPS/datacenter IP blocks Turnstile rendering), use a paid solver.

### Option A: sctg.xyz (legacy API format)

```python
import requests, time

def solve_turnstile_sctg(solver_key, sitekey, pageurl, solver_url="https://api.sctg.xyz"):
    """Submit + poll. Returns (token, status). ~5-15s solve time."""
    r = requests.post(f"{solver_url}/in.php", data={
        "key": solver_key, "method": "turnstile",
        "sitekey": sitekey, "pageurl": pageurl, "json": "1"
    }, timeout=30)
    data = r.json()
    if data.get("status") != 1:
        return None, data.get("request")
    
    task_id = data["request"]
    for _ in range(24):  # max 120s
        time.sleep(5)
        r = requests.get(f"{solver_url}/res.php", params={
            "key": solver_key, "action": "get", "id": task_id, "json": "1"
        }, timeout=30)
        data = r.json()
        if data.get("status") == 1:
            return data["request"], "ok"
        if "CAPCHA_NOT_READY" not in str(data.get("request", "")):
            return None, data.get("request")
    return None, "timeout"
```

### Option B: 2captcha.com (modern /createTask format)

```python
import requests, time

def solve_turnstile_2captcha(solver_key, sitekey, pageurl, solver_url="https://api.2captcha.com"):
    """2captcha.com API — POST /createTask → poll /getTaskResult. ~5-15s solve time."""
    # Create task
    payload = {
        "clientKey": solver_key,
        "task": {
            "type": "TurnstileTaskProxyless",
            "websiteURL": pageurl,
            "websiteKey": sitekey,
            "action": "signup",
            "cdata": "signup",
        },
    }
    r = requests.post(f"{solver_url}/createTask", json=payload, timeout=30)
    data = r.json()
    if data.get("errorId") != 0:
        return None, data.get("errorDescription", str(data))
    
    task_id = data["taskId"]
    
    # Poll (max 45 polls × 5s = ~225s timeout)
    for _ in range(45):
        time.sleep(5)
        r = requests.get(f"{solver_url}/getTaskResult",
                         params={"clientKey": solver_key, "taskId": task_id},
                         timeout=30)
        result = r.json()
        if result.get("status") == "ready":
            token = result["solution"].get("token")
            return (token, "ok") if token else (None, "no_token")
        error = result.get("errorDescription", "")
        if error and "CAPCHA_NOT_READY" not in error:
            return None, error
    return None, "timeout"

# Check balance: GET /res.php?key={KEY}&action=getbalance&json=1
```

### Key Differences Between Formats

| | sctg.xyz | 2captcha.com |
|---|---|---|
| Create | POST `/in.php` (form data) | POST `/createTask` (JSON) |
| Poll | GET `/res.php` (params) | GET `/getTaskResult` (params) |
| Auth | `key` field in request | `clientKey` field in JSON body |
| Timeout | 24 polls × 5s = 120s | 45 polls × 5s = 225s |

### Confirmed Working Sitekeys
- b.ai: `0x4AAAAAADKhTSXIozuHjOoF` — ✅ works on sctg.xyz, ~$0.003/solve

### Cost Estimation
- Turnstile: ~$0.003/solve
- 100 accounts = ~$0.30
- sctg.xyz balance: GET `{solver_url}/res.php?key={KEY}&action=getbalance`
- 2captcha balance: GET `{solver_url}/res.php?key={KEY}&action=getbalance&json=1`

### Parallel Solver Limits
- Max 3 concurrent solver requests recommended (avoid overload/rate limit)
- Concurrency control: `Semaphore(1)` default — captcha solve serialized. Increase via env `CAPTCHA_CONCURRENCY` if solver allows.

### Multi-Key Rotation
When running large campaigns, rotate through multiple 2captcha keys to distribute load and avoid single-key rate limits:
```python
keys = ["key1", "key2", "key3"]  # from ~/.hermes/credentials/2captcha_keys.txt
current_key = keys[account_index % len(keys)]
```
- Use ThreadPoolExecutor(max_workers=3) for claim phase when solver is involved
- **Tesseract fails on complex CAPTCHAs** — Only works for simple distorted text.
- **Turnstile token expiry** — Token valid ~2 minutes. Solve immediately before API call.
- **Google detects Whisper patterns** — After several correct audio solves, Google may switch to harder audio.
- **CloakBrowser humanize=True helps** — Random mouse movements make Turnstile more likely to auto-pass.
