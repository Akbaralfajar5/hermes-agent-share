#!/usr/bin/env python3
"""
Futures Portfolio Monitor — Direct execution script.
Use when cronjob delivery fails or user wants immediate results.

Reads API keys from environment or ~/.hermes/.env
"""
import requests, time, hmac, hashlib, json, os
from urllib.parse import urlencode

# Load from env or fallback to .hermes/.env
API_KEY = os.environ.get('BINANCE_API_KEY', '')
SECRET_KEY = os.environ.get('BINANCE_SECRET_KEY', '')

if not API_KEY:
    env_file = os.path.expanduser('~/.hermes/.env')
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if line.startswith('BINANCE_API_KEY='):
                    API_KEY = line.strip().split('=', 1)[1]
                elif line.startswith('BINANCE_SECRET_KEY='):
                    SECRET_KEY = line.strip().split('=', 1)[1]

# Change to https://fapi.binance.com for production
BASE_URL = os.environ.get('BINANCE_BASE_URL', 'https://testnet.binancefuture.com')

def sign(params):
    query = urlencode(params)
    signature = hmac.new(SECRET_KEY.encode(), query.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature
    return params

headers = {"X-MBX-APIKEY": API_KEY}

# 1. Account info
params = {"timestamp": int(time.time() * 1000), "recvWindow": 10000}
params = sign(params)
r = requests.get(f"{BASE_URL}/fapi/v2/account", params=params, headers=headers)
account = r.json()

if 'code' in account:
    print(f"❌ API Error: {account}")
    print("Possible causes: expired key, testnet reset, IP not whitelisted")
    exit(1)

balance = float(account.get('totalWalletBalance', 0))
unrealized_pnl = float(account.get('totalUnrealizedProfit', 0))
margin_balance = float(account.get('totalMarginBalance', 0))

print("=" * 50)
print("📊 FUTURES PORTFOLIO MONITOR")
print("=" * 50)
print(f"💰 Wallet Balance: ${balance:.2f}")
print(f"📈 Unrealized PnL: ${unrealized_pnl:.2f}")
print(f"🏦 Margin Balance: ${margin_balance:.2f}")
print()

# 2. Open positions
positions = [p for p in account.get('positions', []) if float(p['positionAmt']) != 0]

if not positions:
    print("📭 Tidak ada posisi terbuka.")
else:
    print(f"📋 POSISI TERBUKA ({len(positions)}):")
    print("-" * 50)
    for pos in positions:
        symbol = pos['symbol']
        side = "LONG" if float(pos['positionAmt']) > 0 else "SHORT"
        amt = abs(float(pos['positionAmt']))
        entry = float(pos['entryPrice'])
        pnl = float(pos['unrealizedProfit'])
        leverage = pos['leverage']
        margin = float(pos.get('initialMargin', 0))

        pr = requests.get(f"{BASE_URL}/fapi/v1/ticker/price", params={"symbol": symbol})
        current_price = float(pr.json()['price'])

        if entry > 0:
            if side == "LONG":
                pnl_pct = ((current_price - entry) / entry) * 100 * int(leverage)
            else:
                pnl_pct = ((entry - current_price) / entry) * 100 * int(leverage)
        else:
            pnl_pct = 0

        emoji = "🟢" if pnl >= 0 else "🔴"
        print(f"\n{emoji} {symbol} | {side} {leverage}x")
        print(f"   Entry: ${entry:.4f} → Now: ${current_price:.4f}")
        print(f"   Size: {amt} | Margin: ${margin:.2f}")
        print(f"   PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")

# 3. Open orders
params2 = {"timestamp": int(time.time() * 1000), "recvWindow": 10000}
params2 = sign(params2)
r2 = requests.get(f"{BASE_URL}/fapi/v1/openOrders", params=params2, headers=headers)
orders = r2.json()

print()
if isinstance(orders, list) and len(orders) > 0:
    print(f"📝 OPEN ORDERS ({len(orders)}):")
    print("-" * 50)
    for o in orders:
        if isinstance(o, dict):
            print(f"   {o.get('symbol','?')} | {o.get('side','?')} | {o.get('type','?')} | Price: {o.get('price','?')} | Qty: {o.get('origQty','?')}")
elif isinstance(orders, dict) and 'code' in orders:
    print(f"⚠️ Open Orders error: {orders['msg']}")
else:
    print("📝 Tidak ada open orders.")

print()
print("=" * 50)
print(f"⏰ Updated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
