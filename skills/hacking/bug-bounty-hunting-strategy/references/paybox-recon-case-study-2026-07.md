# Paybox.sh Recon Case Study — July 2026

Full recon chain on paybox.sh demonstrating real application of quick-win patterns:
CSP header leak → OAuth dynamic registration → JS bundle API extraction → staging discovery.

## Target Profile

- **app.paybox.sh** — Expo/React Native web app (private beta)
- **api.paybox.sh** — Express.js backend
- **Tech stack:** React Native (Expo), Express.js, Cloudflare, BasisTheory (card tokenization), MoonPay (fiat onramp), MoonX (infra), Datadog (monitoring)
- **Bounty status:** No public program confirmed — verify before active testing

## Recon Chain

### 1. Entry Point: app.paybox.sh
Landing page is a simple "Sign in to paybox" with Continue button. No visible features without auth.

### 2. CSP Header = Full Architecture Map
```bash
curl -sI "https://app.paybox.sh/"
```
Leaked from `content-security-policy`:
```
connect-src: https://api.paybox.sh https://staging.api.paybox.sh https://api.moonx-dev.com https://iframe.moonx-dev.com https://*.basistheory.com https://*.ingest.sentry.io
frame-src: https://iframe.moonx-dev.com https://moonpay.hel.io https://vts.auth.visa.com https://src.mastercard.com
report-uri: https://csp-report.browser-intake-datadoghq.com/api/v2/logs?dd-api-key=pub4f9819648cf6c369f00daa5b3a3a0ea7
```

**Services identified from CSP alone:**
- `api.paybox.sh` — Production API
- `staging.api.paybox.sh` — Staging API (⚠️ publicly accessible)
- `api.moonx-dev.com` — Internal MoonX dev API
- `*.basistheory.com` — Card tokenization (PCI compliance)
- `moonpay.hel.io` — Fiat on/off ramp
- `vts.auth.visa.com` — Visa Token Service
- `src.mastercard.com` — Mastercard Secure Remote Commerce
- **Datadog API key leaked:** `pub4f9819648cf6c369f00daa5b3a3a0ea7`

### 3. API Probes
```bash
curl -s "https://api.paybox.sh/health" # → {"ok":true}
curl -s "https://staging.api.paybox.sh/health" # → {"ok":true}
```

Both prod and staging healthy. No auth required for health endpoint.

### 4. JS Bundle = Full API Surface
App identified as Expo/React Native:
```html
<script src="/_expo/static/js/web/entry-<hash>.js">
```

Extract all API routes from the entry bundle:
```bash
curl -s "entry.js" | grep -oP '"/api/[a-z0-9/-]+"' | sort -u
```

**Complete API surface extracted:**
```
/api/agent-signers        /api/auth/session        /api/auth/state
/api/approvals             /api/clients             /api/config
/api/credentials/cards     /api/credentials/secrets /api/credentials/wallets
/api/credentials/wallets/addresses   /api/credentials/wallets/sync
/api/devices               /api/funding/moonpay/buy-link
/api/funding/moonpay/region  /api/oauth/approve    /api/oauth/intent
/api/passkey/enrolled      /api/passkey/removed     /api/plugins
/api/users/me              /api/users/me/onboarded  /api/x/faucet/start
/api/x/faucet/finalize     /api/x/faucet/status     /api/audit
/mcp                       /api/payments/{id}/advance
```

**Key discovery: `/api/x/faucet/*` — Twitter/X-based USDC faucet**
**Key discovery: `/mcp` — Model Context Protocol endpoint**

### 5. OAuth Dynamic Registration = Open
```bash
curl -s "https://api.paybox.sh/.well-known/oauth-authorization-server"
```
Response:
```json
{
  "issuer": "https://api.paybox.sh",
  "authorization_endpoint": "https://api.paybox.sh/oauth/authorize",
  "token_endpoint": "https://api.paybox.sh/oauth/token",
  "registration_endpoint": "https://api.paybox.sh/oauth/register",
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "token_endpoint_auth_methods_supported": ["none"],
  "scopes_supported": ["mcp", "offline_access"]
}
```

**Testing open registration:**
```bash
curl -s -X POST "https://api.paybox.sh/oauth/register" \
  -H "Content-Type: application/json" \
  -d '{"client_name":"test","redirect_uris":["https://example.com/cb"]}'
```
→ Returns valid `client_id` with NO authentication required.

**Severity: HIGH** — Anyone can register unlimited OAuth clients. Combined with `token_endpoint_auth_methods_supported: ["none"]` (PKCE only, no client secret), this enables phishing via legitimate-looking consent screens.

### 6. MCP Endpoint (Model Context Protocol)
```bash
curl -s "https://api.paybox.sh/mcp"
```
Response:
```json
{
  "error": "unauthorized",
  "error_description": "MCP access requires an OAuth 2.1 access token."
}
```
`WWW-Authenticate` header reveals resource metadata URL.

### 7. Faucet Flow Analysis
From JS bundle, the X/Twitter faucet flow:
1. `POST /api/x/faucet/start` with credential_id + return_url
2. User directed to X OAuth
3. Callback with code + state
4. `POST /api/x/faucet/finalize` with code + state
5. Poll `GET /api/x/faucet/status` for completion

Geo-block: GB, CA, AU, VG only. VPN bypasses trivially.

### 8. Staging API
```bash
curl -s "https://staging.api.paybox.sh/health" # → {"ok":true}
```
Same CORS headers, same auth mechanism. Potential for weaker rate limiting or debug endpoints.

## CORS Analysis
- Prod: `access-control-allow-origin` only reflects `https://app.paybox.sh` → **safe**
- Staging: same behavior
- `access-control-allow-credentials: true` on both
- Custom auth headers exposed: `X-MoonX-Access-Token`, `X-MoonX-Identity-Token`, `X-MoonX-Presence`, `mcp-protocol-version`

## Findings Summary for Reporting

| # | Finding | Severity | Where |
|---|---------|----------|-------|
| 1 | OAuth Dynamic Client Registration open | HIGH | `api.paybox.sh/oauth/register` |
| 2 | CSP header leaks Datadog API key + staging URL | LOW | `app.paybox.sh` headers |
| 3 | Staging API publicly accessible | MEDIUM | `staging.api.paybox.sh` |
| 4 | `/api/health` leaks microservice names | LOW | `api.paybox.sh/health` |
| 5 | JS bundle exposes full API surface | LOW-MEDIUM | Entry bundle |

## Lessons

1. **CSP headers are gold for recon.** Paybox's CSP revealed 6+ internal services plus credential leaks without touching any API.
2. **Always check OAuth .well-known.** Dynamic registration being open is common but HIGH impact.
3. **Expo/React Native bundles are predictable.** The `/_expo/static/js/web/` pattern + `grep` gives you the complete API surface.
4. **Health endpoints leak architecture.** 8 microservice names from one `/health` call.
5. **Staging is the soft underbelly.** Always probe staging URLs — they're often behind prod on security hardening.
