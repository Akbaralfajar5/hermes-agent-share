# rpow2 Long Shot — Gambling Feature

## Overview
- URL: https://longshot.rpow2.com/
- Uses same `rpow_session` cookie as main rpow2.com
- Allowlist-gated (check access first)
- Rate limit: **10 spins/minute** per IP

## Access Check
```bash
curl -s -b "rpow_session=COOKIE" "https://api.rpow2.com/api/longshot/access" \
  -H "Origin: https://longshot.rpow2.com"
# {"access":"allowed"} or {"access":"denied"}
```

## Spin API
```bash
curl -s -b "rpow_session=COOKIE" -X POST "https://api.rpow2.com/api/longshot/spin" \
  -H "Content-Type: application/json" \
  -H "Origin: https://longshot.rpow2.com" \
  -d '{"stake_base_units":"970000000","odds_choice":"10:1"}'
```
Response:
```json
{
  "id": "uuid",
  "outcome": "WIN",
  "net_user_change_base_units": "9700000000",
  "new_balance_base_units": "174000000000",
  "random_value_hex": "...",
  "signature": "..."
}
```

## Other Endpoints
```bash
# History (last N spins)
GET https://api.rpow2.com/api/longshot/history?limit=100

# Global stats
GET https://api.rpow2.com/api/longshot/stats
```

## Odds & House Edge (from source code)
House edge = **5%** baked into all tiers via formula: `p = (1 - 0.05) / (m + 1)`

| Odds | Win Prob | Payout | EV per spin |
|------|----------|--------|-------------|
| 1:1  | 47.5%    | 1x     | -5%         |
| 2:1  | 31.7%    | 2x     | -5%         |
| 3:1  | 23.75%   | 3x     | -5%         |
| 10:1 | 8.6%     | 10x    | -5%         |

## Randomness (from source code)
```typescript
// randomBytes(8) → CSPRNG, no seed, no prediction possible
const buf = randomBytes(8);
const big = buf.readBigUInt64BE(0);
const bucket = big % 1_000_000_000n;
const threshold = BigInt(Math.floor(p * 1_000_000_000));
return { outcome: bucket < threshold };
```
**No exploitable bug** — fully server-side CSPRNG. Cannot be predicted or manipulated.

## Strategy Notes (live testing May 11, 2026)
- **1:1 = slow bleed** — house edge grinds balance down over 100+ spins. Tested: -12 RPOW over 313 spins
- **10:1 = better for target goals** — single win (+9.7 RPOW) recovers ~10 losses. Hit in 7 spins twice
- Best use: spin with RPOW mined for free (not real money), treat wins as bonus
- Auto-stop at target balance is the right pattern — don't let it run indefinitely

## Auto-Spinner Script
Location: `~/rpow2-miner/longshot.py`

Key config:
```python
STAKE_BASE_UNITS = 970000000   # 0.97 RPOW (just under 1)
ODDS_CHOICE = "10:1"
TARGET = 200_000_000_000       # 200 RPOW — stop when balance hits this
MIN_BALANCE = 10_000_000_000   # 10 RPOW — emergency stop
```

Rate limit handling: on 429, sleep 60s then retry automatically.

## Auth (May 2026)
- `/auth/request` requires Cloudflare Turnstile token — cannot be automated from VPS
- Must login via browser at rpow2.com
- Copy `rpow_session` cookie: DevTools → Application → Cookies → api.rpow2.com
- Cookie TTL: ~30 days (JWT with `exp` field)
