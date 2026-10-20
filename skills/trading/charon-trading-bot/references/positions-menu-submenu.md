# Positions Menu Submenu Structure

## Problem
Monolithic positions menu mixes open and closed positions in single view. With many positions (20+), becomes cluttered and hard to navigate. User wants clean separation.

## Solution: Hierarchical Menu with Submenus

**Files Modified:**
- `src/telegram/menus.js` — text functions + keyboard functions
- `src/telegram/callbacks.js` — callback handlers

### Menu Hierarchy

```
/positions (main)
  ├─ 🟢 Open (submenu)
  │  └─ [list all open positions]
  │     └─ ← Back
  └─ 🔴 Closed (submenu)
     └─ [list last 20 closed positions]
        └─ ← Back
```

### Implementation

#### 1. Main Positions Text (Summary Only)

**File:** `src/telegram/menus.js`

```javascript
export function positionsText() {
  const walletBalance = Number(setting('wallet_balance_sol', '0.0')) || 0;
  
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
    `💰 Wallet: <b>${fmtSol(walletBalance)} SOL</b>`,
    `📊 Total PnL: <b>${totalPnl >= 0 ? '+' : ''}${fmtSol(totalPnl)} SOL</b>`,
    `📈 Win/Loss: <b>${wins}W / ${losses}L</b>`,
    `📂 Terbuka: <b>${openCountAll}</b> · Tertutup: <b>${closedCount}</b>`,
    '',
    'Pilih submenu untuk detail:',
  ];
  
  return lines.filter(Boolean).join('\n');
}
```

**Output:**
```
📍 Posisi

💰 Wallet: 0.3097 SOL
📊 Total PnL: +0.1412 SOL
📈 Win/Loss: 41W / 81L
📂 Terbuka: 3 · Tertutup: 133

Pilih submenu untuk detail:
```

#### 2. Open Positions Submenu

```javascript
export function openPositionsText() {
  const openRows = db.prepare(`SELECT * FROM dry_run_positions WHERE status = 'open' ORDER BY opened_at_ms DESC`).all();
  const walletBalance = Number(setting('wallet_balance_sol', '0.0')) || 0;
  
  const lines = [
    '🟢 <b>Posisi Terbuka</b>',
    '',
    `💰 Wallet: <b>${fmtSol(walletBalance)} SOL</b>`,
    `📂 Total: <b>${openRows.length}</b> posisi`,
    '',
  ];
  
  if (openRows.length) {
    lines.push(...openRows.map(p => {
      const pnl = p.high_water_mcap && p.entry_mcap 
        ? ((p.high_water_mcap / p.entry_mcap) - 1) * 100 
        : 0;
      const emoji = pnl >= 0 ? '🟢' : '🔴';
      return `${emoji} <b>${escapeHtml(p.symbol || short(p.mint))}</b> · ${fmtUsd(p.entry_mcap)} · ${pnl >= 0 ? '+' : ''}${fmtPct(pnl)}`;
    }));
  } else {
    lines.push('Belum ada posisi terbuka.');
  }
  
  return lines.filter(Boolean).join('\n');
}
```

**Output:**
```
🟢 Posisi Terbuka

💰 Wallet: 0.3097 SOL
📂 Total: 3 posisi

🟢 NUTZ · $13.8K · +1.3%
🟢 Phoenix · $16.9K · +13.7%
🟢 PSCAPE · $26.1K · +2.4%
```

#### 3. Closed Positions Submenu

```javascript
export function closedPositionsText() {
  const closedRows = db.prepare(`SELECT * FROM dry_run_positions WHERE status = 'closed' ORDER BY closed_at_ms DESC LIMIT 20`).all();
  const walletBalance = Number(setting('wallet_balance_sol', '0.0')) || 0;
  
  const totals = db.prepare(`
    SELECT
      SUM(CASE WHEN pnl_sol > 0 THEN 1 ELSE 0 END) AS wins,
      SUM(CASE WHEN pnl_sol < 0 THEN 1 ELSE 0 END) AS losses
    FROM dry_run_positions
    WHERE status = 'closed'
  `).get();
  
  const lines = [
    '🔴 <b>Posisi Tertutup</b>',
    '',
    `💰 Wallet: <b>${fmtSol(walletBalance)} SOL</b>`,
    `📂 Total: <b>${closedRows.length}</b> posisi · <b>${totals?.wins || 0}W</b> / <b>${totals?.losses || 0}L</b>`,
    '',
  ];
  
  if (closedRows.length) {
    lines.push(...closedRows.map(p => {
      const emoji = (p.pnl_sol || 0) >= 0 ? '🟢' : '🔴';
      const pnlSol = p.pnl_sol || 0;
      return `${emoji} <b>${escapeHtml(p.symbol || short(p.mint))}</b> · ${p.exit_reason} · ${pnlSol >= 0 ? '+' : ''}${fmtSol(pnlSol)} SOL`;
    }));
  } else {
    lines.push('Belum ada posisi tertutup.');
  }
  
  return lines.filter(Boolean).join('\n');
}
```

**Output:**
```
🔴 Posisi Tertutup

💰 Wallet: 0.3097 SOL
📂 Total: 133 posisi · 41W / 81L

🟢 NUTZ · manual_swap · +0.0000 SOL
🟢 HANSA · manual_swap · +0.0000 SOL
🟢 ANALYST · manual_swap · +0.0000 SOL
🔴 HIM · SL · -0.0118 SOL
🔴 Toly · SL · -0.0112 SOL
...
```

#### 4. Keyboard Functions

```javascript
export function positionsKeyboard() {
  return {
    reply_markup: {
      inline_keyboard: [
        [
          { text: '🟢 Open', callback_data: 'menu:positions_open' },
          { text: '🔴 Closed', callback_data: 'menu:positions_closed' },
        ],
        [
          { text: '← Back', callback_data: 'menu:main' },
        ],
      ],
    },
  };
}

export function openPositionsKeyboard() {
  return {
    reply_markup: {
      inline_keyboard: [
        [
          { text: '← Back', callback_data: 'menu:positions' },
        ],
      ],
    },
  };
}

export function closedPositionsKeyboard() {
  return {
    reply_markup: {
      inline_keyboard: [
        [
          { text: '← Back', callback_data: 'menu:positions' },
        ],
      ],
    },
  };
}
```

#### 5. Callback Handlers

**File:** `src/telegram/callbacks.js`

Add imports:
```javascript
import {
  // ... existing
  openPositionsText,
  closedPositionsText,
  positionsKeyboard,
  openPositionsKeyboard,
  closedPositionsKeyboard,
} from './menus.js';
```

Add handlers in `handleCallback()`:
```javascript
if (data === 'menu:positions') return editMenuMessage(query, positionsText(), positionsKeyboard());
if (data === 'menu:positions_open') return editMenuMessage(query, openPositionsText(), openPositionsKeyboard());
if (data === 'menu:positions_closed') return editMenuMessage(query, closedPositionsText(), closedPositionsKeyboard());
```

### Benefits

1. **Clean hierarchy** — Main menu shows summary, submenus show details
2. **No clutter** — Open and closed positions separated
3. **Easy navigation** — Back buttons to return to parent menu
4. **Scalable** — Works with 3 positions or 300 positions
5. **Consistent** — Follows Telegram inline keyboard patterns

### Verification

```bash
# Restart bot
pm2 restart charon

# Test in Telegram
# /positions → shows summary + [🟢 Open | 🔴 Closed] buttons
# Click 🟢 Open → shows all open positions + [← Back] button
# Click ← Back → returns to summary
```

### Future Enhancements

- Add pagination for closed positions (show 20 at a time, "Next" button)
- Add position detail view (click position → show entry/exit/PnL details)
- Add filter options (by date, by exit reason, by PnL range)
