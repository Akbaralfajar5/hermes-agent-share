# HeadCase Collective — WL Farming Reference

## Project Overview
- **Name:** The HeadCase Collective — Field Notes, Vol I / III
- **Twitter:** @TheHeadCase_nft
- **Website:** https://headcase.store
- **Chain:** Ethereum Mainnet
- **Supply:** 222 anomalies (1/1s)
- **Type:** Points-based whitelist (leaderboard)

## Whitelist System
Points-based leaderboard. Top scorers enter WL when gate opens. Two separate buckets: Tasks and Referrals.

### Anti-Bot Measures
- Non-followers disqualified
- Bot accounts disqualified
- New/inactive X accounts filtered automatically
- OAuth2 PKCE flow (can't fake auth)
- Rate limiting on task completion API (429 after ~6 rapid calls)

## API Endpoints (Next.js on Vercel)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/twitter?redirect=/whitelist` | GET | OAuth2 PKCE → twitter.com authorize |
| `/api/auth/callback` | GET | OAuth callback (sets session cookies) |
| `/api/breach/me` | GET | Current user info, points, completions |
| `/api/breach/tasks` | GET | List available tasks |
| `/api/breach/tasks/complete` | POST | Complete a task `{taskId}` |
| `/api/breach/tasks/daily-tweet` | POST | Submit daily tweet `{tweetUrl}` |
| `/api/breach/wallet` | POST | Submit wallet address `{wallet}` |
| `/api/breach/leaderboard?bucket=tasks&limit=50` | GET | Leaderboard |
| `/api/breach/referral/claim` | POST | Claim referral bonus `{}` |

All endpoints require `credentials: "include"` (session cookies from OAuth).

## OAuth2 Details
- **Client ID:** `ckU1M0FDZkVtM2RmeVVnMVlvMzQ6MTpjaQ`
- **Redirect URI:** `https://headcase.store/api/auth/callback`
- **Scopes:** `users.read tweet.read follows.read offline.access`
- **PKCE:** S256 code_challenge
- **Session cookies set:** `twitter_user`, `twitter_session`

## Tasks (as of May 2026)

| Task ID | Type | Points | One-time |
|---------|------|--------|----------|
| follow_main | follow | 10 | ✅ |
| retweet_promo | retweet | 5 | ✅ |
| like_promo | like | 3 | ✅ |
| retweet_promo_2 | retweet | 5 | ✅ |
| like_promo_2 | like | 3 | ✅ |
| retweet_promo_3 | retweet | 5 | ✅ |
| like_promo_3 | like | 3 | ✅ |
| retweet_1 | retweet | 5 | ✅ |
| retweet_2 | retweet | 5 | ✅ |
| retweet_collab_open | retweet | 5 | ✅ |
| like_collab_open | like | 3 | ✅ |
| like_1 | like | 3 | ✅ |
| like_2 | like | 3 | ✅ |
| daily_tweet | daily_tweet | 20 | ❌ (24h cooldown) |

**Max one-time points:** 58
**Daily tweet:** 20 pts/day
**Top leaderboard (May 7):** 198 pts (~7 days of daily tweets + all one-time)

## Automation Flow (Proven Working)

### Prerequisites
- CloakBrowser (`pip install cloakbrowser`)
- Valid X auth_token + ct0 cookies
- `twitter` CLI (twitter-cli) for actual follow/like/RT on X

### Step 1: Set X cookies in CloakBrowser context
```python
from cloakbrowser import launch
browser = launch(headless=True)
context = browser.contexts[0]
context.add_cookies([
    {"name": "auth_token", "value": TOKEN, "domain": ".x.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "None"},
    {"name": "ct0", "value": CT0, "domain": ".x.com", "path": "/", "secure": True, "sameSite": "Lax"},
    # Same for .twitter.com domain
])
```

### Step 2: Navigate to OAuth, authorize
```python
page = context.new_page()
page.goto('https://headcase.store/api/auth/twitter?redirect=/whitelist')
# Wait for X authorize page
auth_btn = page.query_selector('button:has-text("Izinkan"), button:has-text("Authorize")')
auth_btn.click()
# Wait for redirect back to headcase.store
```

### Step 3: Complete tasks via API
```python
result = page.evaluate('''async () => {
    const res = await fetch("/api/breach/tasks/complete", {
        method: "POST", credentials: "include",
        headers: {"content-type": "application/json"},
        body: JSON.stringify({taskId: "follow_main"})
    });
    return await res.json();
}''')
```

### Step 4: Actually do the social tasks on X
```bash
twitter follow TheHeadCase_nft
twitter like <tweet_id>
twitter retweet <tweet_id>
```

### Step 5: Daily tweet
```bash
twitter post "message @TheHeadCase_nft #TheHeadcase"
```
Then submit URL:
```python
page.evaluate('''async () => {
    await fetch("/api/breach/tasks/daily-tweet", {
        method: "POST", credentials: "include",
        headers: {"content-type": "application/json"},
        body: JSON.stringify({tweetUrl: "https://x.com/user/status/ID"})
    });
}''')
```

## Rate Limiting
- ~6 task completions before 429
- Add 3s delay between task completions
- Daily tweet: 24h cooldown (nextAvailableAt timestamp in response)

## Referral System
- Each user gets a referral code (e.g., `SXW8GXJK`)
- Link format: `https://headcase.store/whitelist/CODE`
- 2 pts per invite + tier bonuses at 10, 25, 50 referrals
- Referral points counted in separate bucket from task points

## Scaling Strategy
For multi-account farming:
1. Need valid X sessions (auth_token + ct0) per account
2. Each account must OAuth separately to HeadCase
3. Rate limit per session — space out task completions
4. Daily tweet needs unique tweet per account (can't reuse URLs)
5. Accounts must actually follow @TheHeadCase_nft (verified server-side via `followsTarget` field)
6. New/inactive accounts get auto-filtered — use aged accounts only

## Key Learnings
- The `/api/breach/tasks/complete` endpoint does NOT verify if you actually did the action on X (follow/like/RT) at submission time — but `followsTarget` is checked separately and can lead to disqualification
- OAuth session persists across page navigations within same browser context
- Referral attribution happens at registration time (first OAuth), not retroactively
- The `referredBy` field stores the referrer's Twitter ID, not their referral code
