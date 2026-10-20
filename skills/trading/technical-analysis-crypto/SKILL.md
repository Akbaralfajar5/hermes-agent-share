---
name: technical-analysis-crypto
description: "Comprehensive crypto technical analysis — indicators, chart patterns, support/resistance, multi-timeframe analysis, entry/exit signals, and risk management for spot and futures trading."
tags: ["trading", "technical-analysis", "crypto", "indicators", "chart-patterns", "signals"]
---

# Technical Analysis for Crypto Trading

## When to Use
- User asks for trade setup, entry/exit, TP/SL
- Chart analysis request (any timeframe)
- Indicator interpretation (RSI, MACD, BB, etc.)
- Support/resistance identification
- Trend analysis / bias determination

## Core Indicators

### Trend Indicators
| Indicator | Settings | Signal |
|-----------|----------|--------|
| EMA 9/21/50/200 | Default | Golden cross (9>21), Death cross (9<21). Price above 200 EMA = bullish macro |
| VWAP | Session | Intraday bias. Above = bullish, below = bearish |
| Ichimoku | 9/26/52 | Cloud support/resistance, TK cross, Chikou confirmation |
| ADX | 14 | >25 = trending, <20 = ranging. DI+ > DI- = up |

### Momentum Indicators
| Indicator | Settings | Signal |
|-----------|----------|--------|
| RSI | 14 | >70 overbought, <30 oversold. Divergence = reversal signal |
| MACD | 12/26/9 | Signal line cross, histogram flip, divergence |
| Stochastic | 14/3/3 | >80 OB, <20 OS. %K cross %D |
| MFI | 14 | Like RSI but volume-weighted. >80/>20 |

### Volatility Indicators
| Indicator | Settings | Signal |
|-----------|----------|--------|
| Bollinger Bands | 20/2 | Squeeze = breakout imminent. Walk the band = strong trend |
| ATR | 14 | SL placement: 1.5-2x ATR from entry |
| Keltner Channel | 20/1.5 | BB outside Keltner = squeeze fire |

### Volume Indicators
| Indicator | Settings | Signal |
|-----------|----------|--------|
| OBV | - | Divergence with price = reversal |
| Volume Profile | Session/Range | POC = magnet, HVN = support, LVN = fast move |
| CVD | - | Cumulative delta divergence = absorption |
| RVOL | - | >2x average = significant move |

## Chart Patterns

### Reversal Patterns
- **Double Top/Bottom** — neckline break = entry, target = pattern height
- **Head & Shoulders** — neckline break, measure head to neckline
- **Rising/Falling Wedge** — rising wedge bearish, falling wedge bullish
- **Evening/Morning Star** — 3-candle reversal at key level

### Continuation Patterns
- **Bull/Bear Flag** — breakout direction of prior trend
- **Ascending/Descending Triangle** — breakout direction, measure height
- **Cup & Handle** — breakout above rim, target = cup depth
- **Pennant** — tight consolidation, break with trend

### Candlestick Patterns (High Probability)
- **Engulfing** — body engulfs prior candle. Bullish at support, bearish at resistance
- **Pin Bar / Hammer** — long wick rejection. Direction opposite to wick
- **Doji** — indecision at key level. Confirm with next candle
- **Three White Soldiers / Black Crows** — strong continuation

## Support & Resistance

### Identification Methods
1. **Swing highs/lows** — obvious horizontal levels
2. **Round numbers** — psychological ($1, $10, $100, $1000)
3. **Volume Profile POC** — price with most volume = strong S/R
4. **Moving averages** — 200 EMA, 50 EMA as dynamic S/R
5. **Fibonacci retracements** — 0.382, 0.5, 0.618, 0.786
6. **Previous day/week high/low** — institutional reference points
7. **VWAP bands** — ±1σ, ±2σ from VWAP

### S/R Strength Rating
- Touches: more touches = stronger (3+ = significant)
- Timeframe: higher TF S/R > lower TF
- Volume: high volume at level = stronger
- Confluence: multiple methods agree = highest probability

## Multi-Timeframe Analysis (MTF)

### Framework: 3-Screen
1. **Higher TF (4H/1D)** — determine BIAS (trend direction)
2. **Middle TF (1H)** — identify STRUCTURE (S/R, patterns)
3. **Lower TF (15m/5m)** — find ENTRY (trigger signal)

### Rules
- Never trade against higher TF trend (unless reversal setup at major level)
- Entry on lower TF, targets on middle TF, bias from higher TF
- If HTF ranging → trade range boundaries only

## Entry/Exit Framework

### Entry Checklist
1. ☐ HTF bias confirmed (trend direction)
2. ☐ Key level identified (S/R, fib, VWAP)
3. ☐ Pattern/signal on entry TF
4. ☐ Volume confirmation
5. ☐ Risk:Reward minimum 1:2
6. ☐ Not entering into resistance (longs) or support (shorts)

### Stop Loss Placement
- Below/above structure (swing low/high)
- 1.5-2x ATR from entry
- Below/above key level that invalidates thesis
- Never arbitrary — always structure-based

### Take Profit Targets
- TP1: 1:1 RR (move SL to breakeven)
- TP2: next major S/R level
- TP3: measured move (pattern height projected)
- Trail: ATR trailing or structure-based trail

## Risk Management

### Position Sizing
```
Position Size = (Account Risk %) / (Entry - Stop Loss %)

Example: $10,000 account, 2% risk, entry $100, SL $95 (5% away)
Risk amount = $200
Position = $200 / 5% = $4,000 (0.4x leverage or 40 units)
```

### Rules
- Max 1-2% account risk per trade
- Max 3 correlated positions simultaneously
- If 3 consecutive losses → stop, review, reduce size
- Never average down without planned levels + thesis intact
- Futures: max 5-10x leverage for swing, 20x for scalp (experienced only)

## Crypto-Specific Patterns

### Funding Rate
- Positive high (>0.05%) = overleveraged longs, short squeeze less likely
- Negative = overleveraged shorts, long squeeze potential
- Neutral (0.01%) = healthy market

### Open Interest
- OI rising + price rising = new longs opening (trend continuation)
- OI rising + price falling = new shorts opening (bearish)
- OI falling + price rising = shorts closing (less conviction)
- OI falling + price falling = longs closing (capitulation)

### Liquidation Levels
- Cluster of liquidations above/below = magnet
- Price often sweeps liquidation clusters then reverses
- Use coinglass.com for liquidation heatmap

### Market Structure (SMC/ICT)
- **BOS** (Break of Structure) — higher high/lower low break
- **CHoCH** (Change of Character) — first sign of reversal
- **Order Block** — last opposite candle before impulsive move
- **Fair Value Gap (FVG)** — 3-candle imbalance, often filled
- **Liquidity sweep** — stop hunt above highs / below lows then reverse

## Analysis Output Template

When providing analysis, use this structure:

```
## [PAIR] — [TIMEFRAME] Analysis

**Bias:** Bullish/Bearish/Neutral
**Trend:** Uptrend/Downtrend/Range (EMA alignment)
**Key Levels:**
- Resistance: $X, $Y
- Support: $A, $B

**Indicators:**
- RSI: XX (OB/OS/neutral)
- MACD: signal (cross direction)
- Volume: above/below average

**Setup:** [pattern/signal description]
**Entry:** $XX
**Stop Loss:** $XX (X% risk, below [structure])
**TP1:** $XX (1:X RR)
**TP2:** $XX (next resistance/support)

**Invalidation:** [what breaks the thesis]
**Confidence:** High/Medium/Low
```

## Pitfalls
1. Don't use indicators in isolation — confluence of 2-3 signals minimum
2. Volume confirms everything — breakout without volume = fake
3. Higher timeframe always wins — don't fight the trend
4. Indicators LAG — they confirm, not predict. Price action leads
5. Crypto trades 24/7 — session opens (Asia 01:00, London 08:00, NY 14:00 WIB) still create volatility
6. Memecoins/microcaps: TA less reliable, use narrative + flow + whale tracking instead
7. Don't overtrade ranging markets — wait for clear setup or trade range boundaries
