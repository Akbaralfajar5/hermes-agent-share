# Camoufox vs Playwright Chromium — Tradeoffs & Conversion Guide

## When to Use Each

| Factor | Camoufox (Firefox) | Playwright Chromium |
|--------|-------------------|---------------------|
| Anti-detection | Built-in (humanize, fingerprint spoofing) | Manual stealth patches needed |
| Window position | xdotool/workaround needed | Native `--window-position` flag |
| Audio mute | `media.volume_scale=0` (Firefox pref) | `--mute-audio` flag |
| Mobile emulation | viewport only | `is_mobile`, `has_touch`, `device_scale_factor` |
| WebRTC IP leak | Firefox prefs | `--force-webrtc-ip-handling-policy` |
| Stealth JS | Not needed (built-in) | Must inject via `add_init_script()` |
| Proxy support | Built-in per-browser | Built-in per-browser or per-context |
| RAM per instance | ~200-300MB | ~300-500MB |
| Headless | Supported | Supported (better) |
| Community/docs | Smaller, Camoufox-specific | Massive, Playwright ecosystem |

**Rule of thumb:**
- **Camoufox** → Quick anti-detect setup, no stealth JS needed, Firefox-native fingerprint
- **Playwright Chromium** → More control, better ecosystem, native window positioning, mobile emulation

## Conversion: Camoufox → Chromium

### 1. Launch

**Camoufox:**
```python
from camoufox.async_api import AsyncCamoufox

cf_opts = {
    'headless': False,
    'humanize': True,
    'window': (420, 900),
    'firefox_user_prefs': {
        'media.peerconnection.enabled': False,
        'media.volume_scale': 0,
    },
}
if use_proxy:
    cf_opts['proxy'] = {'server': '...', 'username': '...', 'password': '...'}
    cf_opts['geoip'] = True

async with AsyncCamoufox(**cf_opts) as browser:
    page = await browser.new_page()
    await page.set_viewport_size({'width': 414, 'height': 896})
```

**Chromium:**
```python
from playwright.async_api import async_playwright

CHROMIUM_ARGS = [
    '--mute-audio',
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--no-first-run',
    '--force-webrtc-ip-handling-policy=disable_non_proxied_udp',
]

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
delete navigator.__proto__.webdriver;
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['id-ID','id','en-US','en']});
if (!window.chrome) window.chrome = {};
if (!window.chrome.runtime) window.chrome.runtime = {};
"""

async with async_playwright() as p:
    browser = await p.chromium.launch(
        headless=False,
        args=CHROMIUM_ARGS + [f'--window-position={x},{y}', f'--window-size={w},{h}'],
        proxy={'server': '...', 'username': '...', 'password': '...'} if use_proxy else None,
        ignore_default_args=['--enable-automation'],
    )
    context = await browser.new_context(
        viewport={'width': 414, 'height': 500},
        user_agent='Mozilla/5.0 (Linux; Android 13; SM-G991B) ...',
        locale='id-ID',
        timezone_id='Asia/Jakarta',
        is_mobile=True,
        has_touch=True,
        device_scale_factor=3,
        color_scheme='dark',
    )
    await context.add_init_script(STEALTH_JS)
    page = await context.new_page()
```

### 2. Firefox Prefs → Chromium Args

| Firefox Pref | Chromium Equivalent |
|---|---|
| `media.volume_scale=0` | `--mute-audio` |
| `media.peerconnection.enabled=False` | `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` |
| `media.peerconnection.ice.no_host=True` | `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` |
| `media.peerconnection.ice.proxy_only=True` | `--force-webrtc-ip-handling-policy=disable_non_proxied_udp` |
| `media.autoplay.default=5` | `--autoplay-policy=user-gesture-required` |

### 3. Window Positioning

**Camoufox:** No native support → use `xdotool` post-launch
```python
import subprocess
subprocess.run(['xdotool', 'search', '--name', 'W-1'], ...)
subprocess.run(['xdotool', 'windowmove', wid, str(x), str(y)], ...)
```

**Chromium:** Native `--window-position=x,y` flag
```python
args=[f'--window-position={x},{y}', f'--window-size={w},{h}']
```

### 4. Grid Layout (2x2 example)

```python
SCREEN_W, SCREEN_H = 1920, 1080
GRID_COLS, GRID_ROWS = 2, 2
GAP = 8
WINDOW = (420, 520)

def get_window_position(worker_id):
    idx = (worker_id - 1) % (GRID_COLS * GRID_ROWS)
    col = idx % GRID_COLS
    row = idx // GRID_COLS
    grid_w = GRID_COLS * WINDOW[0] + (GRID_COLS - 1) * GAP
    grid_h = GRID_ROWS * WINDOW[1] + (GRID_ROWS - 1) * GAP
    offset_x = (SCREEN_W - grid_w) // 2
    offset_y = max(0, (SCREEN_H - grid_h) // 2)
    x = offset_x + col * (WINDOW[0] + GAP)
    y = offset_y + row * (WINDOW[1] + GAP)
    return (x, y)
```

### 5. Stealth JS (Chromium only)

Must inject via `context.add_init_script()` to run before any page JS:

```javascript
// Hide webdriver
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
delete navigator.__proto__.webdriver;

// Fake plugins
Object.defineProperty(navigator, 'plugins', {get: () => {
    const p = [
        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
        {name: 'Native Client', filename: 'internal-nacl-plugin'},
    ];
    p.length = 3;
    return p;
}});

// Languages
Object.defineProperty(navigator, 'languages', {get: () => ['id-ID','id','en-US','en']});

// Chrome runtime
if (!window.chrome) window.chrome = {};
if (!window.chrome.runtime) window.chrome.runtime = {};

// Permissions patch
const origQuery = window.navigator.permissions.query.bind(window.navigator.permissions);
window.navigator.permissions.query = (params) => {
    if (params.name === 'notifications')
        return Promise.resolve({state: Notification.permission});
    return origQuery(params);
};

// Platform spoofing (mobile)
Object.defineProperty(navigator, 'platform', {get: () => 'Linux armv81'});
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 4});
```

## Pitfalls

1. **Camoufox `screen_position` param** — not reliably supported; use xdotool as fallback
2. **Chromium viewport vs window** — viewport (CSS) and window (physical) are independent; page renders at viewport size, window shows scrollbar if smaller
3. **Audio mute** — `--mute-audio` is a launch flag, not a runtime toggle; cannot unmute without restart
4. **Stealth JS timing** — `add_init_script` runs before page JS; `page.evaluate` runs after; for anti-detection, use `add_init_script`
5. **Proxy toggle** — neither Camoufox nor Chromium supports runtime proxy change; must restart browser
6. **Mobile emulation** — `is_mobile=True` affects viewport scaling and touch events; don't set on desktop-target sites
7. **`--window-position`** — ignored in headless mode; only works with `headless=False`
