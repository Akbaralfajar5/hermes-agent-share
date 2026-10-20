# Turnstile Datacenter IP Detection — Case Study (b.ai)

## Problem
Cloudflare Turnstile refuses to render iframe/challenge from datacenter IPs (AWS, GCP, etc).
Widget loads (`typeof turnstile !== 'undefined'` = true), `turnstile.render()` returns widgetId, but iframe count stays 0 and callback never fires.

## What DOESN'T work from VPS:
- xvfb + non-headless (real display) — still blocked
- CloakBrowser stealth mode — still blocked  
- Explicit `turnstile.render('#container', {sitekey, callback})` — widgetId returned but no iframe
- Third-party solvers (sctg.xyz) — return `ERROR_CAPTCHA_UNSOLVABLE`
- Force-enabling disabled button — server validates token (`invalid-input-response`)
- Empty/dummy turnstile token — server rejects (`missing-input-response`)

## What WORKS:
- Run from residential IP (user's PC) — Turnstile auto-solves in 2-10 seconds
- Residential proxy routing browser traffic through residential IP
- Mobile tethering (carrier IP = residential)

## Detection method:
```python
# Poll button.disabled to know when Turnstile solved
for i in range(30):  # 60s max
    time.sleep(2)
    disabled = page.evaluate('''()=>{
        const modal = document.querySelector('.ant-modal-content');
        const btn = modal?.querySelector('button:not(.ant-modal-close)');
        return btn ? btn.disabled : null;
    }''')
    if disabled is False:
        break  # Turnstile solved, button enabled
```

## Architecture decision:
For VPS-based mass automation with Turnstile-protected sites:
1. Script runs on VPS for orchestration
2. Turnstile solving delegated to user's PC or residential proxy
3. OR: entire script runs on user's PC (simplest)
