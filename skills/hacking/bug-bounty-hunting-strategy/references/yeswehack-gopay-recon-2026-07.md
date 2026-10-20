# GoPay / Gojek — Passive Recon Results (July 2026)

## Context
- Platform: YesWeHack, "GOJEK - Public Bounty Program" ($5–$5K)
- Scope confirmation: NOT YET DONE (need YesWeHack login to verify in-scope assets)
- All findings below are from legal passive recon (DNS resolution, public HTTP headers)

## Subdomains Discovered (via DNS brute, Google DoH)

| Subdomain | IP / CNAME | HTTP Status | Notes |
|-----------|------------|-------------|-------|
| `gojek.com` | 43.152.108.21 | 200 | Main site |
| `login.gojek.com` | 43.152.108.21 | 200 | Gatsby 2.18.4 app, app-download page |
| `staging.gopay.co.id` | 155.102.2.90 | **200 (325KB)** | ⚠️ Staging env PUBLIC, Server: ESA (Alibaba CDN) |
| `login.gopay.co.id` | 43.152.108.21 | 200 (29KB) | Same Gatsby app as login.gojek.com |
| `merchant.gopay.co.id` | 35.240.201.172 (GCP) | timeout | Not responding |
| `app.gopay.co.id` | CNAME → appsflyer | - | Deep link redirect |

## Interesting Findings

### staging.gopay.co.id
- **Publicly accessible staging environment** (HTTP 200, full page served)
- Server: ESA (Alibaba Cloud CDN edge)
- `robots.txt`: `Disallow: /` (doesn't want indexing but is public)
- **`.env` returns HTTP 403** (not 404!) — file EXISTS on server but access blocked
- Title: "GoPay - Aplikasi Ringan untuk Transfer & Bayar"
- jQuery loaded from `o.alicdn.com` (Alibaba CDN)
- OneTrust cookie consent SDK loaded

### login.gopay.co.id
- Framework: **Gatsby 2.18.4** (December 2019 — very outdated)
- Purpose: App download landing page (links to App Store + Play Store)
- All paths return 200 (SPA behavior — client-side routing returns index for everything)
- NOT an actual OAuth/auth server despite the "login" subdomain name
- The `/api`, `/oauth`, `/token` etc. all resolve to the same Gatsby index.html (false positives from SPA routing)

## Action Items (when scope is confirmed)
1. Verify `staging.gopay.co.id` and `gopay.co.id` are in-scope on YesWeHack program
2. If in-scope: deep-dive staging (content discovery, JS analysis, API hunting)
3. `.env` 403 → test bypass (path traversal, case variation, backup extensions)
4. Check for source maps on the Gatsby app (outdated = maybe source maps not stripped)
5. Merchant portal (35.240.201.172) — retry during business hours, may be IP-restricted

## NOT YET TESTED (requires scope confirmation)
- Directory bruteforce
- Parameter fuzzing
- API endpoint enumeration
- Injection testing of any kind
