# Pre-News Event Limit Entry Analysis

## When to Use

When user wants to place limit buy/sell orders ahead of high-impact news events (NFP, CPI, FOMC, GDP) to catch the initial whipsaw/dip. Works for any Binance Futures pair but especially effective for Gold (XAUUSDT), BTC, and major pairs that react strongly to macro news.

## Workflow

### Step 1: Fetch Raw Kline Data (No Auth Required)

```python
import requests
import numpy as np

# 15-minute candles (120 for EMA99 accuracy)
url_15m = "https://fapi.binance.com/fapi/v1/klines?symbol=XAUUSDT&interval=15m&limit=120"
data_15m = requests.get(url_15m).json()

# 1-hour candles
url_1h = "https://fapi.binance.com/fapi/v1/klines?symbol=XAUUSDT&interval=1h&limit=120"
data_1h = requests.get(url_1h).json()

# Parse OHLCV
# Format: [openTime, open, high, low, close, volume, closeTime, quoteVol, trades, takerBuyBase, takerBuyQuote, ignore]
closes = [float(c[4]) for c in data_15m]
lows = [float(c[3]) for c in data_15m]
highs = [float(c[2]) for c in data_15m]
opens = [float(c[1]) for c in data_15m]
```

### Step 2: Calculate EMAs

```python
def ema(arr, period):
    k = 2 / (period + 1)
    result = [arr[0]]
    for i in range(1, len(arr)):
        result.append(arr[i] * k + result[i-1] * (1 - k))
    return result

ema7 = ema(closes, 7)[-1]
ema25 = ema(closes, 25)[-1]
ema99 = ema(closes, 99)[-1]
```

### Step 3: Find Swing Lows (Support Levels)

```python
swing_lows = []
for i in range(1, len(data_15m) - 1):
    low = float(data_15m[i][3])
    prev_low = float(data_15m[i-1][3])
    next_low = float(data_15m[i+1][3])
    if low < prev_low and low < next_low:
        swing_lows.append(low)

# Sort descending (nearest to price first)
current_price = closes[-1]
nearby_lows = sorted([l for l in swing_lows if l < current_price], reverse=True)
```

### Step 4: Identify Demand Zones (Bullish Engulfing / Hammer)

```python
demand_zones = []
for i in range(1, len(data_1h)):
    o, h, l, c = float(data_1h[i][1]), float(data_1h[i][2]), float(data_1h[i][3]), float(data_1h[i][4])
    prev_o, prev_c = float(data_1h[i-1][1]), float(data_1h[i-1][4])
    body = abs(c - o)
    
    # Bullish engulfing
    if c > o and prev_c < prev_o and c > prev_o:
        demand_zones.append({'zone_low': l, 'zone_high': o, 'type': 'bullish_engulfing'})
    
    # Hammer/pin bar (long lower wick)
    if c > o and (min(o, c) - l) > body * 1.5:
        demand_zones.append({'zone_low': l, 'zone_high': min(o, c), 'type': 'hammer'})
```

### Step 5: Calculate Fibonacci Retracement

```python
# Find recent swing high and swing low
recent_high = max(highs[-30:])  # Last 30 candles
recent_low = min(lows[-30:])    # Last 30 candles
fib_range = recent_high - recent_low

fib_levels = {
    '0.236': recent_high - fib_range * 0.236,
    '0.382': recent_high - fib_range * 0.382,
    '0.5':   recent_high - fib_range * 0.5,
    '0.618': recent_high - fib_range * 0.618,
    '0.786': recent_high - fib_range * 0.786,
}
```

### Step 6: Find Confluence Zones

The key insight: **stack multiple technical levels together**. The more confluences at a price level, the higher probability it acts as support during a news whipsaw.

```python
# Define candidate levels and count confluences
candidates = {}

# Check each EMA
for name, level in [('EMA7', ema7), ('EMA25', ema25), ('EMA99', ema99)]:
    rounded = round(level)
    candidates.setdefault(rounded, []).append(name)

# Check Fibonacci levels
for name, level in fib_levels.items():
    rounded = round(level)
    candidates.setdefault(rounded, []).append(f'Fib_{name}')

# Check swing lows (cluster within $3)
for low in nearby_lows[:10]:
    rounded = round(low)
    for key in list(candidates.keys()):
        if abs(key - rounded) <= 3:
            candidates[key].append(f'SwingLow_{low:.2f}')
            break
    else:
        candidates.setdefault(rounded, []).append(f'SwingLow_{low:.2f}')

# Check demand zones
for dz in demand_zones:
    mid = round((dz['zone_low'] + dz['zone_high']) / 2)
    for key in list(candidates.keys()):
        if abs(key - mid) <= 3:
            candidates[key].append(f"DemandZone_{dz['type']}")
            break

# Rank by confluence count
ranked = sorted(candidates.items(), key=lambda x: len(x[1]), reverse=True)
```

### Step 7: Structure Limit Entry Orders

**Split strategy for news events:**

| Allocation | Entry Level | Confluences | Rationale |
|---|---|---|---|
| 40% | Best confluence (3-4+ factors) | EMA99 + Fib 0.382 + swing low cluster | Most likely fill on standard whipsaw |
| 30% | Aggressive (1-2 factors) | EMA7/EMA25 + Fib 0.236 | Fills on minor pre-news dip |
| 20% | Conservative (2-3 factors) | Fib 0.5 + swing low | Fills on deeper spike |
| 10% | Deep dip (2+ factors) | Fib 0.618 + demand zone | Lottery ticket, major surprise only |

**Stop Loss:** Below the deepest demand zone or major swing low (the level where the entire bullish structure breaks).

## News Event Timing (WIB)

| Event | Typical Time (WIB) | Volatility |
|---|---|---|
| NFP (Non-Farm Payrolls) | 19:30 (summer) / 20:30 (winter) | Extreme |
| CPI | 19:30 / 20:30 | Very High |
| FOMC Decision | 01:00 (next day) | Extreme |
| FOMC Minutes | 01:00 | High |
| GDP | 19:30 / 20:30 | High |
| Jobless Claims | 19:30 / 20:30 | Moderate |
| PMI | 20:45 / 21:45 | Moderate |

## Key Principles for News Trading

1. **Place limits 30-60 minutes before news** — Spreads widen right at release
2. **Expect whipsaw** — Price often spikes BOTH directions within 1-5 minutes
3. **The initial spike is often fake** — The real move comes 5-15 minutes after
4. **Gold (XAUUSDT) typical NFP range:** $15-40 in first 5 minutes
5. **Use GTC orders** — Don't use IOC/FOK for news limit entries
6. **Cancel unfilled orders 30 min after news** — If not filled, the setup is invalid
7. **Funding rate check** — Neutral/negative funding = less crowded long, better for longs

## Funding Rate & Positioning Check

```python
# Check funding rate (sentiment indicator)
url = "https://fapi.binance.com/fapi/v1/premiumIndex?symbol=XAUUSDT"
data = requests.get(url).json()
funding_rate = float(data['lastFundingRate'])
# Positive = longs pay shorts (crowded long)
# Negative = shorts pay longs (crowded short)
# Near 0 = neutral (ideal for entries)
```

## Example Output Format

```
## XAUUSDT LONG — Pre-NFP Limit Entry Plan

Current: $4,727 | Funding: 0.00% (neutral)

### EMA Levels (15m)
- EMA7: $4,723 | EMA25: $4,718 | EMA99: $4,714

### Confluence Entries (ranked)
🎯 Entry 1 — $4,713 (4 confluences)
   EMA99 + 1h EMA25 + Fib 0.382 + Swing low cluster
   
🎯 Entry 2 — $4,720 (3 confluences)  
   Fib 0.236 + 1h EMA7 + 15m EMA25

🎯 Entry 3 — $4,706 (3 confluences)
   Fib 0.5 + Swing low + Demand zone

🎯 Entry 4 — $4,698 (2 confluences)
   Fib 0.618 + Multiple swing lows

### Risk Management
SL: Below $4,680 (major swing low)
TP1: $4,745 (recent resistance)
TP2: $4,760 (Fib extension)
```

## Pitfalls

- **Don't place ALL capital at one level** — News can spike deeper than expected; ladder entries
- **Gold on Binance Futures (XAUUSDT) has lower liquidity than spot gold** — Slippage can be worse
- **EMA values shift every 15 minutes** — Recalculate close to news time, not hours before
- **Weekend/holiday NFP** — Sometimes released on different day; verify economic calendar
- **Multiple news at same time** — NFP + unemployment rate + average hourly earnings all at 19:30 WIB; combined impact is larger
- **Binance public API (fapi.binance.com) needs no auth** — Use for klines, depth, premiumIndex without API keys
