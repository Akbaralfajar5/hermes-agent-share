# Dynamic SDK Email Validation Bypass

## Context
Dynamic SDK (dynamicauth.com) is a Web3 authentication provider used by many NFT/crypto platforms. It blocks disposable/temp email domains during email-based registration/login.

## How Dynamic Email Validation Works

**API Endpoint Pattern:**
```
POST https://auth-prod.{domain}.com/api/v0/sdk/{environment_id}/emailVerifications/create
Body: {"email": "user@example.com"}
```

**Validation Behavior:**
- `200` → Email accepted, OTP sent
- `422` → "Invalid Email Address" — domain is on blocklist
- `403` → Cloudflare WAF block (missing proper headers or IP blocked)

**Blocked Domains (confirmed):**
- All common temp mail: `mailto.plus`, `wshu.net`, `bjorwi.store`, `mail-temp.com`, `tempmail.dev`, `guerrillamail.com`, `sharklasers.com`, `dispostable.com`, `maildrop.cc`, `harakirimail.com`, `yopmail.com`, `dshznonline.cc`, `tempail.com`, `mohmal.com`, `1secmail.com`, `emailondeck.com`, `throwam.com`, `grr.la`, `tempinbox.com`, `tempr.email`, `tmpmail.net`, `tmpmail.org`, `mailnesia.com`, `mailcatch.com`, `mytemp.email`, `discard.email`, `discardmail.com`, `mailsac.com`, `meltmail.com`

**Accepted Domains:**
- `gmail.com`, `outlook.com`, `yahoo.com`, `hotmail.com` — all major providers accepted

## Bypass Technique: Gmail `+` Aliasing via Emailnator

**Why it works:**
- Gmail ignores dots (`.`) in username and supports `+` aliasing
- `user@example.com` delivers to `user@example.com`
- Dynamic sees `@gmail.com` → passes validation
- Emailnator generates and hosts these addresses

**Emailnator Service:**
- URL: https://www.emailnator.com/
- Generates Gmail addresses with `+` suffix
- Can receive emails on generated addresses
- Has API via RapidAPI: https://rapidapi.com/johndevz/api/gmailnator
- JS app endpoints: `/generate-email`, `/message-list`, `/delete-message`, `/send-message`

**Automation Flow:**
1. Generate temp Gmail via emailnator (e.g., `user@example.com`)
2. Submit to Dynamic auth endpoint → receives 200 (accepted)
3. Poll emailnator inbox for OTP code
4. Submit OTP to Dynamic verification endpoint
5. Account created → proceed to claim/interact
6. Repeat with new email

## Cloudflare Protection on Dynamic API

The `auth-prod.*` endpoints are behind Cloudflare. Direct curl from VPS returns 403 HTML.

**Workarounds:**
- Use browser context (Playwright/Camoufox) for API calls — inherits session cookies
- Use `reverse-api-engineer` to capture proper headers from browser session
- Add `Origin` and `Referer` headers matching the target site
- Use residential proxy if IP is blocked

**Required Headers:**
```
Content-Type: application/json
Origin: https://cards.chimpers.com
Referer: https://cards.chimpers.com/
```

## Key Pitfalls

1. **Rate limiting** — After ~3 rapid requests, API starts returning 422 for ALL domains (even gmail). Wait 30s+ between batches.
2. **Browser fetch interceptor** — Install before clicking submit to capture the exact request/response.
3. **"What's New" modals** — Many Dynamic-powered sites show onboarding modals. Click through before attempting login flow.
4. **OTP expiry** — Dynamic OTP codes expire quickly. Poll emailnator every 3-5 seconds.
5. **Emailnator rate limits** — Generating too many emails in succession may trigger their own limits.

## Example: ChimpersHQ (cards.chimpers.com)

- Dynamic env ID: `5e551d68-2833-4539-82d9-dc14bd2549e8`
- Auth base: `https://auth-prod.chimpers.com/api/v0/sdk/5e551d68-2833-4539-82d9-dc14bd2549e8`
- Login URL: `https://cards.chimpers.com/login`
- Free pack: Chimpcognito (Open Edition, deadline June 15 2026)
- Auth options: Email OTP, Twitter/X, Wallet (MetaMask etc.)
