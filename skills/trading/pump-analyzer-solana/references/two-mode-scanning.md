# Two-Mode Pump.fun Scanning Strategy

## Why Two Modes?

DexScreener and pump.fun WebSocket serve fundamentally different time windows. You cannot use the same analysis pipeline for both.

### Mode 1: "scan micin" — DexScreener + RugCheck (30 min - 6 hours old)

**When to use:** User says "scan micin", "cari token", "analisis token"

**What it catches:** Tokens that survived initial launch, have volume, and are still early (FDV $2K-$30K).

**Pipeline:**
1. DexScreener token-profiles + token-boosts + search
2. Filter: pump.fun/raydium, FDV $2K-$25K, buys > 15, chg24 < 500%
3. RugCheck: mint/freeze revoked, LP locked, score < 5000, top1 < 50%
4. Quality score (0-100) based on holders, distribution, volume, socials
5. Entry plan with Fibonacci retracement zones

**Advantages:** Full safety analysis, entry zones, verified distribution
**Disadvantage:** Tokens already pumped 200-700%, missed the 0-30 min window

### Mode 2: "snipe" — pump.fun WebSocket (0 - 5 minutes old)

**When to use:** User says "snipe", "pantau real-time", "pantau pump.fun"

**What it catches:** Tokens literally seconds after launch at 28-35 SOL market cap.

**Pipeline:**
1. Connect `wss://pumpportal.fun/api/data` → `subscribeNewToken`
2. Filter: mcap 3-100 SOL, mint ends with `pump`, name ≥ 3 chars
3. Skip: spam names (test/Test prefix), generic words (test, scam, rug), name=symbol
4. Print immediately — name, symbol, mcap, CA, pump.fun link
5. Optional: rate-limited RugCheck on top 3 (but see pitfall below)

**Advantages:** True early entry (28-35 SOL = pre-pump), 5-15 tokens per 30 seconds
**Disadvantage:** Zero safety data — RugCheck useless at this stage (see pitfall)

**Script:** `scripts/pumpfun_sniper.py` — run with `python3 pumpfun_sniper.py [duration_sec]`

## PITFALL: RugCheck Useless on Sub-1-Minute Tokens

For tokens < 1 minute old:
- **Top1 holder is always 80-100%** — because the bonding curve IS the holder
- **RugCheck score is always high** — concentrated ownership triggers danger flag
- **Mint/freeze authority** is the only useful check at this stage

This means the standard safety scoring (which penalizes top1 > 40%) will REJECT every legitimate new token. At launch, the only meaningful filter is:
1. Mint authority revoked? ✅
2. Freeze authority revoked? ✅
3. Name quality (not spam/generic)
4. Initial buy not obviously manipulated

Actual safety analysis can only happen 5-15 minutes after launch when trading distributes supply.

## Tradeoff Summary

| Criterion | Mode 1 (DexScreener) | Mode 2 (WebSocket) |
|-----------|---------------------|-------------------|
| Token age | 30 min - 6 hours | 0 - 5 minutes |
| FDV range | $2K - $30K | 28 - 50 SOL |
| Entry price | Already 2-7x from launch | Near launch price |
| Safety data | Full RugCheck | Mint/freeze only |
| Upside | 2-10x from entry | 10-100x from entry |
| Risk | Medium | Very high |
| Volume | Verified | Unknown |

## Combined Strategy (Recommended)

1. **Run `snipe`** → get 5-10 candidates launching right now
2. **Pick 2-3 with best names/potential** → monitor manually on pump.fun
3. **After 15-30 min**, run `scan micin` on those CAs for full analysis
4. **Enter if:** survived 30 min, decent distribution, buy pressure sustained
