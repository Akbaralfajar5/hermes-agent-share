---
name: rpow2-mining
description: RPOW2 centralized PoW mining and gambling automation — mining bots, Long Shot spinner, cookie auth refresh, balance tracking
dependencies:
  - Python 3.8+ with requests
  - Browser for magic-link login (cookie extraction)
triggers:
  - "rpow2"
  - "rpow mining"
  - "longshot"
  - "long shot spinner"
  - "rpow2.com"
  - "hal finney tribute"
---

# RPOW2 Mining & Gambling

RPOW2 (rpow2.com) is a centralized tribute to Hal Finney's original RPOW — Reusable Proofs of Work. Unlike blockchain mining, RPOW2 uses a Postgres ledger operated by one person.

## Key Characteristics

- **Centralized:** Postgres database, not blockchain
- **Fixed supply:** 21,000,000 cap with halving schedule
- **Auth:** Magic-link email login → session cookie
- **Apps:** Mining, Long Shot gambling, wrapping, sending

## Authentication

RPOW2 uses magic-link authentication:
1. Enter email at rpow2.com/#/login
2. Complete Cloudflare Turnstile challenge
3. Click link in email
4. Extract `rpow_session` cookie from browser DevTools

**Cookie format:**
```
rpow_session=eyJlbWFpbCI6InVzZXJAZXhhbXBsZS5jb20iLCJleHAiOjE3ODEwNDEzNzZ9.SIGNATURE
```

**Cookie expiration:** ~30 days from issue. When expired, API returns timeout or auth errors.

## API Endpoints

Base: `https://api.rpow2.com`

```bash
# Get user info + balance
curl -H "Cookie: rpow_session=..." https://api.rpow2.com/me

# Response includes:
# - balance_base_units (integer, divide by 1e9 for RPOW)
# - email
# - created_at
```

## Long Shot Gambling Bot

Long Shot (longshot.rpow2.com) is a spinner game with configurable odds:
- 2:1, 5:1, 10:1, 25:1, 50:1, 100:1
- Higher odds = higher payout but lower win rate
- House edge exists

**Bot location:** `~/rpow2-miner/longshot.py`

**Config variables in script:**
```python
COOKIE = "rpow_session=..."  # Must be fresh
STAKE_BASE_UNITS = 970000000  # 0.97 RPOW per spin
ODDS_CHOICE = "10:1"          # 10x payout, ~9% win rate
MIN_BALANCE = 10_000_000_000  # Stop if < 10 RPOW
```

**Running the bot:**
```bash
cd ~/rpow2-miner
# Background with Hermes tracking
# Use terminal(background=true) in Hermes

# Check if running
ps aux | grep longshot | grep -v grep

# View logs
tail -f ~/rpow2-miner/longshot.log
```

**Log format:**
```
[HH:MM:SS] #SPIN ✅ WIN | Net: +X.XX RPOW | Bal: XXX.XX RPOW | W/L: wins/losses (X.X%) | P&L: +XX.XX RPOW
[HH:MM:SS] #SPIN ❌ LOSE | Net: -0.97 RPOW | Bal: XXX.XX RPOW | W/L: wins/losses (X.X%) | P&L: +XX.XX RPOW
[-] Rate limit, tunggu 60s...
```

## Mining (CPU PoW)

Standard mining at rpow2.com/#/mine:
- Browser-based or script-based
- Difficulty adjusts based on network hashrate
- Reward halves as supply grows

**Miner scripts:**
- `~/rpow2-miner/rpow2_miner.py` — Basic miner
- `~/rpow2-miner/rpow2_miner_v2.py` — Enhanced version

## Pitfalls

- **Cookie expiration:** Session cookies expire after ~30 days. When bot fails with "Balance error" or timeout, cookie needs refresh. Cloudflare Turnstile on login page may block automated refresh — manual browser login required.

- **Rate limiting:** API enforces rate limits. Bot logs `[-] Rate limit, tunggu 60s...` when hit. Built-in 60s backoff handles this.

- **Centralization risk:** Single operator, no recovery guarantees. Don't store significant value.

- **Balance check before gambling:** Always verify current balance before restarting Long Shot bot — balance may have changed since last run.

- **Process management:** Bot runs as background Python process, not PM2. Check with `ps aux | grep longshot`. Logs append to `longshot.log`.

## Verification

```bash
# Check bot status
ps aux | grep longshot | grep -v grep

# View recent activity
tail -20 ~/rpow2-miner/longshot.log

# Check balance via API (requires valid cookie)
curl -s -H "Cookie: rpow_session=..." https://api.rpow2.com/me | jq '.balance_base_units / 1e9'

# Check global stats
# Visit rpow2.com/#/ledger for:
# - Total minted
# - Circulating supply
# - Wrapped amount
# - Active miners
```

## Cookie Refresh Workflow

When bot fails with auth/timeout errors:

1. Open browser to https://rpow2.com/#/login
2. Enter email, complete Cloudflare challenge
3. Check email for magic link, click it
4. In browser DevTools (F12) → Application → Cookies → rpow2.com
5. Copy `rpow_session` value
6. Update `COOKIE` variable in `~/rpow2-miner/longshot.py`
7. Restart bot

**Note:** Cloudflare Turnstile often blocks automated login attempts. Manual browser intervention typically required.

## Related Skills

- `ai-agent-mining` — LLM-based mining (different mechanism)
- `crypto-mining-deployment` — Multi-VPS mining infrastructure
