# Turnstile VPS Failure Pattern — Reproduction & Debugging

## Case: b.ai (chat.b.ai) — June 2025

### Environment
- VPS: AWS EC2 t2.micro, Ubuntu 22.04
- Browser: CloakBrowser (Playwright-based, stealth enabled)
- Display: xvfb-run -s "-screen 0 1280x720x24"
- Sitekey: `0x4AAAAAADKhTSXIozuHjOoF`

### Symptoms
1. `turnstile.render('#cf-turnstile', {sitekey: '...'})` returns widget ID (e.g. `cf-chl-widget-5mbqe`)
2. `typeof turnstile !== 'undefined'` = true
3. Hidden input `#cf-chl-widget-5mbqe_response` created but value stays empty
4. Zero iframes spawned (`document.querySelectorAll('iframe').length === 0`)
5. No callback fires (neither success nor error)
6. Submit button stays `disabled` (gated by Turnstile token)
7. Wait 60+ seconds — no change

### What Was Tried (ALL FAILED)
| Approach | Result |
|----------|--------|
| xvfb + headless=False | Widget renders, no iframe, no token |
| CloakBrowser stealth + humanize | Same |
| Explicit `turnstile.render()` call | Widget ID returned, no solve |
| Waiting 60s+ | Timeout, no change |
| Inject widget on different page element | Same behavior |
| Third-party solver (sctg.xyz) — TurnstileTask | `ERROR_CAPTCHA_UNSOLVABLE` |
| Third-party solver — TurnstileTaskProxyless | `ERROR_CAPTCHA_UNSOLVABLE` |
| Third-party solver — TurnstileTaskS2 | `ERROR_CAPTCHA_UNSOLVABLE` |
| All 3 server URLs (api.sctg.xyz, sctg.xyz, ru.sctg.xyz) | All fail |
| Force-enable button + submit with empty token | Server rejects: `missing-input-response` |
| Force-enable button + submit with dummy token | Server rejects: `invalid-input-response` |

### Root Cause
Cloudflare Turnstile checks the requesting IP's ASN (Autonomous System Number). AWS/GCP/Azure/Hetzner/OVH IPs are flagged as datacenter. When detected:
- Widget JS loads normally
- `turnstile.render()` appears to work
- But the actual challenge iframe is **never injected into the DOM**
- No error is surfaced — complete silent failure

### Solution That Works
Run the script on a machine with **residential IP** (user's PC, not VPS). From residential IP:
- Turnstile auto-solves in 2-5 seconds
- iframe spawns immediately
- Token callback fires
- Button becomes enabled

### b.ai Specific Flow (for residential IP)
```
1. Login via Google OAuth popup
2. Click "Claim Free Credits" button on page
3. Modal opens (ant-modal) containing:
   - <div id="cf-turnstile"> (Turnstile container)
   - <button disabled>Claim</button> (gated by Turnstile)
4. Turnstile auto-solves → button.disabled = false
5. Click "Claim" button
6. Verify via /trpc/lambda/user.hasClaimedSignupBonus
```

### Key API Details
- Claim endpoint: `POST /trpc/lambda/user.claimSignupBonus?batch=1`
- Payload: `{"0":{"json":{"turnstileToken":"...","encryptedToken":"...","type":"oauth:google"}}}`
- encryptedToken: `CryptoJS.AES.encrypt("${displayName} welcome gift-claim|${Date.now()}", key)`
- Key: `1wT1r7z8bZxDHVmZKAs6VFYSXOxmyh0lLByiw5TmF0=`
- Server validates turnstile token server-side (400 BAD_REQUEST if invalid/empty)
