#!/usr/bin/env python3
"""
Futures Portfolio Monitor with Global News Risk Assessment
Executes directly — use as fallback when cronjob delivery fails.

Usage:
    python3 portfolio_monitor_with_news.py

Requires: requests library, API keys in env or hardcoded below.
"""
import requests, time, hmac, hashlib, json, os
from urllib.parse import urlencode

# Config — update these or use env vars
API_KEY = os.environ.get('BINANCE_API_KEY', '<YOUR_API_KEY>')
SECRET_KEY = os.environ.get('BINANCE_SECRET_KEY', '<YOUR_SECRET_KEY>')
BASE_URL = "https://testnet.binancefuture.com"  # Change to https://fapi.binance.com for prod

# SL/TP config — UPDATE THIS per your active positions
SL_TP_CONFIG = {
    # 'SYMBOL': {'side': 'LONG/SHORT', 'lev': N, 'entry': X, 'sl': X, 'tp1': X, 'tp2': X}
}

# News danger/caution keywords
DANGER_KEYWORDS = ['war', 'attack', 'bomb', 'missile', 'invasion', 'nuclear', 'sanction',
                   'hack', 'exploit', 'stolen', 'collapse', 'bankrupt', 'crash', 'ban',
                   'sec sue', 'arrest', 'fraud', 'depeg', 'dump', 'liquidat', 'fed rate',
                   'cpi', 'inflation shock', 'emergency', 'conflict', 'escalat']
CAUTION_KEYWORDS = ['regulation', 'investigate', 'probe', 'warning', 'risk', 'volatil',
                    'sell-off', 'selloff', 'decline', 'drop', 'fear', 'uncertain', 'tariff', 'trade war']


def sign(params):
    query = urlencode(params)
    signature = hmac.new(SECRET_KEY.encode(), query.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature
    return params


def fetch_news():
    """Fetch news and determine risk rating."""
    danger_found = False
    caution_found = False
    headlines = []
    fng_val = "N/A"
    fng_class = "N/A"

    # Fear & Greed Index
    try:
        fng = requests.get("https://api.alternative.me/fng/", timeout=10).json()
        fng_val = fng['data'][0]['value']
        fng_class = fng['data'][0]['value_classification']
    except:
        pass

    # CryptoCompare News
    try:
        news = requests.get("https://min-api.cryptocompare.com/data/v2/news/?lang=EN&sortOrder=latest", timeout=10).json()
        for item in news.get('Data', [])[:10]:
            title = item.get('title', '')
            headlines.append(title)
            title_lower = title.lower()
            for kw in DANGER_KEYWORDS:
                if kw in title_lower:
                    danger_found = True
                    break
            for kw in CAUTION_KEYWORDS:
                if kw in title_lower:
                    caution_found = True
                    break
    except:
        pass

    if danger_found:
        risk = "🔴 DANGER"
    elif caution_found:
        risk = "🟡 CAUTION"
    else:
        risk = "🟢 SAFE"

    return {
        'risk': risk,
        'danger': danger_found,
        'caution': caution_found,
        'fng_val': fng_val,
        'fng_class': fng_class,
        'headlines': headlines[:5]
    }


def fetch_portfolio():
    """Fetch account and positions."""
    headers = {"X-MBX-APIKEY": API_KEY}
    params = {"timestamp": int(time.time() * 1000), "recvWindow": 10000}
    params = sign(params)
    r = requests.get(f"{BASE_URL}/fapi/v2/account", params=params, headers=headers)
    return r.json()


def get_price(symbol):
    """Get current price for a symbol."""
    r = requests.get(f"{BASE_URL}/fapi/v1/ticker/price", params={"symbol": symbol})
    return float(r.json()['price'])


def close_position(symbol, quantity, side):
    """Close a position with market order."""
    headers = {"X-MBX-APIKEY": API_KEY}
    close_side = "SELL" if side == "LONG" else "BUY"
    params = {
        "symbol": symbol, "side": close_side, "type": "MARKET",
        "quantity": quantity, "timestamp": int(time.time() * 1000), "recvWindow": 10000
    }
    params = sign(params)
    r = requests.post(f"{BASE_URL}/fapi/v1/order", params=params, headers=headers)
    return r.json()


def main():
    output = []
    
    # === NEWS SECTION ===
    news = fetch_news()
    output.append("=" * 55)
    output.append("📰 BERITA & SENTIMEN MARKET")
    output.append("=" * 55)
    output.append(f"😱 Fear & Greed Index: {news['fng_val']} ({news['fng_class']})")
    output.append(f"\n📰 Headline Terkini:")
    output.append("-" * 55)
    for i, h in enumerate(news['headlines'], 1):
        output.append(f"  {i}. {h}")
    output.append(f"\n🚦 Risk Rating: {news['risk']}")

    # === PORTFOLIO SECTION ===
    account = fetch_portfolio()
    if 'code' in account:
        output.append(f"\n❌ API Error: {account}")
        print("\n".join(output))
        return

    balance = float(account.get('totalWalletBalance', 0))
    unrealized_pnl = float(account.get('totalUnrealizedProfit', 0))
    margin_balance = float(account.get('totalMarginBalance', 0))
    available = float(account.get('availableBalance', 0))

    output.append("")
    output.append("=" * 55)
    output.append("📊 PORTFOLIO STATUS")
    output.append("=" * 55)
    output.append(f"💰 Wallet Balance:    ${balance:.2f}")
    output.append(f"💵 Available Balance: ${available:.2f}")
    output.append(f"📈 Unrealized PnL:    ${unrealized_pnl:.2f}")
    output.append(f"🏦 Margin Balance:    ${margin_balance:.2f}")

    positions = [p for p in account.get('positions', []) if float(p['positionAmt']) != 0]
    actions_taken = []

    output.append(f"\n📋 POSISI TERBUKA ({len(positions)}):")
    output.append("-" * 55)

    for pos in positions:
        symbol = pos['symbol']
        side = "LONG" if float(pos['positionAmt']) > 0 else "SHORT"
        amt = abs(float(pos['positionAmt']))
        entry = float(pos['entryPrice'])
        pnl = float(pos['unrealizedProfit'])
        leverage = int(pos['leverage'])
        margin = float(pos.get('initialMargin', 0))
        current_price = get_price(symbol)

        if entry > 0:
            if side == "LONG":
                pnl_pct = ((current_price - entry) / entry) * 100 * leverage
            else:
                pnl_pct = ((entry - current_price) / entry) * 100 * leverage
        else:
            pnl_pct = 0

        emoji = "🟢" if pnl >= 0 else "🔴"
        config = SL_TP_CONFIG.get(symbol, {})
        warning = ""

        if config:
            sl = config['sl']
            tp1 = config['tp1']
            if side == "LONG":
                sl_dist = ((current_price - sl) / current_price) * 100
                if current_price <= sl:
                    warning = "🚨 SL HIT!"
                    actions_taken.append(f"🚨 {symbol}: SL HIT @ ${current_price:.4f}")
                elif sl_dist <= 0.3:
                    warning = f"⚠️ DEKAT SL ({sl_dist:.2f}%)"
                if current_price >= tp1:
                    warning += " 🎯 TP1 HIT!"
                    actions_taken.append(f"🎯 {symbol}: TP1 HIT @ ${current_price:.4f}")
            else:
                sl_dist = ((sl - current_price) / current_price) * 100
                if current_price >= sl:
                    warning = "🚨 SL HIT!"
                    actions_taken.append(f"🚨 {symbol}: SL HIT @ ${current_price:.4f}")
                elif sl_dist <= 0.3:
                    warning = f"⚠️ DEKAT SL ({sl_dist:.2f}%)"
                if current_price <= tp1:
                    warning += " 🎯 TP1 HIT!"
                    actions_taken.append(f"🎯 {symbol}: TP1 HIT @ ${current_price:.4f}")

        # DANGER auto cut loss
        if news['danger'] and pnl < 0:
            warning += " 🔴 AUTO CUT LOSS (DANGER NEWS)"
            actions_taken.append(f"🔴 AUTO CUT {symbol}: PnL ${pnl:.2f}")
            # Uncomment to actually execute:
            # close_position(symbol, amt, side)

        output.append(f"\n{emoji} {symbol} | {side} {leverage}x")
        output.append(f"   Entry: ${entry:.4f} -> Now: ${current_price:.4f}")
        output.append(f"   Size: {amt} | Margin: ${margin:.2f}")
        output.append(f"   PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        if config:
            output.append(f"   SL: ${config['sl']} | TP1: ${config['tp1']} | TP2: ${config['tp2']}")
        if warning:
            output.append(f"   {warning}")

    # === ACTIONS ===
    output.append("")
    output.append("=" * 55)
    output.append("⚡ AKSI YANG DIAMBIL")
    output.append("=" * 55)
    if actions_taken:
        for a in actions_taken:
            output.append(f"  {a}")
    else:
        output.append("  ✅ Tidak ada aksi otomatis. Semua posisi dalam range.")

    # === RECOMMENDATIONS ===
    output.append("")
    output.append("=" * 55)
    output.append("💡 REKOMENDASI")
    output.append("=" * 55)
    minus_positions = [p for p in positions if float(p['unrealizedProfit']) < 0]
    plus_positions = [p for p in positions if float(p['unrealizedProfit']) >= 0]

    if news['danger']:
        output.append("  🔴 BERITA BERBAHAYA TERDETEKSI!")
        output.append("  -> Cut loss semua posisi minus")
        output.append("  -> Ketatkan SL posisi profit")
        output.append("  -> Jangan buka posisi baru")
    elif news['caution']:
        output.append("  🟡 Ada berita perlu diperhatikan")
        output.append("  -> Monitor ketat, jangan tambah posisi")
        output.append(f"  -> {len(minus_positions)} minus, {len(plus_positions)} profit")
    else:
        output.append("  🟢 Market relatif aman")
        output.append(f"  -> {len(minus_positions)} minus, {len(plus_positions)} profit")
        if minus_positions:
            worst = min(minus_positions, key=lambda p: float(p['unrealizedProfit']))
            output.append(f"  -> Terburuk: {worst['symbol']} (${float(worst['unrealizedProfit']):.2f})")

    output.append(f"\n⏰ Updated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print("\n".join(output))


if __name__ == "__main__":
    main()
