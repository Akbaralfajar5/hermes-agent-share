# GMGN Multi-Source Scanner

Replaces PumpPortal WebSocket AND single-endpoint scanner. Polls GMGN bridge across 6 sources for comprehensive token discovery with full safety data.

## Source File: `src/signals/newPairs.js`

Key design decisions:
- Polls every 30s (configurable via `new_pairs_poll_ms` setting)
- 6 GMGN sources polled per cycle (see below)
- Safety filter runs BEFORE enrichment/LLM to save API calls
- Tokens marked as seen for 10 minutes (cross-source dedup)
- **Fire-and-forget** handler calls (`.catch()` instead of `await`) — prevents blocking scanner when enrichment is slow
- Passes tokens to same `processCandidateFromSignals` handler as signal server

## 6 Sources

| Source | Endpoint | Route | Purpose |
|--------|----------|-------|---------|
| `new_pairs` | `/rank/sol/swaps/1m?orderby=open_timestamp&direction=desc&limit=30` | `gmgn_new_pairs` | Early entry on fresh tokens |
| `trending_swaps` | `/rank/sol/swaps/5m?orderby=swaps&direction=desc&limit=30` | `gmgn_trending` | Most actively traded |
| `trending_volume` | `/rank/sol/swaps/5m?orderby=volume&direction=desc&limit=20` | `gmgn_trending` | Highest volume |
| `trending_buyers` | `/rank/sol/swaps/5m?orderby=buys&direction=desc&limit=20` | `gmgn_trending` | Most buyer demand |
| `smart_wallet` | `/rank/sol/swaps/5m?orderby=smart_degen_count&direction=desc&limit=30` | `gmgn_smart_wallet` | Smart money signal |
| `kol` | `/rank/sol/swaps/5m?orderby=renowned_count&direction=desc&limit=30` | `gmgn_kol` | KOL/influencer signal |

All paths are prefixed with `/defi/quotation/v1/`.

## Additional GMGN Endpoints Available (not yet integrated)

| Endpoint | Data | Potential Use |
|----------|------|---------------|
| `/rank/sol/wallets/7d?orderby=pnl_7d&direction=desc` | Top profitable wallets | Copy trading signals |
| `?orderby=hot_level&direction=desc` | Viral tokens (hot_level 1-3) | Momentum signal |
| `?orderby=price_change_percent1h&direction=desc` | Top gainers | Momentum (but risky — often at peak) |
| `?orderby=bluechip_owner_percentage&direction=desc` | Blue chip holder overlap | Quality signal |
| `?launchpad=pump.fun` filter | Pump.fun only tokens | Focus on pump.fun ecosystem |

**Fields available per token:** `cto_flag` (community takeover), `dexscr_boost_fee` (paid DexScreener boost), `hot_level` (1-3 virality), `twitter_change_flag`, `twitter_rename_count`.

**Working endpoints outside rank (via bridge proxy, 2026-05-13):**
- `/api/v1/wallet_activity/sol?type=buy&wallet={ADDRESS}&limit=5` — wallet buy history (used by smart copy scanner)
- `/defi/quotation/v1/rank/sol/wallets/7d?orderby=realized_profit_7d&direction=desc&limit=100` — top wallets by profit

**Blocked endpoints (Cloudflare 403):** Token holder list, signal feeds, some wallet detail paths. The bridge's residential proxy + curl_cffi bypasses most Cloudflare blocks — test new paths before assuming they're blocked.

## Safety Filter Rules (hard-coded, pre-LLM)

| Check | Threshold | Reason |
|-------|-----------|--------|
| Dev not closed | `creator_close !== true` | `dev_not_closed` |
| Mint not renounced | `renounced_mint !== 1` | `mint_not_renounced` |
| Freeze not renounced | `renounced_freeze_account !== 1` | `freeze_not_renounced` |
| Bundler rate | > 0.5 (configurable: `new_pairs_max_bundler`) | `bundler` |
| Rug ratio | > 0.2 (configurable: `new_pairs_max_rug_ratio`) | `rug_ratio` |
| Wash trading | `is_wash_trading === true` | `wash_trading` |
| Rat traders | > 0.3 | `rat_traders` |
| Entrapment | > 0.1 | `entrapment` |
| Top 10 holders | > 0.8 | `top10_concentrated` |
| Image duplicates | > 5 | `image_dup` |

## Integration in app.js

```js
// In server mode block (run BOTH signal server + GMGN scanner):
// IMPORTANT: start scanner BEFORE fetchServerSignals() — the fetch blocks for 30-60s
const { startNewPairsScanner, setNewPairsCandidateHandler } = await import('./signals/newPairs.js');
setNewPairsCandidateHandler(processCandidateFromSignals);
startNewPairsScanner();

// Signal server fetch must be NON-BLOCKING (no await) — otherwise it blocks everything
fetchServerSignals().catch(error => console.log(`[server] initial fetch failed: ${error.message}`));
setInterval(() => trackServer(() => fetchServerSignals()), SIGNAL_POLL_MS);
```

## Critical Pitfall: `await fetchServerSignals()` blocks event loop

The initial `fetchServerSignals()` processes 100 signals sequentially, each with GMGN enrichment (15s+ total). If called with `await`, it blocks ALL other code from executing — including the GMGN scanner's `setInterval` callbacks and even `console.log` statements that come after it.

**Fix:** Remove `await` from initial fetch. Use fire-and-forget: `fetchServerSignals().catch(...)`. The `setInterval` handles subsequent polls regardless.

**Symptom:** `[bot] started` appears in logs but nothing after it (no scanner logs, no poll logs). Process appears "running" but scanner never fires.

## Mcap Discrepancy Between Scanner and Enrichment

Scanner sees token at $30K mcap (from rank endpoint). By the time `buildCandidate()` runs enrichment (seconds later), token may have pumped to $300K+. This causes tokens to pass scanner filter but fail `candidateBuilder` mcap filter.

**Fix in `candidateBuilder.js`:** For `gmgn_new_pairs` and `gmgn_trending` routes, cap enriched mcap at `trendingToken.market_cap * 1.5` (allow up to 50% pump from scanner mcap):

```js
const marketCapUsd = (route === 'gmgn_new_pairs' && trendingToken?.market_cap > 0)
  ? Math.min(enrichedMcap || Infinity, trendingToken.market_cap * 1.5)
  : enrichedMcap;
```

## Typical Output

```
[gmgn] multi-source scanner started (new_pairs + trending + smart_wallet + kol, poll: 30000ms)
[gmgn] sources polled: 19 processed, 39 mcap-filtered, 15 safety-rejected, 87 deduped
[gmgn] poll: all 100 deduped (waiting for new tokens)
```

- 6 sources × ~30 tokens = ~160 total (with overlap)
- Dedup removes tokens seen in last 10 min across all sources
- Safety filter rejects ~30-50% (dev not closed, bundler, rug)
- Mcap filter removes tokens outside $7K-$100K range
- Remaining tokens enter pipeline → LLM screening → position

## Settings (SQLite)

| Key | Default | Description |
|-----|---------|-------------|
| `new_pairs_enabled` | `true` | Enable/disable scanner |
| `new_pairs_poll_ms` | `30000` | Poll interval |
| `new_pairs_max_bundler` | `0.5` | Max bundler rate |
| `new_pairs_max_rug_ratio` | `0.2` | Max rug ratio |
