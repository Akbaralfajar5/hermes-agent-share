#!/usr/bin/env python3
"""
Verify Charon settings are synced across all three locations.
User often says "cek lagi semuanya biasanya belum ke setting"
"""
import sqlite3, json

DB_PATH = '/home/ubuntu/charon/charon.sqlite'

# Expected values (user's preferred settings)
EXPECTED = {
    'partial_tp': True,
    'partial_tp_at_percent': 50,
    'partial_tp_sell_percent': 50,
    'trailing_enabled': True,
    'trailing_percent': 35,
    'tp_percent': 0,  # unlimited
    'sl_percent': -30,
}

def main():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    
    print("=" * 50)
    print("🔍 CHARON SETTINGS VERIFICATION")
    print("=" * 50)
    
    # 1. Strategy Config
    print("\n📋 STRATEGY CONFIG (ponyin_scalp):")
    row = con.execute("SELECT config_json FROM strategies WHERE id='ponyin_scalp'").fetchone()
    cfg = json.loads(row['config_json']) if row else {}
    
    for key, expected in EXPECTED.items():
        actual = cfg.get(key)
        status = "✅" if actual == expected else "❌"
        print(f"  {status} {key}: {actual} (expected: {expected})")
    
    # 2. Global Settings
    print("\n📋 GLOBAL SETTINGS:")
    settings_map = {
        'partial_tp': ('partial_tp', 'true'),
        'partial_tp_at_percent': ('partial_tp_at_percent', '50'),
        'partial_tp_sell_percent': ('partial_tp_sell_percent', '50'),
        'trailing_enabled': ('trailing_enabled', 'true'),
        'trailing_percent': ('trailing_percent', '35'),
        'tp_percent': ('default_tp_percent', '0'),
        'sl_percent': ('default_sl_percent', '-30'),
    }
    
    for key, (db_key, expected) in settings_map.items():
        row = con.execute("SELECT value FROM settings WHERE key=?", (db_key,)).fetchone()
        actual = row['value'] if row else 'NOT SET'
        status = "✅" if actual == expected else "❌"
        print(f"  {status} {db_key}: {actual} (expected: {expected})")
    
    # 3. Open Positions
    print("\n📋 OPEN POSITIONS:")
    positions = con.execute("""
        SELECT id, symbol, tp_percent, sl_percent, trailing_enabled, trailing_percent
        FROM dry_run_positions WHERE status='open'
    """).fetchall()
    
    if not positions:
        print("  (no open positions)")
    else:
        for p in positions:
            tp_ok = "✅" if p['tp_percent'] == 0 else "❌"
            sl_ok = "✅" if p['sl_percent'] == -30 else "❌"
            trail_ok = "✅" if p['trailing_enabled'] == 1 and p['trailing_percent'] == 35 else "❌"
            print(f"  {p['symbol']}: TP={tp_ok}{p['tp_percent']}% SL={sl_ok}{p['sl_percent']}% Trail={trail_ok}{p['trailing_percent']}%")
    
    con.close()
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
