"""
NFP Auto-Entry Script for XAUUSDT (or any pair)
================================================
Monitors price around high-impact news release time, waits for confirmation
of direction, then executes market entry with SL/TP management.

Usage:
  PYTHONUNBUFFERED=1 python3 nfp_auto_entry.py

Configuration: Edit the CONFIG section below before running.

Flow:
  1. Wait until T-10s before news release
  2. Record pre-news price
  3. Monitor every 2s after release
  4. If price moves > ENTRY_THRESHOLD in expected direction → MARKET BUY/SELL
  5. Set SL/TP via API (if supported) or monitor manually
  6. If no clear signal after TIMEOUT_MINUTES → skip

Pitfalls:
  - MUST run with PYTHONUNBUFFERED=1 or flush=True on all prints
  - XAUUSDT (commodity pairs) don't support STOP_MARKET via API → uses manual monitor
  - Always use ISOLATED margin for news trading (volatile)
  - Entry threshold should be >0.3% to avoid whipsaw fake-outs
"""

import hashlib, hmac, time, requests, sys
from urllib.parse import urlencode
import datetime

sys.stdout.reconfigure(line_buffering=True)

# ============ CONFIG ============
API_KEY = 'YOUR_API_KEY'
SECRET_KEY = 'YOUR_SECRET_KEY'
BASE_URL = 'https://fapi.binance.com'  # PROD

SYMBOL = 'XAUUSDT'
LEVERAGE = 50
MARGIN_TYPE = 'ISOLATED'
DIRECTION = 'LONG'  # LONG or SHORT
MARGIN_USDT = 116  # How much margin to use
ENTRY_THRESHOLD_PCT = 0.3  # Min % move to confirm direction
SKIP_THRESHOLD_PCT = -0.5  # If moves against by this much, skip
SL_PCT = 0.015  # 1.5% stop loss
TP_PRICE = 4790.00  # Fixed TP price (or set to 0 for ATR-based)
TIMEOUT_MINUTES = 2  # Skip if no signal after this

# News release time (24h format, local timezone)
NEWS_HOUR = 19
NEWS_MINUTE = 30
# ================================

headers = {'X-MBX-APIKEY': API_KEY}

def sign(params):
    qs = urlencode(params)
    sig = hmac.new(SECRET_KEY.encode(), qs.encode(), hashlib.sha256).hexdigest()
    params['signature'] = sig
    return params

def get_price():
    r = requests.get(f'{BASE_URL}/fapi/v1/ticker/price', params={'symbol': SYMBOL})
    return float(r.json()['price'])

def place_order(side, qty, order_type='MARKET', **kwargs):
    params = {
        'symbol': SYMBOL, 'side': side, 'type': order_type,
        'quantity': str(qty),
        'timestamp': int(time.time()*1000), 'recvWindow': 60000
    }
    params.update(kwargs)
    params = sign(params)
    r = requests.post(f'{BASE_URL}/fapi/v1/order', params=params, headers=headers)
    return r.json()

def set_leverage():
    params = sign({'symbol': SYMBOL, 'leverage': LEVERAGE, 'timestamp': int(time.time()*1000), 'recvWindow': 60000})
    return requests.post(f'{BASE_URL}/fapi/v1/leverage', params=params, headers=headers).json()

def set_margin_type():
    params = sign({'symbol': SYMBOL, 'marginType': MARGIN_TYPE, 'timestamp': int(time.time()*1000), 'recvWindow': 60000})
    return requests.post(f'{BASE_URL}/fapi/v1/marginType', params=params, headers=headers).json()

def try_set_sl_tp(entry_price, qty):
    """Attempt API SL/TP. Returns (sl_price, tp_price, needs_manual_monitor)"""
    sl_price = round(entry_price * (1 - SL_PCT), 2) if DIRECTION == 'LONG' else round(entry_price * (1 + SL_PCT), 2)
    tp_price = TP_PRICE if TP_PRICE > 0 else round(entry_price * (1 + SL_PCT * 2), 2)
    close_side = 'SELL' if DIRECTION == 'LONG' else 'BUY'
    
    # Try SL
    params_sl = sign({
        'symbol': SYMBOL, 'side': close_side, 'type': 'STOP_MARKET',
        'stopPrice': str(sl_price), 'quantity': str(qty),
        'reduceOnly': 'true', 'workingType': 'MARK_PRICE',
        'timestamp': int(time.time()*1000), 'recvWindow': 60000
    })
    r_sl = requests.post(f'{BASE_URL}/fapi/v1/order', params=params_sl, headers=headers)
    sl_ok = 'orderId' in r_sl.json()
    
    # Try TP
    params_tp = sign({
        'symbol': SYMBOL, 'side': close_side, 'type': 'TAKE_PROFIT_MARKET',
        'stopPrice': str(tp_price), 'quantity': str(qty),
        'reduceOnly': 'true', 'workingType': 'MARK_PRICE',
        'timestamp': int(time.time()*1000), 'recvWindow': 60000
    })
    r_tp = requests.post(f'{BASE_URL}/fapi/v1/order', params=params_tp, headers=headers)
    tp_ok = 'orderId' in r_tp.json()
    
    needs_manual = not (sl_ok and tp_ok)
    print(f"  SL @ ${sl_price:.2f}: {'✅' if sl_ok else '❌ (will monitor manually)'}", flush=True)
    print(f"  TP @ ${tp_price:.2f}: {'✅' if tp_ok else '❌ (will monitor manually)'}", flush=True)
    return sl_price, tp_price, needs_manual

# ============ MAIN ============
print(f"⏳ Waiting for {NEWS_HOUR}:{NEWS_MINUTE-1}:50...", flush=True)

while True:
    now = datetime.datetime.now()
    target = now.replace(hour=NEWS_HOUR, minute=NEWS_MINUTE-1, second=50, microsecond=0)
    if now >= target:
        break
    time.sleep(1)

print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔴 LIVE MONITORING STARTED", flush=True)
pre_news_price = get_price()
print(f"Pre-news price: ${pre_news_price:.2f}", flush=True)

entered = False
entry_price = 0
qty = 0
sl_price = 0
tp_price = 0
needs_manual = False

while True:
    now = datetime.datetime.now()
    price = get_price()
    ts = now.strftime('%H:%M:%S')
    change = ((price - pre_news_price) / pre_news_price) * 100
    print(f"[{ts}] ${price:.2f} ({change:+.2f}%)", flush=True)
    
    # Entry logic (after news + 1 min)
    if now.hour == NEWS_HOUR and now.minute >= NEWS_MINUTE + 1 and not entered:
        if change > ENTRY_THRESHOLD_PCT:
            print(f"\n🚀 SIGNAL: {DIRECTION}! Move: {change:+.2f}%", flush=True)
            set_leverage()
            set_margin_type()
            
            qty = round((MARGIN_USDT * LEVERAGE) / price, 3)
            side = 'BUY' if DIRECTION == 'LONG' else 'SELL'
            result = place_order(side, qty)
            
            if 'orderId' in result:
                entry_price = float(result.get('avgPrice', price)) or price
                entered = True
                time.sleep(1)
                sl_price, tp_price, needs_manual = try_set_sl_tp(entry_price, qty)
                print(f"\n✅ ENTRY: ${entry_price:.2f} | Qty: {qty} | {LEVERAGE}x {MARGIN_TYPE}", flush=True)
            else:
                print(f"❌ FAILED: {result}", flush=True)
                break
                
        elif change < SKIP_THRESHOLD_PCT:
            print(f"\n⛔ SKIP — wrong direction ({change:+.2f}%)", flush=True)
            break
        
        if now.minute >= NEWS_MINUTE + TIMEOUT_MINUTES and not entered:
            print(f"\n⚪ NO SIGNAL after {TIMEOUT_MINUTES}min. Skip.", flush=True)
            break
    
    # Manual SL/TP monitor
    if entered and needs_manual:
        close_side = 'SELL' if DIRECTION == 'LONG' else 'BUY'
        if (DIRECTION == 'LONG' and price <= sl_price) or (DIRECTION == 'SHORT' and price >= sl_price):
            print(f"\n🛑 SL HIT @ ${price:.2f}", flush=True)
            place_order(close_side, qty, reduceOnly='true')
            break
        elif (DIRECTION == 'LONG' and price >= tp_price) or (DIRECTION == 'SHORT' and price <= tp_price):
            print(f"\n🎯 TP HIT @ ${price:.2f}", flush=True)
            place_order(close_side, qty, reduceOnly='true')
            pnl = abs(price - entry_price) * qty
            print(f"🎉 PROFIT: +${pnl:.2f}", flush=True)
            break
    
    if entered and not needs_manual:
        # SL/TP handled by exchange, monitor for 10 min then exit
        elapsed = (now - now.replace(hour=NEWS_HOUR, minute=NEWS_MINUTE+1, second=0)).total_seconds()
        if elapsed > 600:
            print(f"\n✅ SL/TP active on exchange. Monitor complete.", flush=True)
            break
    
    time.sleep(2)

print("\n--- DONE ---", flush=True)
