# b.ai Turnstile Campaign — Findings (June 2025-2026)

## Target
- Site: chat.b.ai (backend: chat.ainft.com)
- Sitekey: `0x4AAAAAADKhTSXIozuHjOoF`
- Type: Managed Turnstile (click only, no puzzle)
- Placement: Inside claim modal, gates "Claim" button (disabled until solved)

## What Works
- **Residential IP + real Chrome** (channel="chrome") — Turnstile renders and auto-solves
- **Non-headless mandatory** — headless=False required for widget to render
- **5 parallel browsers** — reliable Turnstile render on all instances
- **navigator.webdriver removal** — helps render consistency

## What Does NOT Work
- **VPS/datacenter IP** — Turnstile refuses to render (no iframe spawned, silent fail)
- **Headless browser on VPS** — same as above, no render
- **Paid solver (sctg.xyz)** — token solves but server rejects with "Invalid token" due to IP mismatch between solver and claim request
- **15 parallel browsers** — some instances fail to render Turnstile (Cloudflare throttle per IP)
- **Chromium (Playwright default)** — higher detection rate than real Chrome

## Architecture That Worked (100 accounts, 98% success)
1. Login phase: headless OK (no Turnstile on login)
2. Save cookies to `cookies/{email}.json`
3. Claim phase: non-headless, load cookies, user clicks Claim manually
4. Batch in groups of 5 — reliable Turnstile render

## Turnstile Render Troubleshooting
- If captcha doesn't appear: F5 refresh, or close modal → reopen
- If multiple browsers affected: reduce parallel count (5 > 3)
- Restart router for fresh IP if all browsers fail

## Cost
- Solver: $0 (doesn't work for this target)
- Total: free (residential IP + manual click)
- Time: ~2 min per batch of 5 accounts
