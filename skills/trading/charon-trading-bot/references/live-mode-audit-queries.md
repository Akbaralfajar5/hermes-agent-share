# Charon Live Mode Audit — SQL Queries

## Wallet & Balance

```sql
SELECT label, address FROM saved_wallets;
```

**Current state (May 16, 2026):**
- Wallet: 5j37jsGxkB5Zs5Hgfr1UdubHeBGTqzwCUgaAjQWxq2aq
- Balance: 0.2268 SOL
- Reserve: 0.1 SOL
- Available: 0.1268 SOL

---

## Open Live Positions

```sql
SELECT 
  id, mint, symbol, entry_price, entry_mcap, size_sol, 
  opened_at_ms, high_water_price, high_water_mcap
FROM dry_run_positions
WHERE status='open' AND execution_mode='live'
ORDER BY opened_at_ms DESC;
```

**Output format:**
- Pos ID: symbol (mint[:8]...)
- Entry: $price @ $mcap | High: $hw_price @ $hw_mcap (+gain%)
- Size: X SOL | Opened: HH:MM:SS

---

## Closed Live Positions (Last 6 Hours)

```sql
SELECT 
  id, mint, symbol, entry_price, exit_price, 
  pnl_percent, pnl_sol, closed_at_ms, exit_reason
FROM dry_run_positions
WHERE status='closed' AND execution_mode='live'
  AND closed_at_ms > (strftime('%s', 'now') * 1000 - 21600000)
ORDER BY closed_at_ms DESC;
```

**Output format:**
```
Symbol  ±PnL%  (±PnL_SOL)  EXIT_REASON
$entry → $exit | HH:MM:SS
```

---

## Live Mode Summary Stats

```sql
SELECT 
  COUNT(*) as total_trades,
  SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) as open_count,
  SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) as closed_count,
  SUM(CASE WHEN status='closed' AND pnl_percent >= 0 THEN 1 ELSE 0 END) as wins,
  SUM(CASE WHEN status='closed' AND pnl_percent < 0 THEN 1 ELSE 0 END) as losses,
  AVG(CASE WHEN status='closed' THEN pnl_percent ELSE NULL END) as avg_pnl_pct,
  SUM(CASE WHEN status='closed' THEN pnl_sol ELSE 0 END) as total_pnl_sol
FROM dry_run_positions
WHERE execution_mode='live';
```

**Calculations:**
- Win rate: `wins / (wins + losses) * 100`
- Slots available: `3 - open_count`

---

## Recent Live Decisions (Last 6 Hours)

```sql
SELECT verdict, COUNT(*) as count
FROM decision_logs
WHERE mode LIKE '%live%' 
  AND at_ms > (strftime('%s', 'now') * 1000 - 21600000)
GROUP BY verdict
ORDER BY count DESC;
```

---

## Check Specific Token Status

```sql
SELECT 
  id, mint, symbol, status, execution_mode, 
  entry_price, entry_mcap, size_sol, 
  opened_at_ms, closed_at_ms, exit_reason
FROM dry_run_positions
WHERE symbol = ?
ORDER BY opened_at_ms DESC
LIMIT 10;
```

**Example:** Check HANSA, NUTZ, ANALYST status
- Substitute `?` with token symbol
- Look for `status='open'` vs `status='closed'`
- Check `exit_reason` for close type (SL, TRAILING_TP, manual_close_to_free_live_slots, etc.)

---

## Pitfall: Stale Database State

If user reports open positions not found in DB:
1. Check `closed_at_ms` timestamp — may have just closed
2. Verify `exit_reason` — if `manual_close_to_free_live_slots`, position was intentionally closed
3. Ask user to confirm wallet holdings via Phantom/Solscan
4. Check for pending transactions on-chain (may not be synced to DB yet)

---

## Bot Configuration (Live Mode)

```sql
SELECT key, value FROM settings 
WHERE key IN (
  'trading_mode', 'max_open_positions', 'llm_min_confidence',
  'default_tp_percent', 'default_sl_percent', 
  'default_trailing_enabled', 'default_trailing_percent'
);
```

**Current config:**
- Mode: live
- Max open: 3
- LLM confidence: 60%
- TP: 50% | SL: -25%
- Trailing: enabled (20%)
