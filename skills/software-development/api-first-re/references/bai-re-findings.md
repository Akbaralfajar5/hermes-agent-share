# b.ai RE Findings (2025-06)

## Endpoints
- Claim: `POST /trpc/lambda/user.claimSignupBonus?batch=1`
- Check claimed: `GET /trpc/lambda/user.hasClaimedSignupBonus?batch=1&input={"0":{"json":null}}`
- Session: `GET /api/auth/session`
- Host: `chat.b.ai` (resolves to `chat.ainft.com`)

## Claim Payload
```json
{"0":{"json":{"encryptedToken":"...","turnstileToken":"...","type":"oauth:google"}}}
```

## encryptedToken Generation
```js
CryptoJS.AES.encrypt(`${displayName} welcome gift-claim|${Date.now()}`, "1wT1r7z8bZxDHVmZKAs6VFYSXOxmyh0lLByiw5TmF0=").toString()
```
- `displayName` = user's display name from session (e.g. "AO_hbm6li3x"), NOT email

## Turnstile
- Sitekey: `0x4AAAAAADKhTSXIozuHjOoF`
- Mode: managed (invisible, inside modal)
- Container: `<div id="cf-turnstile">` inside `.ant-modal-content`
- Button disabled until token generated
- **Will NOT solve from datacenter IPs** — silent fail, no iframe rendered
- Third-party solvers (sctg.xyz) return ERROR_CAPTCHA_UNSOLVABLE for this sitekey

## Auth
- AuthJS (not classic NextAuth) — cookies: `__Host-authjs.csrf-token`, `__Secure-authjs.callback-url`
- Google OAuth via GIS popup (postMessage-based)
- Headless browsers fail: GIS popup needs real browser context

## UI Claim Flow
1. Click "Claim Free Credits" button on main page
2. Modal opens (ant-modal) showing "BAI Welcome Gift" + "500,000"
3. Turnstile widget auto-solves in background (residential IP)
4. "Claim" button in modal becomes enabled
5. Click "Claim" → API call fires → done

## Server Validation
- Empty turnstileToken → 400 `missing-input-response`
- Dummy turnstileToken → 400 `invalid-input-response`
- Server-side Turnstile validation cannot be bypassed

## Script
- `bai_claim_v7.py`: Playwright (non-headless), residential IP required
- Fresh browser per account, Google login + modal claim flow
- Resumes from `bai_claims.txt` (tracks done accounts)
