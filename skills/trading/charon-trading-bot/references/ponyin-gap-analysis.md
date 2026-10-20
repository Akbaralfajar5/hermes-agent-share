# Ponyin ↔ Charon Gap Analysis & Command Playbook

Companion to `ponyin-trading-intel.md`. That file captures the raw Ponyin lessons.
This file maps each lesson to the *exact Charon code path* and records where Charon
is MISSING the lesson (gap) so future sessions can patch instead of rediscover.

Cross-reference: `~/charon/src/pipeline/candidateBuilder.js` and `src/db/settings.js`
(defaults) are the two files that matter for tuning.

---

## Coverage Matrix (Ponyin → Charon)

| Ponyin Lesson | Charon Mechanism | Status |
|---------------|------------------|--------|
| BAB 1 Bundle Token | `trending_max_bundler_rate` (filter), `max_top20_holder_percent` | ✅ partial — default `max_top20_holder_percent=100` means effectively off; turn it down |
| BAB 2 Global Fees | `min_gmgn_total_fee_sol`, `trending.is_wash_trading` boolean | ✅ implemented |
| BAB 3 Revoke & Mint Authority | — | 🚫 **GAP** — no direct mint/freeze check; only `trending_max_rug_ratio` as proxy |
| BAB 4 Meme vs Utility | `PUMP_PROGRAM`/`PUMP_AMM` constants, `degen` strategy | ✅ by design |
| BAB 5 Dex Paid / Ads / Boost timing | `trending_min_swaps`, `trending_min_volume_usd`, `trendingHotLevel` | ⚠️ indirect only |
| BAB 6 3 Konfirmasi Candle (10% mark entry) | `max_ath_distance_pct` picks up *that* there was a dip, but buy is full-size | 🚫 **GAP** — no partial entry ladder |
| BAB 7 Cabal Play | `min_saved_wallet_holders` + `/walletadd` command | ✅ strong fit |
| BAB 8 Multi-wallet holder reading | `max_top20_holder_percent`, `min_holders` | ✅ |
| BAB 9 Market Cap Tier | `min_mcap_usd`/`max_mcap_usd` per strategy | ✅ |
| A1 Snipe | `SIGNAL_POLL_MS=30000` ⇒ Charon is NOT a millisecond sniper | ⚠️ by design (detection-based) |
| A2 First $1K (trailing stop) | `trailing_enabled`, `trailing_percent` | ✅ |
| A3 Wallet Ping | `fetchSavedWalletExposure` + `/walletadd` | ✅ |
| A4 Money Mgmt (35% TP + compounding) | `partial_tp`, `partial_tp_at_percent`, `partial_tp_sell_percent` | ✅ if enabled (default off) |
| A5 Direct RPC, no platform fee | Jupiter Ultra + direct Helius RPC | ✅ by design |
| A6 Rent Refund | — | 🚫 **GAP** — no auto-close of empty token accounts |
| A7 Instant Scalping (4 filters) | filter 3 partial (`max_top20_holder_percent`), filter 4 (`min_mcap_usd`) | ⚠️ filter 1 (gas fee) & filter 2 (funded wallet age) missing |
| BONUS Day Phase Trade | `max_ath_distance_pct` + `max_hold_ms` | ✅ can be expressed as a strategy |
| A8 Multi Wallet | single-wallet by design (`SOLANA_PRIVATE_KEY`) | ⚠️ run multiple PM2 instances w/ separate `.env` + `DB_PATH` |
| A9 Unwritten Rules (no one-clip) | `partial_tp` + `trailing_percent` | ✅ if enabled |
| A10 Skema Penipuan | `TELEGRAM_CHAT_ID` whitelist, `confirm` mode, `LIVE_MIN_SOL_RESERVE` | ✅ |

---

## Ponyin-Faithful `/stratset` Playbook (copy-paste into Telegram)

Core sniper, aligned to Ponyin's "target 50% per trade + trailing + partial TP + chart-friendly exit":

```
/stratset sniper tp_percent 50
/stratset sniper sl_percent -25
/stratset sniper partial_tp true
/stratset sniper partial_tp_at_percent 35
/stratset sniper partial_tp_sell_percent 35
/stratset sniper trailing_enabled true
/stratset sniper trailing_percent 25
/stratset sniper max_top20_holder_percent 85
/stratset sniper trending_max_bundler_rate 0.35
/stratset sniper trending_max_rug_ratio 0.25
/stratset sniper min_gmgn_total_fee_sol 15
/stratset sniper min_saved_wallet_holders 1
```

`dip_buy` strategy for Day Phase Trade (swing 3–7 days):

```
/stratset dip_buy min_mcap_usd 1000000
/stratset dip_buy max_mcap_usd 50000000
/stratset dip_buy max_ath_distance_pct -50
/stratset dip_buy token_age_max_ms 1209600000
/stratset dip_buy tp_percent 50
/stratset dip_buy sl_percent -20
/stratset dip_buy max_hold_ms 604800000
/stratset dip_buy trailing_enabled true
/stratset dip_buy trailing_percent 15
```

Cabal wallet registration (plug in addresses as you source them):

```
/walletadd cupsey   <address>
/walletadd cented   <address>
/walletadd log      <address>
/walletadd decu     <address>
/walletadd marcel   <address>
/walletadd lexapro  <address>
/walletadd cooker   <address>
/walletadd wynn     <address>
/walletadd duvel    <address>
```

---

## Patch Opportunities (if you want to close the gaps)

**BAB 3 – Mint/freeze authority check**
Add to `pipeline/candidateBuilder.js` a Solana RPC call (`getAccountInfo` on the mint)
to read `mintAuthority` / `freezeAuthority`. Add strategy field `require_revoked_mint`
and fail the filter if still Active.

**BAB 6 – Partial entry (10% mark position)**
Add strategy fields `mark_entry_percent` (default 10) + `mark_entry_enabled`. In
`executeLiveBuy`, if enabled, place mark-size order first, store a pending-full-entry
record, re-evaluate on next dip candle.

**A6 – Rent refund auto-close**
In `execution/positions.js`, after position close + zero token balance, emit a
`closeAccount` instruction for the token account. Accumulate ~0.002 SOL refund each.

**A7 filter 1 – Gas fee gate**
Before candidate accept, fetch recent prioritization fee average via Helius
`getRecentPrioritizationFees`; if above threshold, temporarily skip entries.

**A7 filter 2 – Funded wallet age**
For top holders, fetch earliest signature of the funding tx; if all/most are funded
<24h before launch, flag as manipulation.

---

## Notes

- `trending_max_rug_ratio` default 0.3 and `trending_max_bundler_rate` default 0.5
  are both too loose for Ponyin-style defense. Tighten to 0.25 and 0.35.
- Ponyin says "holder 7–10% per wallet sudah wajar" for narrative tokens, but Charon's
  `max_top20_holder_percent` is an *aggregate* top-20 %, not per-wallet, so 80–85 is
  still a reasonable ceiling.
- Full consolidated PDF generator: `scripts/generate_ponyin_charon_pdf.py`.
