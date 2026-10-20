# Live PnL Display & Auto-Learn System

Session: May 2026 — fixes Telegram PnL showing peak (high_water_mcap) instead of live price.

## Problem

Telegram bot showed unrealized PnL based on `high_water_mcap` — the highest mcap the token ever reached. This hid rugs: token pumps to +100%, then rugs to -90%, but Telegram still shows +100%.

Dashboard (`charon-dashboard`) already used live Jupiter prices. Telegram was inconsistent.

## Solution: Live Jupiter Price Cache

### New helper in `src/enrichment/jupiter.js`

```js
function getCachedAssetPrice(mint) {
  const cached = jupiterAssetCache.get(mint);
  const data = cached?.data;
  if (!data) return null;
  return {
    mint,
    usdPrice: Number(data.usdPrice || 0) || null,
    mcap: Number(data.mcap || data.fdv || 0) || null,
    liquidity: Number(data.liquidity || 0) || null,
    symbol: data.symbol || null,
    name: data.name || null,
    at: cached.at || null,
    stale_ms: cached.at ? now() - cached.at : null,
  };
}

// Add to exports
export { ..., getCachedAssetPrice };
```

The cache is populated by `monitorPositions()` every 15 seconds — non-blocking read.

### Helper in `src/telegram/menus.js`

```js
import { getCachedAssetPrice } from '../enrichment/jupiter.js';

function livePositionPnlSol(p) {
  const entry = Number(p.entry_mcap) || 0;
  if (entry <= 0) return 0;
  const live = getCachedAssetPrice(p.mint);
  let ref;
  if (live && Number.isFinite(live.mcap) && live.mcap > 0) {
    ref = live.mcap;
  } else if (live && Number.isFinite(live.usdPrice) && live.usdPrice > 0 && Number(p.entry_price) > 0) {
    return Number(p.size_sol) * ((live.usdPrice / Number(p.entry_price)) - 1);
  } else {
    // Cache empty — use entry (shows 0 PnL), NOT high_water (hides rug)
    ref = entry;
  }
  const pct = (ref / entry - 1) * 100;
  return Number(p.size_sol) * (pct / 100);
}
```

Same helper added to `src/telegram/commands.js`.

### Helper in `src/telegram/format.js`

```js
import { getCachedAssetPrice } from '../enrichment/jupiter.js';

function liveRefMcap(position) {
  const entryMcap = Number(position.entry_mcap) || 0;
  const live = getCachedAssetPrice(position.mint);
  if (live && Number.isFinite(live.mcap) && live.mcap > 0) return live.mcap;
  if (live && Number.isFinite(live.usdPrice) && live.usdPrice > 0
      && Number(position.entry_price) > 0 && entryMcap > 0) {
    return entryMcap * (live.usdPrice / Number(position.entry_price));
  }
  return entryMcap;
}
```

### Files patched

1. `src/enrichment/jupiter.js` — add `getCachedAssetPrice()` + export
2. `src/telegram/menus.js` — import helper, add `livePositionPnlSol()`, replace loops in `mainMenuText()` and `positionsText()`
3. `src/telegram/format.js` — import helper, add `liveRefMcap()`, replace `high_water_mcap` references in `formatPosition()` and `formatPositionCompact()`
4. `src/telegram/commands.js` — import helper, add `livePositionPnlSol()`, replace loop in positions command

### Key principle

**Fallback to entry_mcap, NOT high_water_mcap.** If Jupiter cache is empty (token just opened, not yet pinged), show 0% PnL rather than fake peak PnL.

---

## Hourly Auto-Learn Cron

Script: `~/.hermes/scripts/charon_hourly_audit.py`
Cron job ID: `0e0c97420f2e`
Schedule: every 60 minutes

### What it does

1. Pulls closed trades from last 1h and 24h
2. Calculates stats: WR, avg PnL, by route, by mcap bucket, by exit reason
3. Outputs JSON report
4. Agent analyzes and optionally auto-tunes strategy

### Auto-tune rules (agent prompt)

- Route with WR<25% and n>=4 → add to `blocked_routes`
- MCAP bucket with WR=0% and n>=3 → raise `min_mcap_usd`
- MAX_HOLD avg pnl positive but <10% → reduce `max_hold_ms`
- SL hits >60% trades → tighten trailing or filters

### Manual trigger

```bash
python3 ~/.hermes/scripts/charon_hourly_audit.py
```

---

## User Exit Preferences (the user, May 2026)

Confirmed settings:

| Setting | Value | Reason |
|---------|-------|--------|
| `tp_percent` | 999 | Unlimited — trailing handles exit |
| `trailing_percent` | 35 | Drop 35% from peak triggers exit |
| `sl_percent` | -25 | Standard stop loss |
| `max_hold_ms` | 0 | Disabled — no time limit |
| `partial_tp_at_percent` | 35 | Partial TP at +35% |
| `partial_tp_sell_percent` | 40 | Sell 40% at partial TP |

---

## User Filter Preferences (the user, May 2026)

**Disabled (LLM decides):**
- `max_sniper_ratio` → 1.0 (100% = disabled)
- `min_elite_holder_count` → 0
- `min_smart_wallet_count` → 0
- `max_rat_ratio` → 1.0

**Active:**
- `max_bot_degen_rate` → 0.25 (25%)
- `max_bundler_ratio` → 0.6 (60%)
- `min_mcap_usd` → 10000
- `max_mcap_usd` → 100000
- `min_holders` → 60
- `min_liquidity_usd` → 8000
- `token_age_min_ms` → 0 (disabled — new pairs OK)
- `min_buy_sell_ratio_5m` → 0 (disabled)
- `min_buy_sell_ratio_1h` → 0 (disabled)
- `blocked_routes` → [] (empty — all routes OK, LLM decides)

**User quote:** "Gapapa gaada sniper wallet dan elite holder juga, itu urusan LLM aja yg atur"

---

## Route Blacklist Filter

Added to `src/pipeline/candidateBuilder.js` before the return statement in `filterCandidate()`:

```js
// BAB LEARN — Auto-tuned route blacklist
if (Array.isArray(strat.blocked_routes) && strat.blocked_routes.length) {
  const route = candidate.signals?.route || candidate.signals?.label || null;
  if (route && strat.blocked_routes.includes(route)) {
    failures.push(`route blocked by /learn: ${route} (historical WR < threshold)`);
  }
}
```

Set `blocked_routes` array in strategy config_json. Empty array = all routes allowed.

---

## Data-Driven Tuning (86 trades, May 2026)

### By Route
| Route | Trades | WR | Avg PnL | Action |
|-------|--------|-----|---------|--------|
| dual_source | 58 | 34% | +7.4% | ✅ Keep |
| fee_trending | 10 | 50% | +2.5% | ✅ Keep |
| graduated_trending | 15 | 13% | -16.9% | Initially blocked, then unblocked per user |
| fee_graduated_trending | 3 | 0% | -21.1% | Initially blocked, then unblocked per user |

### By MCAP Bucket
| Bucket | Trades | WR | Avg PnL | Action |
|--------|--------|-----|---------|--------|
| <$10K | 15 | **0%** | -25.6% | ❌ Raised min_mcap to $10K |
| $10-30K | 17 | 35% | +4.2% | ✅ Keep |
| $30-60K | 14 | 29% | -13.6% | ⚠️ Marginal |
| $60-100K | 13 | 38% | +10.4% | ✅ Keep |
| >$100K | 27 | 44% | +18.6% | ✅ Best bucket |

### By Exit Reason
| Reason | Count | Avg PnL |
|--------|-------|---------|
| MAX_HOLD | 37 (43%) | +11.0% |
| SL | 36 (42%) | -30.7% |
| TRAILING_TP | 12 (14%) | +65.0% |
| MANUAL | 1 (1%) | +53.1% |

**Insight:** MAX_HOLD exits were profitable on average — tokens that held long enough without hitting SL tended to be winners. But user disabled max_hold ("ga perlu ada kecuali stuck").
