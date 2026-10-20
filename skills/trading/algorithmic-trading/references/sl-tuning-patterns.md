# SL Tuning Patterns & Pitfalls for Trading Engines

## ⚠️ Critical Pitfall: SL-RR Interaction

When you widen SL distance (increase ATR buffer, add minimum SL %), the risk-reward ratio DROPS for the same TP targets. If your engine has a MIN_RR filter (e.g. 1:2), wider SL can silently kill ALL signals.

**Example:**
- Entry: $100, TP target: $104 (4% away)
- Old SL: $99.40 (0.6% away) → RR = 4/0.6 = 6.7 → ✅ passes 1:2 filter
- New SL: $98.00 (2% away) → RR = 4/2 = 2.0 → ⚠️ barely passes
- New SL: $97.50 (2.5% away) → RR = 4/2.5 = 1.6 → ❌ fails 1:2 filter

**Rule:** When adjusting SL parameters, ALWAYS verify that realistic TP targets still produce RR ≥ MIN_RR.

## SL Parameter Tuning Checklist

1. **ATR buffer multiplier** — controls SL distance from structure level
   - 0.1: Very tight (scalping, high-liquidity pairs)
   - 0.3: Moderate (BTC/ETH)
   - 0.5: Normal (altcoins with wicks)
   - 1.0: Wide (very volatile, low-liquidity)

2. **Minimum SL distance** — hard floor as % of entry
   - Altcoins: 1.5–2% minimum
   - BTC/ETH: 0.5–1% minimum
   - Enforcement: `if abs(entry - sl) < entry * min_pct: sl = entry ± entry * min_pct`

3. **After any SL change, verify:**
   - RR calculation still produces values ≥ MIN_RR
   - If signals disappear, check near-misses first (see debug logging below)

## Debug Logging: Near-Miss Pattern

When a trading engine produces NO signals after parameter changes, add near-miss logging to diagnose why. Track signals that almost pass the filter (score ≥ 3 but below threshold, or RR close to minimum).

```python
def scan_with_debug():
    pairs = refresh_pairs()
    results = []
    near_miss = []  # track almost-passing signals

    for symbol in pairs:
        analysis = analyze_symbol(symbol)
        if not analysis:
            continue
        if analysis['score'] >= MIN_SCORE and analysis['rr'] >= MIN_RR:
            results.append(analysis)
        elif analysis['score'] >= 3:  # near miss threshold
            near_miss.append(analysis)

    # Log near-misses when nothing passes filter
    if not results and near_miss:
        near_miss.sort(key=lambda x: (x['score'], x['rr']), reverse=True)
        top3 = near_miss[:3]
        details = []
        for nm in top3:
            sl_dist = abs(nm['entry'] - nm['sl']) / nm['entry'] * 100
            details.append(
                f"{nm['symbol']} {nm['direction']} "
                f"score={nm['score']}/5 rr=1:{nm['rr']:.1f} sl={sl_dist:.1f}%"
            )
        log(f"🔍 No signal passed. Near-misses: {' | '.join(details)}")

    results.sort(key=lambda x: (x['score'], x['rr']), reverse=True)
    return results
```

**What to look for in near-miss output:**
- `rr=1:1.8` with `sl=2.5%` → SL too wide for TP target, consider reducing MIN_RR or TP needs to be further
- `score=3/5` → Structure is there but missing confluence (sweep, PA trigger, fib level)
- `sl=0.8%` → SL still too tight despite buffer increase

## ⚠️ Critical Bug: SL Order Price vs Entry Price (June 2026)

**The bug:** Engine calculates SL based on `signal['sl']` (analysis/structure price), then places the SL stop-order at that price. But the actual fill price (`entry_price` from the order response) can differ significantly due to slippage, especially on volatile altcoins and low-liquidity pairs.

**Real-world example (CHZUSDT SHORT):**
- Analysis price: $0.03850, SL set at $0.03980 (3.4% away → good)
- Actual fill price: $0.03967 (slippage on entry)
- SL stopPrice was $0.03980 → only 0.3% from fill price
- Result: instant SL hit on normal market noise, -$0.02 loss (0.09%)

**Root cause:** Two different prices being used:
```python
# ❌ BUG — SL uses signal price, not fill price
entry_price = float(order['avgPrice'])  # actual fill
sl = signal['sl']  # ← calculated from analysis price, NOT fill
place_sl_order(symbol, sl)  # SL is closer than intended
```

**Fix:** Recalculate SL from actual fill price with minimum distance enforcement:
```python
entry_price = float(order['avgPrice'])  # actual fill
sl_raw = signal['sl']  # structure-based SL
sl_dist = abs(entry_price - sl_raw) / entry_price
min_sl_pct = 0.02  # 2% minimum

if sl_dist < min_sl_pct:
    if signal['direction'] == 'LONG':
        sl = entry_price * (1 - min_sl_pct)
    else:
        sl = entry_price * (1 + min_sl_pct)
    log(f"⚠️ SL adjusted to {min_sl_pct*100}% from fill: {sl}")
else:
    sl = sl_raw

place_sl_order(symbol, sl)  # SL now correct distance from fill
```

**Also update:** State file and return values must use the adjusted `sl`, not `signal['sl']`. If you store `signal['sl']` in state but place the adjusted SL, monitoring shows wrong values.

**When this matters most:**
- Low-cap tokens with wide spreads (CHZ, MEME, 1000PEPE)
- Fast-moving markets where fill slippage is >1%
- Market orders (limit orders have less slippage risk)
- Short positions (price moving up between signal and fill)

## Pre-Entry Safety Filters (Post-Crash Pattern, June 2026)

When a trading engine has SL hits on normal market noise (not just SL too tight), the root cause is often **entering during adverse micro-conditions**. Three filters that block entries before they happen:

### Filter 1: 15M Trend Rejection
Block LONG if price dropped >1% from 15M high (last 3 hours). Block SHORT if rallied >1% from 15M low.

**Why:** A 1% drop on 15M timeframe means the move already happened — entering LONG here is chasing. Altcoins can wick 2-3% in minutes.

```python
highs_15m = [float(k[2]) for k in klines_15m[-12:]]  # last 3 hours
lows_15m = [float(k[3]) for k in klines_15m[-12:]]
high_15m = max(highs_15m)
low_15m = min(lows_15m)

if direction == 'BULLISH':
    drop_pct = (high_15m - price) / high_15m * 100
    if drop_pct > 1.0:
        return None  # skip LONG
else:
    rally_pct = (price - low_15m) / low_15m * 100
    if rally_pct > 1.0:
        return None  # skip SHORT
```

### Filter 2: 1H Falling Knife / Short Squeeze
Block LONG if price dropped >2% from 1H high (last 6 hours). Block SHORT if rallied >2% from 1H low.

**Why:** 2% drop on 1H = established downtrend on lower timeframe. 4H structure says bullish, but 1H says "wait for stabilization." This is the classic "catching a falling knife" scenario.

```python
highs_1h = [float(k[2]) for k in klines_1h[-6:]]
lows_1h = [float(k[3]) for k in klines_1h[-6:]]
high_1h = max(highs_1h)
low_1h = min(lows_1h)

if direction == 'BULLISH':
    drop_pct = (high_1h - price) / high_1h * 100
    if drop_pct > 2.0:
        return None  # falling knife
else:
    rally_pct = (price - low_1h) / low_1h * 100
    if rally_pct > 2.0:
        return None  # short squeeze
```

### Filter 3: Volume Anomaly
Block entry if latest 5M candle volume is >5x the 20-candle average.

**Why:** Volume spikes indicate institutional activity, liquidation cascades, or news events. Entering during these is gambling, not trading. Let the dust settle.

```python
vol_5m = [float(k[5]) for k in klines_5m[-20:]]
avg_vol = sum(vol_5m[:-1]) / len(vol_5m[:-1])
latest_vol = vol_5m[-1]
vol_ratio = latest_vol / avg_vol if avg_vol > 0 else 0

if vol_ratio > 5.0:
    return None  # volume spike, skip
```

### Placement in Analysis Pipeline
These filters go AFTER structure analysis (4H/1H direction determined) but BEFORE scoring/trigger detection. This saves API calls — reject early, don't compute Fib/Sweep/PA for signals that will be blocked anyway.

```
get klines → analyze_structure (4H, 1H) → determine direction
    → SAFETY FILTERS (15M trend, 1H knife, volume)  ← HERE
    → score (Fib, trendline, sweep, PA)
    → SL/TP calculation
```

### Tuning Thresholds
| Filter | Conservative | Default | Aggressive |
|--------|-------------|---------|------------|
| 15M trend | 0.5% | 1.0% | 1.5% |
| 1H knife | 1.5% | 2.0% | 3.0% |
| Volume | 3x | 5x | 8x |

Conservative = fewer entries, higher win rate. Aggressive = more entries, more noise.

### ⚠️ Warning: Filters Can Kill All Signals
If market is trending hard (BTC pumping/dumping), ALL altcoins will show 15M/1H drops/rallies simultaneously. If engine produces zero entries for hours, check if filters are too tight. Add debug logging:

```python
log(f"⚠️ {symbol} SKIP: 15M drop {drop_pct:.1f}% from high (LONG blocked)")
log(f"⚠️ {symbol} SKIP: 1H falling knife {drop_pct:.1f}% drop (LONG blocked)")
log(f"⚠️ {symbol} SKIP: Volume spike {vol_ratio:.1f}x avg (blocked)")
```

## FibStruct v2 Reference Parameters (as of June 2026)

- ATR buffer: 0.5 (was 0.1 — changed due to wick hits on altcoins)
- Min SL distance: 2% (was none — added as hard floor)
- SL recalculation: based on entry_price, not signal price (prevents slippage-induced instant SL)
- Min RR: 1:2
- Min score: 4/5
- Volume filter: $10M
- **Pre-entry filters:**
  - 15M trend rejection: >1% drop blocks LONG, >1% rally blocks SHORT
  - 1H falling knife: >2% drop blocks LONG, >2% rally blocks SHORT
  - Volume anomaly: >5x average blocks entry
- Engine: `/home/ubuntu/fibstruct_engine.py`
- Screen: `fibstruct`
- Log: `/home/ubuntu/fibstruct.log`

## SL Placement Priority (FibStruct)

1. **Liquidity sweep level** ± ATR * 0.5 (best — catches sweep reversal)
2. **Fib 0.786 level** ± ATR * 0.3 (good — structure-based)
3. **Price ± ATR * 1.5** (fallback — no structure available)
4. **Hard minimum**: 2% from entry (enforced after above calculations)

## 🐍 Python Pitfall: Mutable Default Arguments in API Wrappers

**THE silent killer of trading engines.** Classic Python bug that causes zero-error-message failures.

```python
# ❌ BUG — shares ONE dict across ALL calls
def api_get(endpoint, params={}):
    params['timestamp'] = int(time.time() * 1000)
    params['signature'] = sign(params)
    r = requests.get(url, params=params)
    return r.json()

# ✅ FIX
def api_get(endpoint, params=None):
    if params is None:
        params = {}
    params['timestamp'] = int(time.time() * 1000)
    params['signature'] = sign(params)
    r = requests.get(url, params=params)
    return r.json()
```

**Why it's deadly in trading engines:**
- Works perfectly in one-shot tests (`python3 -c "..."`)
- Fails silently in production daemons (params bleed between calls)
- `get_balance()` returns $0.00 because old timestamp/signature from previous call contaminates
- Engine thinks balance is empty → scan never runs → zero entries, zero errors logged
- Symptoms look like "engine works but never opens trades"

**Detection:** If engine runs (periodic logs show) but core function never triggers, audit ALL `def` signatures for `={}` or `=[]`.

**Also fix `api_post` the same way.** Both GET and POST wrappers need `params=None`.

## Engine Silent Failure: Progressive Diagnostic Logging

When a trading engine runs but never enters trades, add logging in layers:

```python
# Layer 1: Balance/positions (guard conditions)
log(f"💰 Balance: avail=${available:.2f} | Pos: {current_pos}/{MAX}")

# Layer 2: Scan progress
log(f"🔍 Scanning {len(pairs)} pairs...")
signals = scan()
log(f"🔍 Scan done: {len(signals)} signal(s) passed")

# Layer 3: Near-misses (why nothing passes filter)
if not results and near_miss:
    top3 = sorted(near_miss, key=lambda x: x['rr'], reverse=True)[:3]
    details = [f"{n['sym']} score={n['score']} rr=1:{n['rr']:.1f}" for n in top3]
    log(f"🔍 Near-misses: {' | '.join(details)}")
```

**Order of investigation:**
1. Is the scan even running? (Layer 2 log missing → guard condition false)
2. Is balance/positions correct? (Layer 1 log shows $0 → API bug)
3. Are signals passing filter? (Layer 3 log shows near-misses → adjust params)
4. Is entry execution working? (signals found but no ENTRY log → order API issue)
