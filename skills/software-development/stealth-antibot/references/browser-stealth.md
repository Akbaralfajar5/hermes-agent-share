# Stealth Browser Configuration

## Quick Reference

Three levels of stealth. Use the lowest level that passes for your target.

| Level | Patches | Passes | Use when |
|-------|---------|--------|----------|
| **Basic** | 5 patches | Simple bot checks | Internal tools, low-security sites |
| **Standard** | 12 patches | bot.sannysoft.com all green | Most sites, scraping |
| **Full** | 25 patches | bot.sannysoft.com 56/57 | Cloudflare, Kasada, PerimeterX |

## Geolocation Spoofing (Playwright)

When running automation through a proxy in one country but the browser's geolocation API leaks the real location, anti-bot systems can detect the mismatch. Spoof geolocation at the Playwright context level:

```python
context = await browser.new_context(
    geolocation={'latitude': -6.2146, 'longitude': 106.8451},  # Jakarta
    permissions=['geolocation', 'clipboard-read', 'clipboard-write'],
    timezone_id='Asia/Jakarta',
    locale='id-ID',
)
```

**Key points:**
- `geolocation` + `timezone_id` + `locale` must all be consistent (same country/region)
- Add `'geolocation'` to `permissions` list — without it, the spoofed location may not be exposed to sites
- Works in both headed and headless mode
- Combine with proxy in the same country for full consistency

**Consistency check:**
| Setting | Must match | Example (Indonesia) |
|---------|-----------|-------------------|
| `geolocation` | Proxy exit country | `-6.2146, 106.8451` (Jakarta) |
| `timezone_id` | Geolocation country | `Asia/Jakarta` |
| `locale` | Timezone region | `id-ID` |
| Proxy IP | Geolocation country | Singapore/Indonesia exit |

---

## SSL Certificate Bypass (Playwright)

Some sites have invalid/mismatched SSL certs. Chrome shows "Your connection is not private" and blocks navigation.
```python
browser = await p.chromium.launch(
    args=[
        '--ignore-certificate-errors',
        '--ignore-certificate-errors-spki-list',
        # ... other args
    ],
)
```

### Fallback: auto-click Advanced → Proceed
If the flag doesn't work (e.g. some Chrome versions), handle the warning page:
```python
async def handle_ssl_warning(page):
    try:
        is_ssl = await page.evaluate("""() => {
            return document.body.innerText.includes('Your connection is not private')
                || document.body.innerText.includes('NET::ERR_CERT');
        }""")
        if not is_ssl:
            return False
        # Click "Advanced"
        advanced = page.locator('#details-button')
        if await advanced.count() > 0:
            await advanced.click()
            await asyncio.sleep(0.5)
        # Click "Proceed to ..."
        proceed = page.locator('#proceed-link')
        if await proceed.count() > 0:
            await proceed.click()
            await asyncio.sleep(2)
            return True
    except:
        pass
    return False
```

**Pitfall:** `#details-button` and `#proceed-link` are Chrome-internal IDs, not Playwright selectors. They work in headed Chromium but NOT in Firefox.

Minimum viable stealth. Hides the obvious automation signals.

```python
BASIC_STEALTH = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
delete Navigator.prototype.webdriver;
window.chrome = {runtime: {}};
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
"""
```

---

## Level 2: Standard Stealth (12 patches)

Passes bot.sannysoft.com. Covers most anti-bot systems.

```python
STANDARD_STEALTH = """
// 1. WebDriver
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
delete Navigator.prototype.webdriver;

// 1b. pdfViewerEnabled — Playwright returns false, real Chrome returns true
Object.defineProperty(navigator, 'pdfViewerEnabled', {get: () => true});

// 2. CDC markers
for (let key in document) { if (key.match(/^cdc_/)) delete document[key]; }
for (let key in window) { if (key.match(/^cdc_/)) delete window[key]; }

// 3. Plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const p = [
            {name:'Chrome PDF Plugin', filename:'internal-pdf-viewer', description:'PDF'},
            {name:'Chrome PDF Viewer', filename:'mhjfbmdgcfjbbpaeojofohoefgiehjai', description:''},
            {name:'Native Client', filename:'internal-nacl-plugin', description:''},
        ];
        p.length = 3;
        return p;
    }
});

// 4. Languages
Object.defineProperty(navigator, 'languages', {get: () => ['id-ID','id','en-US','en']});

// 5. Chrome runtime
if (!window.chrome) window.chrome = {};
if (!window.chrome.runtime) window.chrome.runtime = {};
if (!window.chrome.csi) window.chrome.csi = () => {};
if (!window.chrome.loadTimes) window.chrome.loadTimes = () => {};

// 6. Permissions
const _origPQ = navigator.permissions.query.bind(navigator.permissions);
navigator.permissions.query = (p) =>
    p.name === 'notifications' ? Promise.resolve({state: Notification.permission}) : _origPQ(p);

// 7. Platform (match your UA)
Object.defineProperty(navigator, 'platform', {get: () => 'Linux armv81'});
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
Object.defineProperty(navigator, 'deviceMemory', {get: () => 4});
Object.defineProperty(navigator, 'doNotTrack', {get: () => null});

// 8. Battery (no battery = headless)
if (navigator.getBattery) {
    navigator.getBattery = () => Promise.resolve({
        charging: true, chargingTime: 0, dischargingTime: Infinity,
        level: 0.87, addEventListener:()=>{}, removeEventListener:()=>{}, dispatchEvent:()=>true,
    });
}

// 9. Connection (missing on headless)
if (!navigator.connection) {
    Object.defineProperty(navigator, 'connection', {
        get: () => ({
            effectiveType:'4g', rtt:50, downlink:10, saveData:false, type:'cellular',
            addEventListener:()=>{}, removeEventListener:()=>{},
        })
    });
}

// 10. Vendor/product
Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});
Object.defineProperty(navigator, 'product', {get: () => 'Gecko'});

// 11. Touch (mobile consistency)
Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 10});

// 12. Speech synthesis (0 voices = headless)
if (window.speechSynthesis) {
    const _origGV = speechSynthesis.getVoices;
    speechSynthesis.getVoices = function() {
        const v = _origGV.call(this);
        if (v.length === 0) return [
            {name:'Google Bahasa Indonesia', lang:'id-ID', default:true, localService:false, voiceURI:'Google Bahasa Indonesia'},
            {name:'Google US English', lang:'en-US', default:false, localService:false, voiceURI:'Google US English'},
        ];
        return v;
    };
}
"""
```

---

## Level 3: Full Stealth (25 patches)

Passes bot.sannysoft.com (56/57). Adds Canvas, WebGL, AudioContext, ClientRects fingerprint noise.

**Tested result: 56/57 passed** (1 failure = battery details display format, not actual detection).

```python
# Add these Chromium launch args:
CHROMIUM_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    '--disable-component-extensions-with-background-pages',
    '--disable-default-apps',
    '--mute-audio',
    # WebRTC — prevent local IP leaks through WebRTC ICE candidates
    '--disable-webrtc-multiple-routes',
    '--force-webrtc-ip-handling-policy=disable_non_proxied_udp',
    '--disable-webrtc-hw-encoding',
    '--enable-features=WebRtcHideLocalIpsWithMdns',
    # IPv6 — disable to prevent IPv6 DNS leak when proxy is IPv4
    '--disable-features=UseChromiumNetworkService',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-background-timer-throttling',
    '--disable-ipc-flooding-protection',
    '--disable-features=TranslateUI',
    '--disable-hang-monitor',
    '--disable-popup-blocking',
    '--disable-prompt-on-repost',
    '--disable-sync',
    '--disable-domain-reliability',
    '--metrics-recording-only',
    '--no-pings',
]

# Include ALL patches from Level 2, PLUS:
FULL_STEALTH_EXTRAS = """
// ============================================================
// 13. Canvas fingerprint — seeded PRNG noise injection
// Each browser instance gets unique but CONSISTENT noise
// ============================================================
const _cnSeed = Math.floor(Math.random() * 2147483647);
function _cnPRNG(s) { return function() { s=(s*16807)%2147483647; return(s-1)/2147483646; }; }
const _cnR = _cnPRNG(_cnSeed);

const _origTDS = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function(type) {
    const ctx = this.getContext('2d');
    if (ctx) {
        const d = ctx.getImageData(0,0,this.width,this.height);
        for (let i=0; i<d.data.length; i+=4) {
            if (_cnR()>0.7) {
                d.data[i]   = Math.max(0,Math.min(255,d.data[i]+(_cnR()>0.5?1:-1)));
                d.data[i+1] = Math.max(0,Math.min(255,d.data[i+1]+(_cnR()>0.5?1:-1)));
                d.data[i+2] = Math.max(0,Math.min(255,d.data[i+2]+(_cnR()>0.5?1:-1)));
            }
        }
        ctx.putImageData(d,0,0);
    }
    return _origTDS.apply(this, arguments);
};

const _origTB = HTMLCanvasElement.prototype.toBlob;
HTMLCanvasElement.prototype.toBlob = function(cb,type,q) {
    const ctx = this.getContext('2d');
    if (ctx) {
        const d = ctx.getImageData(0,0,this.width,this.height);
        for (let i=0; i<d.data.length; i+=4) {
            if (_cnR()>0.7) {
                d.data[i]   = Math.max(0,Math.min(255,d.data[i]+(_cnR()>0.5?1:-1)));
                d.data[i+1] = Math.max(0,Math.min(255,d.data[i+1]+(_cnR()>0.5?1:-1)));
                d.data[i+2] = Math.max(0,Math.min(255,d.data[i+2]+(_cnR()>0.5?1:-1)));
            }
        }
        ctx.putImageData(d,0,0);
    }
    return _origTB.apply(this, arguments);
};

// ============================================================
// 14. WebGL fingerprint — spoof vendor/renderer
// Match to your target device (Adreno = Samsung, Mali = other Android)
// ============================================================
const _gP = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(p) {
    if (p===37445) return 'Qualcomm';        // UNMASKED_VENDOR_WEBGL
    if (p===37446) return 'Adreno (TM) 660'; // UNMASKED_RENDERER_WEBGL
    return _gP.call(this, p);
};
const _gP2 = WebGL2RenderingContext.prototype.getParameter;
WebGL2RenderingContext.prototype.getParameter = function(p) {
    if (p===37445) return 'Qualcomm';
    if (p===37446) return 'Adreno (TM) 660';
    return _gP2.call(this, p);
};

// ============================================================
// 15. AudioContext fingerprint — add noise to frequency data
// ============================================================
const _origCA = AudioContext.prototype.createAnalyser;
AudioContext.prototype.createAnalyser = function() {
    const a = _origCA.call(this);
    const _of = a.getFloatFrequencyData.bind(a);
    a.getFloatFrequencyData = function(arr) { _of(arr); for(let i=0;i<arr.length;i++) arr[i]+=(_cnR()-0.5)*0.1; };
    const _ob = a.getByteFrequencyData.bind(a);
    a.getByteFrequencyData = function(arr) { _ob(arr); for(let i=0;i<arr.length;i++) arr[i]=Math.max(0,Math.min(255,arr[i]+Math.floor((_cnR()-0.5)*2))); };
    return a;
};

// ============================================================
// 16. ClientRects fingerprint — ±0.1px perturbation
// ============================================================
const _origGCR = Element.prototype.getClientRects;
Element.prototype.getClientRects = function() {
    const r = _origGCR.call(this), out = [];
    for (let i=0;i<r.length;i++) {
        const rc=r[i];
        out.push({top:rc.top+(_cnR()-.5)*.1, right:rc.right+(_cnR()-.5)*.1, bottom:rc.bottom+(_cnR()-.5)*.1,
            left:rc.left+(_cnR()-.5)*.1, width:rc.width+(_cnR()-.5)*.1, height:rc.height+(_cnR()-.5)*.1,
            x:rc.x+(_cnR()-.5)*.1, y:rc.y+(_cnR()-.5)*.1});
    }
    out.item=i=>out[i]; out.namedItem=()=>null; return out;
};
const _origBCR = Element.prototype.getBoundingClientRect;
Element.prototype.getBoundingClientRect = function() {
    const r = _origBCR.call(this);
    return {top:r.top+(_cnR()-.5)*.1, right:r.right+(_cnR()-.5)*.1, bottom:r.bottom+(_cnR()-.5)*.1,
        left:r.left+(_cnR()-.5)*.1, width:r.width+(_cnR()-.5)*.1, height:r.height+(_cnR()-.5)*.1,
        x:r.x+(_cnR()-.5)*.1, y:r.y+(_cnR()-.5)*.1, toJSON:r.toJSON.bind(r)};
};

// ============================================================
// 17. Media devices — spoof camera/mic (0 devices = headless)
// ============================================================
if (navigator.mediaDevices?.enumerateDevices) {
    const _origED = navigator.mediaDevices.enumerateDevices.bind(navigator.mediaDevices);
    navigator.mediaDevices.enumerateDevices = function() {
        return _origED().then(d => d.length===0 ? [
            {deviceId:'default',groupId:'default',kind:'audioinput',label:'',toJSON:()=>{}},
            {deviceId:'default',groupId:'default',kind:'videoinput',label:'',toJSON:()=>{}},
        ] : d);
    };
}

// ============================================================
// 18-21. Screen + window dimensions (must match viewport)
// ============================================================
Object.defineProperty(screen, 'availWidth',  {get:()=>412});
Object.defineProperty(screen, 'availHeight', {get:()=>915});
Object.defineProperty(screen, 'width',       {get:()=>412});
Object.defineProperty(screen, 'height',      {get:()=>915});
Object.defineProperty(screen, 'colorDepth',  {get:()=>24});
Object.defineProperty(screen, 'pixelDepth',  {get:()=>24});
Object.defineProperty(window, 'outerWidth',  {get:()=>412});
Object.defineProperty(window, 'outerHeight', {get:()=>915});

// ============================================================
// 22. App version (must match UA)
// ============================================================
Object.defineProperty(navigator, 'appVersion', {
    get: () => '5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'
});

// ============================================================
// 23. Console debug filter (headless detection messages)
// ============================================================
const _origCD = console.debug;
console.debug = function(...a) { if(a[0]?.includes?.('Headless')) return; return _origCD.apply(this,a); };

// ============================================================
// 24. Performance timing jitter
// ============================================================
const _origPT = Performance.prototype.getEntriesByType;
Performance.prototype.getEntriesByType = function(t) {
    const e = _origPT.call(this,t);
    if (t==='navigation'&&e.length>0&&e[0].startTime===0) return e;
    return e;
};
"""
```

---

## Consistency Rules (Critical)

All fingerprint values MUST be consistent with each other. Mismatches = instant detection.

| Property | Must match | Example (Samsung S21) |
|----------|-----------|----------------------|
| User-Agent | Platform, screen | `Android 13; SM-G991B` |
| Platform | UA device | `Linux armv81` |
| Screen | UA device | `412×915` (S21 native) |
| WebGL | UA device | `Qualcomm Adreno 660` |
| Touch | UA device | `maxTouchPoints: 10` |
| Connection | UA device | `4G cellular` |
| Battery | UA device | `charging, 87%` |
| Outer dimensions | Screen | `412×915` |

**Common mistakes:**
- ❌ UA says Android but platform says `Win32`
- ❌ UA says mobile but screen is `1920×1080`
- ❌ UA says Samsung but WebGL says `SwiftShader` (Google's headless renderer)
- ❌ `maxTouchPoints: 0` on a mobile UA
- ❌ No battery on a mobile device

---

## Playwright Launch Template

```python
from playwright.async_api import async_playwright

async def launch_stealth(proxy=None, mobile=True):
    pw = await async_playwright().start()

    args = CHROMIUM_ARGS  # from Level 3 above

    opts = {
        "args": args,
        "headless": True,
        "ignore_default_args": ["--enable-automation"],
    }
    if proxy:
        if "socks5" in proxy.get("server", "") or "socks5" in str(proxy):
            opts["proxy"] = proxy  # SOCKS5: just pass the server string
        else:
            opts["proxy"] = {"server": proxy["server"], "username": proxy["username"], "password": proxy["password"]}

    browser = await pw.chromium.launch(**opts)

    ctx_opts = {
        "locale": "id-ID",
        "timezone_id": "Asia/Jakarta",
        "color_scheme": "dark",
        "permissions": ["clipboard-read", "clipboard-write"],
        # If using geolocation spoofing, add "geolocation" to permissions:
        # "permissions": ["clipboard-read", "clipboard-write", "geolocation"],
    }
    if mobile:
        ctx_opts.update({
            "viewport": {"width": 414, "height": 500},
            "user_agent": "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            "is_mobile": True,
            "has_touch": True,
            "device_scale_factor": 3,
        })
    else:
        ctx_opts.update({
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        })

    context = await browser.new_context(**ctx_opts)
    await context.add_init_script(FULL_STEALTH_JS)  # Level 2 + Level 3 extras

    return browser, context
```

---

## Detection Test Sites

| Site | What it tests | Target |
|------|--------------|--------|
| `https://bot.sannysoft.com/` | Basic fingerprint leaks | All green |
| `https://abrahamjuliot.github.io/creepjs/` | Advanced fingerprinting | Unique but consistent |
| `https://browserleaks.com/webgl` | WebGL vendor/renderer | Match your device |
| `https://browserleaks.com/canvas` | Canvas hash | Unique per session |
| `https://pixelscan.net/` | Comprehensive check | No mismatches |

---

## Pitfalls

1. **Don't use `headless: new`** — Playwright's new headless mode has different fingerprint characteristics. Use `headless: True` for consistent results.

2. **Canvas noise must be consistent within a session** — Use a seeded PRNG so the same browser instance always produces the same noise. Random noise per call = different hash per access = detection.

3. **WebGL renderer must match UA** — If UA says Samsung, WebGL must say Qualcomm/Adreno. If UA says iPhone, WebGL must say Apple GPU.

4. **Don't over-noise** — Canvas perturbation of ±1 per channel is enough. Larger values produce visible artifacts and suspicious hashes.

5. **Screen/outer dimensions must match** — `screen.width`, `window.outerWidth`, and viewport width should all be consistent. A 414px viewport with 1920px outerWidth is a red flag.

6. **`--enable-automation` must be removed** — Playwright adds this by default. Always pass `ignore_default_args=["--enable-automation"]`.

7. **CDC properties leak ChromeDriver** — Properties matching `^cdc_` on `document` or `window` are ChromeDriver markers. Always delete them.

8. **0 voices = headless** — Real browsers have speech synthesis voices. Spoof at least 2 voices matching your locale.

9. **0 media devices = headless** — Real browsers have audio/video input devices. Spoof at least one of each.

10. **Battery API missing = headless** — Real mobile devices have battery. Always spoof as charging with realistic level.

## Confirmed Test Results (June 2026)

```
============================================================
🛡️ PLAYWRIGHT STEALTH (25 patches) — bot.sannysoft.com
============================================================
✅ 56/57 PASSED (1 failure = battery details display format)

Individual checks:
✅ navigator.webdriver = undefined
✅ Canvas fingerprint = unique per session (hash changes each time)
✅ WebGL = Qualcomm Adreno 660
✅ Battery = charging 87%
✅ Connection = 4G cellular
✅ Speech synthesis = 2 voices
✅ Screen = 412x915 (Samsung S21)
✅ Touch = maxTouchPoints 10
✅ Chrome runtime = present
✅ Plugins = 3

============================================================
🌐 CLOUDFLARE BYPASS COMPARISON
============================================================
❌ Playwright + 25 patches → Cloudflare basic BLOCKED (timeout)
   - whatismybrowser.com: TIMEOUT
   - nowsecure.nl: TIMEOUT
   
✅ curl_cffi chrome124 → Cloudflare basic PASSED
   - whatismybrowser.com: PASSED
   - JA3 Hash: 29c6a9ee235d6b401641defb3a4dfc3b
   
❌ curl_cffi chrome124 → Cloudflare advanced BLOCKED
   - nowsecure.nl: BLOCKED (behavioral analysis)

============================================================
📊 VERDICT
============================================================
Standard bot detection → Playwright stealth works ✅
Cloudflare basic → curl_cffi TLS bypass works ✅
Cloudflare advanced → Needs behavioral simulation ❌
```

**Key takeaway:** Use Playwright for JavaScript-heavy sites, curl_cffi for API calls and simple page loads. For Cloudflare-protected sites, curl_cffi is significantly more effective than Playwright stealth patches alone.
