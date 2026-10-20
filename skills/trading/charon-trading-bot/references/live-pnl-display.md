# Live PnL Display — Avoiding the high_water_mcap Trap

**Class of bug:** Position display surfaces a *peak* PnL while the live price has crashed. This is not just cosmetic — users make hold/sell decisions on the displayed number.

## Symptom

- Telegram `/menu` shows `Unrealized 🟢 +0.1735 SOL`
- Dashboard at `:5858/api/state` shows `unrealized_pnl_sol: -0.0181`
- Same DB, same positions, opposite sign. User asks "kok beda?"

## Root cause

The Telegram formatters in `src/telegram/menus.js`, `src/telegram/format.js`, and `src/telegram/commands.js` historically computed unrealized PnL from `position.high_water_mcap`:

```js
const ref = Number(p.high_water_mcap) || entry;
const pct = entry > 0 ? (ref / entry - 1) * 100 : 0;
openPnlSol += Number(p.size_sol) * (pct / 100);
```

`high_water_mcap` is the *all-time high since entry* — it never decreases. Once a token pumped to 2x then rugged to 0.05x, the menu still reads "+100% peak" forever. The dashboard, by contrast, polls Jupiter every 15s and shows reality.

## Fix — `getCachedAssetPrice()` helper

`src/enrichment/jupiter.js` already maintains `jupiterAssetCache` keyed by mint, populated by `monitorPositions()` every 15s. Expose it as a non-blocking accessor:

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
```

Add to the export block at the bottom of the file.

## Fix — replace high_water with live in formatters

In every file that computed unrealized PnL for *open* positions:

**`src/telegram/menus.js`** — add helper near top, use it inside `mainMenuText()` and `positionsText()`:
```js
import { getCachedAssetPrice } from '../enrichment/jupiter.js';

function livePositionPnlSol(p) {
  const entry = Number(p.entry_mcap) || 0;
  if (entry <= 0) return 0;
  const live = getCachedAssetPrice(p.mint);
  let ref;
  if (live && Number.isFinite(live.mcap) && live.mcap > 0) {
    ref = live.mcap;
  } else if (live && Number.isFinite(live.usdPrice) && live.usdPrice > 0
             && Number(p.entry_price) > 0) {
    return Number(p.size_sol) * ((live.usdPrice / Number(p.entry_price)) - 1);
  } else {
    // Cache miss — fall back to ENTRY (i.e. 0 PnL), NEVER high_water.
    ref = entry;
  }
  return Number(p.size_sol) * ((ref / entry - 1));
}
```

**`src/telegram/format.js`** — `formatPosition()` and `formatPositionCompact()` both have a `refMcap` ternary; replace the open-position branch:
```js
const refMcap = isClosed
  ? Number(position.exit_mcap) || entryMcap
  : liveRefMcap(position);   // was: Number(position.high_water_mcap) || entryMcap
```
With helper:
```js
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

**`src/telegram/commands.js`** — `sendPositions()` aggregate loop, same swap.

## Pitfall: do NOT fall back to high_water on cache miss

The cache is keyed by mint and only populated for *currently open* positions. On bot restart, the first 15s have an empty cache. Tempting fallback:

```js
// WRONG — this is exactly the bug we're fixing
const ref = live?.mcap || Number(p.high_water_mcap) || entry;
```

Use `entry` as fallback (PnL = 0) until the monitor populates. Better to show ⚪ 0.0 SOL for 15 seconds than to lie about peak gains permanently.

## Verification

After patching, both surfaces should agree within polling jitter:
```bash
curl -s http://localhost:5858/api/state | jq .summary.unrealized_pnl_sol
node -e "import('./src/telegram/menus.js').then(m => console.log(m.mainMenuText()))"
```

If they diverge by more than ±0.005 SOL on a stable position, cache is empty / Jupiter rate-limited — wait one monitor cycle and retry.

## Why this matters operationally

`high_water_mcap` PnL is "peak" tracking. It has uses (showing best case, drawdown calculation), but it is **NEVER the right number for "current unrealized"**. On a rug, peak might be +50% while current is -90%; using peak in the headline number turns a portfolio of dead bags into a fictional green report.

Same lesson applies to any future bot showing position value: **always derive headline unrealized from current price, not stored peak**. Store peak alongside if needed for trailing logic, but never display it as "unrealized".
