# Charon Live Web Dashboard

When the user asks "buatin website live untuk lihat posisi / PnL / LLM decisions", build a separate Node.js + plain-HTML dashboard at `~/charon-dashboard` that reads directly from `~/charon/charon.sqlite` (read-only). Do NOT add this inside the Charon repo — keep the bot and the viewer decoupled.

## Layout

```
~/charon-dashboard/
├── server.js          # Express + better-sqlite3 read-only API (port 5858)
├── public/index.html  # Single-file dark-mode dashboard, 4s auto-refresh
└── package.json
```

## API surface (server.js)

Single endpoint `/api/state` returns one consolidated payload:
```js
{
  strategy: { id, name, ... },     // active strategy from DB
  mode: 'dry_run'|'confirm'|'live',
  summary: { open, max, unrealized_pnl_sol, realized_pnl_sol, total_pnl_sol, win_rate, ... },
  open_positions: [...],            // computed unrealized PnL via Jupiter price refresh
  closed_positions: closedPositions(20),
  recent_decisions: recentDecisions(10),  // includes risks_json parsed
  recent_candidates: recentCandidates(15),
  ts: Date.now(),
}
```

Plus `/api/health` → `{ ok: true }`.

### Recent decisions query (must include risks)

```js
function recentDecisions(limit = 20) {
  const rows = db.prepare(`
    SELECT id, created_at_ms, verdict, confidence, reason, risks_json, selected_mint
    FROM llm_batches ORDER BY id DESC LIMIT ?
  `).all(limit);
  return rows.map(r => {
    let risks = [];
    try { risks = r.risks_json ? JSON.parse(r.risks_json) : []; } catch {}
    return { id: r.id, created_at_ms: r.created_at_ms, verdict: r.verdict,
             confidence: r.confidence, reason: r.reason, risks, selected_mint: r.selected_mint };
  });
}
```

`risks_json` is a JSON string column — always wrap parse in try/catch.

### Live PnL for open positions

For each open position, multiply price refresh by entry mcap ratio. Jupiter price API: batch up to 20 mints per call to `https://lite-api.jup.ag/price/v3?ids=mint1,mint2,...`. Cache result for ~15s to avoid hammering.

## UI conventions (the user preference)

The user wants:
- **Indonesian labels** in the LLM panel: header "🤖 Keputusan LLM (Bahasa Indonesia)", verdict map `BUY→BELI / WATCH→PANTAU / PASS→LEWATI`, "confidence→keyakinan", empty state "Belum ada keputusan LLM."
- **Reason as a highlighted block** with `border-left: 3px solid var(--accent)`, NOT muted small text. Reason is the most important field.
- **Risks as red chips** with ⚠ prefix, wrapped flex.
- Status badge map: `dry_run → 🧪`, `confirm → 🟡`, `live → 🔴`.
- PnL emoji: `🟢 >0`, `⚪ ≈0`, `🔴 <0`.
- Auto-refresh every 4 seconds.

CSS pattern for highlight box:
```css
.decision-reason {
  color: var(--text);
  margin-top: 8px;
  font-size: 12.5px;
  line-height: 1.55;
  background: rgba(255,255,255,0.02);
  padding: 8px 10px;
  border-radius: 6px;
  border-left: 3px solid var(--accent);
}
.risk-chip {
  font-size: 10.5px;
  background: var(--red-soft);
  color: var(--red);
  padding: 3px 8px;
  border-radius: 4px;
}
```

## Process management

Run via PM2 alongside the bot:
```bash
cd ~/charon-dashboard && pm2 start server.js --name charon-dashboard
pm2 save
```

Both `charon` and `charon-dashboard` run as separate PM2 processes. Don't merge them — dashboard restart should never affect the trading bot.

## Public exposure (Tencent Cloud VPS, IP 43.159.56.39)

Tencent Cloud security group blocks most ports by default. Two routes:

### Preferred: open the port in Tencent Cloud console

User opens port 5858 in Tencent Cloud security group → dashboard reachable at `http://43.159.56.39:5858`. Stable URL, no tunnel needed.

UFW must also allow:
```bash
sudo ufw allow 5858/tcp
```

### Fallback: Cloudflare quick tunnel

If user can't open the port, use `cloudflared`:
```bash
# Install once
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Run via PM2 to auto-restart
pm2 start "cloudflared tunnel --url http://localhost:5858 --no-autoupdate" --name charon-tunnel
```

Tunnel URL appears in `pm2 logs charon-tunnel` (e.g. `https://write-rider-antarctica-cigarette.trycloudflare.com`). **Quick tunnels rotate URL on every restart** — only use as temporary access. For permanent URL, user needs Cloudflare account + named tunnel.

When the port is opened in cloud console afterwards, **stop and delete the tunnel** to keep PM2 process list clean:
```bash
pm2 stop charon-tunnel && pm2 delete charon-tunnel && pm2 save
```

## Pitfalls

- **Don't write to charon.sqlite from the dashboard.** Open with `new Database(path, { readonly: true })`. The bot has writers; concurrent writes from a viewer can corrupt WAL state.
- **`sqlite3` CLI is not installed on this VPS.** Always use `node -e` with `better-sqlite3` for ad-hoc queries during dashboard development.
- **`decisions` is NOT a table.** The actual table is `llm_batches` (and `llm_decisions` for per-candidate). Schema audit:
  ```js
  db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all();
  ```
- **`risks_json` parsing in non-strict environments**: GMGN historic batches may have malformed JSON. Always try/catch and default to `[]`.
- **Cloudflared installation hangs on apt without log buffering**. Run via PM2 from the start instead of foreground capture.
