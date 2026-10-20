#!/usr/bin/env python3
"""
Charon Bot Live Mode Audit
Quick snapshot of live trading state, wallet balance, and daily PnL.
Run from ~/charon directory.
"""

import sqlite3
import requests
from datetime import datetime

def get_wallet_balance():
    """Query Helius RPC for current wallet balance."""
    helius_key = "7b9774eb-e198-4d5d-8756-3bfaf03505a0"
    rpc_url = f"https://mainnet.helius-rpc.com/?api-key={helius_key}"
    wallet = "5j37jsGxkB5Zs5Hgfr1UdubHeBGTqzwCUgaAjQWxq2aq"
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet]
    }
    
    try:
        response = requests.post(rpc_url, json=payload, timeout=10)
        balance_lamports = response.json()['result']['value']
        return balance_lamports / 1e9
    except Exception as e:
        print(f"⚠️  Could not fetch balance: {e}")
        return None

def audit_live_mode():
    """Audit live mode trading state."""
    conn = sqlite3.connect('charon.sqlite')
    c = conn.cursor()
    
    print("=" * 70)
    print("CHARON BOT — LIVE MODE AUDIT")
    print(f"{datetime.now().isoformat()}")
    print("=" * 70)
    
    # Wallet balance
    print("\n[1] WALLET")
    print("-" * 70)
    balance = get_wallet_balance()
    if balance:
        print(f"  Balance: {balance:.4f} SOL")
    else:
        c.execute("SELECT value FROM settings WHERE key='wallet_balance_sol'")
        row = c.fetchone()
        balance = float(row[0]) if row else 0
        print(f"  Balance (cached): {balance:.4f} SOL")
    
    # Open positions
    print("\n[2] OPEN POSITIONS")
    print("-" * 70)
    c.execute("""
    SELECT id, symbol, entry_price, entry_mcap, size_sol, opened_at_ms
    FROM dry_run_positions
    WHERE status='open' AND execution_mode='live'
    ORDER BY opened_at_ms DESC
    """)
    open_pos = c.fetchall()
    print(f"  Open: {len(open_pos)}/3")
    for pos in open_pos:
        pos_id, symbol, entry_price, entry_mcap, size_sol, opened_at = pos
        ts = datetime.fromtimestamp(opened_at/1000).strftime('%H:%M:%S')
        print(f"    Pos {pos_id}: {symbol} | ${entry_price:.8f} @ ${entry_mcap:,.0f} | {size_sol}SOL | {ts}")
    
    # Closed positions (last 24h)
    print("\n[3] CLOSED POSITIONS (LAST 24H)")
    print("-" * 70)
    c.execute("""
    SELECT id, symbol, COALESCE(pnl_percent, 0), COALESCE(pnl_sol, 0), exit_reason, closed_at_ms
    FROM dry_run_positions
    WHERE status='closed' AND execution_mode='live' AND closed_at_ms > (strftime('%s', 'now') * 1000 - 86400000)
    ORDER BY closed_at_ms DESC
    LIMIT 10
    """)
    closed = c.fetchall()
    print(f"  Closed (24h): {len(closed)}")
    for pos in closed:
        pos_id, symbol, pnl_pct, pnl_sol, reason, closed_at = pos
        emoji = "🟢" if pnl_sol >= 0 else "🔴"
        pnl_sign = "+" if pnl_sol >= 0 else ""
        ts = datetime.fromtimestamp(closed_at/1000).strftime('%H:%M:%S')
        print(f"    {emoji} Pos {pos_id}: {symbol} | {pnl_sign}{pnl_pct:.1f}% ({pnl_sign}{pnl_sol:.4f}SOL) | {reason} | {ts}")
    
    # Daily PnL
    print("\n[4] DAILY PnL")
    print("-" * 70)
    c.execute("""
    SELECT 
      DATE(closed_at_ms / 1000, 'unixepoch') as trade_date,
      COUNT(*) as trade_count,
      SUM(CASE WHEN pnl_sol > 0 THEN 1 ELSE 0 END) as wins,
      SUM(CASE WHEN pnl_sol < 0 THEN 1 ELSE 0 END) as losses,
      SUM(pnl_sol) as daily_pnl,
      AVG(pnl_percent) as avg_pnl_pct
    FROM dry_run_positions
    WHERE status='closed' AND execution_mode='live'
    GROUP BY trade_date
    ORDER BY trade_date DESC
    LIMIT 7
    """)
    daily = c.fetchall()
    for row in daily:
        trade_date, trade_count, wins, losses, daily_pnl, avg_pnl_pct = row
        emoji = "🟢" if (daily_pnl or 0) >= 0 else "🔴"
        pnl_sign = "+" if (daily_pnl or 0) >= 0 else ""
        print(f"    {emoji} {trade_date} | {trade_count} trades · {wins}W/{losses}L · {pnl_sign}{daily_pnl:.4f}SOL ({pnl_sign}{avg_pnl_pct:.1f}%)")
    
    # Strategy config
    print("\n[5] STRATEGY CONFIG")
    print("-" * 70)
    c.execute("SELECT config_json FROM strategies WHERE enabled=1 LIMIT 1")
    config_row = c.fetchone()
    if config_row:
        import json
        config = json.loads(config_row[0])
        print(f"  TP: {config.get('tp_percent')}% (LOCKED)")
        print(f"  SL: {config.get('sl_percent')}% (LOCKED)")
        print(f"  Trailing: {config.get('trailing_enabled')} ({config.get('trailing_percent')}%)")
        print(f"  Position size: {config.get('position_size_sol')} SOL")
        print(f"  Max open: {config.get('max_open_positions')}")
    
    # Bot status
    print("\n[6] BOT STATUS")
    print("-" * 70)
    import subprocess
    try:
        result = subprocess.run(['pm2', 'status', 'charon'], capture_output=True, text=True)
        if 'online' in result.stdout:
            print("  Status: ONLINE ✓")
        else:
            print("  Status: CHECK PM2")
    except:
        print("  Status: Could not check PM2")
    
    print("\n" + "=" * 70)
    print("END AUDIT")
    print("=" * 70)
    
    conn.close()

if __name__ == '__main__':
    audit_live_mode()
