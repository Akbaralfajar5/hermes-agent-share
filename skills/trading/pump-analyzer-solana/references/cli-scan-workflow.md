# CLI Pump.fun Scan + RugCheck Workflow

> **📢 SUPERSEDED**: For new scans, prefer the `micin-scan` skill — it uses GMGN API (smart money, KOL, bundler, sniper data) + RugCheck + DexScreener in a multi-source pipeline. This reference remains for DexScreener+RugCheck-only fallback.

Python-based scan that queries DexScreener, filters for pump.fun bonding-curve tokens, runs RugCheck on each, quality-scores them, and returns ranked candidates.

## When to use

User asks "cari token early", "scan pump.fun", "sinyal token bagus", or "cariin token yang baru launch".

## API Endpoints

| API | URL | Notes |
|-----|-----|-------|
| Token profiles | `https://api.dexscreener.com/token-profiles/latest/v1?chainId=solana` | Returns ~30 profiles |
| Token boosts | `https://api.dexscreener.com/token-boosts/latest/v1?chainId=solana` | Boosted/promoted tokens |
| Pair search | `https://api.dexscreener.com/latest/dex/search?q={query}` | Broader search, mixed results |
| Pair data | `https://api.dexscreener.com/latest/dex/tokens/{CA}` | FDV, txns, volume, price changes |
| RugCheck | `https://api.rugcheck.xyz/v1/tokens/{CA}/report` | Safety report, holders, LP data |

### Multi-Source Discovery (for broader coverage)

When token profiles endpoint returns limited results, combine 3+ sources:

```python
# Source 1: Token profiles
profiles = requests.get(".../token-profiles/latest/v1?chainId=solana").json()

# Source 2: Token boosts (paid/promoted tokens, often higher quality)
boosts = requests.get(".../token-boosts/latest/v1?chainId=solana").json()

# Source 3: Keyword search (catch tokens missed by profiles)
keywords = ['cat', 'dog', 'meme', 'pepe', 'chill', 'sol', 'moon', 'based']
for kw in keywords:
    pairs = requests.get(f".../search?q={kw}").json()
    # extract pumpfun/raydium solana pairs
    time.sleep(0.2)  # rate limit

# Deduplicate by CA across all sources
```

### Transparent Fallback (when safety filters return 0)

If strict filtering returns 0 candidates, **do NOT report "nothing found"** — the market has tokens, they just fail safety. Instead:

1. Relax filters: FDV $1.5K-$60K, top1 < 55%, RC < 6000, lp_locked ≥ 90%
2. Show ALL candidates with issues explicitly flagged (🚨/⚠️ per issue)
3. Calculate quality score for each anyway
4. Sort by quality score descending
5. Let user see the market reality and decide risk tolerance

This prevents the false impression that "no tokens exist" when the real issue is over-filtering.

## Two scanning modes

### Mode A: Established tokens (graduated + older)

Target FDV $2.7K-$25K, graduated (raydium), decent volume.

```python
# Key filters
if fdv < 2700 or fdv > 25000: continue
if chg24 > 80: continue       # skip already pumped
if buys < 30: continue         # need activity
if dex != "pumpfun": continue  # must be on bonding curve
# RugCheck safety
if top1 > 45: continue
if holders < 20: continue
if lp_locked < 100: continue
if score > 2000: continue
```

### Mode C: Fresh tokens (age-first, < 3 hours)

**When user says:** "token fresh", "token baru", "yang terbaru", "cari token baru launch"

**Key insight:** This is NOT Mode B with tighter filters. Age IS the primary filter. Everything else is secondary.

```python
import time
now_ms = time.time() * 1000
fresh = []

# Multi-source discovery (same as Mode A/B)
all_tokens = {}
# Source 1: token-profiles/latest/v1?chainId=solana
# Source 2: token-boosts/latest/v1?chainId=solana
# Source 3: keyword search (pump, sol, meme, cat, dog, pepe, chad, moon, etc.)

for ca in all_tokens:
    pair = fetch_pair_data(ca)  # DexScreener /latest/dex/tokens/{CA}
    created = pair.get('pairCreatedAt', 0)
    if not created:
        continue
    
    age_hours = (now_ms - created) / 3600000
    
    # PRIMARY FILTER: age < 3 hours
    if age_hours > 3:
        continue
    
    fdv = pair.get('fdv', 0)
    buys = pair.get('txns', {}).get('h24', {}).get('buys', 0)
    
    # Minimal other filters — freshness IS the filter
    if fdv < 1000:       # Much wider than Mode B ($2.7K)
        continue
    if buys < 10:         # Much lower than Mode B (30)
        continue
    
    fresh.append({...})

# Sort by age (newest first), then volume as tiebreaker
fresh.sort(key=lambda x: (x['age_min'], -x['vol']))
```

**Key differences from Mode A/B:**
| | Mode A (Established) | Mode B (Early) | Mode C (Fresh) |
|---|---|---|---|
| Age filter | None | None | < 3 hours (PRIMARY) |
| FDV range | $2.7K-$25K | $2.7K-$15K | $1K+ (wide) |
| Buy threshold | 30 | 30 | 10 (token is minutes old) |
| Sort order | Quality score | Quality score | Age (newest first) |
| DEX filter | pumpfun only | pumpfun + raydium | pumpfun + pumpswap + raydium |
| RugCheck Top1 threshold | < 45% | < 40% | Informational (expected high on bonding curve) |

**RugCheck interpretation for fresh tokens:**
- Top1 > 80% on < 1h token = bonding curve address, NORMAL — not a red flag
- Top1 < 30% on < 1h token = already graduated AND distributed — VERY bullish signal
- Holders < 20 on < 1h token = normal, too early for organic spread
- Holders > 100 on < 1h token = strong organic interest, green flag
- Token-2022 is near-universal on pump.fun now — flag it but don't disqualify
- RugCheck score < 1 = excellent, but expected on fresh bonding curve tokens

**Output format for fresh tokens:**
```
🌱 TOKEN FRESH — Scan Realtime

#N 🟢/🟡/🔴 Symbol (Name) — Quality: XX/100 | Safety: XX/100
• FDV: $X,XXX | Vol: $XX,XXX | Vol/FDV: X.Xx
• 5m: +XX% | 1h: +XX% | B/S: X.Xx
• Age: XXm | Holders: XX | Top1: XX.X%
• DEX: pumpfun/pumpswap | CA: XXXXX...XXXXX

🛡️ RugCheck: ✅ Mint | ✅ Freeze | ✅ LP 100%
⚠️ Issues: Token-2022, Top1 high (bonding curve)
```

**PITFALL:** Don't use the same quality scoring as Mode A/B. On a 10-minute-old token, having 3 holders and Top1 at 90% is NORMAL. The quality score should weight age and volume/FDV ratio more heavily than holder distribution for fresh tokens.

## Quality scoring

Weighted scoring (max ~100):

| Criterion | Weight | Thresholds |
|-----------|--------|-----------|
| Top1 holder % | 25 | <25%=25, <30%=15, else 8 |
| Holder count | 20 | >60=20, >30=10, else 5 |
| RugCheck score | 15 | <500=15, <1000=10, else 0 |
| Social links | 10 | Yes=10, No=0 |
| Creator balance | 5 | 0%=5, else -8 (penalty) |
| Buy/sell ratio | 10 | >1.2x=10, >1.0x=5 |
| FDV (lower=better) | 10 | <$7K=10, else 5 |
| Top5 concentration | 5 | <55%=5, else -3 |
| Vol/FDV ratio | 10 | >0.3x=10, >0.1x=5 |

Minimum quality to qualify: 45-55 (adjustable).

## Deep analysis on single token

When user says "analisis token X lebih dalam" with a CA:

1. **DexScreener pair data** — FDV, price, txns by timeframe (5m/1h/6h/24h), price changes, created time, liquidity
2. **RugCheck full report** — mint/freeze authority, markets/LP, all top holders, creator balance, risks array, token program type
3. **Holder distribution** — identify bonding curve address (usually top1), check if creator still holds, assess concentration
4. **Social links** — from token profiles endpoint, check for Twitter/Telegram/Website
5. **Verdict** — trinity check + distribution assessment + momentum analysis + LP depth

### Key checks in deep analysis

- **Token program**: If `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` (Token-2022), flag as potential hidden features (transfer tax, etc.)
- **LP depth**: If LP < $2K on bonding curve, flag as thin — one sell can crash it
- **Momentum shift**: Compare 1h vs 5m buy/sell ratios — if 1h bullish but 5m bearish, momentum is dying
- **Bonding curve address**: Top holder at 30-40% on pumpfun tokens is usually the bonding curve itself — don't flag it as a whale

## Output format


```
🔍 Sinyal Pump.fun + RugCheck Detail

### #N 🟢/🟡/🔴 Name ($SYMBOL) — XX/100

| Cek | Status |
|-----|--------|
| Mint Revoked | ✅/🚨 |
| Freeze Revoked | ✅/🚨 |
| LP Locked | ✅ X% |
| Creator Balance | ✅/🚨 X% |
| ... | ... |

Holder: X | Top1: X% | Top5: X% | Top10: X%
FDV: $X | 24h: +/-X% | Vol: $X

**Verdict:** ✅/⚠️/🚨 reason
```

## Cron job pattern

Script-only cron (no LLM overhead), every 5 minutes:

```bash
# Create
cronjob create \
  --name "Pump Scanner 5min" \
  --schedule "*/5 * * * *" \
  --script "pump-scanner.py" \
  --no-agent

# Pause/resume (better than delete for re-enable)
cronjob pause --job-id <id>
cronjob resume --job-id <id>
```

Script goes in `~/.hermes/scripts/pump-scanner.py`.

## Trojan/Photon App Data Interpretation

When user shares a screenshot from Trojan, Photon, or similar trading bot apps, extract these **additional security metrics** that DexScreener/RugCheck don't provide:

| Metric | Meaning | Red Flag If |
|--------|---------|-------------|
| **Sniped %** | % of supply bought by sniper bots at launch | >30% = whale exit risk |
| **Sniped Remaining** | % of sniped supply still held | 0% = all snipers exited (dump complete) |
| **Bundled %** | % of supply bought by bundled wallets (coordinated) | >20% = coordinated dump risk |
| **Bundled Remaining** | % still held by bundlers | >10% = more dump incoming |
| **Dev Holdings** | % held by developer wallet | >0% = dev can dump anytime |
| **Insiders** | % held by insider wallets | >5% = insider dump risk |
| **Top 10 (Trojan calc)** | Trojan's own top-10 concentration calc | >25% = concentrated |

### Interpreting combined signals

- **Sniped 30%+ with remaining 0%** + sell volume 2x buy volume = sniper dump in progress, SKIP
- **Bundled 25%+ with remaining 20%+** = bundlers haven't exited yet, wait or SKIP
- **Dev 0% + Insiders 0%** = good sign, but doesn't guarantee safety if sniped/bundled is high
- **Trojan Top 10 vs RugCheck Top 10** may differ — Trojan calculates differently (sometimes by recent activity)

### Cross-reference flow

```
1. User shares Trojan screenshot → Gemini Vision to extract data
2. Cross-check FDV, txns, age against DexScreener API
3. Cross-check holder distribution, LP against RugCheck API  
4. Combine: DexScreener price data + RugCheck safety + Trojan sniper/bundler data = full picture
5. Deliver verdict with all three data sources cited
```

## Critical pitfall

**DexScreener API is too slow for truly early tokens.** By the time a pump.fun token appears in DexScreener's token profiles endpoint, it typically already has 100+ txns and has pumped 300-700%. The endpoint surfaces tokens AFTER they've gained significant volume.

For genuine early detection (0-30 minutes post-launch, pre-pump):
- **pumpportal.fun WebSocket** — subscribe to `newToken` and `tokenTrade` events for sub-second updates
- **Helius RPC** — monitor pump.fun program (`6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`) for new token creates
- **Custom RPC node** with geyser plugin for real-time program monitoring

DexScreener is acceptable for finding "established but still early-ish" tokens (1-4 hours old, graduated or near-graduation), but cannot deliver sub-30-minute entries.
