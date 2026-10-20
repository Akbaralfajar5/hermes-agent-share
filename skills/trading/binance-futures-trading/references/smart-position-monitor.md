# Smart Position Monitor with Technical Exit

## Overview
A position monitoring script that goes beyond simple SL/TP price checks. It analyzes multi-timeframe technicals every 60 seconds and auto-exits if the setup invalidates — even before SL is hit.

## When to Use
- When API conditional orders are blocked (XAUUSDT, commodity pairs)
- When user wants "exit if technicals go bad" instead of fixed SL only
- Post-news entries where momentum can reverse quickly

## Technical Exit Logic

### For SHORT positions, exit if 3+ bullish signals detected while in loss:
1. **5m EMA7 > EMA25** — short-term trend flipped bullish
2. **15m EMA7 > EMA25** — medium-term trend flipped bullish  
3. **1h EMA7 > EMA25** — hourly trend bullish
4. **5m RSI < 30** — oversold = bounce risk
5. **15m RSI < 30** — oversold on higher TF
6. **5m making higher highs** (last 3 candles) — uptrend forming

### For LONG positions, exit if 3+ bearish signals detected while in loss:
1. **5m EMA7 < EMA25** — short-term trend flipped bearish
2. **15m EMA7 < EMA25** — medium-term trend flipped bearish
3. **1h EMA7 < EMA25** — hourly trend bearish
4. **5m RSI > 70** — overbought = reversal risk
5. **15m RSI > 70** — overbought on higher TF
6. **5m making lower lows** (last 3 candles) — downtrend forming

## Key Rule
**Only trigger technical exit when position is IN LOSS.** If position is in profit, let it ride — the technicals might just be a pullback before continuation.

## Timing
- Price check: every 5 seconds (for SL/TP)
- Technical analysis: every 60 seconds (heavier API calls)
- Uses Binance klines endpoint (no auth needed)

## Lessons Learned (May 2026 Session)

1. **NFP didn't move gold as expected** — even with "BAD USD" forecast, actual data was positive USD but gold still went up slightly. Market reactions aren't always logical.

2. **Pre-news entries are risky** — entering 5 hours before NFP led to sideways chop and eventual manual close at small loss. Post-news confirmation entries are safer.

3. **Technical exit saved ~$50+ vs SL** — the SHORT position was closed at -$5.24 via technical exit. If it had waited for SL ($4,780), loss would have been much larger given gold continued rising.

4. **Liquidation price vs SL alignment** — with 50x leverage on ISOLATED, liquidation is very close (~1.5%). SL must be set BELOW liquidation price, otherwise position gets liquidated before SL triggers. Always check `liquidationPrice` from positionRisk endpoint.

5. **Background script buffering** — Python scripts run via `background: true` may show empty logs even with `flush=True`. The watch_patterns feature is the reliable way to get alerts. Always use watch_patterns for critical events.
