# Signup Automation Pitfalls

## When Automation Fails: The 2-Strike Rule

**Pattern observed:** Signup automation for zo.computer failed after 3 different approaches over 30+ minutes. Manual signup took 5 minutes.

**The 2-strike rule:** If 2 fundamentally different automation approaches fail, switch to manual with step-by-step guide rather than trying a 3rd approach.

## Common Signup Blockers

### Temp Mail Services (High Failure Rate)

**Problem:** Most temp mail services are Cloudflare-protected and block automation:
- temp-mail.org → Cloudflare block
- 10minutemail.com → Cloudflare block  
- guerrillamail.com → Generates random emails, can't set custom address

**Workaround:** Use real disposable email (Gmail, Outlook) or GSuite accounts if available.

### Google Workspace for Education

**Problem:** Google Workspace accounts have aggressive bot detection:
- Welcome/consent pages loop indefinitely in automation
- Session timeouts are aggressive (2-3 minutes)
- OAuth flows return 500 errors under automation
- "I understand" buttons require multiple clicks to proceed

**Observed behavior (zo.computer signup via GSuite):**
1. Email/password login succeeds
2. Welcome page appears with "I understand" button
3. Clicking button does nothing or loops back to welcome page
4. Session expires after 2-3 minutes, forcing re-login
5. OAuth consent page returns HTTP 500

**Workaround:** Manual signup is 3-5x faster for GSuite accounts.

### OAuth Errors

**Problem:** OAuth flows fail under automation with generic errors:
- HTTP 500 (server error)
- HTTP 503 (service unavailable)
- Redirect loops

**Root cause:** OAuth providers detect automation via:
- Missing browser fingerprints
- Unusual timing patterns
- Headless browser signals

**Workaround:** Use CloakBrowser for better fingerprinting, or manual signup.

## Decision Tree

```
Signup automation attempt 1 fails
    ↓
Try different approach (different auth method, different temp mail)
    ↓
Attempt 2 fails
    ↓
STOP automation
    ↓
Provide manual step-by-step guide with exact commands
    ↓
User completes signup in 5-10 minutes
```

## Manual Signup Template

When switching to manual, provide:

1. **Exact URL** to visit
2. **Form fields** to fill (with example values)
3. **Expected screens** at each step
4. **Verification steps** (email check, etc.)
5. **Post-signup commands** to run (setup scripts, etc.)

**Example:**
```
1. Go to https://service.com/signup
2. Click "Sign up with Google"
3. Login with: email@example.com / password
4. Click "Allow" on OAuth consent
5. Check email for verification link
6. After verified, run: curl -sSL https://setup.sh | bash
```

## Cost-Benefit Analysis

| Approach | Time Investment | Success Rate | When to Use |
|----------|----------------|--------------|-------------|
| Automation (simple sites) | 10-20 min | 80-90% | Internal tools, no bot detection |
| Automation (protected sites) | 30-60 min | 20-40% | Batch operations (50+ accounts) |
| Manual with guide | 5-10 min | 95%+ | 1-5 accounts, protected sites |

**Rule of thumb:** For 1-10 accounts on protected sites, manual is faster. For 50+ accounts, automation investment pays off (even with 40% success rate).
