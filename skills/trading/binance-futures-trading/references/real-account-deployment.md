# Real Account Deployment Notes

## Differences from Testnet

| Aspect | Testnet | Real Account |
|--------|---------|--------------|
| Conditional orders (STOP_MARKET) | ❌ Never works | ✅ Works for most pairs, ❌ commodity pairs (XAUUSDT, XAGUSDT) |
| Balance | Virtual $5000 | Real money — risk management critical |
| Margin per trade | 2% (loose) | 4% (user preference, May 2026) |
| Max positions | 10 | 3 (conservative for real money) |
| Leverage | Dynamic ATR-based | Same, but more conservative tiers |

## Real Account Config (May 2026)

- **API Key source:** User provides directly (not in .env — separate from testnet keys)
- **Balance:** ~$106 USDT
- **Engine:** `/home/ubuntu/rsi3_real.py`
- **State file:** `/home/ubuntu/rsi3_real_state.json`
- **Pair list:** `/home/ubuntu/rsi3_real_pairs.json` (auto-refreshed from top 200 by volume)
- **Cronjob:** `RSI(3) Real Account (15m)` — every 15 minutes

## SL/TP Strategy on Real Account

1. **First attempt:** Set via API (STOP_MARKET / TAKE_PROFIT_MARKET)
2. **If API fails (-4120):** Fall back to manual polling monitor
3. **Polling interval:** Every 15 minutes via cronjob (checks SL/TP on each run)
4. **User can also set SL/TP manually from Binance app** (recommended for commodity pairs)

## Key Pitfalls Discovered

### Background Script Buffering
Python scripts run via `background: true` produce NO output unless:
- Every `print()` has `flush=True`
- OR script is run with `PYTHONUNBUFFERED=1`
- This caused the NFP auto-entry script to appear "hung" when it was actually running fine

### Margin Insufficient on ISOLATED
When switching from CROSS to ISOLATED, Binance requires slightly more margin than `notional / leverage`. Solution: use 90% of available balance for calculation, retry with decreasing percentages.

### NFP Auto-Entry Lessons (May 8, 2026)
1. Pre-NFP entry (hours before) = risky — price chops sideways, can hit SL before news
2. Post-NFP entry (1-2 min after) = safer — ride confirmed momentum
3. Threshold for entry: >0.3% move in expected direction
4. If data contradicts thesis (expected BAD USD but got GOOD USD) → SKIP or reverse
5. Gold (XAUUSDT) doesn't always follow fundamental logic immediately — market can react opposite to expectations

### Technical Exit Monitor
For real account, added smart technical exit that closes positions when:
- 3+ bullish signals detected while SHORT is in loss (or vice versa)
- Signals: EMA crossovers (5m, 15m, 1h), RSI extremes, higher highs/lower lows pattern
- This saved ~$5-10 vs waiting for SL hit on the XAUUSDT SHORT trade
