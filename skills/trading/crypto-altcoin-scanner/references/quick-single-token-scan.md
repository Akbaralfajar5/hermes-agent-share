# Quick Single-Token Scan (3-TF, 15pt)

When user says "cari entry satu token" or "find me the best token to enter" — use this lightweight pattern instead of full AITS. Fast, no auth needed, pure Binance public API.

## Method

1. Fetch top 50 USDT perpetual pairs by 24h quote volume (`/fapi/v1/ticker/24hr`)
2. Filter: `quoteVolume > $10M`, exclude stablecoins (USDC, BUSD, TUSD, FDUSD, etc.)
3. For each candidate, analyze 3 timeframes: **4H, 1H, 15M**
4. Each TF scores max 5 points:
   - EMA alignment (EMA7 > EMA25 > EMA99): +2 (bull) / -2 (bear)
   - RSI zone (55-75 bull, 25-45 bear): +1
   - MACD histogram direction: +1
   - Price vs EMA99: +1
5. Combined score = sum of all 3 TFs (max 15)
6. Direction = LONG if 2+ TFs are BULL, SHORT if 2+ TFs are BEAR, else skip
7. Filter: RSI not overbought (>75 for LONG) or oversold (<25 for SHORT)
8. Sort by strength descending, pick #1

## Entry Plan Format (User Preference)

Present the best setup as a clean actionable plan:

```
🎯 [SYMBOL] [LONG/SHORT] — Entry Plan

📊 Score: X/15 (4H+1H+15M alignment)
📐 EMA Stack: 7>25>99 ✅
📈 Vol 24h: $XXM | Change: ±XX.X%

🎯 ENTRY: [Market/Limit] $price
🛑 SL: $price (X.X%)
✅ TP1 (30%): $price | RR 1:X.X
✅ TP2 (40%): $price | RR 1:X.X
✅ TP3 (30%): $price | RR 1:X.X
⚡ Leverage: Xx (ATR X.X%)
📦 Margin: 5% balance
```

## SL/TP Calculation (Intraday)

- SL: max(swing_low - ATR*0.3, price - ATR*1.5), capped at 3% from entry
- TP: R:R based (1:1.5, 1:2.5, 1:3.5 from SL distance)
- Leverage: inversely scaled with ATR% (ATR >2% → 10-15x, 1-2% → 20-30x, <1% → 50x)

## Caveats

- This is a MOMENTUM scan — tokens already pumping (+20-30% 24h) score highest
- Warn user if top pick already had big move (pullback risk)
- For entries on tokens that haven't moved yet, use FibStruct engine or full AITS
- Always mention: ideal entry is at EMA7 pullback, not FOMO at current price
- No auth needed — uses public Binance API only
