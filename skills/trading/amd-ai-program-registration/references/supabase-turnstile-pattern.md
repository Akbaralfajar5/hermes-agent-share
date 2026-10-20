# Supabase Auth + Turnstile — Signup Bot Protection Pattern

## Sites using this pattern
- **pioneer.ai** (Fastino Labs) — LLM inference API, $30 free credit on signup
- Any site using Supabase Auth with captcha enabled

## Architecture
```
Frontend (React/Vite) → Supabase JS Client → db.pioneer.ai (Supabase Auth)
                                     ↓
                            Cloudflare Turnstile Widget
```

## How to identify
1. Look for `createClient("https://<project>.supabase.co", "<key>")` in JS bundle
2. Signup API always returns: `{"code":400,"error_code":"captcha_failed","msg":"captcha protection: request disallowed (no captcha_token found)"}`
3. CSP headers include `connect-src ... https://<project>.supabase.co`
4. Page has hCaptcha or Turnstile iframe

## Supabase key format (v2+)
Not JWT format anymore. New format: `sb_publishable_<random-string>`
Example: `sb_publishable_-X8-DgUI2ukUtnNexA5EdA_xdG3opHb`

## Extraction method
Search JS bundle for the key pattern near the Supabase URL:
```python
re.findall(r'(sb_publishable_[A-Za-z0-9_-]+)', js_content)
```
Or look for the context around `db.<domain>` or `<project>.supabase.co` in the bundle.

## Bypass attempts — ALL FAIL without real browser
- ❌ `curl` with Turnstile test token (`1x00000000000000000000AA`)
- ❌ `cf-turnstile-response` header
- ❌ `captcha_token` in body (top-level or nested in `options`)
- ❌ `x-cf-captcha-token` header
- ❌ `cloudscraper` Python library
- ✅ **Only real browser** that renders Turnstile widget can generate valid token

## Browser-based signup (only working method)
1. Navigate to auth page
2. Click "Continue with Email" → "Sign up"
3. Fill email + password
4. Turnstile auto-passes in real browser
5. Submit → redirect to dashboard
6. Confirmation email sent (optional — account works without verification)

## Pioneer.ai specific
- **Supabase URL:** `https://db.pioneer.ai`
- **Anon key:** `sb_publishable_-X8-DgUI2ukUtnNexA5EdA_xdG3opHb`  
- **Auth page:** `https://agent.pioneer.ai/auth`
- **API proxy:** `https://api.pioneer.ai/auth/check-email-canonical` (POST — email canonicalization)
- **Signup flow:** email + password → auto-redirect to dashboard → optional email verification
- **Credit card:** Required only for claiming $30 free credit (post-signup)
- **hCaptcha widget:** Present in DOM but handled automatically by Turnstile
