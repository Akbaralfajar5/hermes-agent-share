# Telegram Menu Updates — Wallet Balance Display

## Pattern: Add Wallet Balance to Bot Menus

When user requests wallet balance visible in Telegram bot menus (e.g., `/positions`, `/menu` → Agent).

### Step 1: Query & Store Wallet Balance

```python
import requests

helius_key = "7b9774eb-e198-4d5d-8756-3bfaf03505a0"  # from .env
rpc_url = f"https://mainnet.helius-rpc.com/?api-key={helius_key}"
wallet = "5j37jsGxkB5Zs5Hgfr1UdubHeBGTqzwCUgaAjQWxq2aq"

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getBalance",
    "params": [wallet]
}

response = requests.post(rpc_url, json=payload, timeout=10)
data = response.json()
balance_lamports = data['result']['value']
balance_sol = balance_lamports / 1e9

# Update database
c.execute("""
INSERT OR REPLACE INTO settings (key, value)
VALUES ('wallet_balance_sol', ?)
""", (str(balance_sol),))

c.execute("""
INSERT OR REPLACE INTO settings (key, value)
VALUES ('wallet_balance_updated_at_ms', ?)
""", (str(int(datetime.now().timestamp() * 1000)),))

conn.commit()
```

### Step 2: Update Menu Functions in `src/telegram/menus.js`

**File:** `src/telegram/menus.js`

**Function: `positionsText()`**
```javascript
export function positionsText() {
  const rows = allPositions(12);
  const openRows = db.prepare(`SELECT * FROM dry_run_positions WHERE status = 'open' ORDER BY opened_at_ms DESC LIMIT 6`).all();
  const closedRows = db.prepare(`SELECT * FROM dry_run_positions WHERE status = 'closed' ORDER BY closed_at_ms DESC LIMIT 6`).all();
  
  // Get wallet balance
  const walletBalance = Number(setting('wallet_balance_sol', '0.0')) || 0;
  
  if (!rows.length && !openRows.length && !closedRows.length) return '📍 <b>Posisi</b>\\n\\nBelum ada posisi.';
  
  const totals = db.prepare(`
    SELECT
      COALESCE(SUM(CASE WHEN status = 'closed' THEN pnl_sol ELSE 0 END), 0) AS total_pnl,
      SUM(CASE WHEN status = 'closed' AND pnl_sol > 0 THEN 1 ELSE 0 END) AS wins,
      SUM(CASE WHEN status = 'closed' AND pnl_sol < 0 THEN 1 ELSE 0 END) AS losses,
      SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) AS closed_count,
      SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS open_count
    FROM dry_run_positions
  `).get();
  
  const totalPnl = Number(totals?.total_pnl || 0);
  const wins = Number(totals?.wins || 0);
  const losses = Number(totals?.losses || 0);
  const closedCount = Number(totals?.closed_count || 0);
  const openCountAll = Number(totals?.open_count || 0);
  
  const lines = [
    '📍 <b>Posisi</b>',
    '',
    `💰 Wallet: <b>${fmtSol(walletBalance)} SOL</b>`,  // ← NEW LINE
    `📊 Total PnL: <b>${totalPnl >= 0 ? '+' : ''}${fmtSol(totalPnl)} SOL</b>`,
    `📈 Win/Loss: <b>${wins}W / ${losses}L</b>`,
    `📂 Terbuka: <b>${openCountAll}</b> · Tertutup: <b>${closedCount}</b>`,
    '',
    // ... rest of function
  ];
  
  return lines.filter(Boolean).join('\\n');
}
```

**Function: `agentText()`**
```javascript
export function agentText() {
  const strat = activeStrategy();
  const walletBalance = Number(setting('wallet_balance_sol', '0.0')) || 0;  // ← NEW LINE
  return [
    '🛶 <b>Charon Agent</b>',
    `Strategy: <b>${escapeHtml(strat.name)}</b>`,
    `Agent: <b>${boolSetting('agent_enabled', true) ? 'on' : 'off'}</b>`,
    `Mode: <b>${escapeHtml(tradingMode())}</b>`,
    `💰 Wallet: <b>${fmtSol(walletBalance)} SOL</b>`,  // ← NEW LINE
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

### Step 3: Restart Bot

```bash
cd ~/charon && pm2 restart charon
```

### Step 4: Verify

- Open Telegram bot
- Send `/positions` → should show `💰 Wallet: 0.3097 SOL` below title
- Send `/menu` → select Agent → should show wallet balance after Mode line

## Key Points

- **Import:** `setting()` function from `db/settings.js` to read wallet_balance_sol
- **Format:** Use `fmtSol()` helper to format SOL values with proper decimals
- **Fallback:** Default to `'0.0'` if setting not found
- **Update frequency:** Wallet balance updates when audit is run (RPC query + DB update)
- **Display:** Emoji `💰` for visual clarity in Telegram

## Related

- Helius RPC endpoint: `https://mainnet.helius-rpc.com/?api-key=<KEY>`
- Settings table: `INSERT OR REPLACE INTO settings (key, value) VALUES (...)`
- Format helpers: `fmtSol()`, `fmtPct()`, `fmtUsd()` from `format.js`
