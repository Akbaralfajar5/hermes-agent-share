#!/usr/bin/env python3
"""
Multi-Timeframe Intraday Scanner for Futures Trading
Scans top-volume pairs on Binance Futures and scores them 0-9 based on
4H/1H/15M trend alignment (EMA structure + MACD cross).

Usage:
    python3 multi_tf_intraday_scanner.py

Output: Ranked table of candidates with direction, score, RSI, and pullback status.
"""

import requests
import json
import sys

def get_klines(symbol, interval, limit=100):
    """Fetch OHLCV from Binance Futures API."""
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    resp = requests.get(url)
    data = resp.json()
    closes = [float(d[4]) for d in data]
    highs = [float(d[2]) for d in data]
    lows = [float(d[3]) for d in data]
    volumes = [float(d[5]) for d in data]
    return closes, highs, lows, volumes

def calc_rsi(closes, period=14):
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_ema(data, period):
    ema = [data[0]]
    k = 2 / (period + 1)
    for i in range(1, len(data)):
        ema.append(data[i] * k + ema[-1] * (1 - k))
    return ema

def analyze_tf(symbol, interval):
    """Analyze a single timeframe: trend, RSI, MACD."""
    closes, highs, lows, volumes = get_klines(symbol, interval)
    rsi = calc_rsi(closes)
    ema9 = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    ema50 = calc_ema(closes, 50)
    
    price = closes[-1]
    trend = "BULL" if ema9[-1] > ema21[-1] > ema50[-1] else \
            "BEAR" if ema9[-1] < ema21[-1] < ema50[-1] else "MIXED"
    
    # MACD
    ema12 = calc_ema(closes, 12)
    ema26 = calc_ema(closes, 26)
    macd_line = [ema12[i] - ema26[i] for i in range(len(closes))]
    signal = calc_ema(macd_line, 9)
    macd_cross = "BULL" if macd_line[-1] > signal[-1] else "BEAR"
    
    return {
        'trend': trend,
        'rsi': rsi,
        'price': price,
        'ema9': ema9[-1],
        'ema21': ema21[-1],
        'ema50': ema50[-1],
        'macd_cross': macd_cross,
    }

def get_top_volume_pairs(exclude=None, top_n=20):
    """Get top volume USDT futures pairs, excluding specified symbols."""
    if exclude is None:
        exclude = ['BTCUSDT', 'ETHUSDT']
    
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    resp = requests.get(url)
    data = resp.json()
    
    usdt_pairs = [d for d in data if d['symbol'].endswith('USDT') and float(d['volume']) > 0]
    usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
    
    # Filter out excluded, pump coins (>50% change), and low-quality pairs
    candidates = []
    for p in usdt_pairs:
        if p['symbol'] in exclude:
            continue
        change = abs(float(p['priceChangePercent']))
        if change > 50:  # Skip pump/dump coins
            continue
        candidates.append(p['symbol'])
        if len(candidates) >= top_n:
            break
    
    return candidates

def scan_multi_tf(symbols):
    """Score each symbol across 4H/1H/15M timeframes."""
    results = []
    
    for sym in symbols:
        try:
            tf4h = analyze_tf(sym, '4h')
            tf1h = analyze_tf(sym, '1h')
            tf15m = analyze_tf(sym, '15m')
            
            # BULL score (max 9)
            bull_score = 0
            if tf4h['trend'] == 'BULL': bull_score += 3
            if tf1h['trend'] == 'BULL': bull_score += 2
            if tf15m['trend'] == 'BULL': bull_score += 1
            if tf4h['macd_cross'] == 'BULL': bull_score += 1
            if tf1h['macd_cross'] == 'BULL': bull_score += 1
            if tf15m['macd_cross'] == 'BULL': bull_score += 1
            
            # BEAR score (max 9)
            bear_score = 0
            if tf4h['trend'] == 'BEAR': bear_score += 3
            if tf1h['trend'] == 'BEAR': bear_score += 2
            if tf15m['trend'] == 'BEAR': bear_score += 1
            if tf4h['macd_cross'] == 'BEAR': bear_score += 1
            if tf1h['macd_cross'] == 'BEAR': bear_score += 1
            if tf15m['macd_cross'] == 'BEAR': bear_score += 1
            
            if bull_score >= bear_score:
                score = bull_score
                direction = "LONG"
            else:
                score = bear_score
                direction = "SHORT"
            
            # RSI filter
            rsi_ok = True
            if direction == "LONG" and tf4h['rsi'] > 75: rsi_ok = False
            if direction == "SHORT" and tf4h['rsi'] < 25: rsi_ok = False
            
            # Pullback bonus
            pullback = False
            if direction == "LONG" and 35 < tf15m['rsi'] < 55: pullback = True
            if direction == "SHORT" and 45 < tf15m['rsi'] < 65: pullback = True
            
            results.append({
                'symbol': sym,
                'direction': direction,
                'score': score,
                'rsi_ok': rsi_ok,
                'pullback': pullback,
                'tf4h': tf4h,
                'tf1h': tf1h,
                'tf15m': tf15m
            })
        except Exception as e:
            print(f"  ⚠️ {sym}: {e}", file=sys.stderr)
    
    return sorted(results, key=lambda x: (x['score'], x['pullback'], x['rsi_ok']), reverse=True)

def main():
    # Exclude pairs already in portfolio (customize as needed)
    exclude = ['BTCUSDT', 'ETHUSDT']
    
    print("🔍 Fetching top volume pairs...")
    symbols = get_top_volume_pairs(exclude=exclude, top_n=15)
    
    print(f"📊 Scanning {len(symbols)} pairs across 4H/1H/15M...\n")
    results = scan_multi_tf(symbols)
    
    # Print results
    print(f"{'PAIR':15s} | {'4H':6s} | {'1H':6s} | {'15M':6s} | {'RSI4H':5s} | {'RSI1H':5s} | {'RSI15M':6s} | {'SCORE':5s} | DIR")
    print("-" * 90)
    
    for r in results:
        flags = ""
        if r['pullback']: flags += "✅PB "
        if not r['rsi_ok']: flags += "⚠️RSI "
        print(f"{r['symbol']:15s} | {r['tf4h']['trend']:6s} | {r['tf1h']['trend']:6s} | {r['tf15m']['trend']:6s} | "
              f"{r['tf4h']['rsi']:5.1f} | {r['tf1h']['rsi']:5.1f} | {r['tf15m']['rsi']:5.1f} | "
              f"{r['score']}/9   | {r['direction']} {flags}")
    
    # Top pick
    if results:
        best = results[0]
        print(f"\n🏆 TOP PICK: {best['symbol']} — {best['direction']} | Score: {best['score']}/9")
        print(f"   Entry zone: 15M EMA21 = ${best['tf15m']['ema21']:.5f}")
        print(f"   Current:    ${best['tf15m']['price']:.5f}")

if __name__ == '__main__':
    main()
