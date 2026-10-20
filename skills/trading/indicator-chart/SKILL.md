---
name: indicator-chart
description: "Create interactive Plotly candlestick charts with technical indicators for crypto and forex. Supports EMA, RSI, MACD, Bollinger Bands, Supertrend, Ichimoku, Stochastic, ADX, OBV, VWAP, and more. Generates HTML charts from OHLC data."
tags: [trading, chart, candlestick, technical-analysis, plotly, crypto, forex]
---

# Indicator Chart

Create interactive Plotly candlestick charts with technical indicators overlaid.

## When to Use
- User asks to see a chart for any crypto or forex pair
- User wants visual TA (candlestick + indicators)
- Need to generate chart image or interactive HTML
- User asks to scan/find altcoins for entry
- User says "analyze X" for any crypto/forex pair

## User Workflow Preference
**ALWAYS check global news FIRST** (via market-news-analyst skill) before presenting technical analysis. The user wants holistic analysis: News → Market Conditions → Chart → TA → Recommendation.

## CRITICAL: Timeframe Selection Rules

**The user explicitly corrected this — never violate:**

| Trading Mode | Analysis TFs | Entry TF | SL Range | Hold Time |
|---|---|---|---|---|
| **Futures (leveraged)** | 4H (trend) → 1H (confirm) → 15M (entry) | 5M–15M | 1–3% | Minutes to hours |
| **Spot (swing)** | 1D (trend) → 4H (confirm) | 4H–1D | 10–20% | Days to weeks |

**Rationale:**
- Futures with high leverage = tight SL mandatory → need lower TF for precision
- Daily TF gives SL too wide for leveraged positions (risk of liquidation)
- Spot has no liquidation risk → can use wider SL on higher TF

**Multi-Timeframe Top-Down Flow:**
```
Higher TF → Determine DIRECTION (trend bias: long or short)
Middle TF → Determine AREA (zone for entry)
Lower TF  → Determine TIMING (exact entry candle)
```

**NEVER entry against the higher TF direction.**

### Intraday Futures Scanning Workflow
1. Scan 25+ tokens on 4H: EMA7 vs EMA21, MACD histogram, RSI
2. Filter: 4H trend aligned + 1H confirms same direction
3. Entry: Wait for 15M pullback (RSI 40-55 for longs, 45-60 for shorts)
4. SL: 2x ATR on 15M timeframe (~1-2% from entry)
5. TP: 2x/4x/6x ATR (1:1, 1:2, 1:3 R:R)

See `references/intraday-futures-workflow.md` for full scoring system.

## Workflow

### Step 1: Fetch OHLC Data
Use Binance API (crypto) — no API key needed for market data:

```python
import urllib.request, json, numpy as np

def fetch_binance_ohlc(symbol="BTCUSDT", interval="1d", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())
```

### Step 2: Calculate Indicators
```python
def calc_ema(data, period):
    k = 2 / (period + 1)
    ema = [data[0]]
    for d in data[1:]:
        ema.append(d * k + ema[-1] * (1 - k))
    return np.array(ema)

def calc_rsi(closes, period=14):
    rsi_vals = np.full(len(closes), np.nan)
    deltas = np.diff(closes)
    for i in range(period, len(closes)):
        gains = [d for d in deltas[i-period:i] if d > 0]
        losses = [-d for d in deltas[i-period:i] if d < 0]
        avg_g = sum(gains)/period if gains else 0
        avg_l = sum(losses)/period if losses else 0.001
        rsi_vals[i] = 100 - (100 / (1 + avg_g/avg_l))
    return rsi_vals

def calc_macd(closes, fast=12, slow=26, signal=9):
    macd_line = calc_ema(closes, fast) - calc_ema(closes, slow)
    signal_line = calc_ema(list(macd_line), signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
```

### Step 3: Generate Chart (PNG)
```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
    row_heights=[0.55, 0.22, 0.23], vertical_spacing=0.04,
    subplot_titles=[f'{symbol} {interval}', 'RSI(14)', 'MACD'])

fig.add_trace(go.Candlestick(...), row=1, col=1)
fig.add_trace(go.Scatter(y=ema7, name='EMA7', line=dict(color='cyan')), row=1, col=1)
fig.add_trace(go.Scatter(y=ema21, name='EMA21', line=dict(color='orange')), row=1, col=1)
# RSI on row 2, MACD on row 3...

fig.update_layout(template='plotly_dark', height=700, xaxis_rangeslider_visible=False)
fig.write_image(f'/tmp/{symbol}_chart.png', width=1200, height=700, scale=2)
```

## Supported Indicators

### Overlay (on candlestick)
| Indicator | Type |
|-----------|------|
| EMA, SMA, WMA | Line overlay |
| Bollinger Bands | Fill-between bands |
| Supertrend | Color-coded line |
| Ichimoku | 5 lines + cloud |
| SAR | Dot markers |

### Subplot (separate panel)
| Indicator | Type |
|-----------|------|
| RSI | Line + 30/70 zones |
| MACD | Line + signal + histogram |
| Stochastic | K% + D% + 20/80 zones |
| ADX | DI+, DI-, ADX lines |
| Volume | Bar chart (green/red) |
| OBV | Cumulative line |

## Timeframe Codes (Binance)
| Interval | Code | Typical Lookback |
|----------|------|-----------------|
| 1 min | 1m | 7 days |
| 5 min | 5m | 30 days |
| 15 min | 15m | 90 days |
| 1 hour | 1h | 180 days |
| 4 hour | 4h | 365 days |
| Daily | 1d | 365 days |
| Weekly | 1w | 2 years |

## Pitfalls

### Kaleido v1+ requires Chrome
```python
import kaleido
kaleido.get_chrome_sync()  # Run once — downloads Chrome headless
```
`plotly_get_chrome` CLI hangs on non-interactive stdin. Use Python API.

### Venv isolation
Hermes agent venv may not see system packages. Always:
```bash
python3 -m pip install plotly kaleido numpy pandas
```

### urllib.request for minimal environments
No httpx needed — stdlib works fine for Binance public API.

## References
- `references/intraday-futures-workflow.md` — Full intraday scanning + scoring + position sizing for futures
- `references/altcoin-screening-workflow.md` — Spot swing screening workflow

## Scripts
- `scripts/generate_chart.py` — Multi-panel chart generation (candlestick + EMA + RSI + MACD) with PNG export
