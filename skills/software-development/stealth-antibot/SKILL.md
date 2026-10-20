---
name: stealth-antibot
description: >
  Anti-bot detection toolkit for AI agents. Diagnoses why your agent is getting
  blocked and fixes it. Use when: agent hits 403/429 errors, encounters CAPTCHAs
  (hCaptcha, reCAPTCHA, Cloudflare Turnstile), gets detected as a bot, receives
  fake/empty data from websites, encounters Cloudflare challenges, needs to bypass
  IP blocks, or is running on a datacenter/cloud IP. Covers: residential proxy setup,
  CAPTCHA solver configuration, stealth browser fingerprinting. For web scraping,
  browser automation, form filling, and any task where bot detection is a problem.
  Compatible with Puppeteer, Playwright, Selenium, and headless Chrome.
---

# Stealth — Anti-Bot Detection for AI Agents

Three layers, applied in order. Most blocks are solved at Layer 1.

## Quick Diagnostic

Run this first to understand the problem:

```bash
curl -s https://ipinfo.io/json | python3 -c "
import sys,json;d=json.load(sys.stdin)
org=d.get('org','')
h=d.get('privacy',{}).get('hosting') if 'privacy' in d else None
dc=h or any(x in org.lower() for x in ['digital','amazon','google','microsoft','azure','linode','vultr','hetzner','ovh','cloud'])
print(f'IP: {d[\"ip\"]} | Org: {org} | Datacenter: {dc}')
if dc: print('⚠️  Datacenter IP detected → Layer 1 (proxy) required')
else: print('✅ Residential IP — skip to Layer 2 or 3 if still blocked')
"
```

### Block type reference

| Symptom | Cause | Layer |
|---------|-------|-------|
| 403 Forbidden | IP/bot block | 1 |
| 429 Too Many Requests | Rate limit (if persists after UA change → IP-level ban, see CrowdGen case below) | 1 |
| Cloudflare challenge | Bot detection | 1 + 3 |
| CAPTCHA appears | Verification gate | 2 |
| 200 but wrong content | Honeypot/fake data | 3 |
| Redirect loop | Cookie/session detection | 3 |
| Blocked after form submit | Behavioral analysis | 6 |
| Login/register blocked but page loads fine | Timing/mouse patterns | 6 |

## Layer 1: Residential Proxy

**The #1 fix.** Datacenter IPs are flagged instantly by Cloudflare, Akamai, PerimeterX, and most anti-bot systems. A residential proxy routes traffic through real ISP connections.

See `references/proxy-setup.md` for provider comparison and setup instructions.

**Quick test after setup:**
```bash
curl -x http://USER:PASS@HOST:PORT -s https://ipinfo.io/json | python3 -c "
import sys,json;d=json.load(sys.stdin)
print(f'Proxy IP: {d[\"ip\"]} | Org: {d.get(\"org\")}')
"
```
Org should show an ISP (Comcast, Verizon, AT&T), not a cloud provider.

## Layer 2: CAPTCHA Solving

**Never attempt CAPTCHAs yourself.** You will fail, burn tokens, and trigger escalated challenges. Always use a solver service.

**Critical routing rule:** 2Captcha dropped hCaptcha support entirely in late 2025. Use CapSolver for hCaptcha.

| CAPTCHA type | Provider |
|-------------|----------|
| hCaptcha | CapSolver only |
| reCAPTCHA v2/v3 | 2Captcha or CapSolver |
| Cloudflare Turnstile | Either |
| Image/text | 2Captcha |

See `references/captcha-setup.md` for provider setup, API integration code, and token injection.

## Layer 3: Stealth Browser

**When proxy alone isn't enough.** Sites fingerprint headless browsers via navigator properties, WebGL, Canvas, and automation flags.

See `references/browser-stealth.md` for **three levels** of stealth (Basic 5-patch, Standard 12-patch, Full 25-patch) with complete code, consistency rules, and pitfalls.

See `references/cloudflare-limitations-june2026.md` for **what stealth patches DON'T fix** — Cloudflare advanced challenges require residential proxy + behavioral simulation + TLS fingerprint matching.

## Layer 4: TLS Fingerprint Bypass (curl_cffi)

**When Playwright stealth patches aren't enough.** Cloudflare, Akamai, and PerimeterX fingerprint the TLS handshake (JA3/JA4 hash). Standard HTTP libraries and even Playwright have known TLS fingerprints that are flagged.

**Key insight (June 2026):** Playwright with 25 stealth patches: ❌ Cloudflare basic STILL BLOCKED. curl_cffi with Chrome 124 profile: ✅ Cloudflare basic PASSED.

See `references/tls-fingerprint-bypass.md` for curl_cffi setup, browser profiles, Netflix cookie injection, and when to use curl_cffi vs Playwright.

## Layer 5: API Reverse Engineering

**When browser automation is too slow or complex.** Many sites have hidden API endpoints that can be called directly, bypassing JavaScript challenges entirely.

See `references/api-reverse-engineering.md` for methodology, endpoint discovery, and case studies.

## Layer 6: Behavioral Simulation

**When fingerprint patches pass but you still get blocked during form submission or navigation.** Sites analyze HOW you act — mouse movement, timing, scroll patterns, typing speed. Fixed delays and instant `.fill()` calls are bot signals.

See `references/behavioral-simulation.md` for human_delay, human_click (bezier curve), human_scroll, and human_type implementations with Playwright.

**Quick check:** If `bot.sannysoft.com` shows all green but the site still blocks you after login/form submit → you need Layer 6.

**Quick test your config:**
```bash
python3 scripts/test_stealth.py              # Full test
python3 scripts/test_stealth.py --basic      # Basic only
```

## Geo-Blocked Services

Some services block access by country, not just by datacenter detection. Common with crypto/prediction market platforms.

**Polymarket** is the most common case — blocked in US, UK, France, Germany, Italy, Australia, and 25+ other countries.

See [`references/polymarket-geoblock.md`](references/polymarket-geoblock.md) for the full blocked country list, detection methods, recommended proxy countries, and provider-specific targeting syntax.

## IP-Level Cascade Bans (WordPress.com Sites)

Some sites (notably **CrowdGen/Appen**) exhibit cascading 429 bans at the infrastructure level — once the browser triggers a 429, the entire IP is banned for all user agents and paths. UA rotation, cookie clearing, and session tricks do NOT help.

See [`references/crowdgen-429-cascade.md`](references/crowdgen-429-cascade.md) for the full timeline, detection pattern, and prevention rule. **Key lesson: residential proxy must be active from the FIRST request — you cannot recover after triggering.**

## Confirmed Test Results (June 2026)

```
============================================================
🛡️ PLAYWRIGHT STEALTH (25 patches) — bot.sannysoft.com
============================================================
✅ 56/57 PASSED (1 failure = battery details display format)
✅ navigator.webdriver = undefined
✅ Canvas fingerprint = unique per session
✅ WebGL = Qualcomm Adreno 660
✅ Battery = charging 87%
✅ Connection = 4G cellular
✅ Speech synthesis = 2 voices
✅ Screen = 412x915 (Samsung S21)

============================================================
🧪 CLOUDFLARE BYPASS — curl_cffi vs Playwright
============================================================
❌ Playwright + 25 patches → Cloudflare basic BLOCKED (timeout)
✅ curl_cffi chrome124 → Cloudflare basic PASSED
❌ curl_cffi chrome124 → Cloudflare advanced BLOCKED (behavioral)

============================================================
📊 VERDICT
============================================================
✅ Standard bot detection → Playwright stealth works
✅ Cloudflare basic → curl_cffi TLS bypass works
❌ Cloudflare advanced → Needs behavioral simulation
✅ TLS fingerprint → curl_cffi matches real Chrome 124
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Blocked after proxy | Verify IP is residential via `ipinfo.io`. Cheap providers resell datacenter IPs. |
| CAPTCHA solver error | Wrong provider for captcha type? 2Captcha cannot solve hCaptcha. |
| Site serves fake data | Add stealth browser config (Layer 3). **Missing common patch:** `navigator.pdfViewerEnabled` — Playwright returns `false`, real Chrome returns `true`. Add `Object.defineProperty(navigator, 'pdfViewerEnabled', {get: () => true})`. |
| Slow responses | Try proxy server closer to target site's region. |
| Blocked after many requests | Enable IP rotation in proxy dashboard. |
| Browser closes immediately / `TargetClosedError` on every page | Proxy auth failure. Test browser WITHOUT proxy first, then test proxy separately with `curl -x`. See `references/proxy-debugging.md`. |
| `ERR_PROXY_AUTH_UNSUPPORTED` in Playwright | Default Playwright Chromium can't handle authenticated proxy (DataImpulse, residential providers). **Two fixes:** (A) **CloakBrowser (preferred):** Use `executable_path=CLOAK_PATH` + put `proxy={...}` at `browser.launch()` level — CloakBrowser handles 407 auth natively. Do NOT put proxy in `browser.new_context()` when using CloakBrowser. (B) **Without CloakBrowser:** Use a local relay proxy (Python script on localhost) that adds `Proxy-Authorization` header. See `references/local-proxy-relay.md`. **Common mistake:** putting proxy in `new_context()` instead of `launch()` — Playwright's context-level proxy auth works for some providers but NOT DataImpulse with CloakBrowser (causes auth to be sent twice / conflict). |
| Worker closes on first SSL/WAF error | Add retry loop with reload (up to 5 attempts) before giving up. See `references/playwright-resilience-patterns.md`. Users expect resilient workers that don't die on transient errors. |
| `NS_ERROR_PROXY_CONNECTION_REFUSED` in Playwright | Proxy server refusing connection. Test with `curl -x http://user:pass@host:port https://target.com`. 407 = credentials wrong/expired. Connection refused = server down. |
| `407 Proxy Authentication Required` | Proxy credentials invalid. Check: account expired, password rotated, username format changed. Test with curl first before debugging browser code. |
| 429 persists after UA change | IP-level ban. See `references/crowdgen-429-cascade.md` for WordPress.com cascade pattern. Residential proxy must be active from FIRST request. |
| CrowdGen/Appen registration | Aggressive WordPress.com anti-bot. Residential proxy required from first load — once IP flagged, cooldown 10-30 min. See `references/crowdgen-429-cascade.md`. |
| "request was rejected because it was considered high risk" | WAF detected datacenter IP. DataImpulse (`__cr.id`) is known to route through datacenter IPs despite marketing as residential. Switch to VPS-based SOCKS5 proxy in target region. Also add WAF retry handler — see `references/playwright-resilience-patterns.md` §1. |
| WebRTC leaks real IP despite proxy | Add `--disable-webrtc-hw-encoding`, `--enable-features=WebRtcHideLocalIpsWithMdns`, `--disable-features=UseChromiumNetworkService` to Chromium launch args. See `references/browser-stealth.md` §Level 3 for full flag set. |
| Geolocation API exposes real location | Spoof at Playwright context level with `geolocation={'lat','lng'}` + `permissions: ['geolocation']`. See `references/browser-stealth.md` §Geolocation Spoofing. |
| SSL "Your connection is not private" / `NET::ERR_CERT_COMMON_NAME_INVALID` | Invalid SSL cert on target site. Add `--ignore-certificate-errors` to Chromium launch args. If the flag doesn't work, use the auto-click handler (Advanced → Proceed). See `references/browser-stealth.md` and `references/playwright-resilience-patterns.md` §2 for retry loop. |
| Worker closes immediately on SSL/WAF error | Don't give up on first attempt. Add retry loop with reload (up to 5 attempts) before closing worker. See `references/playwright-resilience-patterns.md`. |
