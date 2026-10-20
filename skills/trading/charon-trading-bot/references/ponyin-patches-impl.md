# Ponyin Intel → Charon Implementation Patches

Concrete code patterns for translating Ponyin trading lessons into Charon bot filters/logic.
Companion to `ponyin-trading-intel.md` (which captures the concepts).

**IMPORTANT — file organization rule**: extend existing files, don't create new siblings.
- On-chain enrichment → append to `src/enrichment/jupiter.js` (not a new `ponyin.js`)
- Wallet/keypair ops (incl. rent refund close) → append to `src/liveExecutor.js` (not a new `rentRefund.js`)
- Filter logic → extend `src/pipeline/candidateBuilder.js` `filterCandidate()`
- Schema / strategy seed → extend `src/db/connection.js` `initDb()` + `ensureColumn()`
- Position lifecycle → extend `src/execution/positions.js` `refreshPosition()` + `src/db/positions.js` `createDryRunPosition()`

---

## 1. BAB 3 Mint/Freeze Authority Check

Append to `src/enrichment/jupiter.js`. Imports needed: `Connection`, `PublicKey` from `@solana/web3.js`, `SOLANA_RPC_URL` from `../config.js`.

```js
let solanaConn = null;
function getSolanaConn() {
  if (!solanaConn) solanaConn = new Connection(SOLANA_RPC_URL, 'confirmed');
  return solanaConn;
}

const mintAuthorityCache = new Map();
const MINT_AUTH_TTL_MS = 5 * 60 * 1000;

async function fetchMintAuthority(mint) {
  const cached = mintAuthorityCache.get(mint);
  if (cached && now() - cached.at < MINT_AUTH_TTL_MS) return cached.data;
  const c = getSolanaConn();
  const info = await c.getParsedAccountInfo(new PublicKey(mint));
  const parsed = info.value?.data?.parsed?.info;
  const data = {
    mintAuthority: parsed?.mintAuthority || null,
    freezeAuthority: parsed?.freezeAuthority || null,
    mintAuthorityRevoked: !parsed?.mintAuthority,
    freezeAuthorityRevoked: !parsed?.freezeAuthority,
  };
  mintAuthorityCache.set(mint, { at: now(), data });
  return data;
}
```

Strategy fields (opt-in, add to strategy JSON): `require_mint_revoked: true`, `require_freeze_revoked: true`.

Filter clause in `candidateBuilder.js` `filterCandidate()`:
```js
if (strat.require_mint_revoked && ponyin.mintAuthority?.mintAuthorityRevoked === false) {
  failures.push('mint authority: still active (BAB 3 — not revoked)');
}
```

---

## 2. A7 Filter 2 — Funded Wallet Age

Sample top 10 holders, check oldest signature age. Uses `getSignaturesForAddress(address, {limit: 1000})` and takes the LAST element (oldest, since signatures return newest-first).

```js
const walletAgeCache = new Map();
const WALLET_AGE_TTL_MS = 60 * 60 * 1000;

async function fetchWalletAgeMs(address) {
  const cached = walletAgeCache.get(address);
  if (cached && now() - cached.at < WALLET_AGE_TTL_MS) return cached.ageMs;
  const c = getSolanaConn();
  const sigs = await c.getSignaturesForAddress(new PublicKey(address), { limit: 1000 });
  if (!sigs.length) return 0;
  const oldest = sigs[sigs.length - 1];
  const oldestMs = (oldest.blockTime || 0) * 1000;
  const ageMs = oldestMs > 0 ? now() - oldestMs : 0;
  walletAgeCache.set(address, { at: now(), ageMs });
  return ageMs;
}

async function fetchHolderAgeStats(holders, sampleSize = 10) {
  const top = (holders || []).slice(0, sampleSize);
  const ages = [];
  for (const h of top) {
    const ageMs = await fetchWalletAgeMs(h.address);
    if (ageMs != null) ages.push(ageMs);
    await new Promise(r => setTimeout(r, 50));  // RPC throttle
  }
  const oneDay = 24 * 60 * 60 * 1000;
  const freshUnder1d = ages.filter(a => a > 0 && a < oneDay).length;
  return { sampled: ages.length, freshUnder1d, freshRatio: ages.length ? freshUnder1d / ages.length : null };
}
```

Strategy field: `max_fresh_holder_ratio: 0.5` (reject if >50% of top holders are <1 day old).

Filter clause:
```js
if (strat.max_fresh_holder_ratio > 0 && ponyin.holderAges?.freshRatio > strat.max_fresh_holder_ratio) {
  failures.push(`A7 fresh holders: ${(ponyin.holderAges.freshRatio * 100).toFixed(0)}% fresh`);
}
```

---

## 3. A7 Filter 3 — Top Holder SOL Balance

`getBalance` on each top holder address, count ones <0.2 SOL.

```js
async function fetchTopHolderBalances(holders, sampleSize = 10) {
  const top = (holders || []).slice(0, sampleSize);
  const balances = [];
  for (const h of top) {
    const lamports = await getSolanaConn().getBalance(new PublicKey(h.address));
    balances.push(lamports / 1_000_000_000);
    await new Promise(r => setTimeout(r, 50));
  }
  const weakHolders = balances.filter(s => s < 0.2).length;
  return { sampled: balances.length, weakRatio: weakHolders / balances.length };
}
```

Strategy field: `max_weak_holder_ratio: 0.6`.

---

## 4. A7 Filter 1 — Network Priority Fee (gas war detector)

```js
async function fetchRecentPriorityFee() {
  const fees = await getSolanaConn().getRecentPrioritizationFees({ lockedWritableAccounts: [] });
  const sorted = fees.map(f => Number(f.prioritizationFee || 0)).sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];  // median
}
```

Strategy field: `max_network_priority_fee: 1000000` (skip if median > 1M micro-lamports/CU).

---

## 5. BAB 6 — Partial Entry (10% Mark) + DCA on Dip

**Schema migration** — add to `db/connection.js` `initDb()`:
```js
ensureColumn('dry_run_positions', 'intended_full_size_sol', 'REAL');
ensureColumn('dry_run_positions', 'dca_done', 'INTEGER DEFAULT 0');
```

**Strategy fields**: `entry_mode: 'partial_dip'`, `mark_position_fraction: 0.1`, `dca_trigger_percent: -12`.

**In `db/positions.js` `createDryRunPosition()`** — compute size as fraction of full intended:
```js
const fullSize = strat.position_size_sol ?? numSetting('dry_run_buy_sol', 0.1);
const markFraction = (strat.entry_mode === 'partial_dip' && strat.mark_position_fraction)
  ? Number(strat.mark_position_fraction) : 1;
const sizeSol = fullSize * markFraction;
// INSERT also stores intended_full_size_sol=fullSize, dca_done=(markFraction<1 ? 0 : 1)
```

**In `execution/positions.js` `refreshPosition()`** — BEFORE the tpHit/slHit calculation:
```js
const positionStratForDca = strategyById(position.strategy_id);
if (positionStratForDca?.entry_mode === 'partial_dip'
    && !position.dca_done
    && position.intended_full_size_sol
    && pnlPercent <= Number(positionStratForDca.dca_trigger_percent ?? -12)) {
  const remainingSol = Number(position.intended_full_size_sol) - Number(position.size_sol);
  if (remainingSol > 0) {
    const newTotalSize = Number(position.intended_full_size_sol);
    // weighted average entry price/mcap
    const prevValue = Number(position.size_sol) * Number(position.entry_mcap || 0);
    const addedValue = remainingSol * Number(mcap || 0);
    const newAvgMcap = (prevValue + addedValue) / newTotalSize;
    // ... similar for entry_price
    db.prepare(`UPDATE dry_run_positions SET size_sol=?, entry_price=?, entry_mcap=?, dca_done=1 WHERE id=?`)
      .run(newTotalSize, newAvgPrice, newAvgMcap, position.id);
    db.prepare(`INSERT INTO dry_run_trades ... reason='BAB6_DCA' ...`).run(...);
    // Recalc pnl at new average, update local position var
    pnlPercent = (Number(mcap) / newAvgMcap - 1) * 100;
    pnlSol = newTotalSize * pnlPercent / 100;
    position = { ...position, size_sol: newTotalSize, entry_mcap: newAvgMcap, entry_price: newAvgPrice, dca_done: 1 };
  }
}
```

Trade log uses `reason: 'BAB6_DCA'` for auditability.

---

## 6. A6 Rent Refund — Auto-Close Empty Token Account

Append to `src/liveExecutor.js` (NOT a new file — wallet/keypair already lives here).

Imports needed: `Transaction`, `sendAndConfirmTransaction` from `@solana/web3.js`; `createCloseAccountInstruction`, `getAssociatedTokenAddress` from `@solana/spl-token`.

```bash
npm install --save @solana/spl-token
```

```js
export async function closeEmptyTokenAccount(mint) {
  if (!liveWallet || !solanaConnection) return { skipped: true, reason: 'no_wallet' };
  const mintPk = new PublicKey(mint);
  const ata = await getAssociatedTokenAddress(mintPk, liveWallet.publicKey);
  const balance = await solanaConnection.getTokenAccountBalance(ata).catch(() => null);
  const raw = Number(balance?.value?.amount || 0);
  if (raw > 0) return { skipped: true, reason: 'nonzero_balance', balance: raw };
  const info = await solanaConnection.getAccountInfo(ata);
  if (!info) return { skipped: true, reason: 'account_missing' };
  const tx = new Transaction().add(
    createCloseAccountInstruction(ata, liveWallet.publicKey, liveWallet.publicKey)
  );
  const sig = await sendAndConfirmTransaction(solanaConnection, tx, [liveWallet], { commitment: 'confirmed' });
  const rentRefundSol = (info.lamports || 0) / 1_000_000_000;
  return { success: true, signature: sig, rentRefundSol };
}
```

**Hook in `execution/positions.js`** — after live sell write, non-blocking:
```js
if (boolSetting('rent_refund_enabled', true)) {
  setTimeout(async () => {
    const refund = await closeEmptyTokenAccount(position.mint);
    if (refund?.success) {
      db.prepare(`INSERT INTO dry_run_trades ... side='rent_refund' reason='A6_RENT_REFUND' ...`).run(...);
    }
  }, 5000);  // delay to let the sell settle
}
```

Setting default: `rent_refund_enabled: 'true'`.

---

## 7. Aggregator Helper (conditional fetch to skip unused RPC calls)

```js
async function fetchPonyinChecks(mint, holders, opts = {}) {
  const { skipMintAuthority, skipWalletAge, skipBalances, skipGas } = opts;
  const result = {};
  if (!skipMintAuthority) result.mintAuthority = await fetchMintAuthority(mint);
  if (!skipWalletAge && holders?.holders?.length) result.holderAges = await fetchHolderAgeStats(holders.holders, 10);
  if (!skipBalances && holders?.holders?.length) result.holderBalances = await fetchTopHolderBalances(holders.holders, 10);
  if (!skipGas) result.networkPriorityFee = await fetchRecentPriorityFee();
  return result;
}
```

Call-site in `candidateBuilder.js` `buildCandidate()` — only fetch what strategy uses:
```js
const ponyinNeedsMintAuth = !!(strat.require_mint_revoked || strat.require_freeze_revoked);
const ponyinNeedsAges = strat.max_fresh_holder_ratio > 0;
const ponyinNeedsBalances = strat.max_weak_holder_ratio > 0;
const ponyinNeedsGas = strat.max_network_priority_fee > 0;
const ponyin = (ponyinNeedsMintAuth || ponyinNeedsAges || ponyinNeedsBalances || ponyinNeedsGas)
  ? await fetchPonyinChecks(mint, holders, {
      skipMintAuthority: !ponyinNeedsMintAuth,
      skipWalletAge: !ponyinNeedsAges,
      skipBalances: !ponyinNeedsBalances,
      skipGas: !ponyinNeedsGas,
    })
  : null;
// ...attach to candidate.ponyin
```

Backward compat: strategies without the new fields → `ponyin = null` → zero RPC overhead, zero behavior change.

---

## 8. Ponyin-Tuned Strategy Seeds

**`sniper` retuned** (default enabled=1):
- `require_mint_revoked: true`, `require_freeze_revoked: true`
- `max_top20_holder_percent: 85` (was 100)
- `trending_max_bundler_rate: 0.35` (was 0.5)
- `partial_tp: true, partial_tp_at_percent: 35, partial_tp_sell_percent: 35` (anti one-clip per A9)
- `trailing_percent: 25` (was 20)
- `min_gmgn_total_fee_sol: 15` (was 10 — stricter wash-trading filter per BAB 2)
- `llm_min_confidence: 65` (was 50)

**New `ponyin_scalp`** (A7 Instant Scalping, rule-based `use_llm: false`):
- `token_age_max_ms: 1_800_000` (30 min fresh only)
- `min_mcap_usd: 3000, max_mcap_usd: 100_000`
- `max_fresh_holder_ratio: 0.5, max_weak_holder_ratio: 0.6, max_network_priority_fee: 1_000_000`
- `tp_percent: 60` (A7 sweet spot)
- `max_hold_ms: 1_800_000` (scalp = fast)

**New `day_phase`** (Bonus Strat, partial_dip entry):
- `entry_mode: 'partial_dip', mark_position_fraction: 0.1, dca_trigger_percent: -12`
- `token_age_max_ms: 1_209_600_000` (14 days — trending 1-2 weeks ago)
- `min_mcap_usd: 1_000_000, max_mcap_usd: 50_000_000` (FDV $1M+)
- `max_ath_distance_pct: -50` (must already dip 50%+)
- `max_hold_ms: 604_800_000` (7 days max hold)

---

## 9. Verification Checklist

```bash
cd ~/charon
source ~/.nvm/nvm.sh && nvm use 20
npm install              # pulls @solana/spl-token
npm run check            # syntax on all modified files
node -e "import('./src/enrichment/jupiter.js').then(m => console.log(Object.keys(m).sort().join(',')))"
node -e "import('./src/liveExecutor.js').then(m => console.log(Object.keys(m).sort().join(',')))"
```

Expected exports:
- `jupiter.js` should include `fetchMintAuthority`, `fetchHolderAgeStats`, `fetchTopHolderBalances`, `fetchRecentPriorityFee`, `fetchPonyinChecks`
- `liveExecutor.js` should include `closeEmptyTokenAccount`

**Extend `package.json` check script** to cover the files you modified:
```json
"check": "node --check index.js && node --check src/app.js && node --check src/config.js && node --check src/liveExecutor.js && node --check src/enrichment/jupiter.js && node --check src/pipeline/candidateBuilder.js && node --check src/execution/positions.js && node --check src/db/positions.js && node --check src/db/connection.js"
```

---

## 10. Pitfalls Hit During Implementation

1. **`INSERT OR IGNORE` strategy seeds don't overwrite existing DB rows.** If user has an old `charon.sqlite`, retuned sniper values won't apply until they drop the `strategies` row or use `/stratset` per field.
2. **`const pnlPercent` cannot be reassigned** — DCA logic needs `let pnlPercent` + `let pnlSol`. Verify they're already `let` before adding DCA block.
3. **`position` parameter reassignment** — mutating `position = { ...position, ... }` inside `refreshPosition` is fine (JS param, not const) but the downstream code needs to see the new values. Reassign before the tpHit/slHit calculation.
4. **RPC throttle** — `await new Promise(r => setTimeout(r, 50))` between holder-sample RPC calls prevents 429s on shared Helius plans.
5. **Caches are module-scoped Maps** — don't forget TTLs; in-process only (fine for single-instance Charon).
6. **Rent refund only works in `live` mode** — `closeEmptyTokenAccount` returns `{skipped: true, reason: 'no_wallet'}` when liveWallet is null. Gated behind `boolSetting('rent_refund_enabled', true)` so users can disable.
7. **`setTimeout(async () => ...)` after live sell** — fire-and-forget is intentional (don't block exit telegram message on close-account confirmation).
