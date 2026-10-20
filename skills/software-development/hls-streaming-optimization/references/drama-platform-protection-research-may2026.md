# Drama Platform Protection Research (May 2026)

Session: my-project multi-platform scraping attempt, May 19, 2026

## Executive Summary

Attempted to create scrapers for 9 short-drama platforms after ShortMax success. Result: Only ShortMax is scrapeable from Vercel. All others have protection that requires residential proxy, paid API, or complex reverse engineering.

## Platform-by-Platform Analysis

### ✅ ShortMax (shorttv.live) - WORKING
- **Method:** Cheerio HTML scraping + HLS proxy
- **Protection:** None for HTML, custom encryption for video segments
- **Video URLs:** In network requests (Playwright needed for capture)
- **See:** `references/shortmax-api-reverse-engineering-may2026.md`

- **Protection:** Akamai WAF
- **Error:** `<H1>Access Denied</H1>` with `Reference #18.xxxxx`
- **API:** `sapi.streaming-servicedb.com` with RSA-SHA256 signature
- **Bypass attempts:**
  - httpcloak TLS fingerprinting: Failed
  - DataImpulse residential proxy: Failed (Akamai detects signature, not just IP)
  - curl-impersonate: Not tested
- **Conclusion:** Akamai validates request signature, not just IP. Would need to reverse engineer Android app signing.

### ❌ NetShort (netshort.com)
- **Protection:** Encrypted API requests
- **Headers required:**
  ```
  encrypt-key: <RSA-encrypted session key>
  canary: v1
  content-language: en_US
  version: 1.0.0
  os: 4
  ```
- **Body:** Base64-encoded encrypted JSON
- **API:** `netshort.com/prod-web-api/web/web/v2/...`
- **Conclusion:** Full request/response encryption. Would need to reverse engineer JS bundle for encryption logic.

### ❌ ReelShort (reelshort.com)
- **Protection:** Client-side rendered (no SSR data)
- **API:** `public-dta.epubgame.com/dt/api/event/log` (analytics only)
- **Drama data:** Loaded via encrypted API after page render
- **Conclusion:** No public API discovered. Would need Playwright + API interception.

### ❌ GoodShort (goodshort.com)
- **Protection:** Client-side rendered
- **API:** `api.xintaicz.cn/sa.gif` (analytics only)
- **Drama data:** Not in initial HTML
- **Conclusion:** Same as ReelShort - client-side only.

### ❌ Melolo (melolo.com)
- **HTML scraping:** Works for drama list (45 links found)
- **Video URLs:** NOT in HTML or network requests
- **Playwright capture:** 0 m3u8 URLs captured
- **Conclusion:** Likely uses DRM or iframe embed from another platform. Video source not discoverable.

### ❌ PineDrama (pinedrama.com)
- **Protection:** Client-side rendered (Vue/Nuxt)
- **HTML scraping:** 0 drama links in initial HTML
- **Playwright:** 0 drama cards found after render
- **API:** Only analytics endpoints visible
- **Conclusion:** Heavy client-side rendering, no public API.

### ❌ FreeReels
- **Status:** Domain not responding (ConnectionError)
- **Conclusion:** Platform may be defunct or domain changed.

### ❌ my-project (my-project.com)
- **Status:** 200 but only 114 chars response
- **Conclusion:** Redirect or minimal landing page. Not a functional platform.

## API Aggregator Status

### Sansekai (api.sansekai.my.id)
- **Status:** Blacklisted ALL server IPs (Vercel, VPS, AWS, etc.)
- **Error:** `{"error":"Forbidden","message":"IP Anda telah diblacklist karena aktivitas mencurigakan..."}`
- **Covers:** 15+ platforms
- **Conclusion:** Unusable without residential proxy or purchasing source code.

### Anichin (api.anichin.bio)
- **Status:** Working from Vercel
- **Covers:** 15 platforms
- **Limitation:** Episodes 1-5 only (trial)
- **Conclusion:** Good for free tier, limited content.

### CUTAD (cutad.web.id)
- **Status:** Working (paid)
- **Pricing:** Rp 5,000 - 175,000
- **Covers:** 15 providers
- **Conclusion:** Best option for full access.

## Protection Patterns Observed

- Validates TLS fingerprint (JA3/JA4)
- Validates request signature
- Blocks datacenter IP ranges
- **Bypass difficulty:** Very High

### 2. Encrypted API (NetShort)
- RSA-encrypted session key in header
- AES-encrypted request/response body
- **Bypass difficulty:** High (need to reverse engineer JS)

### 3. Client-Side Rendering (ReelShort, GoodShort, PineDrama)
- No data in initial HTML
- API calls after JS execution
- Often with additional encryption
- **Bypass difficulty:** Medium-High (need Playwright + API interception)

### 4. DRM/Embed (Melolo)
- Video from third-party player
- No discoverable m3u8 URLs
- **Bypass difficulty:** Very High (may be impossible)

### 5. IP Blacklist (Sansekai)
- Blocks entire datacenter CIDR ranges
- Tracks request patterns
- **Bypass difficulty:** Medium (residential proxy works)

## Recommendations

### For Free Streaming Sites
1. **Use ShortMax** - Only platform with working scraper
2. **Use Anichin API** - Free, 15 platforms, episodes 1-5
3. **Accept limitations** - Not all platforms are scrapeable

### For Paid/Commercial Sites
1. **Buy CUTAD API** - Rp 5k-175k, full access
2. **Buy Sansekai source** - Self-host with residential proxy
3. **Partner with platforms** - Official API access

### For Technical Deep-Dive
1. **NetShort encryption** - Reverse engineer `encrypt-key` generation from JS bundle
3. **Melolo video source** - Trace iframe/embed chain to find actual video host

## Tools Used

| Tool | Purpose | Result |
|------|---------|--------|
| httpcloak | TLS fingerprint spoofing | Failed for Akamai |
| Playwright | Browser automation | Works for HTML, limited for encrypted APIs |
| Cheerio | HTML parsing | Works for SSR sites |
| requests | HTTP client | Blocked by most WAFs |
| DataImpulse proxy | Residential IP | Works for IP blocks, not signature validation |

## Key Learnings

1. **Akamai validates more than IP** - TLS fingerprint and request signature matter
2. **Encrypted APIs are common** - Most platforms encrypt request/response
3. **Client-side rendering hides data** - Need Playwright for JS-heavy sites
4. **DRM makes video inaccessible** - Some platforms use unbypassable protection
5. **Aggregator APIs are the practical solution** - Don't reinvent the wheel
6. **Free options have limits** - Full access requires payment or complex reverse engineering
