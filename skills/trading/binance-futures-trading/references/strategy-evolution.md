# Strategy Evolution (from crypto-futures-trading-system)

## Timeline
- AITS (Complex SMC) → Failed: too complex, 4H not 15m scalping
- EMA-VWAP Scalping → Failed: 37.5% WR, -$182 loss
- S/R + Volume Profile → Deployed but didn't improve
- BB+RSI Mean Reversion → 79.2% WR backtest but ZERO live signals (thresholds too strict)
- **RSI(3) + EMA(50) + Volume (CURRENT)** → 72.1% WR, 8.3 trades/day, PF 1.63

## Current Strategy: RSI(3) Mean Reversion + EMA(50) + Volume
- RSI Period: 3 (very responsive)
- RSI Entry: < 25 (LONG) / > 75 (SHORT)
- RSI Exit: > 75 (LONG) / < 25 (SHORT)
- Trend Filter: EMA(50)
- Volume Filter: Signal candle volume > 1.2x 20-period average
- SL: 2%
- Engine: `/home/ubuntu/rsi3_engine.py`
- State file: `/home/ubuntu/rsi3_state.json`

## Key Lessons
- High WR in backtest ≠ practical strategy (BB+RSI: 79% WR, 0 signals/day)
- Signal frequency matters as much as accuracy
- RSI(3) at 25/75 triggers 8-30x/day vs RSI(21) barely triggers
- Simple (2 indicators + volume) = easy to debug and automate
- Complexity doesn't equal profitability (AITS had 5 components, still lost)
- MUST backtest with 100+ historical trades before live deployment

## Comprehensive Backtest Results (12 Strategies)
1. 🥇 BB + RSI Mean Reversion — 79.2% WR (optimized), +48.41% PnL, PF 3.79
2. 🥈 VWAP + RSI Div + Vol — 51.9% WR, +9.42% PnL, PF 1.47
3. 🥉 EMA 8/21 + ADX>25 — 47.8% WR, +11.3% PnL, PF 1.46
4-12. All others lost money

## TP/SL Rules (Non-Negotiable)
- TP1 (1.5% profit): Close 30%
- TP2 (3% profit): Close 40%
- TP3 (5% profit): Close 20%
- Trailing Stop (after TP3): 2% from peak for remaining 10%
- SL: 2% from entry, CLOSE IMMEDIATELY

## Monitoring Interval
- Every 1 minute (Mon-Fri) for SL/TP enforcement
- Testnet has NO native conditional orders — must poll

## CloakBrowser for Scraping
All browser-based scraping (CMC, CoinGlass, news sites) MUST use CloakBrowser:
```python
from cloakbrowser import launch
browser = launch(headless=True)
page = browser.new_page()
page.goto("https://coinmarketcap.com/charts/")
browser.close()
```
Installed in hermes venv. Passes Cloudflare Turnstile, FingerprintJS, BrowserScan.
