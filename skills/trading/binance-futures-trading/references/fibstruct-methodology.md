# FibStruct Methodology

## Overview

FibStruct is a 4-layer confluence trading system combining Fibonacci retracement, Market Structure (SMC), Liquidity Sweep detection, and Trendline analysis. Designed for automated futures trading with high selectivity (1-3 trades/day) and minimum 1:2 R:R.

**Target:** 60-68% win rate with 1:2-1:3 R:R
**Minimum score:** 4/5 confluences for entry
**Timeframes:** 4H (bias) → 1H (confirm) → 15M (zone) → 5M (trigger)

## The 4 Layers

### Layer 1: Market Structure (DIRECTION)
- **4H timeframe** determines overall BIAS (Bullish/Bearish)
- Uses fractal-based swing point detection (lookback=7 for 4H)
- BOS (Break of Structure) = trend continuation
- CHoCH (Change of Character) = reversal signal
- **1H timeframe** must CONFIRM alignment with 4H
- If 4H is NEUTRAL → no trade

**Scoring:**
- 4H structure clear (BULLISH or BEARISH) = +1 point
- 1H structure aligned with 4H = +1 point

### Layer 2: Trendline (FILTER)
- **15M timeframe** — connect 2+ swing points
- Uptrend: connect Higher Lows, price must be ABOVE projected trendline
- Downtrend: connect Lower Highs, price must be BELOW projected trendline
- Slope must be positive (uptrend) or negative (downtrend)
- If trendline broken → setup weakened (but not invalidated alone)

**Scoring:**
- Trendline intact + correct slope = +1 point

### Layer 3: Fibonacci OTE (ENTRY ZONE)
- **15M timeframe** — Fib from last impulse swing
- LONG: Fib from swing low → swing high, entry at 0.618-0.786 retracement
- SHORT: Fib from swing high → swing low, entry at 0.618-0.786 retracement
- Golden pocket (0.618-0.65) is the sweet spot
- Price must be IN or NEAR (within 0.2%) the OTE zone

**Scoring:**
- Price in Fib OTE zone = +1 point

**Extensions for TP:**
- TP1: -0.618 extension (or 1:2 R:R, whichever is closer)
- TP2: -1.0 extension (or 1:3 R:R)

### Layer 4: Liquidity Sweep + Price Action (TRIGGER)
- **5M timeframe** — confirmation before entry
- Liquidity sweep: wick below swing low (LONG) or above swing high (SHORT) then closes back
- Price action: Bullish/Bearish engulfing, Pin bar (rejection wick > 2x body)
- Either sweep OR PA trigger counts

**Scoring:**
- Liquidity sweep detected = +1 point
- OR Price action trigger (engulfing/pin bar) = +1 point

## Entry Rules

### LONG Setup (all must align):
```
✅ 4H: BOS bullish (HH formed)
✅ 1H: Structure bullish (HH + HL)
✅ 15M: Trendline rising, intact
✅ 15M: Price in Fib 0.618-0.786 retracement
✅ 5M: Liquidity sweep below swing low + rejection / engulfing
```

### SHORT Setup (all must align):
```
✅ 4H: BOS bearish (LL formed)
✅ 1H: Structure bearish (LH + LL)
✅ 15M: Trendline falling, intact
✅ 15M: Price in Fib 0.618-0.786 retracement
✅ 5M: Liquidity sweep above swing high + rejection / engulfing
```

## SL/TP Placement

### Stop Loss:
- **Primary:** Below/above liquidity sweep wick + 0.1x ATR buffer
- **Fallback (no sweep):** Below/above Fib 0.786 level + 0.3x ATR buffer
- **Last resort:** 1.5x ATR from entry

### Take Profit:
- **TP1:** 1:2 R:R from entry (close 50%)
- **TP2:** 1:3 R:R or Fib extension -0.618 (close 30%)
- **TP3:** Trail remaining 20% with trendline break as exit

### Leverage (based on SL distance):
| SL Distance | Leverage |
|-------------|----------|
| < 0.5% | 50x |
| 0.5-1.0% | 30x |
| 1.0-2.0% | 20x |
| > 2.0% | 10x |

## Comparison with RSI(3) Mean Reversion

| Aspect | RSI(3) | FibStruct |
|--------|--------|-----------|
| Win rate | ~50-55% | Target 60-68% |
| R:R | 1:1 | 1:2 minimum |
| Trades/day | 5-10 | 1-3 |
| SL distance | Wide (1.5x ATR) | Tight (below wick) |
| False signals | Many | Few (4-layer filter) |
| Scan time | Fast (RSI only) | Slower (multi-TF + structure) |
| Best for | High-frequency, large balance | Small balance, quality over quantity |

## Implementation Notes

### Swing Point Detection (Fractal Method):
```python
def find_swing_points(highs, lows, lookback=5):
    # Swing high: higher than `lookback` candles on BOTH sides
    # Swing low: lower than `lookback` candles on BOTH sides
    # Lookback values: 4H=7, 1H=5, 15M=5, 5M=3
```

### Structure Detection:
- Need minimum 2 swing highs + 2 swing lows to determine structure
- HH + HL = BULLISH, LH + LL = BEARISH, mixed = NEUTRAL
- BOS confirmed when price breaks last swing high (bull) or low (bear)

### Trendline Projection:
- Connect last 2 swing lows (uptrend) or swing highs (downtrend)
- Calculate slope, project to current candle index
- Intact = price on correct side of projected line + slope direction correct

### Liquidity Sweep Detection:
- Check last 3 candles on 5M
- LONG: candle low < recent swing low BUT close > swing low (wick swept it)
- Rejection confirmed: lower wick > 50% of body size
- SHORT: candle high > recent swing high BUT close < swing high

### Scan Performance:
- 200 pairs × 4 timeframes × kline fetch = ~25-30 seconds per full scan
- SL/TP polling (position check only) = <1 second
- Recommended: scan every 5 minutes, SL/TP every 30 seconds

## Daemon Architecture

```
┌─────────────────────────────────────────┐
│         FibStruct Daemon                 │
│  (screen -S fibstruct)                   │
├─────────────────────────────────────────┤
│  Loop:                                   │
│    Every 30s → check_sl_tp()            │
│    Every 5min → scan_fibstruct()        │
│              → execute_entry() if valid  │
├─────────────────────────────────────────┤
│  State: /home/ubuntu/fibstruct_state.json│
│  Log: /home/ubuntu/fibstruct.log         │
│  Watchdog: cronjob every 5min            │
└─────────────────────────────────────────┘
```

## When to Use FibStruct vs Other Methods

- **Small account (<$200):** FibStruct (fewer trades, higher quality, preserves capital)
- **Large account (>$1000):** Can mix RSI(3) for volume + FibStruct for quality
- **High volatility market:** FibStruct (structure-based SL is more reliable)
- **Ranging/choppy market:** Neither works well — reduce size or sit out
- **Strong trending market:** FibStruct excels (structure + trendline + fib all align)
