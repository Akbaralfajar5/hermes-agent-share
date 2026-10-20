# SND/SNR Zone Engine v3 — Trading Strategy Reference

> **Replaced FibStruct v2** (June 21, 2026). Old fibstruct_engine.py archived, screen killed.

Engine: `~/snd_engine.py`, screen `snd_engine`, state `~/snd_state.json`
Config: 5% margin, max 3 pos, score≥4/6, RR≥1:2, vol>$10M

## Strategy: Support & Resistance + Supply & Demand Zones

### Analysis Pipeline (4 timeframes)

1. **4H: Market Structure** → determine bias (BULLISH/BEARISH/NEUTRAL)
   - HH+HL = BULLISH, LH+LL = BEARISH
   - NEUTRAL = skip (no trade)

2. **4H: S/R Levels** → horizontal support/resistance from swing points
   - Cluster nearby levels (within 0.5%)
   - Track touch count, S/R flips (level that was both support AND resistance)

3. **1H: S/D Zone Detection** → supply and demand zones
   - Supply: rally → base (small body <40% of range) → drop
   - Demand: drop → base → rally
   - Score: freshness (untested > tested), tightness (<1.5% range), volume on departure

4. **15M: Proximity Check** → is price near a zone or S/R level?

5. **5M: Entry Trigger** → candlestick confirmation
   - ENGULF: engulfing candle in trade direction
   - PIN_BAR: rejection wick (>2x body, >60% of range)
   - MOMENTUM: body >70% of range
   - SR_FLIP: price crossed S/R and closed on other side
   - ZONE_BOUNCE: price touched zone and closed away

### Scoring (max 6 points, need ≥4)

| # | Condition | Points |
|---|-----------|--------|
| 1 | 4H structure aligned | +1 |
| 2 | Price at valid S/D zone | +1 |
| 3 | Zone is fresh (untested) | +1 |
| 4 | Zone has strong formation (≥2/3) | +1 |
| 5 | S/R level confirms | +1 |
| 6 | Entry trigger on 5M | +1 |

### SL/TP Calculation

- **SL**: Below demand zone (or support) minus ATR*0.5 for LONG; above supply zone (or resistance) plus ATR*0.5 for SHORT
- **Min SL distance**: 2% from entry
- **TP1**: 2R (risk-reward 1:2)
- **TP2**: 3R OR nearest opposing zone/SR (whichever is closer)
- **TP3**: 4R

### Safety Filters (inherited from FibStruct v2)

1. **15M Trend Filter**: Skip LONG if price dropped >1% from 15M high; skip SHORT if rallied >1%
2. **1H Falling Knife Filter**: Skip LONG if dropped >2% from 1H high; skip SHORT if rallied >2%
3. **Volume Anomaly**: Skip if latest 5M volume >5x average

## Key Differences from FibStruct v2

| Aspect | FibStruct v2 | SND v3 |
|--------|-------------|--------|
| Primary signal | Fibonacci OTE (0.618-0.786) | S/D zones (rally-base-drop) |
| Trendline | Required | Removed |
| BOS/CHoCH | Primary structure | Simplified to HH/HL/LH/LL |
| S/R | Not used | Horizontal S/R from swing points |
| Entry trigger | Liquidity sweep + PA | 5 trigger types (engulf, pin, momentum, SR flip, zone bounce) |
| TP target | Fib extensions | Nearest opposing zone/SR |
| Max score | 5 | 6 |

## Pitfalls

1. **Zone detection needs volume**: Without volume data on the departure candle, zone strength scoring is weaker. The vol_ratio check helps but isn't perfect.

2. **Fresh zones are rare**: Most detected zones are already tested. Score bonus for freshness means most signals score 4-5, rarely 6.

3. **S/R flip is the strongest signal**: When a level that was resistance becomes support (or vice versa), it's the highest-confidence entry. Prioritize these.

4. **ATR buffer matters**: Using ATR*0.5 for SL buffer. Too tight (0.1) gets stopped out by noise. Too wide (1.0) reduces RR.

5. **Python mutable default args**: Never use `params={}` in function defaults. Use `params=None` with `if params is None: params = {}`.

## Files

- `~/snd_engine.py` — main engine (~400 lines)
- `~/snd_engine.log` — engine log
- `~/snd_state.json` — active positions state
- `~/fibstruct_engine.py` — archived v2 engine (screen killed)
