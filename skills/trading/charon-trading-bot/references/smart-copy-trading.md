# Smart Wallet Copy Trading

## Overview

File: `src/signals/smartCopy.js`
Monitors top 100 profitable wallets from GMGN, copies their fresh buys directly (bypasses LLM).

## Architecture

```
Top 100 Wallets (refreshed hourly)
    ↓ poll every 60s (10 concurrent)
Fresh Buys (last 5 min)
    ↓ dedup by tx_hash + mint (1 entry per token per hour)
Pipeline (buildCandidate → safety filter → mcap filter)
    ↓ route = 'smart_copy' → bypass LLM
Direct BUY (confidence: 85)
    ↓
Position opened (profit_lock tiers active)
```

## Key Design Decisions

- **Bypasses LLM entirely** — smart wallets ARE the filter (historically profitable traders)
- **Fire-and-forget handler** — `.catch()` pattern, doesn't block poll cycle
- **Concurrency 10** — polls 10 wallets in parallel, full cycle ~5s for 100 wallets
- **Fresh window 5 min** — only buys from last 300 seconds (prevents copying old positions)
- **Wallet list refresh 1 hour** — top wallets don't change that fast

## Anti-Duplicate (3 layers)

1. **TX hash dedup** (`seenTxs` Map, 30 min TTL) — same transaction never processed twice
2. **Mint dedup** (`seenMints` Map, 1 hour TTL) — same token only enters pipeline once per hour, even if 10 wallets buy it
3. **Position-level dedup** (`hasMintPosition()` in orchestrator) — if token already has open position OR was closed in last hour, skip entirely

## GMGN Endpoints Used

```
# Wallet ranking (refreshed hourly)
GET /defi/quotation/v1/rank/sol/wallets/7d?orderby=realized_profit_7d&direction=desc&limit=100

# Wallet activity (polled every 60s per wallet)
GET /api/v1/wallet_activity/sol?type=buy&wallet={ADDRESS}&limit=5
```

## Orchestrator Integration

In `src/pipeline/orchestrator.js`, smart_copy route bypasses LLM:

```js
if (!strat.use_llm || signals.route === 'smart_copy') {
  // Direct BUY — no LLM needed
  batchDecision = {
    verdict: 'BUY',
    confidence: 85,
    reason: `Smart wallet copy: top trader bought ${symbol} (${sol} SOL, wallet profit $${profit}/7d)`,
    risks: ['copy trade — wallet may exit before us'],
  };
}
```

## Performance (2026-05-13, first session)

- 17 trades total (GOLD token dominated due to pre-fix duplicate entries)
- 4W / 13L (24% win rate)
- **Total PnL: +0.6563 SOL** (profitable despite low win rate)
- Best trades: +954%, +687%, +533% (GOLD — smart wallet entry at $72K mcap, pumped to $700K+)
- Losses: mostly -25% to -95% (SL hit, some with extreme slippage on low-liq)
- Key insight: winners are MASSIVE (5-10x), losses are capped at position size

## Configuration

Settings in SQLite (hot-read):
- `smart_copy_enabled` (default: true) — enable/disable scanner
- Strategy `max_mcap_usd` applies — tokens above this are filtered by candidateBuilder

Constants in `smartCopy.js`:
- `CONCURRENCY = 10` — parallel wallet fetches
- `WALLET_REFRESH_MS = 3600000` — refresh wallet list every 1 hour  
- `POLL_MS = 60000` — poll activity every 60s
- `FRESH_BUY_WINDOW_S = 300` — only buys from last 5 minutes
- `MAX_WALLETS = 100` — top 100 by 7d profit
- `SEEN_TX_TTL_MS = 1800000` — 30 min tx dedup
- `SEEN_MINT_TTL_MS = 3600000` — 1 hour mint dedup

## Pitfalls

- **Bridge overload** — 100 wallet polls + GMGN scanner + signal server all hit bridge. If bridge returns timeouts, smart copy silently returns empty arrays (no crash). Recovers next cycle.
- **Wallet activity endpoint returns max 5 buys** — if a whale makes 10 buys in 5 min, we only see the latest 5. Acceptable tradeoff for API simplicity.
- **Fresh window too short** — if poll cycle takes >5 min (bridge slow), some buys may age out before being seen. The 60s poll interval + 300s window gives 5 chances to catch each buy.
- **Smart wallet may exit before us** — we copy the BUY but don't track their SELL. Profit lock tiers handle our exit independently. Risk: wallet sells at +50%, we're still holding waiting for tier 2.
- **Position-level dedup resets on restart** — `hasMintPosition()` queries DB (persistent), but `slCooldownMap` and `seenMints` are in-memory (reset on restart). After restart, first poll may re-enter tokens that were recently SL'd. The DB-level check (`hasMintPosition`) catches open positions and recently-closed ones (1 hour window).

## Startup in app.js

```js
// Start Smart Wallet Copy scanner (top 100 wallets)
const { startSmartCopyScanner, setSmartCopyHandler } = await import('./signals/smartCopy.js');
setSmartCopyHandler(processCandidateFromSignals);
await startSmartCopyScanner(); // await is intentional — needs wallet list loaded first
```

Note: `await` is intentional here (unlike GMGN scanner which is fire-and-forget). Smart copy needs the wallet list loaded before first poll, otherwise first cycle has 0 wallets. The wallet fetch is fast (~1s).

## Log Output

```
[smart_copy] loaded 100 wallets (top: $113571, bottom: $5495)
[smart_copy] scanner started (100 wallets, poll: 60s, fresh window: 300s)
[smart_copy] poll: 2 fresh buys found, 2 sent to pipeline, 0 mcap-filtered, 57 too old
```
