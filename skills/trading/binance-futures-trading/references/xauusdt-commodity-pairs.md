# XAUUSDT & Commodity Pairs on Binance Futures

## Key Differences from Crypto Pairs

### Price Discrepancy
- Binance Futures XAUUSDT trades at ~$4,700+ (May 2026)
- Spot gold (Kitco, Investing.com, TradingView) shows ~$3,385
- NEVER use external gold price sources for Binance Futures calculations
- Always verify via: `GET https://fapi.binance.com/fapi/v1/ticker/price?symbol=XAUUSDT`
- Or check browser title on `https://www.binance.com/en/futures/XAUUSDT`

### API Limitations (Discovered May 8, 2026)
**Conditional orders are BLOCKED for XAUUSDT via REST API:**

All of these return error `-4120`:
```
POST /fapi/v1/order (type=STOP_MARKET) → -4120
POST /fapi/v1/order (type=TAKE_PROFIT_MARKET) → -4120
POST /fapi/v1/order (type=STOP) → -4120
POST /fapi/v1/order (type=TAKE_PROFIT) → -4120
POST /fapi/v1/order (closePosition=true, type=STOP_MARKET) → -4120
POST /fapi/v1/batchOrders (type=STOP_MARKET) → -4120
```

Error message: `"Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."`

**But the Algo Order API doesn't support SL/TP either:**
- `/sapi/v1/algo/futures/newOrderVp` — only for TWAP/VP execution algorithms
- Returns "Insufficient margin" or "Invalid algoType" for stop-loss attempts

**What DOES work:**
- `LIMIT` orders ✅
- `MARKET` orders ✅
- Position queries (`/fapi/v2/positionRisk`) ✅
- Balance queries (`/fapi/v2/balance`) ✅

### Workarounds for SL/TP
1. **Manual via App** (RECOMMENDED) — User sets TP/SL from Binance mobile app or web
2. **Polling Monitor** — Script checks mark price every 10-30 seconds, executes MARKET SELL when SL breached
3. **WebSocket** — Connect to `wss://fstream.binance.com/ws/xauusdt@markPrice` for real-time price, trigger MARKET close

### Contract Specifications
- Tick size: $0.01
- Min quantity: 0.001 XAU
- Max quantity: 600 XAU
- Step size: 0.001
- Min notional: $5
- Supported order types (per exchangeInfo): LIMIT, MARKET, STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET
  - Note: These are LISTED but NOT FUNCTIONAL via API (only via app/web UI)

### NFP Trading on XAUUSDT
- NFP typical move: 1-2% ($47-94 at $4,700 level)
- Whipsaw can be $50-80 in first 30 seconds
- With 50x leverage: liquidation at ~1.5% ($71) — VERY tight for NFP
- Recommended max leverage for NFP: 20x (liquidation at ~5%)
- Always use ISOLATED margin for news trading
- Entry timing: wait 1-2 min after release for whipsaw to settle

### Funding Rate
- Typically 0.00000% or very low
- 4-hour funding cycle
- Not a significant cost factor for short-term NFP trades
