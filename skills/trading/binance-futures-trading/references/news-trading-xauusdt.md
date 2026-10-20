# XAUUSDT News Trading Reference

## Price Discrepancy: Binance Futures vs Spot Gold

| Source | Price (May 2026) | Notes |
|--------|-----------------|-------|
| Binance Futures XAUUSDT Perp | ~$4,720-4,730 | USE THIS for trading |
| Kitco/Investing.com spot | ~$3,360-3,390 | Physical gold spot — WRONG for Binance |

**Why different:** Binance XAUUSDT is a crypto perpetual contract with its own price discovery, funding rate, and premium/discount vs spot. Always verify price directly from Binance API or browser title.

## NFP (Nonfarm Payrolls) Trading Playbook

### Typical Gold Reaction to NFP:
- NFP MISS (actual < forecast) → USD weak → Gold UP (LONG)
- NFP BEAT (actual > forecast) → USD strong → Gold DOWN (SHORT)
- Average Hourly Earnings UP → Inflation fear → Gold UP (secondary)
- Unemployment Rate UP → Recession fear → Gold UP (safe haven)

### NFP Whipsaw Pattern:
```
T+0s:   Initial spike (often WRONG direction — liquidity grab)
T+30s:  Reversal back to pre-news level
T+60s:  True direction begins
T+5min: Main move established (ride this)
T+15-30min: Move exhausts, consolidation begins
```

### Entry Strategies (Ranked by Safety):
1. **Limit at confluence zone** — Place BEFORE news, catch whipsaw dip (SAFEST)
2. **Wait 1-2 min** — Enter after direction confirmed (SAFE)
3. **Market at release** — Maximum exposure to whipsaw (RISKY)

### Confluence Zone Identification (for limit orders):
Best limit entry = zone where multiple levels converge:
- EMA99 (15m) 
- EMA25 (1h)
- Fibonacci 0.382 of recent swing
- Swing low cluster
- Demand zone (bullish engulfing base)

4+ confluences = highest probability fill zone on whipsaw.

### Leverage Guide for News Events (Small Account <$50):

| Leverage | Liq Distance | NFP Survival | Recommendation |
|----------|-------------|--------------|----------------|
| 10x | ~9-10% | ✅ Very safe | Conservative |
| 20x | ~4-5% | ✅ Safe | Recommended |
| 50x | ~1.5-2% | ⚠️ Risky | Only if SL set |
| 75x | ~1.3% | ❌ Dangerous | Avoid |
| 100x | ~0.8% | ❌ Instant liq | Never |

### Critical Reminders:
1. ISOLATED margin (not Cross) — always for news trading
2. Set SL BEFORE news — can't react fast enough manually
3. Cross margin + high leverage + all-in = account wipe on whipsaw
4. Spread widens 2-5x during NFP release — factor into entry

## User's PROD vs Testnet Keys

- **Testnet keys:** Stored in `~/.hermes/.env` and shell env vars
- **PROD keys:** User provides ad-hoc in chat (not stored permanently)
- **Base URLs:**
  - PROD: `https://fapi.binance.com`
  - Testnet: `https://testnet.binancefuture.com`
- When checking "akun real" → use PROD URL with user-provided keys
