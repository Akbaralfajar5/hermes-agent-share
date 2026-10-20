# GachaSlabz.com Reverse Engineering — June 2026

Pokemon card gacha site with Cloudflare Turnstile + email OTP auth + TanStack Start backend.

## Site Structure

- **Frontend**: React + Vite, loaded from `https://gachaslabz.com/assets/`
- **Backend**: TanStack Start with Seroval serialization
- **API**: Server functions at `/_serverFn/{HASH}?createServerFn`
- **CSP reveals**: `connect-src` includes `https://api.gachaslabz.com` and `wss://api.gachaslabz.com`
- **CDN**: Cloudflare (cf-ray header, Turnstile)
- **Wallet**: Solana-based (NFTs are Solana tokens)

## Turnstile

- **Sitekey**: `0x4AAAAAADIuvWlSI_lLvhpv`
- **Type**: Interactive checkbox (`input[type="checkbox"]` inside Cloudflare iframe)
- **Behavior with CloakBrowser**:
  - Hermes `browser_navigate` → iframe renders → checkbox appears → auto-solves ✅
  - Python `cloakbrowser.launch_async()` → iframe exists but body always empty ❌
- See `references/cloakbrowser-turnstile-launch-gap.md` for full analysis

## Login Flow

### Step 1: Send Code
- **URL**: `POST /_serverFn/0a4bb50b2f3e8be675a1fd0ac78237f4c70e0adcbdb39be9f37b0bfd36f9439e?createServerFn`
- **Headers**: `Content-Type: application/json`, `x-tsr-redirect: manual`
- **Body** (Seroval): `{"t":{...},"f":31,"m":[]}` containing `{data: {email, turnstileToken, fingerprint}}`
- **Fingerprint**: Client-side generated via canvas hash + navigator properties, stored in `localStorage.slabz_device_fingerprint`

### Step 2: Verify Code
- **URL**: `POST /_serverFn/763802dc8ca26b51eee6aab970551ff4bc021b90673f57e94a513cdf95df30b8?createServerFn`
- **Body**: `{data: {email, code, referralCode, utm, fingerprint}}`
- **Referral**: Auto-submitted after first login if user doesn't have affiliate code

### OTP UI
- 6 separate text inputs with auto-tab between them
- Auto-detects 6 digits (typing "123456" in first input → auto-submit)
- Error: "Bad request: Invalid or expired login code"

## Server Function Hashes

Extracted from JS bundle `/assets/main-BeKoufej.js`:

| Function | Hash (64 chars) | Purpose |
|---|---|---|
| Send Code | `0a4bb50b2f3e8be675a1fd0ac78237f4c70e0adcbdb39be9f37b0bfd36f9439e` | Email + Turnstile → OTP |
| Verify Code | `763802dc8ca26b51eee6aab970551ff4bc021b90673f57e94a513cdf95df30b8` | OTP → login |
| Get Quests | `c814b4e9edd56764c8b3c9ddb2320b7eeac07156cd8596cf546b441edab277e9` | GET quests list |
| Start Quest | `c3c1fff507712d60886ff1b0fac985d50cc61fc503d5b2eaf8900e53c82201c3` | POST start quest by slug |
| Claim Quest | `ed942e35060184a7f7bd6c582719e46aec7b3166d53c3232a9df100abae8c8eb` | POST claim quest reward |
| Claim Free Spins | `ed912f1f6b80dce9ca804ec73d29b5a0a2eec82f4a260a4883a9ed0f4d90982a` | POST claim accumulated spins |
| Get Daily Login | `03cf7ff7fed8a1334af9d139b3b2aa9b18353c2bf812b70b494aadcb79b0f002` | GET daily login status |
| Claim Daily | `7fa1cf4468b083792d7d095feb9a66c46ff3b2c5e748f7bb425383712d0d3932` | POST claim daily reward |
| Submit Affiliate | `0defb90c20598988704b02259ee6a5103e680f7d37866323dba6ddf347b4fe33` | POST affiliate code |

## Seroval Serialization

TanStack Start uses Seroval for RSC serialization. Type codes:
- `t: 0` = null/undefined
- `t: 1` = string (`s: "value"`)
- `t: 10` = object (`p: {k: [keys], v: [values], s: count}`)
- `f: 31` = server function ID (constant)

Request structure:
```json
{
  "t": { "t": 10, "i": 0, "p": { "k": ["data"], "v": [...], "s": 1 }, "o": 0 },
  "f": 31,
  "m": []
}
```

Response uses similar encoding with `$TSR/Error` type for errors.

## Earn Section

### Quest Types
- **PARTNER**: External links to visit (highest priority, sorted first)
- **Standard**: Simple tasks (follow, join, etc.)
- Quests rotate daily, max 3 shown by default (expandable)

### Quest States
- `AVAILABLE`: Can start → POST start quest → opens CTA URL in new tab
- `VERIFYING`: Waiting for completion verification (countdown timer)
- `CLAIMABLE`: Ready to claim reward → POST claim quest
- `CLAIMED`: Already done

### Free Spins
- Points accumulate per quest completed
- Free spin threshold: `pointsPerFreeSpin` (default 10)
- Progress bar shows percentage to next spin
- Claim button appears when `spinsClaimable > 0`

### Daily Login
- Separate section with countdown timer
- Claimable once per day

## Email Considerations

### maildrop.cc
- **GraphQL API**: `https://api.maildrop.cc/graphql`
- **Query**: `{ inbox(mailbox: "user@maildrop.cc") { id subject html date } }`
- **Fields**: `id`, `ip`, `helo`, `date`, `mailfrom`, `rcptto`, `headerfrom`, `subject`, `data`, `html`
- **⚠️ Does NOT receive GachaSlabz emails** — tested June 2026, 30s+ polling returned empty inbox. Likely blocked by spam filter.

### Alternatives
- **Guerrilla Mail** (recommended): More reliable for crypto/gaming site emails
- **Temp-Mail.org**: Has REST API
- **Custom catchall domain**: Most reliable but costs $

## Automation Strategy

### Approach A: Pure API (requires 2captcha)
1. Solve Turnstile via 2captcha → get token
2. Build Seroval body → POST send-code
3. Poll Guerrilla Mail → extract OTP
4. POST verify → get auth cookie
5. GET/POST quests → claim rewards
6. POST claim-spins

**Speed**: ~5-10s per account (no browser overhead), 1000 accounts in ~1-2 hours with 10 workers

### Approach B: Hermes Browser Tools (no captcha cost)
1. `browser_navigate` → Turnstile auto-solves via CloakBrowser
2. `browser_type` + `browser_click` → fill email, send code
3. Poll email API → get OTP
4. `browser_type` → fill 6 OTP digits
5. Navigate to `/earn` → complete quests

**Speed**: ~30-60s per account (browser overhead), best with 2-3 parallel workers

### Approach C: Direct Python CloakBrowser ❌
Does NOT work for Turnstile — iframe body stays empty. Use Hermes browser tools instead.

## Test Results

- **Browser test (Hermes)**: Turnstile solved ✅, email sent ✅, OTP screen loaded ✅
- **Email delivery (maildrop)**: ❌ No email received after 30s
- **OTP UI test**: Typing "123456" auto-triggered validation, returned "Bad request: Invalid or expired login code"
