# Ponyin Integration (the user' Charon fork at ~/charon on VPS)

This fork of yunus-0x/charon has been extended with filters and logic derived from ponyin.id's Vol.1 + Vol.2 materials. If the user mentions "ponyin", "BAB 6 / A7 / A6", or "ponyin_scalp / day_phase" strategies, these patches are already in place.

## New files

- `src/enrichment/ponyin.js` — on-chain enrichment module
  - `fetchMintAuthority(mint)` — mint/freeze authority check (BAB 3 Revoke & Minting)
  - `fetchHolderAgeStats(holders, sampleSize=10)` — funded wallet age (A7 filter 2)
  - `fetchTopHolderBalances(holders, sampleSize=10)` — top holder SOL balance (A7 filter 3)
  - `fetchRecentPriorityFee()` — gas war detector (A7 filter 1)
  - `fetchPonyinChecks(mint, holders, opts)` — orchestrator; opts allow skipping branches strategy doesn't need

- `src/execution/rentRefund.js` (A6 Rent Refund)
  - `closeEmptyTokenAccount(mint)` — close ATA after live sell, reclaim ~0.002 SOL
  - Requires `@solana/spl-token` (installed)
  - Exposes `liveWalletKeypair()` in liveExecutor.js

## New strategy fields (opt-in; each strategy chooses which to enable)

| Field | Meaning | Ponyin ref |
|---|---|---|
| `require_mint_revoked: bool` | fail if mint authority still active | BAB 3 |
| `require_freeze_revoked: bool` | fail if freeze authority still active | BAB 3 |
| `max_fresh_holder_ratio: 0..1` | fraction of top-10 holders with wallet < 1d old | A7 filter 2 |
| `max_weak_holder_ratio: 0..1` | fraction of top-10 holders with balance < 0.2 SOL | A7 filter 3 |
| `max_network_priority_fee: number` | reject if median priority fee > value (lamports/CU) | A7 filter 1 |
| `entry_mode: 'partial_dip'` | buy small mark position, DCA on dip | BAB 6 |
| `mark_position_fraction: 0..1` | fraction of intended size for the initial mark (e.g. 0.1) | BAB 6 |
| `dca_trigger_percent: negative` | pnl% threshold to trigger full DCA (e.g. -12) | BAB 6 |

Filter logic lives at the end of `filterCandidate()` in `src/pipeline/candidateBuilder.js`, guarded on `candidate.ponyin`. Enrichment call is conditional in `buildCandidate()` — only fetches the branches the active strategy needs, to save RPC calls.

## New strategies seeded in `src/db/connection.js`

- `ponyin_scalp` — Ponyin Instant Scalping (A7). Disabled by default. mcap 3k-100k, all 4 A7 filters on, TP 60%, max_hold 30 min.
- `day_phase` — Ponyin Day Phase Trade (Bonus Strat). `entry_mode: 'partial_dip'`, mark 10%, dca_trigger -12%, FDV 1M-50M, ATH dist ≤ -50%, TP 50%, max_hold 7 days.
- `sniper` (default enabled) — re-tuned Ponyin-faithful: bundler 0.35, top20 85%, partial TP 35% at +35%, trailing 25%, mint revoke required, fresh/weak holder filters, LLM confidence 65.

## DB migrations (handled via ensureColumn)

- `dry_run_positions.intended_full_size_sol REAL`
- `dry_run_positions.dca_done INTEGER DEFAULT 0`
- setting `rent_refund_enabled` default `'true'`

## Behavior changes in execution

- `createDryRunPosition` / `createLivePosition` — if strategy uses `entry_mode='partial_dip'`, the initial buy is only `fullSize * mark_position_fraction`. `intended_full_size_sol` stored for later DCA.
- `refreshPosition` — before TP/SL evaluation, checks if position needs DCA (partial_dip + !dca_done + pnl <= dca_trigger_percent), executes it, recalculates weighted avg entry, logs trade with `reason='BAB6_DCA'`.
- Live sell path — schedules `closeEmptyTokenAccount` 5s after close when `rent_refund_enabled=true`, logs `reason='A6_RENT_REFUND'`.

## npm run check

Extended to include: `src/enrichment/ponyin.js`, `src/execution/rentRefund.js`, `src/pipeline/candidateBuilder.js`, `src/execution/positions.js`, `src/db/positions.js`, `src/db/connection.js`. Always run after edits.

## Ponyin → Charon mapping (for future consolidation work)

| Ponyin material | Charon config/code |
|---|---|
| BAB 1 Bundle Token | `trending_max_bundler_rate`, `max_top20_holder_percent`, `min_source_count` |
| BAB 2 Global Fees | `min_gmgn_total_fee_sol`, `trending.is_wash_trading` |
| BAB 3 Revoke & Minting | `require_mint_revoked`, `require_freeze_revoked` (NEW) |
| BAB 5 Dex Paid/Ads/Boost | `trending_min_swaps`, `trending_min_volume_usd` (context timing) |
| BAB 6 3 Konfirmasi Candle | `entry_mode='partial_dip'` + `mark_position_fraction` + `dca_trigger_percent` (NEW) |
| BAB 7 Cabal Play | saved wallets + `min_saved_wallet_holders` + `/walletadd` |
| BAB 9 Market Cap Tier | `min_mcap_usd` / `max_mcap_usd` per strategy |
| A4 Money Management | `tp_percent`, `sl_percent`, `trailing_*`, `partial_tp*` |
| A6 Rent Refund | `rent_refund_enabled` + `closeEmptyTokenAccount` (NEW) |
| A7 Instant Scalping | `max_fresh_holder_ratio`, `max_weak_holder_ratio`, `max_network_priority_fee` (NEW) |
| A9 Unwritten Rules (anti one-clip) | `partial_tp` + `trailing_enabled` |
| Bonus Day Phase Trade | `day_phase` strategy (NEW) |

## Consolidation PDF

Generated once at `/home/ubuntu/Ponyin_x_Charon_Consolidation.pdf` using `reportlab` via `/usr/bin/python3` (see python-venv gotcha in memory). Scripts live at `/tmp/pnyn/`: `data.py` (topics), `charon_data.py` (mapping), `gen.py` (renderer).
