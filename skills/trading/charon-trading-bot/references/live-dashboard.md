# Charon Live Dashboard

Standalone web dashboard that reads `charon.sqlite` directly and shows real-time positions, PnL, LLM decisions, and candidate pipeline. Runs as a separate PM2 process — does not touch the bot.

## Architecture

```
charon (PM2 #0)         — bot, writes to charon.sqlite
charon-dashboard (PM2 #1) — Express server, reads charon.sqlite (readonly), exposes /api/state
                            serves static index.html that polls /api/state every 4s
```

Dashboard is **read-only** — opens DB with `{ readonly: true }`. Cannot interfere with bot writes.

## Layout

```
~/charon-dashboard/
  server.js          — Express + better-sqlite3 + axios (Jupiter price enrichment)
  public/index.html  — single-file dashboard UI (dark theme, vanilla JS, no build step)
  package.json       — minimal: express, better-sqlite3, axios
```

## /api/state payload

```js
{
  strategy: { id, name, ... config },
  mode: 'dry_run' | 'confirm' | 'live',
  summary: {
    open_count, max_open, exposure_sol,
    unrealized_pnl_sol, realized_pnl_sol, total_pnl_sol,
    wins, losses, win_rate, avg_pnl_pct_closed
  },
  open_positions: [...],   // with live price enrichment
  closed_positions: [...], // last 20
  recent_decisions: [...], // last 10 from llm_batches with risks parsed
  recent_candidates: [...],// last 15 from candidates
  ts: Date.now(),
}
```

## LLM decisions panel — Indonesian labels

The dashboard MUST display LLM verdict, reason, and risks in Bahasa Indonesia (matching the bot's preference):

```js
const verdictLabel = { BUY: 'BELI', WATCH: 'PANTAU', PASS: 'LEWATI' };
// Header: "🤖 Keputusan LLM (Bahasa Indonesia)"
// Confidence label: "keyakinan 72%"
// Reason: highlighted box with accent border, full text shown (not truncated muted)
// Risks: array of red chips with ⚠ prefix, one per risk item
```

Server side, `recentDecisions(limit)` must parse `risks_json` from the `llm_batches` table:
```js
function recentDecisions(limit = 20) {
  const rows = db.prepare(`
    SELECT id, created_at_ms, verdict, confidence, reason, risks_json, selected_mint
    FROM llm_batches ORDER BY id DESC LIMIT ?
  `).all(limit);
  return rows.map(r => {
    let risks = [];
    try { risks = r.risks_json ? JSON.parse(r.risks_json) : []; } catch {}
    return { ...r, risks };
  });
}
```

## Hosting / Public Access

VPS port exposure path (Tencent Cloud, but applies generally):
1. UFW: `sudo ufw allow 5858/tcp`
2. Cloud security group: open port 5858 in the provider portal (UFW alone is not enough — cloud firewall sits in front)
3. Test: `curl http://<public-ip>:5858/api/health`

If cloud security group cannot be modified, fallback is **Cloudflare Quick Tunnel**:
```bash
# Install once
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared

# Run as PM2 process pointing to local dashboard
pm2 start cloudflared --name charon-tunnel -- tunnel --url http://localhost:5858
# Get URL from logs:
pm2 logs charon-tunnel --lines 30 --nostream | grep -oE "https://[a-z-]+\.trycloudflare\.com" | head -1
```

Quick tunnel URL changes on every restart. For stable URL, use a real Cloudflare account + named tunnel + DNS record.

Once direct port access is open, **delete the cloudflare tunnel** to keep PM2 clean — direct IP is faster anyway.

## Telemetry-only — no controls

The dashboard is **observation only**. It does not expose buy/sell/close endpoints. All control happens via Telegram. This is intentional:
- Read-only DB connection cannot mutate state
- No CSRF/auth needed because nothing is mutable
- If user wants controls in dashboard later, build them as separate authenticated endpoints, never as direct DB writes (avoid concurrent-write conflicts with the bot)

## PM2 setup

```bash
cd ~/charon-dashboard
pm2 start server.js --name charon-dashboard
pm2 save
```

After both processes are saved, `pm2 startup` ensures auto-start on reboot. Note: `systemctl status pm2-ubuntu` may show `enabled / inactive` — this is normal. The unit only activates on system boot; PM2 itself runs the processes once started.

## Design preferences (the user)

- Dark theme with cyan/green accents
- Auto-refresh 4s
- 8 stat cards across the top (open/max, unrealized, realized, total, win rate, avg pnl, exposure, strategy info)
- Open positions panel: progress bar visualizing SL→0→TP with current PnL marker
- Tags on positions: `MARK 10%`, `DCA DONE`, `PARTIAL TP`, `TRAIL ARMED`
- Closed positions table: exit reason colored by type
- LLM panel: large reason box, risks as red chips
- Candidate pipeline panel: status badge + failure reasons inline
