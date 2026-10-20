"""
Intraday Multi-Timeframe Scanner for Binance Futures
Scans top volume pairs and scores them on 4H→1H→15M→5M alignment.
Returns valid setups (score >= 3/4) ready for execution.

Usage: Run directly or import scan_for_entries()
Requires: requests
"""
import requests, time, json

BASE_URL = "https://testnet.binancefuture.com"  # Change to https://fapi.binance.com for prod

def get_klines(symbol, interval, limit=100):
    try:
        r = requests.get(f"{BASE_URL}/fapi/v1/klines",
                        params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=10)
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            return data
    except:
        pass
    return None

def calc_ema(closes, period):
    if len(closes) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(closes[:period]) / period
    for price in closes[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calc_macd(closes):
    if len(closes) < 26:
        return None, None, None
    ema12 = calc_ema(closes, 12)
    ema26 = calc_ema(closes, 26)
    if ema12 and ema26:
        return ema12 - ema26, ema12, ema26
    return None, None, None

def calc_atr(klines, period=14):
    trs = []
    for i in range(1, len(klines)):
        high = float(klines[i][2])
        low = float(klines[i][3])
        prev_close = float(klines[i-1][4])
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    if len(trs) >= period:
        return sum(trs[-period:]) / period
    return sum(trs) / len(trs) if trs else 0

def analyze_tf(klines):
    """Analyze single timeframe. Returns (score, direction, details)"""
    if not klines or len(klines) < 50:
        return (0, "NEUTRAL", "Insufficient data")

    closes = [float(k[4]) for k in klines]
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    volumes = [float(k[5]) for k in klines]

    current = closes[-1]
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    macd, _, _ = calc_macd(closes)

    if not ema20 or not ema50:
        return (0, "NEUTRAL", "EMA calc failed")

    bullish = 0
    bearish = 0
    details = []

    # EMA alignment
    if current > ema20 > ema50:
        bullish += 2; details.append("EMA20>EMA50 ✅")
    elif current < ema20 < ema50:
        bearish += 2; details.append("EMA20<EMA50 ✅")
    else:
        details.append("EMA mixed")

    # MACD
    if macd and macd > 0:
        bullish += 1; details.append("MACD+ ✅")
    elif macd and macd < 0:
        bearish += 1; details.append("MACD- ✅")

    # Momentum (last 5 candles)
    if closes[-1] > closes[-5]:
        bullish += 1; details.append("Momentum↑")
    else:
        bearish += 1; details.append("Momentum↓")

    # Structure (HH/HL or LH/LL)
    recent_highs = highs[-10:]
    recent_lows = lows[-10:]
    if recent_highs[-1] > max(recent_highs[:5]) and recent_lows[-1] > min(recent_lows[:5]):
        bullish += 1; details.append("HH/HL ✅")
    elif recent_highs[-1] < min(recent_highs[:5]) and recent_lows[-1] < max(recent_lows[:5]):
        bearish += 1; details.append("LH/LL ✅")

    direction = "LONG" if bullish > bearish else "SHORT" if bearish > bullish else "NEUTRAL"
    return (max(bullish, bearish), direction, " | ".join(details))


def scan_for_entries(exclude_symbols=None, min_score=3, max_results=5):
    """
    Scan top volume pairs for intraday setups.
    
    Args:
        exclude_symbols: list of symbols to skip (already in portfolio)
        min_score: minimum TF alignment score (default 3/4)
        max_results: max number of valid setups to return
    
    Returns: list of dicts with symbol, direction, score, price, atr_15m, atr_1h, details
    """
    if exclude_symbols is None:
        exclude_symbols = []

    # Get top volume pairs
    r = requests.get(f"{BASE_URL}/fapi/v1/ticker/24hr")
    tickers = r.json()
    usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT') and float(t['quoteVolume']) > 0]
    usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)

    # Filter: exclude active positions, skip extreme movers (>80% or <-30%)
    candidates = []
    for t in usdt_pairs:
        if t['symbol'] in exclude_symbols:
            continue
        change = float(t['priceChangePercent'])
        if -30 < change < 80:  # Skip pump/dump coins
            candidates.append(t)
        if len(candidates) >= 30:
            break

    results = []
    for t in candidates:
        symbol = t['symbol']
        k4h = get_klines(symbol, "4h", 100)
        k1h = get_klines(symbol, "1h", 100)
        k15m = get_klines(symbol, "15m", 100)
        k5m = get_klines(symbol, "5m", 100)

        if not all([k4h, k1h, k15m, k5m]):
            continue

        r4h = analyze_tf(k4h)
        r1h = analyze_tf(k1h)
        r15m = analyze_tf(k15m)
        r5m = analyze_tf(k5m)

        directions = [r[1] for r in [r4h, r1h, r15m, r5m]]
        long_count = directions.count("LONG")
        short_count = directions.count("SHORT")

        if long_count >= min_score:
            aligned = "LONG"
            score = long_count
        elif short_count >= min_score:
            aligned = "SHORT"
            score = short_count
        else:
            continue

        atr_15m = calc_atr(k15m)
        atr_1h = calc_atr(k1h)
        current_price = float(k5m[-1][4])

        results.append({
            'symbol': symbol,
            'direction': aligned,
            'score': score,
            'price': current_price,
            'atr_15m': atr_15m,
            'atr_1h': atr_1h,
            'tf_details': {
                '4H': f"{r4h[1]} ({r4h[2]})",
                '1H': f"{r1h[1]} ({r1h[2]})",
                '15M': f"{r15m[1]} ({r15m[2]})",
                '5M': f"{r5m[1]} ({r5m[2]})"
            }
        })

    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:max_results]


def calculate_sl_tp(price, atr_15m, direction, sl_multiplier=1.2):
    """Calculate SL/TP based on ATR 15M"""
    sl_distance = atr_15m * sl_multiplier
    tp1_distance = sl_distance * 1.5  # RR 1:1.5
    tp2_distance = sl_distance * 2.5  # RR 1:2.5
    tp3_distance = sl_distance * 3.5  # RR 1:3.5

    if direction == "LONG":
        return {
            'sl': price - sl_distance,
            'tp1': price + tp1_distance,
            'tp2': price + tp2_distance,
            'tp3': price + tp3_distance
        }
    else:
        return {
            'sl': price + sl_distance,
            'tp1': price - tp1_distance,
            'tp2': price - tp2_distance,
            'tp3': price - tp3_distance
        }


if __name__ == "__main__":
    print("🔍 Scanning for intraday setups...")
    setups = scan_for_entries(exclude_symbols=["NEARUSDT", "DOGEUSDT"])
    
    if setups:
        print(f"\n✅ Found {len(setups)} valid setups:\n")
        for s in setups:
            levels = calculate_sl_tp(s['price'], s['atr_15m'], s['direction'])
            print(f"🎯 {s['symbol']} — {s['direction']} (Score: {s['score']}/4)")
            print(f"   Price: ${s['price']}")
            print(f"   SL: ${levels['sl']:.6f} | TP1: ${levels['tp1']:.6f} | TP2: ${levels['tp2']:.6f}")
            print(f"   4H: {s['tf_details']['4H']}")
            print(f"   1H: {s['tf_details']['1H']}")
            print(f"   15M: {s['tf_details']['15M']}")
            print(f"   5M: {s['tf_details']['5M']}")
            print()
    else:
        print("❌ No valid setups found (all scores < 3/4)")
