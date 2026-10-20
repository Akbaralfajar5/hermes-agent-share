# Proxy Debugging for Browser Automation

## Symptom: Proxy works with curl but browsers timeout/hang

**User report:** "lemot ya muter terus, padahal proxy saya aman kok kalo dipake" (slow and spinning, but my proxy is safe when I use it)

**Root cause:** Proxy handles simple HTTP requests (curl) fine, but struggles with browser automation's parallel connections, WebSocket upgrades, and long-lived sessions.

## Diagnostic Workflow

### 1. Test proxy with curl first
```bash
# Test 1: Verify proxy works and returns correct country
curl -x http://USER:PASS@proxy.com:port https://ipinfo.io/json --connect-timeout 10
# Expected: {"country": "ID", ...} (or target country)

# Test 2: Verify target site is accessible
curl -x http://USER:PASS@proxy.com:port -I https://target-site.com --connect-timeout 10
# Expected: HTTP 200, not geo-block page

# Test 3: Measure latency
time curl -x http://USER:PASS@proxy.com:port https://target-site.com -o /dev/null
# Expected: <5 seconds for good proxy, >10 seconds = slow
```

### 2. If curl succeeds but browser times out

**Asymmetric behavior patterns:**
- ✅ curl: 2-5 seconds, HTTP 200
- ❌ browser: 30+ seconds timeout, or infinite "muter terus" (spinning)

**Root causes:**
1. **Proxy rate limiting** - Allows single requests but throttles parallel connections
2. **WebSocket blocking** - Proxy doesn't support WebSocket upgrades (needed for some sites)
3. **Datacenter IP detection** - Site allows curl but blocks browser fingerprints from datacenter IPs
4. **VPS → Proxy latency** - High latency from VPS to proxy (but low from client machine to proxy)

**Solutions (in order of preference):**

#### Option 1: Run bot from client machine (Windows/Mac)
```bash
# User's Windows machine, not VPS
python example-target_open_10.py
```
**Why this works:** Residential/client networks often have lower latency to proxy than datacenter VPS. Proxy providers optimize routing for consumer traffic, not server-to-server.

**When to recommend:** If curl succeeds on VPS but browser times out 3+ times, recommend user run bot locally instead of continuing to debug VPS networking.

#### Option 2: Test without proxy (if site allows)
```python
USE_PROXY = False  # Line 19 in bot script
```
**Why this works:** Eliminates proxy as variable. If site loads fast without proxy, proxy is the bottleneck.

**When to use:** If site doesn't geo-block user's location, test without proxy first to isolate issue.

#### Option 3: Reduce parallel workers
```python
MAX_WORKERS = 3  # Instead of 10
BATCH_SIZE = 2   # Instead of 3-5
```
**Why this works:** Fewer parallel connections = less proxy load.

**When to use:** If user insists on using VPS + proxy, reduce workers to 2-3 and test.

#### Option 4: Use VPS in target country (no proxy)
```bash
# Deploy bot to VPS in Indonesia (for example-target.com example)
# No proxy needed if VPS is in allowed region
```
**Why this works:** Eliminates proxy latency entirely.

**When to use:** If user has budget for VPS in target region, this is most reliable.

### 3. Optimize browser wait strategy

**Problem:** `wait_until='networkidle'` waits for ALL network requests to finish, including ads/analytics that may never complete through slow proxy.

**Solution:** Use faster wait strategies with fallback:
```python
try:
    await page.goto(url, wait_until='load', timeout=30000)
except Exception:
    await page.goto(url, wait_until='domcontentloaded', timeout=20000)
```

**Performance comparison:**
- `networkidle`: 60+ seconds (waits for ads/analytics)
- `load`: 5-10 seconds (waits for DOM + main resources)
- `domcontentloaded`: 2-5 seconds (waits for DOM only)

## Proxy Toggle Pattern

Add `USE_PROXY` flag to bot for easy testing:

```python
# Config
USE_PROXY = True  # Set False to test without proxy

# Launch browser
launch_options = {
    'headless': False,
    'args': [...]
}

if USE_PROXY:
    launch_options['proxy'] = {
        'server': f'http://{PROXY_HOST}:{PROXY_PORT}',
        'username': PROXY_USER,
        'password': PROXY_PASS
    }
    print("Using Indonesia proxy")
else:
    print("Using direct connection (no proxy)")

browser = await cloakbrowser.launch_async(**launch_options)
```

**User workflow:**
1. Test with `USE_PROXY = False` first (if site allows)
2. If fast → proxy is bottleneck
3. If still slow → site/Cloudflare is bottleneck
4. Enable proxy only if geo-blocking requires it

## When to Give Up on VPS + Proxy

**Signal:** Proxy works with curl, but browser times out 3+ times despite:
- Reducing workers to 2-3
- Using `wait_until='load'` instead of `networkidle`
- Increasing timeout to 60s

**Action:** Recommend user run bot from their Windows/Mac machine instead of VPS. Say:
> "Proxy bekerja dengan curl tapi browser timeout terus. Kemungkinan latency VPS → proxy terlalu tinggi. Coba jalankan bot dari laptop/PC kamu langsung, biasanya lebih cepat karena latency lebih rendah."

**Why this works:** Asymmetric latency (curl fast, browser slow) usually indicates datacenter IP detection or routing issues that won't resolve with config changes. Client machines have better proxy routing.

## Case Study: example-target.com

**Environment:** Ubuntu VPS in Singapore, DataImpulse Indonesia proxy

**Symptoms:**
- ✅ curl: 2 seconds, HTTP 200, IP shows Indonesia
- ❌ browser: "muter terus" (infinite spinning), never loads

**Root cause:** `wait_until='networkidle'` + slow proxy + heavy ad payload

**Solution:**
1. Changed `wait_until='networkidle'` → `wait_until='load'`
2. Added fallback to `domcontentloaded` if timeout
3. Reduced timeout from 60s → 30s → 20s cascade
4. Added `USE_PROXY` toggle for testing
5. Recommended user run bot from Windows machine (lower latency)

**Result:** Bot loads in 5-10 seconds instead of timing out.

**Full transcript:** See main skill for example-target.com reference.

## ERR_PROXY_AUTH_UNSUPPORTED in Playwright

**Symptom:** `net::ERR_PROXY_AUTH_UNSUPPORTED` when using `browser.new_context(proxy={...})` with DataImpulse or similar authenticated HTTP proxies.

**Root cause:** The `server` URL uses `https://` scheme instead of `http://`. DataImpulse and most HTTP proxies do NOT speak HTTPS to the proxy server — only the *tunneled* target connection uses TLS. When Playwright tries `https://proxy:port`, Chrome sees an unsupported auth scheme and refuses.

**Fix:**

```python
# ❌ WRONG — causes ERR_PROXY_AUTH_UNSUPPORTED
PROXY = {
    'server': 'https://gw.dataimpulse.com:823',
    'username': 'user',
    'password': 'pass',
}

# ✅ CORRECT — use http:// scheme
PROXY = {
    'server': 'http://gw.dataimpulse.com:823',
    'username': 'user',
    'password': 'pass',
}
```

**Why this works:** HTTP proxy scheme (`http://`) tells Chrome to use CONNECT for TLS targets and plain HTTP for non-TLS. The auth credentials are sent in the initial CONNECT handshake, which Playwright handles natively. `https://` scheme implies the proxy *itself* speaks TLS, which HTTP auth proxies don't.

**Verification:** After fixing the scheme, curl with `-x http://user:***@host:port` returns 200 quickly. The same proxy with `-x https://user:***@host:port` fails with auth errors.

**Applies to:** All Playwright `context`-level proxy configs (`browser.new_context`, `browser.new_page`). Not specific to DataImpulse — any HTTP proxy with username/password authentication.

**Does NOT apply to:** `--proxy-server` CLI flag (launch args) — that bypasses Playwright's auth layer entirely and requires a separate credential mechanism.
