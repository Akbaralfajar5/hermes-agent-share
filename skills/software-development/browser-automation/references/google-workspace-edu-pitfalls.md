# Google Workspace for Education Signup Pitfalls

## Problem: Welcome Page Loop

**Symptom:** After successful login with Google Workspace for Education account, browser gets stuck in infinite welcome page loop. Clicking "I understand" button reloads the same welcome page instead of proceeding to inbox/dashboard.

**Root cause:** Google Workspace for Education accounts managed by schools/institutions have mandatory onboarding flows that don't work well with headless automation. The welcome page uses client-side state tracking that breaks in automated contexts.

**Tested approaches that failed:**
- Multiple clicks on "I understand" button
- Waiting 5-10 seconds between clicks
- Checking for page navigation after click
- Session persistence across navigation

**Why automation fails here:**
- Welcome flow expects specific browser fingerprints
- Client-side JavaScript state doesn't persist correctly in automation
- Institution-managed accounts have additional security checks

## Solution: Don't Automate GSuite Edu Logins

**When you encounter Google Workspace for Education accounts:**
1. **Stop automation immediately** after detecting the welcome page loop (2 failed attempts max)
2. **Switch to manual approach:** Provide step-by-step instructions for user to complete manually
3. **Alternative:** Use personal Gmail accounts instead of institutional GSuite accounts for automation

**Detection signals:**
- Domain ends in `.edu` or custom school domain
- Login page shows "Google Workspace for Education" branding
- After successful OAuth, redirects to `accounts.google.com/...welcome...` or similar onboarding URL
- "I understand" or "Get Started" buttons that don't advance the flow

## Temp Mail + OAuth Pitfalls

**Problem:** Temp mail services (guerrillamail.com, 10minutemail.com, etc.) don't support custom email addresses for verification links.

**What fails:**
- Generating custom email like `user-1234@guerrillamail.com` — service assigns random email instead
- Accessing inbox for verification link — can't retrieve inbox for custom address
- OAuth flows that require email verification — no way to access verification link

**Solution:**
- Use real disposable email services that support custom addresses (e.g., GSuite with catch-all, temp-mail.org with API)
- Or provide manual signup instructions when email verification is required
- For batch operations, use pre-created accounts with known credentials

## The 2-Strike Rule for Signup Automation

**Rule:** After 2 failed automation attempts on the same flow, stop and diagnose before trying again.

**Why:**
- Repeated failed attempts trigger rate limiting
- Account lockouts from suspicious activity
- Wasted time on approaches that won't work

**What to do after 2 strikes:**
1. Analyze what's blocking automation (Cloudflare, OAuth complexity, verification requirements)
2. Test manually with browser tools to understand the full flow
3. Decide: fix automation approach OR switch to manual/hybrid approach
4. Document the blocker for future reference

**Example from session:** zo.computer signup via Google OAuth failed 3+ times (temp mail issues, GSuite welcome loop, API 500 errors). Should have switched to manual approach after 2nd failure.
