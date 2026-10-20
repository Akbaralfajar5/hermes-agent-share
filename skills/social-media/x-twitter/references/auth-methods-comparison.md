# X/Twitter Authentication Methods Comparison

## Three Auth Methods Available

### 1. OAuth 1.0a API Keys (x-twitter skill) — RECOMMENDED for automation
**How:** Register at developer.x.com → create App → get 4 keys
**Keys:** X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET

| Aspect | Detail |
|--------|--------|
| Permanence | Keys never expire unless manually revoked |
| Stability | Official API, no bot detection issues |
| Setup time | 5-10 min (one-time) |
| Cost | Free tier: 1,500 tweets/month |
| Risk | None — official, ToS-compliant |
| Cron-friendly | ✅ Perfect for scheduled automation |

**Common user confusion:** "Do I need a separate account?" → NO. Developer features activate on the SAME X account. It's not a new account, just enabling API access on the existing one. Go to https://developer.x.com while logged into normal X account.

**X API vs X Data:** Users see both on the developer portal. X API = posting/engagement automation (what we need, free). X Data = bulk historical data access for enterprise research (expensive, NOT needed for content creators).

**⚠️ PITFALL (as of 2026):** X Developer Portal now shows a credit-based billing system. Even the "Free" tier may require purchasing credits ($5 minimum) before API keys can be generated. If user sees $0.00 credits and cannot create an App or generate keys, the Free tier is effectively paywalled. In this case, fall back to cookies (method 2) immediately — don't waste user's time trying to work around it.

### 2. Browser Cookies (twitter-cli) — FALLBACK for quick testing
**How:** Extract auth_token + ct0 from browser cookies
**Tool:** `pip install twitter-cli` → `twitter` CLI command

| Aspect | Detail |
|--------|--------|
| Permanence | auth_token ~1 year, but can die anytime |
| Stability | Risk of error 226 "automated behavior" on writes |
| Setup time | 2 min (but must repeat when expired) |
| Cost | Free |
| Risk | Account suspension possible (unofficial scraping) |
| Cron-friendly | ⚠️ Fragile — cookies expire unpredictably |

**When cookies die early:** logout, password change, X security flag, browser cookie clear.

**Headless server setup (Method C):** User must extract full cookie string from browser DevTools (F12 → Network → Request Headers → Cookie), then:
```bash
export TWITTER_AUTH_TOKEN=$(echo "$FULL_COOKIE" | grep -oE 'auth_token=[a-f0-9]+' | cut -d= -f2)
export TWITTER_CT0=$(echo "$FULL_COOKIE" | grep -oE 'ct0=[a-f0-9]+' | cut -d= -f2)
twitter whoami  # verify
```

### 3. OAuth 2.0 PKCE (xurl) — ALTERNATIVE official method
**How:** `xurl auth oauth2 --app my-app` (browser-based OAuth flow)
**Tool:** xurl CLI from X developer platform

| Aspect | Detail |
|--------|--------|
| Permanence | Auto-refreshing tokens |
| Stability | Official, reliable |
| Setup time | 10 min (needs developer app + browser for OAuth) |
| Cost | Same API limits as method 1 |
| Cron-friendly | ✅ Tokens auto-refresh |

## Decision Framework

```
User wants X automation
├── Long-term daily posting (monetization goal)?
│   ├── Can user pay $5+ for X API credits?
│   │   └── YES → Use OAuth 1.0a API Keys (method 1)
│   │       └── Guide to developer.x.com signup
│   │   └── NO → Cookies (method 2) — warn about instability
│   └── User refuses developer signup entirely?
│       └── Cookies as fallback, but warn about instability
├── Quick one-off test?
│   └── YES → Cookies OK (method 2)
└── User sends username/password?
    └── REFUSE. Explain cookies (auth_token + ct0) or API keys instead.
```

## Security Rules (ALL methods)
- NEVER accept username/password in chat — users often try to send X login creds directly. Refuse and explain the cookie or API key approach.
- NEVER echo cookie values or API secrets to stdout
- API keys can be sent in chat (they're revocable, not login creds)
- Cookies should be treated as secrets (contain session auth)
- Save credentials to a file with chmod 600, not in env or chat history

## Cookie-Based Setup (Proven Workflow)

When user provides auth_token + ct0 values:

```bash
# 1. Save credentials securely
cat > ~/.hermes/x_credentials.env << 'EOF'
TWITTER_AUTH_TOKEN=<auth_token_value>
TWITTER_CT0=<ct0_value>
EOF
chmod 600 ~/.hermes/x_credentials.env

# 2. Test authentication
source ~/.hermes/x_credentials.env
twitter whoami --json

# 3. Before any twitter command in scripts/cron:
source ~/.hermes/x_credentials.env
```

**How to guide user to get cookies:**
1. Open x.com in Chrome/Edge (must be logged in)
2. F12 → Application tab → Cookies → https://x.com
3. Find `auth_token` (40 char hex) and `ct0` (long hex string)
4. Send both values

**Alternative (full cookie string):**
F12 → Network tab → refresh → click any x.com request → Request Headers → Cookie → copy full value. Then extract with grep.

## Installed Tools on This Server
- `twitter` CLI (twitter-cli v0.8.5) — cookie-based, Python
- `x-twitter` skill (node-based) at ~/.hermes/skills/social-media/x-twitter/ — API key-based
- `xurl` skill available but CLI not yet installed
