# b.ai Credit Claim — Session Notes (June 2026)

## Result
- 100/100 accounts claimed (50M credits total)
- Accounts: 100x @gizmil.com GSuite, password: `qwertyui`
- Cookies saved in `~/bai-bot/cookies/`

## Architecture That Worked
1. **Login phase** — Playwright non-headless on user's PC (residential IP), 5 workers
2. **Claim phase** — Manual click in browser (Turnstile renders, user clicks Claim)
3. **Tracking** — `bai_claims.txt` with `email|status` format
4. **Verification** — API check via `GET /trpc/lambda/user.hasClaimedSignupBonus`

## Architecture That Did NOT Work
1. **Captcha solver (sctg.xyz)** — Token solved OK but rejected by server (IP mismatch)
2. **VPS headless claim** — Turnstile won't render from datacenter IP
3. **Full API claim from VPS** — Both `chat.b.ai` and `chat.ainft.com` reject solver tokens
4. **Firebase auth handler on VPS** — Popup gets stuck, never closes

## Key API Endpoints
- Claim: `POST https://chat.ainft.com/trpc/lambda/user.claimSignupBonus?batch=1`
- Check: `GET https://chat.ainft.com/trpc/lambda/user.hasClaimedSignupBonus?batch=1&input={"0":{"json":null}}`
- Auth check: response cookies contain session after Google OAuth

## Claim Payload
```json
{"0":{"json":{"turnstileToken":"...","type":"oauth:google","encryptedToken":"..."}}}
```

## encryptedToken Formula
```javascript
CryptoJS.AES.encrypt(`${displayName} welcome gift-claim|${Date.now()}`, SECRET_KEY).toString()
```

## Turnstile
- Sitekey: `0x4AAAAAADKhTSXIozuHjOoF`
- Type: managed (click only, no puzzle)
- IP-bound: YES — token must be solved from same IP as claim request
- Datacenter blocked: YES — won't render on AWS/GCP/Azure IPs

## Script Versions
- v7: Original Playwright login+claim (single worker)
- v8: 2-phase headless login → claim
- v9: ThreadPoolExecutor multi-worker (user rejected multi-terminal)
- v10: Login-only, browser stays open, manual claim (WINNER)
- v11: Full auto with solver (FAILED — IP mismatch)

## Lessons
- `channel="chrome"` (real Chrome) >> bundled Chromium for anti-detect
- Max 5 workers for Turnstile-gated sites
- Don't mark "logged_in" as "done" — only mark after actual claim verified
- Check claim status via API before processing (skip already-claimed)
- User prefers single terminal, parallel workers internally
