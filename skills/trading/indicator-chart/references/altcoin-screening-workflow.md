# Altcoin Screening & Entry Workflow

Complete workflow for finding altcoins with entry potential, analyzing them, and executing trades.

## Phase 1: Global Context (ALWAYS FIRST)

Before any TA, check:
1. **Market news** (market-news-analyst skill) — Fed decisions, geopolitics, regulations
2. **Market environment** — Risk-on/off, VIX, BTC dominance
3. **BTC trend** — Must be bullish/stable for altcoin entries

Key metrics to check:
- BTC Dominance (BTC.D) — above 60% = capital in BTC, not ideal for alts; declining = altseason approaching
- Fear & Greed Index — 75+ = Greed, be selective; 25-49 = Fear, best accumulation
- ETH/BTC ratio — recovering = early altseason signal

## Phase 2: Altcoin Scanning

### CoinGecko API (free, no key)
```bash
# Trending coins
curl -sf "https://api.coingecko.com/api/v3/search/trending"

# Top 100 by market cap with 24h/7d changes
curl -sf "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=24h,7d"

# Page 2 (rank 101-200) for mid-caps
curl -sf "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=2&sparkline=false&price_change_percentage=24h,7d"
```

### Filtering Criteria
| Filter | Spot Entry | Futures Entry |
|--------|-----------|---------------|
| Market Cap | $100M - $5B | $200M+ (needs futures listing) |
| 24h Change | +3% to +20% | +3% to +15% |
| 7d Change | Positive (uptrend) | Positive |
| RSI(14) | 40-65 (room to run) | 45-60 (not overbought) |
| EMA7 vs EMA21 | Price > EMA7 > EMA21 | Same |
| Volume | Vol/MCap > 10% | High OI + low funding |

### Disqualifiers
- RSI > 75 (overbought — wait for pullback)
- Already pumped 40%+ in 7 days (chasing)
- Large token unlock within 2 weeks
- No Binance futures listing (for futures trades)

## Phase 3: Technical Analysis per Candidate

### Quick TA via Binance API
```python
import json, urllib.request
import numpy as np

def analyze(symbol, interval="1d", limit=60):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
    
    closes = np.array([float(d[4]) for d in data])
    highs = np.array([float(d[2]) for d in data])
    lows = np.array([float(d[3]) for d in data])
    
    # EMA
    def ema(data, period):
        k = 2/(period+1)
        e = [data[0]]
        for d in data[1:]: e.append(d*k + e[-1]*(1-k))
        return np.array(e)
    
    ema7 = ema(closes, 7)[-1]
    ema21 = ema(closes, 21)[-1]
    current = closes[-1]
    
    # RSI
    deltas = np.diff(closes)
    gains = [d for d in deltas[-14:] if d > 0]
    losses = [-d for d in deltas[-14:] if d < 0]
    avg_g = sum(gains)/14 if gains else 0
    avg_l = sum(losses)/14 if losses else 0.001
    rsi = 100 - (100 / (1 + avg_g/avg_l))
    
    # ATR
    tr_list = []
    for i in range(1, len(data)):
        h, l, pc = float(data[i][2]), float(data[i][3]), float(data[i-1][4])
        tr_list.append(max(h-l, abs(h-pc), abs(l-pc)))
    atr14 = np.mean(tr_list[-14:])
    
    # Fibonacci from 30d swing
    high30 = max(highs[-30:])
    low30 = min(lows[-30:])
    fib_range = high30 - low30
    
    signal = "BULLISH" if current > ema7 > ema21 else "NEUTRAL" if current > ema21 else "BEARISH"
    
    return {
        "price": current, "rsi": rsi, "atr": atr14,
        "ema7": ema7, "ema21": ema21, "signal": signal,
        "fib_382": high30 - fib_range * 0.382,
        "fib_618": high30 - fib_range * 0.618,
        "high30": high30, "low30": low30
    }
```

## Phase 4: Position Sizing

### Futures Position Sizing (2-3% risk, max leverage)
```python
def calc_position(balance, risk_pct, leverage, entry, sl):
    risk_amount = balance * risk_pct
    sl_distance = abs(entry - sl) / entry
    position_notional = risk_amount / sl_distance
    margin_needed = position_notional / leverage
    quantity = position_notional / entry
    liq_price = entry * (1 - 1/leverage + 0.02)  # approx for isolated
    return {
        "quantity": quantity,
        "notional": position_notional,
        "margin": margin_needed,
        "risk_amount": risk_amount,
        "liq_price": liq_price
    }
```

### Spot Position Sizing (SL at -20%)
```python
def calc_spot_position(balance, entry):
    sl_price = entry * 0.80  # -20% SL
    # Allocate based on max loss tolerance
    # If willing to lose 3% of portfolio at -20% SL:
    risk_amount = balance * 0.03
    position_size = risk_amount / 0.20  # amount to invest
    quantity = position_size / entry
    return {"quantity": quantity, "invest": position_size, "sl": sl_price}
```

## Phase 5: TP/SL Levels

### Standard TP/SL Framework
| Level | Method | Typical |
|-------|--------|---------|
| SL | Below EMA21 or Fib 0.618 or -20% (spot) | 1.5-2x ATR below entry |
| TP1 | Fib 0.236 from swing or recent high | +15-20% |
| TP2 | Fib extension 1.272 | +30-50% |
| TP3 | Fib extension 1.618 | +50-80% |

### Partial TP Strategy
- TP1 hit → Close 30%, move SL to breakeven
- TP2 hit → Close 40%
- TP3 hit → Close remaining 30%

## Phase 6: Futures Execution Checklist

```
[ ] Check max leverage for symbol (notional-and-leverage-brackets)
[ ] Set leverage (change-initial-leverage)
[ ] Set margin type ISOLATED (change-margin-type)
[ ] Check current price (symbol-price-ticker)
[ ] Calculate position size (2-3% risk)
[ ] Verify notional doesn't exceed bracket limit
[ ] Place entry order (MARKET or LIMIT)
[ ] Confirm fill (position-information-v3)
[ ] Place SL order (STOP_MARKET, reduceOnly=true)
[ ] Place TP orders (TAKE_PROFIT_MARKET, partial quantities)
[ ] Record entry details for monitoring
```

## Futures Availability Check
```bash
# Check if symbol has futures
curl -sf "https://fapi.binance.com/fapi/v1/ticker/price?symbol=INJUSDT"

# Check funding rate (negative = shorts pay longs = bullish bias)
curl -sf "https://fapi.binance.com/fapi/v1/fundingRate?symbol=INJUSDT&limit=3"

# Check open interest
curl -sf "https://fapi.binance.com/fapi/v1/openInterest?symbol=INJUSDT"
```
