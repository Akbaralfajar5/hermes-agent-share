"""
AITS Multi-Entry Script for Binance Futures Testnet
Executes multiple LIMIT entries with calculated TP/SL levels.
TP/SL are recorded (not placed as orders) since testnet doesn't support conditional orders.

Usage:
  BINANCE_API_KEY=xxx BINANCE_SECRET_KEY=yyy python3 testnet_multi_entry.py

Modify the `trades` list to change entries.
"""
import requests, time, hmac, hashlib, os, json, math
from urllib.parse import urlencode

BASE = "https://testnet.binancefuture.com"
API_KEY = os.environ['BINANCE_API_KEY']
API_SECRET = os.environ['BINANCE_SECRET_KEY']

def signed_req(method, endpoint, params=None):
    if params is None: params = {}
    params['timestamp'] = int(time.time() * 1000)
    params['recvWindow'] = 10000
    qs = urlencode(params)
    sig = hmac.new(API_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    qs += f"&signature={sig}"
    headers = {"X-MBX-APIKEY": API_KEY}
    url = f"{BASE}{endpoint}?{qs}"
    if method == 'GET':
        r = requests.get(url, headers=headers, timeout=15)
    elif method == 'POST':
        r = requests.post(url, headers=headers, timeout=15)
    elif method == 'DELETE':
        r = requests.delete(url, headers=headers, timeout=15)
    return r.json()

def get_symbol_info(symbol):
    r = requests.get(f"{BASE}/fapi/v1/exchangeInfo", timeout=10).json()
    for s in r['symbols']:
        if s['symbol'] == symbol:
            pf = [f for f in s['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
            lf = [f for f in s['filters'] if f['filterType'] == 'LOT_SIZE'][0]
            return float(pf['tickSize']), float(lf['stepSize']), float(lf['minQty'])
    return None, None, None

def round_step(value, step):
    precision = len(str(step).rstrip('0').split('.')[-1]) if '.' in str(step) else 0
    return round(math.floor(value / step) * step, precision)

def round_price(value, tick):
    precision = len(str(tick).rstrip('0').split('.')[-1]) if '.' in str(tick) else 0
    return round(round(value / tick) * tick, precision)

# ============ CONFIGURATION ============
# Modify these trades as needed
trades = [
    {"symbol": "ETHUSDT", "side": "BUY", "direction": "LONG", "leverage": 20},
    {"symbol": "BNBUSDT", "side": "SELL", "direction": "SHORT", "leverage": 25},
    {"symbol": "XRPUSDT", "side": "BUY", "direction": "LONG", "leverage": 25},
]

RISK_PCT = 0.02  # 2% margin per trade
ENTRY_OFFSET = 0.001  # 0.1% offset from market for limit order
TP1_PCT = 0.015  # +1.5%
TP2_PCT = 0.03   # +3%
TP3_PCT = 0.05   # +5%
SL_PCT = 0.02    # -2%

# ============ EXECUTION ============
print("=" * 60)
print("  AITS MULTI-ENTRY EXECUTION (TESTNET)")
print("=" * 60)

# Get balance
account = signed_req('GET', '/fapi/v2/account')
balance = float(account.get('totalWalletBalance', 0))
available = float(account.get('availableBalance', 0))
margin_per_trade = balance * RISK_PCT
print(f"\nBalance: ${balance:.2f} | Available: ${available:.2f} | Margin/Trade: ${margin_per_trade:.2f}")

# Step 1: Cancel all existing orders for target symbols
print("\nStep 1: Cleaning existing orders...")
for t in trades:
    r = signed_req('DELETE', '/fapi/v1/allOpenOrders', {"symbol": t["symbol"]})
    print(f"  {t['symbol']}: {r.get('msg', 'OK')}")

time.sleep(1)

# Step 2: Execute entries
print("\nStep 2: Placing entries...")
results = []

for t in trades:
    sym = t["symbol"]
    side = t["side"]
    close_side = "SELL" if side == "BUY" else "BUY"
    lev = t["leverage"]
    direction = t["direction"]
    
    tick, step, min_qty = get_symbol_info(sym)
    if not tick:
        print(f"  {sym}: Symbol not found, skipping")
        continue
    
    ticker = requests.get(f"{BASE}/fapi/v1/ticker/price", params={"symbol": sym}, timeout=10).json()
    price = float(ticker['price'])
    
    # Set leverage + margin
    signed_req('POST', '/fapi/v1/leverage', {"symbol": sym, "leverage": lev})
    signed_req('POST', '/fapi/v1/marginType', {"symbol": sym, "marginType": "ISOLATED"})
    
    # Calculate qty
    notional = margin_per_trade * lev
    qty = round_step(notional / price, step)
    if qty < min_qty:
        qty = min_qty
    
    # Calculate entry + TP/SL
    if direction == "LONG":
        entry = round_price(price * (1 - ENTRY_OFFSET), tick)
        tp1 = round_price(entry * (1 + TP1_PCT), tick)
        tp2 = round_price(entry * (1 + TP2_PCT), tick)
        tp3 = round_price(entry * (1 + TP3_PCT), tick)
        sl = round_price(entry * (1 - SL_PCT), tick)
    else:
        entry = round_price(price * (1 + ENTRY_OFFSET), tick)
        tp1 = round_price(entry * (1 - TP1_PCT), tick)
        tp2 = round_price(entry * (1 - TP2_PCT), tick)
        tp3 = round_price(entry * (1 - TP3_PCT), tick)
        sl = round_price(entry * (1 + SL_PCT), tick)
    
    # TP quantities (30/40/30)
    tp1_qty = round_step(qty * 0.3, step)
    tp2_qty = round_step(qty * 0.4, step)
    tp3_qty = max(round_step(qty - tp1_qty - tp2_qty, step), min_qty)
    
    # Place entry order
    eo = signed_req('POST', '/fapi/v1/order', {
        "symbol": sym, "side": side, "type": "LIMIT",
        "quantity": qty, "price": entry, "timeInForce": "GTC"
    })
    
    if 'orderId' in eo:
        print(f"\n  {sym} {direction} | Entry: ${entry} | Qty: {qty} | Lev: {lev}x | orderId: {eo['orderId']}")
        print(f"    TP1: ${tp1} (30%={tp1_qty}) | TP2: ${tp2} (40%={tp2_qty}) | TP3: ${tp3} (30%={tp3_qty})")
        print(f"    SL: ${sl} (full={qty})")
        print(f"    NOTE: TP/SL recorded for cron monitoring (testnet can't place conditional orders)")
        results.append({
            "symbol": sym, "direction": direction, "entry": entry,
            "qty": qty, "leverage": lev,
            "tp1": tp1, "tp2": tp2, "tp3": tp3, "sl": sl,
            "tp1_qty": tp1_qty, "tp2_qty": tp2_qty, "tp3_qty": tp3_qty,
            "orderId": eo['orderId']
        })
    else:
        print(f"\n  {sym} FAILED: {eo}")
    
    time.sleep(0.5)

# Step 3: Verify
print("\n" + "=" * 60)
print("  VERIFICATION")
print("=" * 60)
time.sleep(1)
orders = signed_req('GET', '/fapi/v1/openOrders')
if isinstance(orders, list):
    print(f"\nOpen Orders: {len(orders)}")
    for o in orders:
        print(f"  {o['symbol']:12s} | {o['side']:4s} LIMIT | Qty: {o['origQty']:>10s} | Price: {o['price']:>12s}")

# Output SL/TP tracking data for cronjob
print("\n\nSL/TP TRACKING (add to cronjob prompt):")
print("-" * 40)
for r in results:
    print(f"{r['symbol']} {r['direction']}:")
    print(f"  Entry: {r['entry']} | Qty: {r['qty']} | Lev: {r['leverage']}x")
    print(f"  SL: {r['sl']} | TP1: {r['tp1']} | TP2: {r['tp2']} | TP3: {r['tp3']}")
