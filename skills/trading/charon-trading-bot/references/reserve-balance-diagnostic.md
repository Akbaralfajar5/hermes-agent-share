# Reserve Balance Diagnostic

**Error:** "Insufficient SOL balance. Need 0.3000 SOL including reserve."  
**Root cause:** `wallet_balance < (entry_amount + reserve)`

## The Check

`src/execution/router.js`, line ~35:

```javascript
const amountLamports = Math.floor((strat.position_size_sol ?? numSetting('dry_run_buy_sol', 0.1)) * 1_000_000_000);
const balance = await liveWalletBalanceLamports();
if (balance < amountLamports + LIVE_MIN_SOL_RESERVE_LAMPORTS) {
  throw new Error(`Insufficient SOL balance. Need ${fmtSol((amountLamports + LIVE_MIN_SOL_RESERVE_LAMPORTS) / 1_000_000_000)} SOL including reserve.`);
}
```

## Config Sources

### 1. Entry Size

**Priority order:**
1. Strategy `position_size_sol` (database)
2. `.env` `DRY_RUN_BUY_SOL` (fallback)
3. Hardcoded default: `0.1 SOL`

**Check strategy config:**
```bash
cd ~/charon && node -e "
const db = require('better-sqlite3')('charon.sqlite');
const strat = db.prepare('SELECT config_json FROM strategies WHERE enabled=1').get();
const config = JSON.parse(strat.config_json);
console.log('position_size_sol:', config.position_size_sol || 'NOT SET');
"
```

**Check .env:**
```bash
grep DRY_RUN_BUY_SOL ~/charon/.env
```

### 2. Reserve

**Source:** `.env` `LIVE_MIN_SOL_RESERVE` (default: `0.02`)

**Check:**
```bash
grep LIVE_MIN_SOL_RESERVE ~/charon/.env
```

**Code location:** `src/config.js`, line ~40:
```javascript
export const LIVE_MIN_SOL_RESERVE_LAMPORTS = Math.floor(Number(process.env.LIVE_MIN_SOL_RESERVE || 0.02) * 1_000_000_000);
```

## Example Failure

**Session:** May 16, 2026  
**Wallet balance:** 0.2853 SOL  
**Entry size:** 0.2 SOL (from strategy `position_size_sol`)  
**Reserve:** 0.1 SOL (from `.env` override)  
**Required:** 0.2 + 0.1 = **0.3 SOL**  
**Result:** ❌ Insufficient (0.2853 < 0.3)

## Solutions

### Option A: Lower Reserve (Recommended)

Reserve is for transaction fees only. 0.02 SOL is sufficient for most swaps.

```bash
# Edit .env
sed -i 's/LIVE_MIN_SOL_RESERVE=0.1/LIVE_MIN_SOL_RESERVE=0.02/' ~/charon/.env
pm2 restart charon
```

**New calculation:** 0.2 + 0.02 = 0.22 SOL ✅ (0.2853 > 0.22)

### Option B: Lower Entry Size

```bash
# Edit .env
echo "DRY_RUN_BUY_SOL=0.15" >> ~/charon/.env
pm2 restart charon
```

**New calculation:** 0.15 + 0.1 = 0.25 SOL ✅ (0.2853 > 0.25)

### Option C: Update Strategy Config

```bash
cd ~/charon && node -e "
const db = require('better-sqlite3')('charon.sqlite');
const strat = db.prepare('SELECT id, config_json FROM strategies WHERE enabled=1').get();
const config = JSON.parse(strat.config_json);
config.position_size_sol = 0.15;
db.prepare('UPDATE strategies SET config_json=? WHERE id=?').run(JSON.stringify(config), strat.id);
console.log('Updated position_size_sol to 0.15');
"
pm2 restart charon
```

## Verification

After fix, check next entry attempt:

```bash
tail -f ~/.pm2/logs/charon-out.log | grep -E "Insufficient|live.*buy|entry.*executed"
```

Should see:
```
[router] live_entry_executed: position 140, swap 2DoAYPw...
```

No more "Insufficient SOL balance" errors.

## Pitfall

**Don't confuse with wallet balance query.** The error happens BEFORE swap execution, during balance check. Even if wallet has enough SOL for the swap itself, bot requires `entry_amount + reserve` to proceed.

**Reserve purpose:** Cover transaction fees, rent exemptions, and priority fees. Default 0.02 SOL is sufficient. Higher values (0.1+) are overly conservative and cause unnecessary failures.

## Related

- **Wallet balance query:** `references/wallet-and-rpc.md`
- **Strategy config:** Main skill section "Strategy Configuration"
- **Entry size defaults:** `src/db/connection.js` line ~320 (strategy defaults)

## Problem

Bot fails to execute BUY decisions with error:
```
Error: Insufficient SOL balance. Need 0.3000 SOL including reserve.
```

Despite having sufficient balance for the entry amount alone.

## Root Cause

Bot checks: `wallet_balance >= entry_amount + reserve_amount`

The reserve is a safety buffer for transaction fees and is configured via `.env`:
```bash
LIVE_MIN_SOL_RESERVE=0.1  # Default 0.02, may be overridden
```

Entry amount comes from:
1. Strategy config `position_size_sol` (database)
2. OR `.env` `DRY_RUN_BUY_SOL` (fallback default, typically 0.1)

## Diagnostic Workflow

### 1. Check Current Balance

```bash
cd ~/charon && node -e "
const { Connection, PublicKey, LAMPORTS_PER_SOL } = require('@solana/web3.js');
const conn = new Connection('https://mainnet.helius-rpc.com/?api-key=7b9774eb-e198-4d5d-8756-3bfaf03505a0');
(async () => {
  const wallet = new PublicKey('5j37jsGxkB5Zs5Hgfr1UdubHeBGTqzwCUgaAjQWxq2aq');
  const bal = await conn.getBalance(wallet);
  console.log('Balance:', (bal / LAMPORTS_PER_SOL).toFixed(4), 'SOL');
})();
"
```

### 2. Check Reserve Setting

```bash
cd ~/charon && grep LIVE_MIN_SOL_RESERVE .env
# Expected: LIVE_MIN_SOL_RESERVE=0.02 (or 0.1 if overridden)
```

### 3. Check Entry Size

**From strategy config:**
```bash
cd ~/charon && node -e "
const db = require('better-sqlite3')('charon.sqlite');
const strat = db.prepare('SELECT config_json FROM strategies WHERE enabled=1').get();
const config = JSON.parse(strat.config_json);
console.log('Entry size:', config.position_size_sol || 'NOT SET (uses DRY_RUN_BUY_SOL)');
"
```

**From .env fallback:**
```bash
cd ~/charon && grep DRY_RUN_BUY_SOL .env
# Expected: DRY_RUN_BUY_SOL=0.1 (or custom value)
```

### 4. Calculate Required Balance

```
Required = entry_size + reserve
```

**Example failure case:**
- Balance: 0.2853 SOL
- Entry: 0.2 SOL (from strategy or DRY_RUN_BUY_SOL)
- Reserve: 0.1 SOL (from LIVE_MIN_SOL_RESERVE)
- **Required: 0.3 SOL**
- **Result: FAIL** (0.2853 < 0.3)

## Solutions

### Option A: Lower Reserve (Recommended)

Reserve is only for transaction fees. 0.02 SOL is sufficient for most Solana swaps.

```bash
cd ~/charon
# Edit .env
sed -i 's/LIVE_MIN_SOL_RESERVE=.*/LIVE_MIN_SOL_RESERVE=0.02/' .env

# Restart bot
pm2 restart charon
```

**Result:** Required = 0.2 + 0.02 = 0.22 SOL ✅ (0.2853 > 0.22)

### Option B: Lower Entry Size

Reduce position size to fit within available balance:

```bash
cd ~/charon
# Edit .env
sed -i 's/DRY_RUN_BUY_SOL=.*/DRY_RUN_BUY_SOL=0.15/' .env

# OR update strategy config in database
node -e "
const db = require('better-sqlite3')('charon.sqlite');
const strat = db.prepare('SELECT id, config_json FROM strategies WHERE enabled=1').get();
const config = JSON.parse(strat.config_json);
config.position_size_sol = 0.15;
db.prepare('UPDATE strategies SET config_json=? WHERE id=?').run(JSON.dumps(config), strat.id);
"

# Restart bot
pm2 restart charon
```

**Result:** Required = 0.15 + 0.1 = 0.25 SOL ✅ (0.2853 > 0.25)

### Option C: Add More SOL to Wallet

Transfer additional SOL to wallet to meet reserve + entry requirements.

## Verification

After applying fix, monitor logs for successful entry:

```bash
tail -f ~/.pm2/logs/charon-out.log | grep -E "live.*buy|entry.*executed|Insufficient"
```

Expected output:
```
[router] live_entry_executed: positionId=139, mint=Vf7GDT..., amountLamports=200000000
```

No more "Insufficient SOL balance" errors.

## Code Reference

**File:** `src/execution/router.js`

```javascript
const amountLamports = Math.floor((strat.position_size_sol ?? numSetting('dry_run_buy_sol', 0.1)) * 1_000_000_000);
const balance = await liveWalletBalanceLamports();
if (balance < amountLamports + LIVE_MIN_SOL_RESERVE_LAMPORTS) {
  throw new Error(`Insufficient SOL balance. Need ${fmtSol((amountLamports + LIVE_MIN_SOL_RESERVE_LAMPORTS) / 1_000_000_000)} SOL including reserve.`);
}
```

**Config:** `src/config.js`

```javascript
export const LIVE_MIN_SOL_RESERVE_LAMPORTS = Math.floor(Number(process.env.LIVE_MIN_SOL_RESERVE || 0.02) * 1_000_000_000);
```

## Related Issues

- **LLM decisions not executing** — If bot makes BUY decisions but no positions created, check reserve balance first before debugging LLM confidence thresholds or agent_enabled settings.
- **Manual exits reducing balance** — After manual Phantom swaps, wallet balance may drop below reserve threshold. Re-check balance after any manual intervention.
