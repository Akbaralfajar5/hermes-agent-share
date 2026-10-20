# Project Legitimacy Check via X/Twitter Smart Followers

## When to Use
Before farming, minting, or investing in any new crypto project — especially when:
- User shares a project URL and asks "is this legit?" or "scam ga?"
- User wants to check who's sharing/promoting a project
- User says "cek smart followers" or "cari di X dulu"
- Project has no established reputation yet

## Prerequisites
- `twitter` CLI (cookie-based, `pip install twitter-cli`)
- Environment variables: `TWITTER_AUTH_TOKEN` + `TWITTER_CT0` (from user's X account)
- **NOT xurl** — xurl requires developer API keys (OAuth2 setup). `twitter` CLI works with browser cookies and is already configured on this VPS.

## Workflow

### Step 1: Search for the project URL on X
```bash
twitter search "dogeshit.meme" --json 2>&1 | python3 -c "
import sys, json
data = json.load(sys.stdin)
tweets = data.get('data', [])
print(f'Total tweets found: {len(tweets)}\n')
for t in tweets:
    author = t.get('author', {})
    metrics = t.get('metrics', {})
    print(f'@{author.get(\"screenName\",\"\")} ({author.get(\"name\",\"\")}) | verified={author.get(\"verified\",False)} | views={metrics.get(\"views\",0)} | likes={metrics.get(\"likes\",0)}')
    print(f'  {t.get(\"createdAtLocal\",\"\")}: {t.get(\"text\",\"\")[:150]}')
    print()
"
```

### Step 2: Look up each sharer's profile (followers, bio, account age)
```bash
for user in Feng_btc Big_Tea_Rice luyuban69; do
  twitter user "$user" --json 2>&1 | python3 -c "
import sys, json
d = json.load(sys.stdin).get('data', {})
print(f\"@{d.get('screenName','')} | {d.get('followers',0)} followers | {d.get('following',0)} following | created: {d.get('createdAt','')[:16]} | bio: {d.get('bio','')[:80]}\")"
done
```

### Step 3: Assess legitimacy based on signals

**Green flags (likely legit):**
- Multiple mid-tier KOLs (5K-50K followers) sharing independently
- Sharers have established accounts (>1 year old)
- Sharers have relevant bios (crypto/web3/DeFi)
- Sharers add disclaimers ("DYOR", "自行研究") — shows honesty
- Project has verified contract, revoke mechanism, no admin keys

**Red flags (likely scam/rug):**
- Only bot accounts or <100 follower accounts sharing
- All shares are copy-paste identical text (paid promotion)
- Project's own X account doesn't exist or was just created
- No contract verification, no revoke mechanism
- Sharers are all from same network (coordinated shill)
- Token has no liquidity/market yet but promises returns

**Yellow flags (proceed with caution):**
- Only Chinese CT (crypto twitter) sharing — may be regional alpha but also common for scam promotion
- Project is brand new (same day) — no track record
- "几U利润" (few USD profit) claims without verification
- All sharers say "haven't tried yet" (自行决定, 还没有实操)

### Step 4: Report to user with verdict
Format: list each sharer with followers + bio, then give overall assessment with green/red/yellow flags.

## Important Notes
- Browser-based X search requires login (redirects to login page)
- Google/DuckDuckGo search from VPS IP often gets captcha-blocked
- `twitter` CLI with cookies is the most reliable method from VPS
- Cookie auth_token lasts ~1 year, ct0 can change more frequently
- If cookies expire, user needs to re-extract from browser (F12 → Application → Cookies → x.com)

## Example Output Format (for Telegram)
```
📊 Analisis Smart Followers

Yang share (hari ini):
- @Feng_btc (币胜客) | 11.6K followers | 撸毛 blogger
- @Big_Tea_Rice (SuperLeo) | 16.7K followers | Web3 KOL

🔍 Verdict: [LEGIT/CAUTION/SCAM]
✅ Positif: [list green flags]
⚠️ Concern: [list yellow/red flags]
💡 Rekomendasi: [action suggestion]
```
