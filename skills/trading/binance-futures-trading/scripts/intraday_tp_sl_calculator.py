"""
Intraday TP/SL Calculator for Binance Futures Positions
Calculates ATR-based stop loss and take profit levels using 1H + 15M data.
Usage: Update the `pairs` dict with current positions, then run.
"""
import requests

def get_klines(symbol, interval, limit=100):
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}'
    return requests.get(url).json()

def calc_ema(data, period):
    ema = [data[0]]
    k = 2 / (period + 1)
    for i in range(1, len(data)):
        ema.append(data[i] * k + ema[-1] * (1 - k))
    return ema

def calc_atr(highs, lows, closes, period=14):
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        trs.append(tr)
    return sum(trs[-period:]) / period

# UPDATE THIS with current positions
pairs = {
    'INJUSDT':  {'side': 'LONG',  'entry': 3.6738,  'lev': 25},
    'TAOUSDT':  {'side': 'LONG',  'entry': 263.044, 'lev': 20},
    'APTUSDT':  {'side': 'LONG',  'entry': 1.0151,  'lev': 20},
    'NEARUSDT': {'side': 'SHORT', 'entry': 1.298,   'lev': 20},
    'DOGEUSDT': {'side': 'LONG',  'entry': 0.109,   'lev': 20},
}

for sym, info in pairs.items():
    kl1h = get_klines(sym, '1h', 100)
    c1h = [float(k[4]) for k in kl1h]
    h1h = [float(k[2]) for k in kl1h]
    l1h = [float(k[3]) for k in kl1h]

    kl15m = get_klines(sym, '15m', 100)
    c15m = [float(k[4]) for k in kl15m]
    h15m = [float(k[2]) for k in kl15m]
    l15m = [float(k[3]) for k in kl15m]

    price = c15m[-1]
    atr1h = calc_atr(h1h, l1h, c1h)
    atr15m = calc_atr(h15m, l15m, c15m)

    rh1h = max(h1h[-10:])
    rl1h = min(l1h[-10:])
    rh15m = max(h15m[-15:])
    rl15m = min(l15m[-15:])

    side = info['side']
    entry = info['entry']

    if side == 'LONG':
        sl = round(rl15m - atr15m * 0.3, 5)
        tp1 = round(min(rh1h, price + atr1h * 1.0), 5)
        tp2 = round(price + atr1h * 1.8, 5)
        tp3 = round(price + atr1h * 2.5, 5)
        sl_pct = (entry - sl) / entry * 100
        tp1_pct = (tp1 - entry) / entry * 100
        tp2_pct = (tp2 - entry) / entry * 100
        tp3_pct = (tp3 - entry) / entry * 100
    else:
        sl = round(rh15m + atr15m * 0.3, 5)
        tp1 = round(max(rl1h, price - atr1h * 1.0), 5)
        tp2 = round(price - atr1h * 1.8, 5)
        tp3 = round(price - atr1h * 2.5, 5)
        sl_pct = (sl - entry) / entry * 100
        tp1_pct = (entry - tp1) / entry * 100
        tp2_pct = (entry - tp2) / entry * 100
        tp3_pct = (entry - tp3) / entry * 100

    rr1 = tp1_pct / sl_pct if sl_pct > 0 else 0
    rr2 = tp2_pct / sl_pct if sl_pct > 0 else 0

    print(f"{side} {sym} {info['lev']}x | Entry: {entry} | Now: {price:.5f}")
    print(f"  SL:  {sl}  ({sl_pct:.2f}%)")
    print(f"  TP1: {tp1}  ({tp1_pct:+.2f}% | {rr1:.1f}R)")
    print(f"  TP2: {tp2}  ({tp2_pct:+.2f}% | {rr2:.1f}R)")
    print(f"  TP3: {tp3}  ({tp3_pct:+.2f}%)")
    print()
