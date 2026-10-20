# CrowdGen (Appen) — 429 IP Cascade Case Study

## Platform
- **URL:** https://crowdgen.com (by Appen)
- **Purpose:** AI training data work — annotation, labeling, evaluation. Pays per task.
- **Hosting:** WordPress.com (shared infrastructure)
- **Anti-bot:** Extremely aggressive — WordPress.com-level rate limiting + bot detection

## The 429 Cascade Pattern

CrowdGen exhibits a **cascading IP ban** behavior that's worse than typical 429:

1. **Browser automation** navigates to site → triggers 429 on first/second page load
2. **IP gets flagged** at WordPress.com infrastructure level (not just CrowdGen app)
3. **ALL subsequent requests from that IP fail** — even curl with different user agents
4. **Cooldown is long** — 60+ seconds insufficient, likely 5-15 minutes minimum
5. **Different paths/URLs** all return 429 (`/`, `/signup`, `/signin`, `/create-account`)

### Timeline (observed)
```
T+0s    Browser loads crowdgen.com → 200 OK (first load works)
T+30s   Browser clicks "Create account" → empty page / 429
T+60s   Browser retry → 429 (IP flagged)
T+90s   curl with Chrome UA → 429 (IP-level ban)
T+120s  curl with Safari UA → 429 (UA rotation doesn't help)
T+150s  curl with Firefox UA → 429
T+180s  curl to /signup path → 429
```

### Key Insight
Once triggered, **the ban is IP-level, not session/cookie-level.** Changing user-agent, clearing cookies, or using incognito does NOT help. The block is at the CDN/infrastructure layer (WordPress.com).

## Required Approach

**Option A: Residential Proxy (recommended)**
- Must use residential proxy BEFORE first request
- Once IP is flagged, proxy won't help (flagged IP stays flagged)
- Proxy must be in place from the very first navigation

**Option B: Wait it out**
- Cooldown appears to be 10-30 minutes
- Not practical for automation

**Option C: Manual registration**
- User registers on their phone/personal device (residential IP)
- Agent guides step-by-step

## CrowdGen Registration Flow (manual)

1. Go to `https://crowdgen.com` → "Create your account"
2. Enter email → receive 6-digit verification code
3. Set password
4. Fill profile: name, country, timezone
5. Select domain expertise (Technology, Language, etc.)
6. Language proficiency ratings
7. Identity verification (may require ID)
8. Wait for approval + project matching

### What to Select for Max Earnings
- **Language: Indonesian** — native speaker = high demand, fewer competitors
- **Language: English** — opens more projects
- **Domain: Technology/Software** — tech tasks pay more
- **Domain: General** — more available tasks but lower pay

## Prevention Rule

> **ALWAYS use residential proxy when automating registration on CrowdGen or any WordPress.com-hosted platform.** The 429 cascade is IP-level and cannot be reversed by session tricks.

This applies to any site resolving through WordPress.com infrastructure, not just CrowdGen.
