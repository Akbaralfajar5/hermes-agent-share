# AITS Implementation Notes (Deployed 2026-05-02)

## Live Script Location
`/home/ubuntu/aits_engine.py` — ~24KB Python script

## Key Functions

| Function | Purpose |
|---|---|
| `get_klines(symbol, interval, limit, mainnet)` | Fetch candle data (tries mainnet first, fallback testnet) |
| `find_swing_points(highs, lows, lookback)` | Detect swing highs/lows (fractal-based) |
| `detect_structure(swing_highs, swing_lows)` | BOS/CHoCH detection → trend + confidence |
| `find_order_blocks(...)` | Identify institutional S/D zones |
| `calc_fibonacci(swing_high, swing_low, direction)` | Fib levels + OTE zone + extensions |
| `calc_vwap(highs, lows, closes, volumes)` | Volume-weighted average price |
| `detect_volume_divergence(closes, volumes)` | Price/volume divergence detection |
| `detect_liquidity_sweep(...)` | Stop-hunt / wick rejection detection |
| `analyze_aits(symbol, mainnet=True)` | Full multi-TF analysis for one symbol |
| `score_setup(tf_results, direction)` | Score 0-100 with factor breakdown |
| `generate_entry(symbol, tf_results, direction)` | Calculate entry/SL/TP from Order Blocks |
| `scan_and_execute(btc_bias, risk_rating, wallet, max_pos, current_pos)` | Full scan + filter + return top setups |

## Swing Lookback Per Timeframe
- 4H: 7 candles (~28 hours)
- 1H: 5 candles (~5 hours)
- 15M: 5 candles (~75 minutes)
- 5M: 3 candles (~15 minutes)

## Order Block Strength Calculation (0-1)
- Volume at origin vs 20-period average: 30%
- Departure speed (impulsive move): 25%
- Freshness (untested = 0.2, tested once = 0.1): 20%
- Base score: 15%
- Zone size relative to ATR (smaller = better): 10%

## Order Block Validity Rules
- Invalid if price closes THROUGH the zone (not just wicks into it)
- Invalid if tested more than 2 times (diminishing returns)
- Must have impulsive move > 1.5x ATR after the OB candle
- Must have >50% candles in move direction (confirms impulsive, not gradual)

## SL/TP Logic
- **SL:** Below/above Order Block zone + 0.1x ATR buffer
- **TP1:** 2x risk (R:R 1:2)
- **TP2:** 3x risk or Fibonacci -0.618 extension
- **TP3:** 5x risk or Fibonacci -1.618 extension
- Adjusted by opposing zones (TP capped at nearest opposing OB)

## Testnet Limitations Encountered
- `BTCDOMUSDT`: PERCENT_PRICE filter error (price deviation too large)
- `BBUSDT`: Quantity greater than max quantity
- `BNBUSDT`: Exceeded maximum allowable position at current leverage
- Some pairs have very low max position sizes on testnet

## Integration with Cronjob
The cronjob imports from `/home/ubuntu/aits_engine.py` directly:
```python
import sys
sys.path.insert(0, '/home/ubuntu')
from aits_engine import *
```

## User Target
- Win rate: **80-90%** (benchmark for migration to real account)
- Testing period: 3 days starting 2026-05-02
- If target met → migrate to real Binance account with real funds
