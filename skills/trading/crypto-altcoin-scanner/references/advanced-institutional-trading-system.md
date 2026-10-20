# Advanced Institutional Trading System (AITS)

## Planned Upgrade from Basic EMA/RSI/MACD to Smart Money Methodology

### Current Method (Basic — in production)
- EMA 20/50 trend direction (lagging)
- RSI 14 momentum (many false signals in trending)
- MACD 12,26 momentum (lagging, whipsaw in sideways)
- HH/HL vs LH/LL structure (correct concept, imprecise)
- Score 3/4 TF aligned for entry

### Upgraded Method (AITS — to implement)

Combines 5 advanced techniques for institutional-grade analysis:

#### 1. Market Structure via SMC (replaces EMA trend)
- **BOS (Break of Structure)** — continuation signal, replaces EMA cross
- **CHoCH (Change of Character)** — reversal signal, much earlier than EMA cross
- Uses swing point detection with fractal-based lookback per TF:
  - 4H: lookback=7, 1H: lookback=5, 15M: lookback=5, 5M: lookback=3
- **Leading** indicator vs EMA which is lagging

#### 2. Supply & Demand Zones / Order Blocks (replaces generic S/R)
- **Bullish OB (Demand):** Last bearish candle before impulsive move UP that caused BOS
- **Bearish OB (Supply):** Last bullish candle before impulsive move DOWN that caused BOS
- Zone = candle range (low to high)
- **Fresh zones** (untested) are strongest
- Zones become invalid after 3+ tests or full penetration
- Strength scoring: volume (30%), departure speed (25%), freshness (20%), CHoCH association (15%), zone size (10%)

#### 3. Fibonacci OTE (Optimal Trade Entry)
- OTE Zone = 0.618 - 0.786 retracement of impulsive move
- **Confluence with Order Block** = highest probability entry
- Premium zone (above 50%) = sell zone
- Discount zone (below 50%) = buy zone
- Extensions for TP: -0.618 (TP1), -1.000 (TP2), -1.618 (TP3)

#### 4. Volume Profile + VWAP (confirmation layer)
- **POC (Point of Control):** Highest volume price = fair value / magnet
- **VAH/VAL:** Value Area boundaries = S/R
- **HVN:** High volume nodes = consolidation zones
- **LVN:** Low volume nodes = price moves fast through these
- **VWAP:** Institutional benchmark — above = bullish bias, below = bearish
- Volume divergence detection: price up + volume down = bearish divergence

#### 5. Liquidity Sweeps / Stop Hunts (manipulation detection)
- Liquidity pools at: equal highs/lows, swing points, round numbers
- **Sweep = wick through level + close back inside** (rejection)
- Confirmed sweep + reversal candle = high-probability entry
- AMD Cycle: Accumulation → Manipulation (sweep) → Distribution (real move)

### Multi-TF Framework (AITS)

```
4H  → BIAS (BOS/CHoCH determines direction)
       ↓
1H  → CONFIRMATION (structure alignment + VWAP position)
       ↓
15M → SETUP ZONE (Order Block + Fibonacci OTE + confluence mapping)
       ↓
5M  → TRIGGER (CHoCH inside zone + volume spike = entry)
```

### Entry Criteria (all must be met)
1. 4H bias clear (BOS/CHoCH, not ranging)
2. 1H structure aligned with 4H
3. 15M has fresh Order Block in discount/premium zone
4. OB overlaps with Fibonacci 0.618-0.786 (confluence)
5. 5M shows CHoCH inside the zone (trigger)
6. Volume spike on trigger candle

### SL/TP (AITS)
- **SL:** Below/above Order Block + small ATR buffer (much tighter than ATR-only method)
- **TP1:** Nearest opposing zone or 1:2 R:R
- **TP2:** Fibonacci -0.618 extension or 1:3 R:R
- **TP3:** Fibonacci -1.618 extension or 1:5 R:R

### Expected Performance Improvement
| Metric | Basic Method | AITS |
|---|---|---|
| Win Rate | ~50-55% | ~60-68% |
| Risk:Reward | 1:1.5 | 1:3 - 1:5 |
| SL Width | Wide (ATR-based) | Tight (zone-based) |
| False Signals | Many | Minimal (multi-confluence) |
| Entry Precision | Low | High |

### Implementation Status
- [ ] Market Structure analyzer (BOS/CHoCH detection)
- [ ] Supply & Demand zone detector (Order Blocks)
- [ ] Fibonacci calculator with OTE zones
- [ ] Volume Profile + VWAP calculator
- [ ] Liquidity sweep detector
- [ ] Multi-TF confluence engine
- [ ] Quality scoring system (0-100)
- [ ] Integration with cronjob auto-entry

### Key Python Classes (designed, not yet deployed)
- `MarketStructureAnalyzer` — swing points, BOS/CHoCH detection
- `SupplyDemandDetector` — Order Block identification and scoring
- `FibonacciCalculator` — retracement/extension with OTE zones
- `VolumeAnalyzer` — Volume Profile, VWAP, divergence detection
- `LiquidityAnalyzer` — pool identification, sweep detection
- `MultiTimeframeEngine` — orchestrates all components, generates TradeSetup objects
