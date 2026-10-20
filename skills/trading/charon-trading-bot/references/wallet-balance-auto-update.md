# Wallet Balance Auto-Update Implementation

**Problem:** Telegram menu shows stale wallet balance after trades. `settings.wallet_balance_sol` is manual-update only and never auto-syncs.

**User preference:** Real-time query on every menu display (not periodic background sync) for immediate accuracy.

---

## Solution: Make agentText() Async with RPC Query

Convert `agentText()` from sync function to async, query real-time balance via `liveWalletBalanceLamports()` on every menu display.

### 1. Update agentText() Function

**File:** `~/charon/src/telegram/menus.js`

**Before:**
```javascript
export function agentText() {
  const strat = activeStrategy();
  const walletBalance = Number(setting('wallet_balance_sol', '0.0')) || 0;
  return [
    '🛶 <b>Charon Agent</b>',
    // ...
    `💰 Wallet: <b>${fmtSol(walletBalance)} SOL</b>`,
    // ...
  ].join('\\n');
}
```

**After:**
```javascript
export async function agentText() {
  const strat = activeStrategy();
  
  // Get real-time wallet balance
  let walletBalance = 0;
  try {
    const { liveWalletBalanceLamports } = await import('../liveExecutor.js');
    const balanceLamports = await liveWalletBalanceLamports();
    walletBalance = balanceLamports / 1_000_000_000;
  } catch (err) {
    // Fallback to cached value if live wallet not available
    walletBalance = Number(setting('wallet_balance_sol', '0.0')) || 0;
  }
  
  return [
    '🛶 <b>Charon Agent</b>',
    `Strategy: <b>${escapeHtml(strat.name)}</b>`,
    `Agent: <b>${boolSetting('agent_enabled', true) ? 'on' : 'off'}</b>`,
    `Mode: <b>${escapeHtml(tradingMode())}</b>`,
    `💰 Wallet: <b>${fmtSol(walletBalance)} SOL</b>`,
    `LLM: <b>${strat.use_llm && ENABLE_LLM && LLM_API_KEY ? 'configured' : 'disabled'}</b>`,
    `Confidence: ${fmtPct(strat.llm_min_confidence || numSetting('llm_min_confidence', 75))}`,
    `Open positions: ${openPositionCount()}/${strat.max_open_positions || 'unlimited'}`,
    `Batch candidates: ${numSetting('llm_candidate_pick_count', 10)}`,
    `Candidate freshness: ${Math.round(numSetting('llm_candidate_max_age_ms', 600000) / 1000)}s`,
    `Size: ${fmtSol(strat.position_size_sol)} SOL`,
    `TP/SL: ${fmtPct(strat.tp_percent)} / ${fmtPct(strat.sl_percent)}`,
    `Trailing: ${strat.trailing_enabled ? fmtPct(strat.trailing_percent) : 'off'}`,
  ].join('\\n');
}
```

---

### 2. Update All Callers to Await

**File:** `~/charon/src/telegram/callbacks.js`

Find all `agentText()` calls and add `await`:

```javascript
// Line ~47
if (data === 'menu:agent') {
  return editMenuMessage(query, await agentText(), agentKeyboard());
}

// Line ~51
if (data === 'toggle:agent') {
  setSetting('agent_enabled', boolSetting('agent_enabled', true) ? 'false' : 'true');
  return editMenuMessage(query, await agentText(), agentKeyboard());
}

// Line ~65
if (data === 'menu:settings') return editMenuMessage(query, `${await agentText()}\\n\\n${filtersText()}`, navKeyboard([
  // ...
]));

// Line ~282 (in handleSetCallback)
const text = key.startsWith('default_') || key === 'dry_run_buy_sol' || key === 'trading_mode' || key === 'llm_min_confidence' || key === 'llm_candidate_pick_count' || key === 'llm_candidate_max_age_ms' || key === 'max_open_positions'
  ? await agentText()
  : filtersText();
```

**File:** `~/charon/src/telegram/menus.js`

```javascript
// Line ~595 (in sendAgentMenu function)
if (query) return editMenuMessage(query, await agentText(), keyboard);
const { bot } = await import('./bot.js');
await bot.sendMessage(chatId, await agentText(), { parse_mode: 'HTML', ...keyboard });
```

---

### 3. Verify RPC Function Exists

**File:** `~/charon/src/liveExecutor.js`

Function should already exist:

```javascript
export async function liveWalletBalanceLamports() {
  requireLiveExecution();
  return solanaConnection.getBalance(liveWallet.publicKey, 'confirmed');
}
```

This queries Helius RPC (from `SOLANA_RPC_URL` in `.env`) and returns balance in lamports.

---

## Result

- ✅ Menu displays **real-time balance** from blockchain on every open
- ✅ No manual sync needed
- ✅ Fallback to cached value if RPC unavailable
- ✅ ~200ms latency per menu open (acceptable for accuracy)

---

## Alternative Considered: Periodic Background Sync

**Rejected** — User chose real-time query for immediate accuracy. Background sync would require:
- Cron job or setInterval to poll RPC every N seconds
- Update `settings.wallet_balance_sol` in database
- Still shows stale data between sync intervals

Real-time query is simpler and more accurate.

---

## Verification

After restart, open Telegram bot and check Agent menu:

```
🛶 Charon Agent
Strategy: degen
Agent: on
Mode: live
💰 Wallet: 0.2414 SOL  ← Real-time from blockchain
LLM: configured
Confidence: 60%
Open positions: 0/1
Batch candidates: 10
Candidate freshness: 3600s
Size: 0.15 SOL
TP/SL: 999% / -75%
Trailing: 35%
```

Balance updates immediately after trades without manual intervention.

---

## Files Modified

1. `src/telegram/menus.js` — `agentText()` function (line ~117)
2. `src/telegram/callbacks.js` — 4 call sites (lines ~47, ~51, ~65, ~282)
3. `src/telegram/menus.js` — `sendAgentMenu()` function (line ~595)

Restart required: `pm2 restart charon`
