# b.ai Welcome Gift Modal — Turnstile Inject + tRPC Discovery (June 2026)

## Site Information

- **Domain**: chat.b.ai (B.AI — AI Agent infrastructure platform)
- **Auth**: Google OAuth (`oauth:google`) / Wallet login
- **Turnstile sitekey**: `0x4AAAAAADKhTSXIozuHjOoF`
- **Captcha solver**: sctg.xyz (2Captcha-compatible API)
- **Solver API key**: `5KommRyhe023IM3yibzgApgv4mPi7Qsg`

## Modal Structure

When "Claim Free Credits" is clicked, a modal appears with:

```
<div class="ant-modal">
  <div class="ant-modal-body">
    <div id="cf-turnstile" style="margin-bottom: 16px;">
      <div>
        <input type="hidden" name="cf-turnstile-response" id="cf-chl-widget-XXXXX_response">
      </div>
    </div>
    <button type="button" class="ant-btn ..." disabled>
      <span>Claim</span>
    </button>
  </div>
</div>
```

The "Claim" button is `disabled` by default and only becomes enabled after Turnstile completes.

## Turnstile Loading Sequence

1. Click "Claim Free Credits" in the top header
2. React loads Turnstile CDN script: `https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onloadTurnstileCallback&render=explicit`
3. `window.turnstile` becomes available with APIs: `render`, `execute`, `getResponse`, `reset`, `remove`, `ready`, `isExpired`
4. Page calls `turnstile.render('#cf-turnstile', { callback: handleToken, sitekey: '0x4...' })`
5. Cloudflare iframe loads and begins challenge
6. In headless CloakBrowser, the iframe fails → no callback → button stays disabled forever

## Captcha Solver Integration (sctg.xyz)

### Format
```
/in.php?key=API_KEY&method=turnstile&pageurl=https://chat.b.ai/chat&sitekey=0x4AAAAAADKhTSXIozuHjOoF
  → OK|TASK_ID

/res.php?key=API_KEY&action=get&id=TASK_ID
  → CAPCHA_NOT_READY
  → OK|TOKEN (after 15-60s)
```

### Token Length
~816 characters containing `+`, `/`, `-`, `_`, `.` — must be passed as evaluate() argument, not interpolated in f-strings.

## tRPC API Discovery

### Endpoint: `POST /trpc/lambda/user.claimSignupBonus?batch=1`

Required fields discovered via error responses:
1. `encryptedToken` (string) — raw Turnstile token, or RSA-encrypted version
2. `turnstileToken` (string) — same token
3. `type` (string) — `"oauth:google"` or `"wallet"`

### Other Endpoints Found
- `GET /api/auth/session` — returns `{user: {id, name, image}, expires}`
- `GET /trpc/lambda/user.hasClaimedSignupBonus,usage.points?batch=1&input=...`
- `GET /trpc/lambda/config.getGlobalConfig?batch=1&input=...`

### Mutation Body Format
```json
{"0": {"json": {"encryptedToken": "1.xxx...", "turnstileToken": "1.xxx...", "type": "oauth:google"}}}
```
### Token Rejection

The API accepts the schema but returns `"Invalid token: Token verification failed or expired"` for solver-produced tokens.

**Validation chain discovered via error messages:**
1. Send only `turnstileToken` → error: `"encryptedToken" required` + `"type" required`
2. Send `encryptedToken` (alone) → error: `"turnstileToken" required` + `"type" required`
3. Send `turnstileToken` + `type: "oauth:google"` → error: `"encryptedToken" required`
4. Send `encryptedToken` + `turnstileToken` + `type: "oauth:google"` → **schema PASSES** (no more field errors) but returns `"Invalid token: Token verification failed or expired"`
5. This pattern continues even if you swap which token value goes in which field — the three fields are simply **co-required** on the validation schema

**Key insight**: The co-requirement of `encryptedToken` and `turnstileToken` does NOT necessarily mean RSA encryption is happening. The `encryptedToken` field could be:
- A **legacy naming convention** from an earlier version of the API
- A naming choice made when Turnstile support was added
- Simply the same token repeated in two schema slots for compatibility reasons

**Why the token is rejected (not a format issue):**
- The tRPC mutation returns a real Cloudflare verification error, not a schema/zod validation error
- Possible causes:
  - **Token expired**: Turnstile tokens expire in ~5 minutes (unlikely — our solver returns fresh tokens in ~45s)
  - **Solver quality**: The solver's Cloudflare worker might use headless browsers that don't pass Cloudflare's backend checks
  - **Action/cData binding**: If the page passes `action` or `cData` to `turnstile.render()`, the token binds to those values — our solver only gets the sitekey/pageurl, not the custom data
  - **Session binding**: Some Turnstile implementations bind the token to the browser session (fingerprint, cookies)
- **Bottom line**: When the schema passes but verification fails, the solver token itself is being rejected by Cloudflare's backend — this is a solver quality issue, not an API format issue

**To test:** Try the raw token from the browser's own Turnstile widget (if it ever completes) vs a solver token. If the browser's token works but the solver's doesn't, the solver's Cloudflare worker is the bottleneck, not the API format.

```bash
# Check config for encryption key
curl -s -b "__Secure-authjs.session-token=TOKEN" \
  "https://chat.b.ai/trpc/lambda/config.getGlobalConfig?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%7B%220%22%3A%5B%22__N_SSg%22%5D%7D%7D%7D%7D" \
  | python3 -m json.tool | grep -i "encrypt\|public\|rsa\|key"
```

### Important Checks

- `window.turnstile` is FALSE on the login page — it only loads AFTER clicking "Claim Free Credits" (dynamic import)
- The Turnstile API keys: `['_private', 'execute', 'getResponse', 'isExpired', 'ready', 'remove', 'render', 'reset']`
- The widget ID follows pattern `cf-chl-widget-XXXXX` from the input ID `cf-chl-widget-XXXXX_response`
- Object.defineProperty interceptors on `window.turnstile` BREAK the Turnstile loading (entirely)
- MutationObserver watching for `document.getElementById('cf-turnstile-script')` also breaks Turnstile in practice
- DO NOT try to intercept Turnstile — let it load naturally and inject the token into the response input

## Script Location

Full multi-worker claimer: `/home/ubuntu/bai-bot/bai_claimer_v2.py`
Test scripts: `test_*.py` files in `/home/ubuntu/bai-bot/`

## Debugging Commands (run on VPS)

```bash
# Check Turnstile loading
cd /home/ubuntu/bai-bot && timeout 120 python3 test_turnstile_check.py 2>/dev/null

# Test captcha solver directly
curl -s "https://sctg.xyz/in.php?key=API_KEY&method=turnstile&pageurl=https://chat.b.ai/chat&sitekey=0x4AAAAAADKhTSXIozuHjOoF"

# Check claim status
curl -s -b "__Secure-authjs.session-token=TOKEN" "https://chat.b.ai/trpc/lambda/user.hasClaimedSignupBonus?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%7D%7D"
```
