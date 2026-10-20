#!/usr/bin/env python3
"""Scan & Execute - Entry top N posisi berdasarkan FibStruct scoring"""
import hashlib, hmac, time, requests, json, datetime, math, os
from urllib.parse import urlencode

API_KEY = os.environ.get('BINANCE_API_KEY', '')
SECRET_KEY = os.environ.get('BINANCE_SECRET_KEY', '')
BASE_URL = 'https://fapi.binance.com'
headers = {'X-MBX-APIKEY': API_KEY}

MIN_VOLUME = 10_000_000
MIN_SCORE = 4
MARGIN_PCT = 0.05
MAX_ENTRIES = 3

def sign(params):
    qs = urlencode(params)
    params['signature'] = hmac.new(SECRET_KEY.encode(), qs.encode(), hashlib.sha256).hexdigest()
    return params

def api_get(endpoint, params={}):
    params['timestamp'] = int(time.time() * 1000)
    params['recvWindow'] = 60000
    params = sign(params)
    r = requests.get(f'{BASE_URL}{endpoint}', params=params, headers=headers, timeout=10)
    return r.json()

def api_post(endpoint, params={}):
    params['timestamp'] = int(time.time() * 1000)
    params['recvWindow'] = 60000
    params = sign(params)
    r = requests.post(f'{BASE_URL}{endpoint}', params=params, headers=headers, timeout=10)
    return r.json()

def get_klines(symbol, interval, limit=100):
    r = requests.get(f'{BASE_URL}/fapi/v1/klines', params={'symbol': symbol, 'interval': interval, 'limit': limit}, timeout=10)
    data = r.json()
    return data if isinstance(data, list) else []

def find_swing_points(highs, lows, lookback=5):
    sh, sl = [], []
    for i in range(lookback, len(highs) - lookback):
        if all(highs[i] >= highs[i-j] for j in range(1, lookback+1)) and all(highs[i] >= highs[i+j] for j in range(1, lookback+1)):
            sh.append((i, highs[i]))
        if all(lows[i] <= lows[i-j] for j in range(1, lookback+1)) and all(lows[i] <= lows[i+j] for j in range(1, lookback+1)):
            sl.append((i, lows[i]))
    return sh, sl

def analyze_structure(klines, lookback=5):
    if len(klines) < 30: return 'NEUTRAL'
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    sh, sl = find_swing_points(highs, lows, lookback)
    if len(sh) < 2 or len(sl) < 2: return 'NEUTRAL'
    rsh, rsl = sh[-3:], sl[-3:]
    hh = len(rsh) >= 2 and rsh[-1][1] > rsh[-2][1]
    hl = len(rsl) >= 2 and rsl[-1][1] > rsl[-2][1]
    lh = len(rsh) >= 2 and rsh[-1][1] < rsh[-2][1]
    ll = len(rsl) >= 2 and rsl[-1][1] < rsl[-2][1]
    if hh and hl: return 'BULLISH'
    elif lh and ll: return 'BEARISH'
    return 'NEUTRAL'

def check_trendline(klines, direction):
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    closes = [float(k[4]) for k in klines]
    sh, sl = find_swing_points(highs, lows, 3)
    if direction == 'BULLISH' and len(sl) >= 2:
        sl1, sl2 = sl[-2], sl[-1]
        if sl2[0] == sl1[0]: return False
        slope = (sl2[1] - sl1[1]) / (sl2[0] - sl1[0])
        tv = sl2[1] + slope * (len(closes)-1 - sl2[0])
        return closes[-1] > tv and slope > 0
    elif direction == 'BEARISH' and len(sh) >= 2:
        sh1, sh2 = sh[-2], sh[-1]
        if sh2[0] == sh1[0]: return False
        slope = (sh2[1] - sh1[1]) / (sh2[0] - sh1[0])
        tv = sh2[1] + slope * (len(closes)-1 - sh2[0])
        return closes[-1] < tv and slope < 0
    return False

def find_fib_ote(klines, direction):
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    closes = [float(k[4]) for k in klines]
    sh, sl = find_swing_points(highs, lows, 3)
    if direction == 'BULLISH' and sh and sl:
        last_sh = sh[-1]
        rl = [s for s in sl if s[0] < last_sh[0]]
        if not rl: return None, False
        swl, swh = rl[-1][1], last_sh[1]
        if swh <= swl: return None, False
        rng = swh - swl
        f618, f786 = swh - rng*0.618, swh - rng*0.786
        p = closes[-1]
        in_ote = f786 <= p <= f618 or f786*0.998 <= p <= f618*1.002
        return {'fib_786': f786, 'fib_618': f618, 'swing_low': swl, 'swing_high': swh}, in_ote
    elif direction == 'BEARISH' and sh and sl:
        last_sl = sl[-1]
        rh = [s for s in sh if s[0] < last_sl[0]]
        if not rh: return None, False
        swh, swl = rh[-1][1], last_sl[1]
        if swh <= swl: return None, False
        rng = swh - swl
        f618, f786 = swl + rng*0.618, swl + rng*0.786
        p = closes[-1]
        in_ote = f618 <= p <= f786 or f618*0.998 <= p <= f786*1.002
        return {'fib_786': f786, 'fib_618': f618, 'swing_low': swl, 'swing_high': swh}, in_ote
    return None, False

def detect_sweep(klines, direction, sl_list, sh_list):
    if len(klines) < 5: return False, None
    for i in range(-3, 0):
        cl, ch, co, cc = float(klines[i][3]), float(klines[i][2]), float(klines[i][1]), float(klines[i][4])
        body = abs(cc - co)
        if direction == 'BULLISH' and sl_list:
            for idx, sp in sl_list[-3:]:
                lw = min(co, cc) - cl
                if cl < sp and cc > sp and lw > body * 0.5: return True, sp
        elif direction == 'BEARISH' and sh_list:
            for idx, sp in sh_list[-3:]:
                uw = ch - max(co, cc)
                if ch > sp and cc < sp and uw > body * 0.5: return True, sp
    return False, None

def detect_pa(klines, direction):
    if len(klines) < 3: return False, ''
    c, prev = klines[-2], klines[-3]
    co, ch, cl, cc = float(c[1]), float(c[2]), float(c[3]), float(c[4])
    po, pc = float(prev[1]), float(prev[4])
    cb, cr = abs(cc-co), ch-cl
    pb = abs(pc-po)
    if cr == 0: return False, ''
    if direction == 'BULLISH':
        if cc > co and cb > pb and cc > po and co < pc: return True, 'ENGULF'
        lw = min(co,cc) - cl
        if lw > cb*2 and lw > cr*0.6: return True, 'PIN'
    elif direction == 'BEARISH':
        if cc < co and cb > pb and co > pc and cc < po: return True, 'ENGULF'
        uw = ch - max(co,cc)
        if uw > cb*2 and uw > cr*0.6: return True, 'PIN'
    return False, ''

def analyze_symbol(symbol):
    try:
        k4h = get_klines(symbol, '4h', 100)
        k1h = get_klines(symbol, '1h', 100)
        k15m = get_klines(symbol, '15m', 100)
        k5m = get_klines(symbol, '5m', 60)
        if not k4h or not k1h or not k15m or not k5m: return None
        if len(k4h) < 30 or len(k15m) < 30: return None
        
        s4h = analyze_structure(k4h, 7)
        s1h = analyze_structure(k1h, 5)
        if s4h == 'NEUTRAL': return None
        
        score, reasons = 0, []
        score += 1; reasons.append(f"4H: {s4h}")
        if s1h == s4h: score += 1; reasons.append(f"1H: {s1h}")
        else: reasons.append(f"1H: {s1h} NO")
        
        tlint = check_trendline(k15m, s4h)
        if tlint: score += 1; reasons.append("15M: Trendline")
        else: reasons.append("15M: Trendline NO")
        
        td = 'BULLISH' if s4h == 'BULLISH' else 'BEARISH'
        fib, in_ote = find_fib_ote(k15m, td)
        if fib and in_ote: score += 1; reasons.append("15M: Fib OTE")
        else: reasons.append("15M: Fib OTE NO")
        
        h5 = [float(k[2]) for k in k5m]
        l5 = [float(k[3]) for k in k5m]
        sh5, sl5 = find_swing_points(h5, l5, 3)
        sweep, swl = detect_sweep(k5m, td, sl5, sh5)
        pa, pat = detect_pa(k5m, td)
        if sweep or pa:
            score += 1
            info = []
            if sweep: info.append(f"Sweep@{swl:.4f}")
            if pa: info.append(pat)
            reasons.append(f"5M: {' + '.join(info)}")
        else:
            reasons.append("5M: No trigger")
        
        price = float(k5m[-1][4])
        atr_data = k15m[-15:]
        atr_vals = []
        for i in range(1, len(atr_data)):
            h, l, pc = float(atr_data[i][2]), float(atr_data[i][3]), float(atr_data[i-1][4])
            atr_vals.append(max(h-l, abs(h-pc), abs(l-pc)))
        atr = sum(atr_vals)/len(atr_vals) if atr_vals else price*0.01
        
        if s4h == 'BULLISH':
            sl = (swl - atr*0.1) if sweep and swl else (fib['fib_786'] - atr*0.3) if fib else price - atr*1.5
            risk = price - sl
        else:
            sl = (swl + atr*0.1) if sweep and swl else (fib['fib_786'] + atr*0.3) if fib else price + atr*1.5
            risk = sl - price
        
        rr = (risk * 2) / risk if risk > 0 else 0
        
        return {'symbol': symbol, 'direction': 'LONG' if s4h=='BULLISH' else 'SHORT', 'score': score, 'reasons': reasons, 'price': price, 'sl': sl, 'rr': rr, 'atr': atr}
    except:
        return None

def execute_entry(signal, total_balance):
    sym = signal['symbol']
    direction = signal['direction']
    price = signal['price']
    sl_price = signal['sl']
    
    sl_dist = abs(price - sl_price) / price * 100
    if sl_dist < 0.5: leverage = 50
    elif sl_dist < 1.0: leverage = 30
    elif sl_dist < 2.0: leverage = 20
    else: leverage = 10
    
    lev_data = api_get('/fapi/v1/leverageBracket', {'symbol': sym})
    if isinstance(lev_data, list) and lev_data:
        max_lev = lev_data[0]['brackets'][0]['initialLeverage']
        leverage = min(leverage, max_lev)
    
    api_post('/fapi/v1/leverage', {'symbol': sym, 'leverage': leverage})
    try: api_post('/fapi/v1/marginType', {'symbol': sym, 'marginType': 'ISOLATED'})
    except: pass
    
    r = requests.get(f'{BASE_URL}/fapi/v1/exchangeInfo', timeout=10)
    info = r.json()
    qty_prec = 3
    for s in info.get('symbols', []):
        if s['symbol'] == sym:
            qty_prec = s.get('quantityPrecision', 3)
            break
    
    margin = total_balance * MARGIN_PCT
    notional = margin * leverage
    qty = round(notional / price, qty_prec)
    
    if qty <= 0:
        return None
    
    side = 'BUY' if direction == 'LONG' else 'SELL'
    result = api_post('/fapi/v1/order', {
        'symbol': sym, 'side': side, 'type': 'MARKET', 'quantity': str(qty)
    })
    
    if 'orderId' in result:
        entry_actual = float(result.get('avgPrice', price))
        if entry_actual == 0: entry_actual = price
        
        risk = abs(entry_actual - sl_price)
        if direction == 'LONG':
            tp1 = round(entry_actual + risk * 2, 6)
            tp2 = round(entry_actual + risk * 3, 6)
            tp3 = round(entry_actual + risk * 4, 6)
        else:
            tp1 = round(entry_actual - risk * 2, 6)
            tp2 = round(entry_actual - risk * 3, 6)
            tp3 = round(entry_actual - risk * 4, 6)
        
        sl_side = 'SELL' if direction == 'LONG' else 'BUY'
        sl_set = False
        tp_set = False
        try:
            sr = api_post('/fapi/v1/order', {
                'symbol': sym, 'side': sl_side, 'type': 'STOP_MARKET',
                'stopPrice': str(sl_price), 'quantity': str(qty),
                'reduceOnly': 'true', 'workingType': 'MARK_PRICE'
            })
            sl_set = 'orderId' in sr
        except: pass
        try:
            tr = api_post('/fapi/v1/order', {
                'symbol': sym, 'side': sl_side, 'type': 'TAKE_PROFIT_MARKET',
                'stopPrice': str(tp1), 'quantity': str(qty),
                'reduceOnly': 'true', 'workingType': 'MARK_PRICE'
            })
            tp_set = 'orderId' in tr
        except: pass
        
        return {
            'symbol': sym, 'direction': direction, 'entry': entry_actual,
            'qty': qty, 'leverage': leverage, 'sl': sl_price,
            'tp1': tp1, 'tp2': tp2, 'tp3': tp3, 'margin': margin,
            'sl_api': sl_set, 'tp_api': tp_set, 'score': signal['score'],
            'time': datetime.datetime.now().isoformat()
        }
    return None

# ==================== MAIN ====================
print("="*50)
print("FIBSTRUCT SCAN & EXECUTE")
print("="*50)

r = requests.get(f'{BASE_URL}/fapi/v1/ticker/24hr', timeout=15)
data = r.json()
usdt = [d for d in data if d['symbol'].endswith('USDT') and float(d['quoteVolume']) > MIN_VOLUME]
usdt.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
pairs = [p['symbol'] for p in usdt[:200]]

bal_data = api_get('/fapi/v2/balance')
total = 0
for b in bal_data:
    if b.get('asset') == 'USDT':
        total = float(b['balance'])
        break

pos_data = api_get('/fapi/v2/positionRisk')
existing = []
if isinstance(pos_data, list):
    for p in pos_data:
        if float(p.get('positionAmt', 0)) != 0:
            existing.append(p['symbol'])

print(f"Balance: ${total:.2f}")
print(f"Existing: {len(existing)} - {existing}")
print(f"Scanning {len(pairs)} pairs (vol > ${MIN_VOLUME/1e6:.0f}M)...")

results = []
for i, sym in enumerate(pairs):
    if sym in existing: continue
    a = analyze_symbol(sym)
    if a and a['score'] >= MIN_SCORE:
        results.append(a)
    if (i+1) % 50 == 0:
        print(f"  {i+1}/{len(pairs)}... {len(results)} signals")

results.sort(key=lambda x: (x['score'], x['rr']), reverse=True)
print(f"\n{len(results)} signal(s) found\n")

for i, r in enumerate(results[:15]):
    print(f"#{i+1} {r['symbol']} {r['direction']} | Score: {r['score']}/5 | Price: {r['price']:.6f} | SL: {r['sl']:.6f}")

to_execute = [s for s in results if s['symbol'] not in existing][:MAX_ENTRIES]
print(f"\n{'='*50}")
print(f"EXECUTING {len(to_execute)} ENTRIES")
print(f"{'='*50}\n")

executed = []
for signal in to_execute:
    # Re-query balance before each entry
    bal_data = api_get('/fapi/v2/balance')
    for b in bal_data:
        if b.get('asset') == 'USDT':
            total = float(b['balance'])
            break
    
    entry = execute_entry(signal, total)
    if entry:
        executed.append(entry)
        state_file = '/home/ubuntu/fibstruct_state.json'
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
        except:
            state = {'positions': {}}
        state['positions'][entry['symbol']] = entry
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        sl_mode = 'API' if entry['sl_api'] else 'Monitor'
        print(f"OK {entry['symbol']} {entry['direction']} @ {entry['entry']:.6f}")
        print(f"   Qty: {entry['qty']} | Lev: {entry['leverage']}x | Margin: ${entry['margin']:.2f}")
        print(f"   SL: {entry['sl']:.6f} ({sl_mode}) | TP1: {entry['tp1']:.6f}")
    else:
        print(f"FAIL {signal['symbol']}")

print(f"\n{'='*50}")
print(f"SUMMARY: {len(executed)} new entries | Total positions: {len(existing) + len(executed)}")
print(f"{'='*50}")
