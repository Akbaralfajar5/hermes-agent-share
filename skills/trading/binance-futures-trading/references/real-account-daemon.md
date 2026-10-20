# Real Account Daemon Architecture

## Overview

For real-money trading, use a persistent daemon process instead of per-minute cronjobs. This provides:
- 30-second SL/TP enforcement (vs 60s+ with cronjobs)
- Single process = no race conditions between overlapping cron runs
- Separate scan interval (5 min) from SL/TP check interval (30s)
- Silent operation — only outputs on actions

## Architecture

```
┌─────────────────────────────────────────┐
│  screen -S fibstruct                     │
│  └─ python3 -u fibstruct_engine.py      │
│     ├─ Loop every 30s: check_sl_tp()    │
│     └─ Loop every 5m: scan_fibstruct()  │
└─────────────────────────────────────────┘
         ↑ watchdog
┌─────────────────────────────────────────┐
│  Cronjob (every 5 min)                   │
│  └─ Check screen alive → restart if dead │
│  └─ Grep log for actions → report only   │
│     if ENTRY/SL/TP/EXIT found            │
└─────────────────────────────────────────┘
```

## Strategy Evolution (May 2026)

### RSI(3) Mean Reversion (deprecated for real account)
- Simple: RSI(3) < 10 + price > EMA50 = LONG, RSI(3) > 90 + price < EMA50 = SHORT
- ~50% win rate, 1:1 R:R — too many small losses for small accounts
- Still valid for testnet or large balance accounts
- Files: `/home/ubuntu/rsi3_real_daemon.py`, `/home/ubuntu/rsi3_real_state.json`

### FibStruct (current — May 2026)
- 4-layer confluence: Market Structure + Trendline + Fibonacci OTE + Liquidity Sweep
- Target 60-68% win rate, minimum 1:2 R:R
- Very selective: 1-3 trades/day (most scans find 0-1 valid setups)
- Files: `/home/ubuntu/fibstruct_engine.py`, `/home/ubuntu/fibstruct_state.json`
- Screen: `fibstruct`
- Log: `/home/ubuntu/fibstruct.log`
- Watchdog cronjob: `728ffc5be136` ("FibStruct Engine Watchdog")

## Key Design Decisions

### SL/TP Enforcement Strategy
1. **Try API first** — `STOP_MARKET` / `TAKE_PROFIT_MARKET` via `/fapi/v1/order`
2. **If -4120 error** (commodity pairs like XAUUSDT, or any pair that blocks it) → mark `sl_api=false` in state
3. **Daemon polls every 30s** — for positions where `sl_api=false`, compare mark price vs SL/TP levels
4. **Execute MARKET close** when SL/TP breached

### State File (`fibstruct_state.json`)
```json
{
  "positions": {
    "ETHUSDT": {
      "symbol": "ETHUSDT",
      "direction": "LONG",
      "entry": 2288.37,
      "qty": 0.093,
      "leverage": 50,
      "sl": 2279.82,
      "tp1": 2296.92,
      "tp2": 2302.62,
      "margin": 4.25,
      "sl_api": false,
      "tp_api": false,
      "score": 4,
      "reasons": ["4H: BULLISH ✅", "1H: BULLISH ✅", "15M: Trendline ✅", "15M: Fib OTE ✅", "5M: No trigger ❌"],
      "time": "2026-05-08T20:12:04"
    }
  }
}
```

### FibStruct Signal Scan (every 5 min)
1. Refresh top 200 pairs by 24h volume from `/fapi/v1/ticker/24hr`
2. For each pair, run full 4-layer analysis:
   - Layer 1: 4H structure (BOS/CHoCH) + 1H confirmation
   - Layer 2: 15M trendline (intact/broken)
   - Layer 3: 15M Fibonacci OTE (price in 0.618-0.786 zone)
   - Layer 4: 5M liquidity sweep + price action trigger
3. Score 0-5, require ≥4 for entry
4. Check R:R ≥ 1:2
5. Pick best signal, execute immediately

### Entry Execution
1. Calculate dynamic leverage based on SL distance:
   - SL < 0.5% → 50x
   - SL 0.5-1% → 30x
   - SL 1-2% → 20x
   - SL > 2% → 10x
2. Set leverage via API
3. Set margin type to ISOLATED
4. Get quantity precision from exchangeInfo
5. Calculate qty: (balance × 4% × leverage) / price
6. Place MARKET order
7. Attempt API SL/TP → record success/failure in state
8. Log entry details with full confluence reasons

### SL/TP Placement (FibStruct-specific)
- **SL:** Below liquidity sweep wick + 0.1x ATR buffer (tight, structure-based)
- **Fallback:** Below Fib 0.786 + 0.3x ATR
- **TP1:** 1:2 R:R from entry
- **TP2:** 1:3 R:R or Fib extension -0.618

## Pitfalls Discovered (May 2026)

1. **Python stdout buffering** — Background processes produce no output without `python3 -u` or `PYTHONUNBUFFERED=1`. Always use `-u` flag when running via screen.

2. **XAUUSDT price ≠ spot gold** — Binance XAUUSDT perpetual trades at ~$4,726 while spot gold (Kitco) is ~$3,385. Never use spot gold prices for Binance Futures calculations. When user says "harga XAU 4726", trust them.

3. **Margin insufficient on ISOLATED** — When switching from CROSS to ISOLATED, available margin decreases. Use iterative qty reduction (90% → 80% → 60%) if -2019 error.

4. **API type checking** — Binance API sometimes returns dict (error) instead of list. Always check `isinstance(data, list)` AND `isinstance(item, dict)` before iterating/accessing.

5. **Duplicate positions** — If daemon runs scan while a position from previous scan is still being opened, can double-enter. Track existing symbols and skip.

6. **NFP/news trading** — For high-impact news events, the daemon's 5-min scan interval is too slow. Use a separate one-off script that monitors price every 2s and enters on confirmation (>0.3% move in expected direction). See `scripts/nfp_auto_entry.py`.

7. **Pre-news entry at high leverage is dangerous** — User entered XAUUSDT LONG at 50x CROSS before NFP. Price sideways for 5 hours, eventually closed at small loss. Lesson: pre-news entries should use lower leverage (20x) or wait for post-news confirmation.

8. **Cross margin on news events = full account risk** — User initially set CROSS margin on 50x XAUUSDT. If liquidated, entire $28 balance gone. Always recommend ISOLATED for news trading.

9. **Technical exit monitor** — When holding positions through volatile periods, a smart monitor that checks EMA crossovers + RSI + higher highs/lows every 60s can auto-exit when setup invalidates (3+ bullish signals while SHORT, or vice versa). This caught a SHORT exit at -$5 instead of letting it run to -$20+.

10. **Scan time for 200 pairs** — Full FibStruct analysis (4 TFs × 200 pairs) takes ~25-30 seconds. This is acceptable for 5-min scan interval but would be too slow for 1-min polling. Keep scan and SL/TP check as separate intervals.

11. **User preference: report only on actions** — User explicitly said "report ke chat hanya kalau ada aksi (entry/close/SL/TP hit)". Watchdog cronjob uses grep for action keywords and responds "silent" (suppresses delivery) when nothing happened.

## File Locations (the user VPS — May 2026)

### FibStruct (current):
- Engine/Daemon: `/home/ubuntu/fibstruct_engine.py`
- State: `/home/ubuntu/fibstruct_state.json`
- Log: `/home/ubuntu/fibstruct.log`
- Screen: `fibstruct`
- Watchdog cronjob ID: `728ffc5be136`

### RSI(3) (legacy, paused):
- Daemon: `/home/ubuntu/rsi3_real_daemon.py`
- Engine (standalone): `/home/ubuntu/rsi3_real.py`
- State: `/home/ubuntu/rsi3_real_state.json`
- Pairs list: `/home/ubuntu/rsi3_real_pairs.json`
- Log: `/home/ubuntu/rsi3_real.log`
- Screen: `rsi3real` (stopped)
- Cronjob: `cec4a5ba3988` (paused)

### Real Account Config:
- API Key: provided per-session (not in env vars)
- Base URL: `https://fapi.binance.com`
- Balance: ~$106 USDT (May 2026)
- Max positions: 3
- Margin per trade: 4%
- Margin type: ISOLATED (always)
