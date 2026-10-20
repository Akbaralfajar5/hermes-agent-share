# GMGN API Cloudflare Protection (May 2026)

## Issue
GMGN's OpenAPI (`openapi.gmgn.ai`) now uses Cloudflare managed challenge protection. Direct API calls from servers return 403 with Cloudflare challenge HTML instead of JSON data.

## Symptoms
```
[gmgn] new_pairs error: 403 Request failed with status code 403
[gmgn] trending error: 403 Request failed with status code 403
```

Response body contains:
```html
<title>Just a moment...</title>
<!-- Cloudflare challenge script -->
```

## Detection in Code
The `src/enrichment/gmgn.js` already detects this:
```javascript
if (/<title>\s*Just a moment/i.test(raw) || /challenge-platform|cf_chl/i.test(raw)) {
  return 'Cloudflare managed challenge';
}
```

## Workarounds

### Option 1: Use Charon Signal Server (Recommended)
Signal server (`api.thecharon.xyz`) already aggregates GMGN data along with other sources. No direct GMGN polling needed.

Sources from signal server:
- `axiom_trending`
- `jupiter_trending`
- `pump_graduated`
- `fee_claim`

### Option 2: GMGN Bridge with Puppeteer/Playwright
Set up a local bridge service that:
1. Uses headless browser to solve Cloudflare challenge
2. Maintains session cookies
3. Proxies API requests with valid session

Bridge endpoint pattern: `http://localhost:9876/gmgn/...`

### Option 3: Residential Proxy + Browser Headers
Some users report success with:
- Residential rotating proxy (DataImpulse, etc.)
- Full browser User-Agent
- Proper cookie handling

## Code Location
- Direct polling (disabled): `src/signals/gmgnSource.js`
- Enrichment with backoff: `src/enrichment/gmgn.js`
- App integration: `src/app.js` (GMGN polling commented out)

## Status
As of May 2026, direct GMGN API polling is disabled in Charon. Signal server provides equivalent data.
