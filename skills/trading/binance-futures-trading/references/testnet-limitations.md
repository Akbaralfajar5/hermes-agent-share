# Testnet Limitations & Workarounds

## Known Testnet Limitations (as of May 2026)

### Conditional Orders NOT Supported
Despite `exchangeInfo` listing STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET as valid order types, placing them returns:
```
{"code": -4120, "msg": "Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."}
```

The Algo Order endpoint also fails:
```
{"code": -4120, "msg": "Invalid algoType."}
```

Endpoints tried and failed:
- `/fapi/v1/order` POST with type=STOP_MARKET → -4120
- `/fapi/v2/order` POST → -5000 "Path invalid"
- `/fapi/v1/conditional/order` POST → -5000 "Path invalid"
- `/fapi/v1/algo/futures/newOrder` POST → -5000 "Path invalid"
- `binance-cli futures-usds new-algo-order --algo-type STOP_MARKET` → "Invalid algoType"
- `binance-cli futures-usds new-algo-order --algo-type VP` → "Invalid algoType"

### What DOES Work on Testnet
- MARKET orders ✅
- LIMIT orders ✅
- Position queries ✅
- Leverage changes ✅
- Margin type changes ✅
- Account balance queries ✅
- Exchange info ✅

### Workaround: Cron-Based SL/TP
Set up a cron job (every 15 minutes) that:
1. Reads mark price from position-information-v3
2. Compares against predefined SL/TP levels
3. Executes MARKET close order if SL breached
4. Executes partial MARKET close if TP1/TP2/TP3 hit
5. If position within 0.3% of SL, cut immediately (don't wait for next poll)

**Also tested and confirmed NOT working on testnet:**
- `/fapi/v1/order` with type STOP/TAKE_PROFIT (with price param) → same error
- `/fapi/v1/batchOrders` with conditional types → same error per item
- `/fapi/v1/algo/order` → "Path invalid"
- `/fapi/v1/conditional/order` → "Path invalid"
- `/sapi/v1/algo/futures/newOrderTwap` → connection error (not available on testnet domain)

### Testnet API URL
- Base: `https://testnet.binancefuture.com`
- Set via: `export BINANCE_API_ENV=testnet`

### Testnet Default Balance
- 5,000 USDT + 5,000 USDC + 0.01 BTC (virtual)

### Testnet API Key
- Create at: https://testnet.binancefuture.com/
- Separate from prod API keys
- Login with regular Binance account

## Prod vs Testnet Quick Reference

| Feature | Testnet | Prod |
|---------|---------|------|
| MARKET orders | ✅ | ✅ |
| LIMIT orders | ✅ | ✅ |
| STOP_MARKET | ❌ | ✅ (except commodity pairs) |
| TAKE_PROFIT_MARKET | ❌ | ✅ (except commodity pairs) |
| TRAILING_STOP | ❌ | ✅ (except commodity pairs) |
| Algo Orders (TWAP/VP) | ❌ | ✅ |
| Conditional Orders | ❌ | ✅ (except commodity pairs) |
| Real money | ❌ | ✅ |

## PROD: Commodity Pairs (XAUUSDT) — Conditional Orders BLOCKED

**Discovered May 2026:** XAUUSDT (Gold perpetual) on PROD Binance Futures returns the SAME `-4120` error as testnet for ALL conditional order types:

```
{"code":-4120,"msg":"Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."}
```

**Endpoints tested on PROD (all failed for XAUUSDT):**
- `/fapi/v1/order` POST with type=STOP_MARKET → -4120
- `/fapi/v1/order` POST with type=TAKE_PROFIT_MARKET → -4120
- `/fapi/v1/order` POST with closePosition=true → -4120
- `/fapi/v1/batchOrders` with STOP_MARKET → -4120
- `/fapi/v1/conditional/order` → 404
- `/fapi/v2/order`, `/fapi/v3/order` → 404
- `/sapi/v1/algo/futures/newOrderVp` → -20193 "Insufficient margin" (different error, endpoint exists but not for SL)

**This likely affects ALL commodity-class perpetuals on Binance** (XAUUSDT, possibly XAGUSDT if it exists).

**Workaround:** User must set TP/SL manually via the Binance app/web UI. The API can only place MARKET and LIMIT orders for these pairs.

**Alternative monitoring approach:** Set up a polling script that checks mark price every 5-15s and executes a MARKET SELL (reduceOnly) if price breaches SL level. MARKET orders DO work on XAUUSDT.

**Margin Insufficient Error (-2019):** When switching from CROSS to ISOLATED margin on XAUUSDT, the margin requirement increases. Use 90% of available balance for qty calculation, or reduce qty iteratively (90% → 80% → 60%) if error persists:
```python
for pct in [0.90, 0.80, 0.60]:
    qty = round((available * pct * leverage) / price, 3)
    result = api_post('/fapi/v1/order', {...})
    if 'orderId' in result:
        break
```

**News-event auto-entry:** For high-impact news (NFP, CPI, FOMC), use `scripts/nfp_auto_entry.py` which:
1. Monitors price pre-news
2. Waits for confirmation (>0.3% move in expected direction)
3. Executes MARKET entry with leverage/margin config
4. Falls back to manual polling for SL/TP since API conditional orders are blocked

**CRITICAL: Run with `PYTHONUNBUFFERED=1`** — without this, background scripts produce no visible output due to stdout buffering in non-TTY mode.

**XAUUSDT Price Note:** The Binance Futures XAUUSDT perpetual trades at a DIFFERENT price than spot gold (XAU/USD). As of May 2026: Binance XAUUSDT ≈ $4,726 while spot gold ≈ $3,385. Do NOT confuse the two — always check the actual Binance Futures price, not Kitco/Investing.com spot prices.
