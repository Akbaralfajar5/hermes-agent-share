# FibStruct v2 — Safety Filters & SL Fix Patterns (June 2026)

> **SUPERSEDED by SND Engine v3** (June 21, 2026). See `references/snd-snr-zone-engine.md`.
> Engine: `~/snd_engine.py`, screen `snd_engine`. Old fibstruct_engine.py archived, screen killed.
> Safety filters below are INHERITED by v3 — still relevant.

Engine: `~/fibstruct_engine.py` (archived), screen `fibstruct` (killed).
Config: 5% margin, max 3 pos, score≥4/5, RR≥1:2, vol≥$10M, 178 pairs.

## Safety Filters (post-crash, added June 19 2026)

Three filters added to `analyze_symbol()` to prevent entries during adverse conditions:

### 1. 15M Trend Filter
Skip LONG if price dropped >1% from 15M high. Skip SHORT if rallied >1% from 15M low.
```python
highs_15m = [float(k[2]) for k in klines_15m[-12:]]  # last 3 hours
high_15m = max(highs_15m)
if direction == 'BULLISH':
    drop = (high_15m - price) / high_15m * 100
    if drop > 1.0:
        return None  # skip LONG
```

### 2. 1H Falling Knife Filter
Skip LONG if price dropped >2% from 1H high. Skip SHORT if rallied >2% from 1H low.
```python
highs_1h = [float(k[2]) for k in klines_1h[-6:]]  # last 6 hours
high_1h = max(highs_1h)
if direction == 'BULLISH':
    drop = (high_1h - price) / high_1h * 100
    if drop > 2.0:
        return None  # falling knife, skip
```

### 3. Volume Anomaly Filter
Skip if latest 5M volume >5x average (institutional activity).
```python
vol_5m = [float(k[5]) for k in klines_5m[-20:]]
avg_vol = sum(vol_5m[:-1]) / len(vol_5m[:-1])
if vol_5m[-1] / avg_vol > 5.0:
    return None  # volume spike
```

**PITFALL**: Filters run AFTER direction is determined but BEFORE scoring. Place them between `direction = struct_4h` and `score = 0`.

## SL Recalculation Fix (June 19 2026)

**Bug**: SL order used `signal['sl']` (from analysis price) instead of recalculating from actual `entry_price`. Slippage moved entry, making SL too tight (0.09% instead of 2%).

**Fix**: Recalculate SL from `entry_price` after fill:
```python
# LONG
sl = min(signal_sl, entry_price * 0.98)  # at least 2% below entry
# SHORT
sl = max(signal_sl, entry_price * 1.02)  # at least 2% above entry
```

**PITFALL**: Must update BOTH the SL order AND the state dict. Two places to patch, not one.

## ATR Buffer Fix

Changed from `atr * 0.1` → `atr * 0.5` for SL buffer. 0.1 was too tight for altcoin volatility.

## Mutable Default Params Bug

`api_get()` and `api_post()` had `params={}` as default argument. Python reuses the same dict object, causing parameter contamination between calls. `get_balance()` returned $0.00 because stale params from previous call leaked in.

**Fix**: `params=None` with `if params is None: params = {}` at function start.

**PITFALL**: Never use mutable default arguments (`{}`, `[]`) in Python functions that get called repeatedly. Always use `None` sentinel pattern.

## Debug Logging

Added to `scan_fibstruct()`: near-miss logging (score 3/5), balance check logging, scan progress logging. Helps diagnose why signals are/aren't triggering.

## Files
- `~/fibstruct_engine.py` — main engine (~955 lines, heavily patched)
- `~/fibstruct.log` — engine log (duplicate lines = stdout+stderr redirect)
- `~/fibstruct_state.json` — active positions state
