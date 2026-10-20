#!/usr/bin/env python3
"""
Quick TA scanner for Binance-listed tokens.
Usage: python3 ta_scanner.py BTCUSDT ETHUSDT INJUSDT ...
Outputs bullish score (0-6), RSI, EMA status, MACD for each symbol.
"""
import json, urllib.request, sys
import numpy as np

def fetch(symbol, interval="1d", limit=60):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read())

def ema(data, p):
    k = 2/(p+1); e = [data[0]]
    for d in data[1:]: e.append(d*k + e[-1]*(1-k))
    return np.array(e)

def rsi(closes, p=14):
    vals = np.full(len(closes), np.nan)
    d = np.diff(closes)
    for i in range(p, len(closes)):
        g = [x for x in d[i-p:i] if x>0]
        l = [-x for x in d[i-p:i] if x<0]
        ag = sum(g)/p if g else 0; al = sum(l)/p if l else 0.001
        vals[i] = 100 - (100/(1+ag/al))
    return vals

symbols = sys.argv[1:] if len(sys.argv) > 1 else ["BTCUSDT","ETHUSDT","SOLUSDT","INJUSDT","PENDLEUSDT","DOGEUSDT"]

print(f"{'Symbol':<14} {'Price':>10} {'RSI':>6} {'EMA':>12} {'MACD':>8} {'Score':>6} {'Signal':>8}")
print("-" * 70)

for sym in symbols:
    try:
        data = fetch(sym)
        closes = np.array([float(d[4]) for d in data])
        cur = closes[-1]
        e7, e21, e50 = ema(closes,7)[-1], ema(closes,21)[-1], ema(closes,50)[-1]
        r14 = rsi(closes)[-1]
        hist = (ema(closes,12) - ema(closes,26))[-1] - ema(list(ema(closes,12)-ema(closes,26)),9)[-1]
        
        score = sum([cur>e7, cur>e21, e7>e21, e21>e50, hist>0, r14>50])
        ema_str = "7>21>50" if e7>e21>e50 else "7<21" if e7<e21 else "mixed"
        signal = "LONG" if score>=5 else "SHORT" if score<=1 else "WAIT"
        
        print(f"{sym:<14} ${cur:>9.4f} {r14:>5.1f} {ema_str:>12} {hist:>+7.4f} {score:>4}/6 {signal:>8}")
    except Exception as e:
        print(f"{sym:<14} ERROR: {e}")
