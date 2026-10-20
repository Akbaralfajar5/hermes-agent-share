# Cronjob Prompt Template (AITS Version — 2026-05-02)

## Structure (6 phases)

```
=== BAGIAN 1: BERITA & SENTIMEN ===
1. Scrape @marketfeed: https://t.me/s/marketfeed (20 post terbaru)
2. CryptoCompare: https://min-api.cryptocompare.com/data/v2/news/?lang=EN&sortOrder=latest
3. CMC Fear & Greed (REAL-TIME): scrape https://coinmarketcap.com/charts/fear-and-greed-index/
   → re.findall(r'"score"\s*:\s*(\d+)', text)[0]
   → ❌ JANGAN pakai api.alternative.me (delayed/inaccurate!)
4. Risk Rating: 🟢 SAFE / 🟡 CAUTION / 🔴 DANGER

=== BAGIAN 2: ANALISA BTC (WAJIB) ===
Import: sys.path.insert(0, '/home/ubuntu'); from aits_engine import *
Use analyze_aits("BTCUSDT") → BTC bias from 4H BOS/CHoCH

=== BAGIAN 3: MONITOR POSISI ===
- Account info, all positions, PnL
- Check SL/TP levels (listed in prompt)
- AUTO SL → close. AUTO TP1 → close 30%, SL to BE. TP2 → 40%. TP3 → rest.
- New positions without SL/TP → calculate from Order Block + ATR

=== BAGIAN 4: RE-ANALISA VALIDITY (AITS) ===
For each position: analyze_aits(symbol) → score_setup()
- Score < 40 → AUTO CLOSE
- 4H CHoCH against position → AUTO CLOSE
- Report validity status per position

=== BAGIAN 5: AUTO SCAN ENTRY (IF POSITIONS < 5) ===
Use scan_and_execute(btc_bias, risk_rating, wallet, 5, current)
- AITS scoring (BOS/CHoCH + Order Blocks + Fib OTE + Volume + Liquidity)
- Minimum score 60 (75 if against BTC)
- Token news check before entry
- Dynamic leverage (ATR-based)
- LANGSUNG EKSEKUSI, jangan tanya

=== BAGIAN 6: FORMAT OUTPUT (Bahasa Indonesia, SINGKAT) ===
₿ BTC: [arah] | 😱 F&G: [score] | 🚦 [rating]
📊 Portfolio: [balance] | PnL: [total]
[list posisi + validity status]
⚡ Aksi: [SL/TP/close/entry]
💡 Saran singkat
```

## Key Rules
- Toolsets required: `["terminal", "web"]`
- Schedule: every 15m
- All actions AUTO-EXECUTE (no asking user)
- Output in Indonesian, compact format
- AITS script at `/home/ubuntu/aits_engine.py`
