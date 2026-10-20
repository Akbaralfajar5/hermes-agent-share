# XAUUSDT (Gold) Trading on Binance Futures — Quirks & Notes

## Price Discrepancy
- **Binance Futures XAUUSDT Perpetual** trades at a DIFFERENT price than spot gold (XAU/USD from Kitco/Investing.com)
- As of May 2026: Binance XAUUSDT ≈ $4,700+ while spot gold ≈ $3,385
- This is because Binance's XAUUSDT is a crypto perpetual contract with its own pricing, funding rate, and premium
- **Always check Binance price directly** — do NOT use spot gold prices from Kitco/TradingView for Binance Futures calculations

## API Limitations (PROD)
- **Conditional orders (SL/TP) do NOT work via API** for XAUUSDT
- Error: `{"code":-4120,"msg":"Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."}`
- Affected order types: STOP_MARKET, TAKE_PROFIT_MARKET, STOP, TAKE_PROFIT
- Also fails via batch orders endpoint
- **MARKET and LIMIT orders work fine**
- User must set SL/TP from the Binance mobile app or web UI

## Workaround for SL/TP
1. **Manual from app** (recommended) — fastest execution, server-side
2. **Polling monitor script** — check price every 15s, execute MARKET SELL when SL hit
   - Downside: 15s gap means price can slip past SL
   - Use for backup monitoring, not primary SL

## Contract Specs
- Tick size: $0.01
- Min qty: 0.001
- Step size: 0.001
- Min notional: $5
- Funding rate: every 4 hours

## NFP/News Trading on XAUUSDT
- Gold is highly sensitive to USD news (NFP, CPI, FOMC)
- Typical NFP move: 1-3% within first 5 minutes
- Pre-news: sideways/choppy (dangerous for leveraged positions)
- Post-news: strong directional momentum (safer for high leverage entry)
- Spread widens significantly at exact release time (wait 30-60s)
