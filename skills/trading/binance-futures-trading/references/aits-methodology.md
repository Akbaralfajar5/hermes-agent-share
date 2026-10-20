# Advanced Institutional Trading System (AITS)

## Overview

AITS replaces the basic EMA/RSI/MACD scoring method with institutional-grade analysis. The basic method was found to be too lagging and produced too many false signals (~50-55% win rate). AITS targets 60-68% win rate with 1:3-1:5 R:R.

## Why Basic Method Failed

| Indicator | Problem |
|---|---|
| EMA 20/50 | Lagging — signals come AFTER the move |
| RSI 14 | Too many false signals in trending markets |
| MACD (12,26) | Lagging, whipsaws in sideways |
| HH/HL scoring | Correct concept but lacks precision |

## AITS Components

### 1. Market Structure (SMC) — Replaces EMA for Trend
- **BOS (Break of Structure)** — Continuation signal (price breaks last swing H/L in trend direction)
- **CHoCH (Change of Character)** — Reversal signal (price breaks last swing H/L AGAINST trend)
- Leading indicator, not lagging like EMA crossovers
- Swing point detection uses fractal-based lookback (4H=7, 1H=5, 15M=5, 5M=3)

### 2. Supply & Demand Zones (Order Blocks) — Replaces RSI for Entry
- **Bullish OB (Demand)** = Last bearish candle before impulsive move UP that caused BOS
- **Bearish OB (Supply)** = Last bullish candle before impulsive move DOWN that caused BOS
- Entry at these zones = entering where institutions placed orders
- Much more precise than "RSI oversold = buy"

### 3. Fibonacci OTE (Optimal Trade Entry) — Precision Layer
- OTE Zone = 0.618 - 0.786 retracement of last impulse
- When OTE overlaps with Order Block = HIGH CONFLUENCE entry
- Extensions (-0.618, -1.0, -1.618) used for TP targets

### 4. Volume Profile + VWAP — Confirmation
- VWAP position (above = bullish bias, below = bearish bias)
- Volume divergence detection (price up + volume down = bearish divergence)
- Replaces simple "volume spike" check

### 5. Liquidity Sweep Detection — Edge
- Identifies where stop losses cluster (above swing highs, below swing lows)
- Detects when price sweeps these levels then reverses (stop hunt)
- Entry AFTER sweep = entering with smart money post-manipulation

### 6. Liquidation Heatmap (CoinGlass) — Macro Confirmation
- Source: https://www.coinglass.com/pro/futures/LiquidationHeatMap?coin=BTC
- Yellow zones = high concentration of liquidation levels
- Cluster ABOVE price = short liquidations (price magnet upward)
- Cluster BELOW price = long liquidations (price magnet downward)
- Used as CONFIRMATION, not primary signal

## Multi-Timeframe Framework

```
4H  → BIAS (BOS/CHoCH determines bullish/bearish/ranging)
      Output: Direction + Confidence (0-1)
       ↓
1H  → CONFIRMATION (Structure alignment + VWAP position)
      Output: Aligned / Not Aligned
       ↓
15M → SETUP ZONE (Order Block identification + Fibonacci OTE)
      Output: Exact entry zone + zone strength
       ↓
5M  → TRIGGER (CHoCH inside zone + volume spike)
      Output: Entry signal + exact SL placement
```

## Scoring System (0-100)

| Factor | Max Points | Source |
|---|---|---|
| 4H Bias alignment | 25 | Market Structure (BOS/CHoCH) |
| 1H Confirmation | 20 | Structure + VWAP |
| 15M Order Block quality | 20 | OB strength (freshness, volume, departure speed) |
| VWAP alignment | 10 | Price vs VWAP |
| Volume confirmation | 10 | Divergence / healthy trend |
| 5M Trigger | 10 | Structure + momentum |
| Liquidity sweep bonus | 5 | Recent sweep detected |

**Minimum score for entry: 60/100**
**Minimum R:R: 1:2**

## SL/TP Placement (AITS vs Basic)

### Basic Method (old):
- SL = 1.2x ATR from entry (arbitrary distance)
- TP = fixed R:R multiples (1.5x, 2.5x, 3.5x risk)

### AITS Method (new):
- **SL** = Below/above Order Block zone + small ATR buffer (0.1x ATR)
  - Much tighter because OB is a precise institutional level
  - If price breaks through OB, the setup is truly invalid
- **TP1** = 1:2 R:R or nearest opposing zone (whichever is closer)
- **TP2** = 1:3 R:R or Fibonacci extension -0.618
- **TP3** = 1:5 R:R or Fibonacci extension -1.618

## Implementation

Script location: `/home/ubuntu/aits_engine.py`

Key functions:
- `analyze_aits(symbol)` — Full multi-TF AITS analysis
- `score_setup(tf_results, direction)` — Score a setup 0-100
- `generate_entry(symbol, tf_results, direction)` — Calculate entry/SL/TP
- `scan_and_execute(btc_bias, risk_rating, wallet, max_pos, current_pos)` — Full scan + execute

## Weekend Filter

Since BTC ETF approval (Jan 2024), crypto markets behave more like TradFi:
- Weekday: High volume, institutional activity, reliable signals
- Weekend: Low volume (50-70% less), wide spreads, fake moves

**Filter rules:**
- **Monday-Friday:** Normal operation, entry allowed
- **Saturday-Sunday:** MONITOR ONLY — no new entries
  - Exception 1: DANGER news + SHORT score ≥75
  - Exception 2: Clear liquidity sweep + score ≥80
- SL/TP management continues 24/7 regardless of day

**Preferred entry days:** Monday (institutions open positions), Wednesday (mid-week rebalancing), Friday (options expiry, rebalancing)
