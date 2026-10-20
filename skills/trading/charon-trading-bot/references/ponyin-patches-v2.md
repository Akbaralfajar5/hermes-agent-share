# Charon × Ponyin Integration Patches (v2)

Additive patches that make Charon faithful to Ponyin trading principles. All patches are
**opt-in** — existing strategies that don't set the new fields keep their original behavior.
No rename of files; everything consolidated into existing files (jupiter.js, liveExecutor.js).

Scope: BAB 3 Revoke & Minting, BAB 6 3 Konfirmasi Candle, A6 Rent Refund, A7 Instant Scalping
(4 filter), plus 2 new seeded strategies (`ponyin_scalp`, `day_phase`).

---

## Architectural principle (user preference)

**DO NOT create new files when integrating features.** User explicitly corrected this:
> "Itu nama file diubah tidak apa2? Padahal biarkan aja untuk nama file yg penting isinya yg di integrasikan"

The rule: consolidate additions into existing files where ownership is natural. Solana
on-chain checks belong in `enrichment/jupiter.js` (same domain). Rent refund close
instruction belongs in `liveExecutor.js` (it owns the Connection + Keypair already).

If a new util truly doesn't fit any existing file, ask the user first.

---

## File-by-file integration map

### `src/enrichment/jupiter.js` (consolidation target for on-chain enrichment)

Append at the end, before the `export { ... }` block. Import additions:
```js
import { Connection, PublicKey } from '@solana/web3.js';
import { WSOL_MINT, JSON_HEADERS, SOLANA_RPC_URL } from '../config.js';
```

Add 5 exports to the bottom export block:
```
fetchMintAuthority,
fetchHolderAgeStats,
fetchTopHolderBalances,
fetchRecentPriorityFee,
fetchPonyinChecks,
```

Local state:
- `solanaConn` lazy singleton via `getSolanaConn()`
- `mintAuthorityCache` TTL 5 min
- `walletAgeCache` TTL 60 min
- `balanceCache` TTL 5 min
- `feeCache` TTL 30 s (median priority fee)

All functions throttle 50ms between RPC calls in loops (avoids Helius rate limiting).
`fetchPonyinChecks(mint, holders, opts)` orchestrator respects skip flags so strategies
that don't use a filter don't pay RPC cost.

### `src/liveExecutor.js` (consolidation target for wallet-signing actions)

Add to imports at the top:
```js
import { Connection, Keypair, PublicKey, Transaction, VersionedTransaction, sendAndConfirmTransaction } from '@solana/web3.js';
import { createCloseAccountInstruction, getAssociatedTokenAddress } from '@solana/spl-token';
```

Append `closeEmptyTokenAccount(mint)` — reuses module-level `liveWallet` + `solanaConnection`,
no external keypair getter needed. Returns `{success, signature, rentRefundSol}` or
`{skipped, reason}` or `{success: false, error}`.

### `src/pipeline/candidateBuilder.js`

1. Import addition: add `fetchPonyinChecks` to existing `enrichment/jupiter.js` import.
2. In `buildCandidate`, after existing enrichment calls, add conditional Ponyin enrichment:
```js
const ponyinNeedsMintAuth = !!(strat.require_mint_revoked || strat.require_freeze_revoked);
const ponyinNeedsAges = strat.max_fresh_holder_ratio != null && strat.max_fresh_holder_ratio > 0;
const ponyinNeedsBalances = strat.max_weak_holder_ratio != null && strat.max_weak_holder_ratio > 0;
const ponyinNeedsGas = strat.max_network_priority_fee != null && strat.max_network_priority_fee > 0;
const ponyin = (ponyinNeedsMintAuth || ponyinNeedsAges || ponyinNeedsBalances || ponyinNeedsGas)
  ? await fetchPonyinChecks(mint, holders, { skipMintAuthority: !ponyinNeedsMintAuth, skipWalletAge: !ponyinNeedsAges, skipBalances: !ponyinNeedsBalances, skipGas: !ponyinNeedsGas })
  : null;
```
3. Attach to candidate object: `ponyin,` before `createdAtMs: now()`.
4. In `filterCandidate`, after trending filters, add 4 opt-in guards:
   - `require_mint_revoked` / `require_freeze_revoked` — BAB 3
   - `max_fresh_holder_ratio` — A7 filter 2
   - `max_weak_holder_ratio` — A7 filter 3
   - `max_network_priority_fee` — A7 filter 1

All guards are `strat.field != null && strat.field > 0` gated, so legacy strategies skip them.

### `src/db/positions.js`

In `createDryRunPosition`, implement BAB 6 partial entry:
```js
const fullSize = strat.position_size_sol ?? numSetting('dry_run_buy_sol', 0.1);
const markFraction = (strat.entry_mode === 'partial_dip' && strat.mark_position_fraction)
  ? Number(strat.mark_position_fraction) : 1;
const sizeSol = fullSize * markFraction;
```
And persist `intended_full_size_sol` + `dca_done` columns (0 if partial_dip mode, 1 otherwise).

### `src/execution/positions.js`

In `refreshPosition`, before the TP/SL check, insert DCA-on-dip logic. Key nuances:
- Guard by `positionStratForDca?.entry_mode === 'partial_dip'` — strategy might have changed,
  but the POSITION's strategy is what matters. Use `strategyById(position.strategy_id)`,
  not `activeStrategy()`.
- Only fires when `!position.dca_done` (idempotent).
- Weighted avg entry price/mcap: prev_value + added_value / total_size.
- After DCA, recompute pnlPercent + pnlSol using NEW avg mcap.
- Reassign `position = { ... }` locally — works because JS function params are mutable.
- Write trade log with `reason = 'BAB6_DCA'` for audit trail.

Rent refund hook after live sell completes:
```js
if (boolSetting('rent_refund_enabled', true)) {
  setTimeout(async () => {
    const refund = await closeEmptyTokenAccount(position.mint);
    if (refund?.success) { /* insert dry_run_trades row side='rent_refund' reason='A6_RENT_REFUND' */ }
  }, 5000);
}
```
5-second delay ensures the sell tx is finalized on-chain before we try to close the ATA.

### `src/db/connection.js`

1. Two new schema columns via `ensureColumn`:
```js
ensureColumn('dry_run_positions', 'intended_full_size_sol', 'REAL');
ensureColumn('dry_run_positions', 'dca_done', 'INTEGER DEFAULT 0');
```
2. Default setting: `rent_refund_enabled: 'true'`.
3. Retune `sniper` strategy to Ponyin defaults (see next section).
4. Seed 2 new strategies: `ponyin_scalp`, `day_phase`.

### `package.json`

Add `@solana/spl-token` dependency. Extend `check` script to include all modified files
(`jupiter.js`, `candidateBuilder.js`, `positions.js`, `db/positions.js`, `db/connection.js`).

---

## Default strategy values (Ponyin-tuned sniper)

Key changes from original defaults:
- `min_gmgn_total_fee_sol`: 10 → **15** (A7 Global Fees stricter)
- `max_top20_holder_percent`: 100 → **85** (BAB 8 multi-wallet aware)
- `trending_max_rug_ratio`: 0.3 → **0.25**
- `trending_max_bundler_rate`: 0.5 → **0.35** (BAB 1 anti-bundle)
- `trailing_percent`: 20 → **25** (BAB 6 give more room for meme volatility)
- `partial_tp`: false → **true** (A9 unwritten rules anti-one-clip)
- `partial_tp_at_percent`: 0 → **35** (A4 35% TP strategy)
- `partial_tp_sell_percent`: 0 → **35**
- `llm_min_confidence`: 50 → **65**
- `require_mint_revoked`: **true** (BAB 3)
- `require_freeze_revoked`: **true** (BAB 3)
- `max_fresh_holder_ratio`: **0.6** (A7 filter 2, lenient default)
- `max_weak_holder_ratio`: **0.7** (A7 filter 3, lenient default)

---

## New strategies seeded

### `ponyin_scalp` (full A7 Instant Scalping)
- Token age: 30 min max (fresh launch only)
- MC: $3K–$100K (filter 4)
- Hold max: 30 min
- TP: 60%, SL: -25%, trailing: 20%
- Partial TP: 35% at +35%
- Position size: 0.05 SOL, max 4 open
- LLM: **OFF** (rule-based, fast execution)
- A7 filters aktif semua: fresh holder 0.5, weak holder 0.6, priority fee 1M lamports
- Mint & freeze revoke: required

### `day_phase` (Bonus Strat swing 3-7 hari)
- **entry_mode: 'partial_dip'** (unique — only strategy using BAB 6)
- `mark_position_fraction: 0.1` (beli 10% dulu)
- `dca_trigger_percent: -12` (DCA full kalau dip -12%)
- Token age: 14 hari
- MC: $1M–$50M (FDV $1M+)
- ATH distance max: -50% (wajib sudah dip 50%+)
- Min holders: 500
- Max top 20: 70%
- GMGN fees: 50 SOL min (organic volume thick)
- TP: 50%, SL: -20%, trailing: 15%
- Partial TP: 35% at +40%
- Max hold: 7 hari (A9 strict rule)
- LLM: ON, confidence 65

---

## Verification & testing

```bash
cd ~/charon && source ~/.nvm/nvm.sh && nvm use 20
npm install  # picks up @solana/spl-token
npm run check  # syntax-check all modified files
```

Module-level smoke test:
```bash
node -e "
import('./src/enrichment/jupiter.js').then(m => console.log(Object.keys(m).sort().join(',')));
import('./src/liveExecutor.js').then(m => console.log(Object.keys(m).sort().join(',')));
"
```

Expected jupiter.js exports include: `fetchMintAuthority,fetchHolderAgeStats,
fetchTopHolderBalances,fetchRecentPriorityFee,fetchPonyinChecks`.
Expected liveExecutor.js exports include: `closeEmptyTokenAccount`.

Runtime verification (logs should show filter triggers):
- `market cap min: X < 7000` → sniper mcap filter
- `GMGN total fees: X < 15` → Ponyin-tuned fee filter
- `A7 weak holders: X% under 0.2 SOL > 70% threshold` → A7 filter 3 firing
- `A7 fresh holders: X% fresh (<1d) > 50% threshold` → A7 filter 2 firing
- `mint authority: still active (BAB 3 — not revoked)` → BAB 3 firing

---

## Backward compatibility notes

1. **Existing DB:** `INSERT OR IGNORE INTO strategies` means existing sniper rows are NOT
   overwritten. Users with pre-existing `charon.sqlite` need to manually update sniper
   config or drop/recreate. Fresh install: gets Ponyin defaults automatically.
2. **New columns:** `ensureColumn` migrates gracefully — existing positions get NULL
   `intended_full_size_sol` and `dca_done=0`, which is the "legacy / no partial dip" state.
3. **LLM cost:** `ponyin_scalp` has `use_llm: false` → no LLM cost. `day_phase` uses LLM
   at confidence 65 with larger position size — cost-effective.

---

## Switch strategy programmatically (bypassing Telegram)

If `/strategy` via Telegram is inconvenient or bot chat isn't active:
```bash
cd ~/charon && source ~/.nvm/nvm.sh && nvm use 20
node -e "
import('better-sqlite3').then(({default: Database}) => {
  const db = new Database('./charon.sqlite');
  db.prepare('UPDATE strategies SET enabled = 0').run();
  db.prepare('UPDATE strategies SET enabled = 1 WHERE id = ?').run('ponyin_scalp');
});"
```
Strategy cache in `db/settings.js` reloads within 5 seconds. No process restart needed.

---

## Dependency: @solana/spl-token

Version pinned: `^0.4.14`. Required only for `closeEmptyTokenAccount`. If install reports
vulnerabilities, they are typically in transitive deps (bigint-buffer etc.) — not exploitable
for our usage pattern.
