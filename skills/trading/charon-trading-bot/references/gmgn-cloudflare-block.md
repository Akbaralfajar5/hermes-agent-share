# GMGN API Cloudflare Block (May 2026)

## Status
GMGN API (`openapi.gmgn.ai`) is now protected by **Cloudflare Turnstile managed challenge**. Direct API access fails.

## Bypass Methods Tested (All Failed)

### 1. Puppeteer + Stealth Plugin
```javascript
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
puppeteer.use(StealthPlugin());
```
Result: 403 with "Just a moment..." page

### 2. Rotating Residential Proxy (DataImpulse)
```
--proxy-server=gw.dataimpulse.com:823
page.authenticate({ username, password })
```
Result: Same 403, Cloudflare detects headless browser regardless of IP

### 3. 2Captcha Turnstile Solver
```javascript
// Direct API call
const submitUrl = 'https://2captcha.com/in.php?method=turnstile&sitekey=...&pageurl=...';
```
Result: `ERROR_BAD_PARAMETERS` — managed challenge has no visible sitekey widget

### 4. Combined Approaches
All combinations of above methods fail. Cloudflare managed challenge uses advanced bot detection beyond IP/fingerprint.

## Working Workaround

Use **Charon Signal Server** (`api.thecharon.xyz`) which:
- Aggregates signals from multiple sources
- Has their own GMGN bypass
- Provides: axiom_trending, jupiter_trending, pump_graduated, fee_claim

```javascript
// In serverClient.js
const SIGNAL_SERVER_URL = 'https://api.thecharon.xyz/api';
const res = await axios.get(`${SIGNAL_SERVER_URL}/signals`, {
  headers: { 'x-api-key': SIGNAL_SERVER_KEY }
});
```

## GMGN Enrichment Still Works (Intermittently)

Individual token info via `enrichment/gmgn.js` still works with caching:
- Uses rate limiting and backoff
- Caches results for 5 minutes
- Falls back gracefully on 403

## Future Options

1. **Capsolver** — Specialized Cloudflare managed challenge solver
2. **Official GMGN API tier** — May have bypass for paid accounts
3. **Scrape GMGN website** — Website may be more lenient than API

## Bridge Code (For Future Use)

Files created but not working due to CF block:
- `src/bridge/gmgnBridge.js` — Puppeteer bridge with 2Captcha
- `src/bridge/runBridge.js` — PM2 entry point
- `src/signals/gmgnSource.js` — GMGN signal polling

These can be adapted if Capsolver integration is added.
