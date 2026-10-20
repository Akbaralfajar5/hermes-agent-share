# Supabase Auth Captcha Bypass Patterns

## The 2-Layer Captcha Problem

Supabase projects with captcha protection enabled enforce it at **two independent layers**:

1. **Frontend:** hCaptcha/Turnstile widget (visible or invisible) on the signup form
2. **API:** `gotrue_meta_security.captcha_token` required in POST body to `/auth/v1/signup`

This means even if you extract the Supabase URL + anon key and call the API directly, you STILL need a valid captcha token. No pure API bypass possible.

## Diagnostics: Identify What Captcha Is In Use

### Step 1: Check console errors
```javascript
// Browser console
// Look for: hcaptcha.com, challenges.cloudflare.com, turnstile
```

### Step 2: Check network requests
```python
page.on("response", lambda resp: print(resp.url) if "captcha" in resp.url.lower() or "turnstile" in resp.url.lower() else None)
```

### Step 3: Check API error
```bash
curl -s 'https://<supabase-url>/auth/v1/signup' \
  -H 'apikey: <anon-key>' \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@test.com","password":"Test1234!"}'
# Response: {"code":400,"error_code":"captcha_failed","msg":"captcha protection: request disallowed (no captcha_token found)"}
```

The API error message confirms it's a Supabase-level captcha, not just frontend.

## Extracting Supabase Config from Minified JS

### Pattern 1: Search for `db.*` custom domain
```bash
curl -s '<main-js-bundle>' | grep -oP '.{0,40}db\.[a-z]+\.[a-z]+.{0,200}'
```
Look for `const xxx="https://db.domain.com"` near `sb_publishable_*` key.

### Pattern 2: Search for `supabaseUrl` or `supabase`
```bash
curl -s '<main-js-bundle>' | grep -oP 'supabaseUrl[^,;]{0,200}'
curl -s '<main-js-bundle>' | grep -oP 'sb_publishable_[A-Za-z0-9_-]{30,}'
```

### Pattern 3: Check network requests for Supabase domains
- `*.supabase.co` — standard Supabase
- `db.*.com` — custom domain (common for production apps)
- `*.supabase.in` — India region

### Pattern 4: Browser runtime extraction
```javascript
// In browser console
Object.getOwnPropertyNames(window).filter(k => 
    k.toLowerCase().includes('supabase') || k.toLowerCase().includes('env')
);
```
Note: Modern bundlers (Vite, webpack) often don't expose these on `window`.

## Temp Mail Domain Trust Scoring

Many platforms now check temp mail domain reputation BEFORE accepting signup:

### How to detect
```bash
# Watch network for domain-check endpoints
# Common patterns: /auth/check-domain, /check-email, /validate-domain
```

### Working temp mail services (as of June 2026)
| Service | API | Domain Trust | Notes |
|---------|-----|-------------|-------|
| 10minutemail.net | `GET /address.api.php` | ✅ Good | laoia.com passes most checks |
| mail.tm | `POST /accounts` | ⚠️ Medium | wshu.net rate-limited after ~10 |
| Guerrilla Mail | `GET /ajax.php?f=get_email_address` | ❌ Poor | Blocked by many sites |

### Testing methodology
```bash
# 1. Get temp email
EMAIL=$(curl -s 'https://10minutemail.net/address.api.php' | jq -r '.mail_get_mail')
DOMAIN=$(echo $EMAIL | cut -d@ -f2)

# 2. Test domain trust
curl -s 'https://api.target.com/auth/check-domain-limit' \
  -H 'Content-Type: application/json' \
  -d "{\"domain\":\"$DOMAIN\"}"

# 3. If rejected, try next service
```

## hCaptcha Sitekey Extraction

From the page source or network requests:
```bash
# From JS bundle
grep -oP 'sitekey["\s:=]+["\x27]([a-f0-9-]{30,})' bundle.js

# From hCaptcha API call
# Look for: api.hcaptcha.com/checksiteconfig?host=...&sitekey=XXXXX

# From HTML
grep -oP 'data-sitekey="([^"]+)"' page.html
```

## Browser Automation Patterns That DON'T Work

- **Mobile user-agent:** hCaptcha still appears (12+ hcaptcha calls on iPhone UA)
- **Accessibility cookie:** `hc_accessibility=1` sometimes enables audio but unreliable
- **`hcaptcha.execute()` from console:** Returns no token without user interaction
- **`page.click()` on hCaptcha iframe checkbox:** Invisible widgets don't have clickable checkboxes

## When to Use a Captcha Solver

If ALL of these are true:
1. Direct API returns `captcha_failed`
2. hCaptcha/Turnstile invisible widget on form
3. Mobile/accessibility bypasses fail
4. You need >3 accounts

Then use Capsolver (~$0.50/1K hCaptcha, ~$0.80/1K Turnstile) or 2captcha (~$1/1K).

## Pioneer.ai — Full Case Study

See `references/pioneer-ai-registration-june2026.md` for the complete walkthrough:
- Supabase at custom domain `db.pioneer.ai`
- hCaptcha sitekey: `c646a2ec-0a3e-415c-affe-c502978ede9c`
- Domain trust check at `api.pioneer.ai/auth/check-domain-limit`
- 10minutemail.net (laoia.com) is the only working temp mail
