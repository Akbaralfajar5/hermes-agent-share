# Web App Recon Quick Wins — Patterns That Pay

## 1. Express.js Backend Detection via Error Pages

When a site is a SPA (React/Vue/Next) but has a backend, probe `/api/`:

```bash
curl -s "https://target.com/api/" | head -10
```

If you see: `<pre>Cannot GET /api/</pre>` → **Express.js backend confirmed**.

Then enumerate with common REST patterns:
```bash
for path in /api/health /api/auth/login /api/user/me /api/stats /api/config; do
  code=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" "https://target.com${path}")
  if [ "$code" != "404" ]; then echo "[$code] ${path}"; fi
done
```

**Why it works:** Express returns a distinctive error page for routes that don't match. 404 = route truly doesn't exist. 200/301/401/403 = route exists (even if auth-gated).

## 2. CSP Header as Service Map

Content-Security-Policy headers leak the ENTIRE internal service architecture:

```bash
curl -sI "https://target.com/" | grep -i "content-security-policy"
```

Extract:
- `connect-src` → API endpoints, staging APIs, third-party services
- `frame-src` → embedded services (payment processors, auth providers)
- Datadog/Sentry API keys (public but reveal monitoring infra)
- Staging/dev URLs (often less protected)

**Real example (paybox.sh Jul 2026):**
```
connect-src: https://api.paybox.sh https://staging.api.paybox.sh https://api.moonx-dev.com
```
→ Exposed staging API, internal MoonX dev API, BasisTheory card tokenization.

## 3. OAuth Dynamic Client Registration (RFC 7591)

Check if the OAuth server allows unauthenticated client registration:

```bash
# First discover OAuth metadata
curl -s "https://api.target.com/.well-known/oauth-authorization-server"

# If registration_endpoint exists, try registering
curl -s -X POST "https://api.target.com/oauth/register" \
  -H "Content-Type: application/json" \
  -d '{"client_name":"test","redirect_uris":["https://example.com/cb"]}'
```

If it returns a `client_id` without auth → **HIGH severity finding**:
- Attacker can create unlimited OAuth clients
- Phishing via legitimate-looking OAuth consent screen
- If `token_endpoint_auth_methods_supported: ["none"]` → PKCE-only, public clients everywhere

## 4. /api/health Information Disclosure

Health endpoints often leak microservice architecture:

```bash
curl -s "https://api.target.com/health"
```

Look for:
- Service names (reveals internal architecture)
- Uptime (tells you when last deploy happened)
- Database connection status
- Queue/worker status
- Version numbers

**Severity:** Medium (Information Disclosure) — useful for targeted follow-up attacks.

## 5. CORS Misconfiguration Check

```bash
# Check if arbitrary origins are reflected with credentials
curl -sI -H "Origin: https://evil.com" "https://api.target.com/health" | grep -i "access-control"
```

Vulnerable if:
- `access-control-allow-origin: https://evil.com` (reflects attacker origin)
- AND `access-control-allow-credentials: true`

Safe if:
- Only whitelisted origins reflected (e.g., only `https://app.target.com`)
- No credentials flag

Also check what custom headers are allowed:
```
access-control-allow-headers: x-custom-token, authorization
```
→ Reveals authentication header names used internally.

## 6. Expo/React Native Web App JS Bundle Analysis

Expo apps serve a predictable bundle structure:
```
/_expo/static/js/web/entry-<hash>.js
/_expo/static/js/web/__common-<hash>.js
```

Extract ALL API routes from the entry bundle:
```bash
curl -s "https://target.com/_expo/static/js/web/entry-*.js" | grep -oP '"/api/[a-z0-9/-]+"' | sort -u
```

This reveals the complete API surface including internal/admin endpoints not visible in the UI.

## 7. Staging API — Always Check

If CSP or JS reveals a staging URL, ALWAYS probe it:
```bash
curl -s "https://staging.api.target.com/health"
```

Staging often has:
- Weaker rate limiting
- Debug endpoints exposed
- Test accounts with elevated permissions
- Swagger/OpenAPI docs not blocked
- Same auth mechanism but weaker validation
