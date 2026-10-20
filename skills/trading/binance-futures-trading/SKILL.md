---
name: binance-futures-trading
description: "Execute and manage Binance Futures trades via binance-cli and direct API. Covers position opening, leverage, margin type, TP/SL, monitoring, and testnet vs prod differences. Trigger on: futures trading, open position, set leverage, stop loss, take profit, binance API trading, position management."
tags: [trading, binance, futures, crypto, execution, api]
---

# Binance Futures Trading Execution

End-to-end workflow for executing and managing futures trades on Binance via `binance-cli` or direct HMAC-signed API calls.

## Prerequisites

- **Node.js 22+** required for `binance-cli` (v18 fails with `styleText` import error)
- `npm install -g @binance/binance-cli` (v1.1.1+)
- Environment variables: `BINANCE_API_KEY`, `BINANCE_SECRET_KEY`, `BINANCE_API_ENV` (prod|testnet)
- NVM setup: `source ~/.nvm/nvm.sh && nvm use 22`

## Environment Setup

```bash
source ~/.nvm/nvm.sh && nvm use 22
export BINANCE_API_KEY="<key>"
export BINANCE_SECRET_KEY="<secret>"
export BINANCE_API_ENV=testnet  # or prod
```

## Workflow

### Step 1: Check Balance
```bash
binance-cli futures-usds futures-account-balance-v3
```

### Step 2: Check Max Leverage
```bash
binance-cli futures-usds notional-and-leverage-brackets --symbol INJUSDT
```

### Step 3: Set Leverage
```bash
binance-cli futures-usds change-initial-leverage --symbol INJUSDT --leverage 25
```

### Step 4: Set Margin Type (Isolated recommended)
```bash
binance-cli futures-usds change-margin-type --symbol INJUSDT --margin-type ISOLATED
```
Note: Returns "No need to change margin type" if already set.

### Step 5: Open Position — Choose Order Type

**Decision rule (UPDATED — Limit Order Default):** ALWAYS prefer LIMIT ORDER at the calculated S/D zone or Fibonacci OTE level. Market order ONLY if price is already within 0.15% of the entry zone. This "sniper entry" approach reduces fees (maker rate), eliminates slippage, and prevents FOMO entries at bad prices. Auto-cancel limit orders not filled within 2 hours.

```bash
# Market order (price already at entry zone)
binance-cli futures-usds new-order --symbol INJUSDT --side BUY --type MARKET --quantity 316

# Limit order (waiting for pullback — PREFERRED for precision)
binance-cli futures-usds new-order --symbol INJUSDT --side BUY --type LIMIT --price 3.55 --quantity 316 --time-in-force GTC
```

**Direct Python API (more reliable than binance-cli profiles):**
```python
import hashlib, hmac, time, requests, os
from urllib.parse import urlencode

API_KEY = os.environ['BINANCE_API_KEY']
SECRET_KEY = os.environ['BINANCE_SECRET_KEY']
BASE_URL = "https://testnet.binancefuture.com"  # or https://fapi.binance.com for prod

def sign_request(params):
    query_string = urlencode(params)
    params['signature'] = hmac.new(SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    return params

def api_request(method, endpoint, params={}):
    params['timestamp'] = int(time.time() * 1000)
    params = sign_request(params)
    headers = {'X-MBX-APIKEY': API_KEY}
    url = f"{BASE_URL}{endpoint}"
    return (requests.get if method == 'GET' else requests.post)(url, params=params, headers=headers).json()

# Limit order example
order = api_request('POST', '/fapi/v1/order', {
    'symbol': 'DOGEUSDT', 'side': 'BUY', 'type': 'LIMIT',
    'timeInForce': 'GTC', 'quantity': 18000, 'price': 0.10900
})
```

### Step 6: Set TP/SL (PROD ONLY)
```bash
# Stop Loss
binance-cli futures-usds new-order --symbol INJUSDT --side SELL --type STOP_MARKET --stop-price 3.18 --quantity 316 --reduce-only true --working-type MARK_PRICE

# Take Profit
binance-cli futures-usds new-order --symbol INJUSDT --side SELL --type TAKE_PROFIT_MARKET --stop-price 4.20 --quantity 95 --reduce-only true --working-type MARK_PRICE
```

### Step 7: Monitor Position
```bash
binance-cli futures-usds position-information-v3 --symbol INJUSDT
```

### Step 8: Close Position
```bash
# Close LONG
binance-cli futures-usds new-order --symbol INJUSDT --side SELL --type MARKET --quantity 316

# Close SHORT
binance-cli futures-usds new-order --symbol WIFUSDT --side BUY --type MARKET --quantity 8800
```

## XAUUSDT (Gold) on Binance Futures

**CRITICAL:** Binance Futures XAUUSDT trades at a DIFFERENT price than spot gold (XAU/USD from Kitco/Investing.com). As of May 2026:
- Binance Futures XAUUSDT Perp: ~$4,720-4,730
- Spot gold (Kitco/Investing.com): ~$3,360-3,390

**Always check the actual Binance Futures price** — do NOT use spot gold prices from external sources for position sizing or liquidation calculations. The Binance perpetual contract has its own price discovery.

**Conditional Orders (SL/TP) BLOCKED on XAUUSDT PROD:**
STOP_MARKET, TAKE_PROFIT_MARKET all return `-4120` on XAUUSDT. User must set SL/TP from app/web UI. API workaround: polling script that checks mark price every 5s and executes MARKET close (reduceOnly) when SL/TP breached.

**Margin Insufficient (-2019) with Full Balance:**
When opening with high leverage using full available balance, Binance rejects because it reserves for fees + funding. Solution: use 90% of available, retry at 80%/60% if still fails:
```python
usable = available_balance * 0.90
qty = round((usable * leverage) / price, 3)
```

**Checking XAUUSDT price:** Use browser to visit `https://www.binance.com/en/futures/XAUUSDT` and read `document.title` which shows live price, OR use the API:
```python
r = requests.get(f"{BASE_URL}/fapi/v1/ticker/price", params={'symbol': 'XAUUSDT'})
```

## Position Sizing Formula

```
risk_amount = balance × risk_pct (e.g., 2%)
margin_per_trade = balance × 0.02  # Fixed 2% margin
notional = margin × leverage
quantity = notional / entry_price
```

## Leverage Strategy: DYNAMIC BASED ON VOLATILITY

**Exception — News Event Trading (NFP, CPI, FOMC):**
When entering AFTER a high-impact news release with confirmed direction (post-confirmation entry, not pre-news), higher leverage (50x) is acceptable even on volatile pairs because:
- Momentum is strong and directional (not choppy)
- Entry is WITH the move, not waiting in sideways
- The key distinction: pre-news entry at 50x = dangerous (sideways chop can liquidate); post-news confirmation entry at 50x = riding momentum

**Pre-news vs Post-news entry:**
| Timing | Leverage OK | Why |
|--------|------------|-----|
| Before news (hours ahead) | 10-20x max | Sideways chop, whipsaw risk, no momentum |
| After news (1-2 min post-release, direction confirmed >0.3%) | 50x OK | Momentum confirmed, riding the wave |

**Rule:** Leverage is determined by token volatility (ATR%), NOT always max. Risk is controlled by margin size (2%) + SL distance. Higher volatility tokens need LOWER leverage so SL has room to breathe.

**LESSON LEARNED (TAGUSDT incident):** Using max leverage (50x) on a highly volatile shitcoin caused immediate SL hit because the SL distance was too tight relative to normal price swings. The position lost ~$39 within minutes. Solution: scale leverage inversely with volatility.

**Volatility-Based Leverage Formula:**
```python
# 1. Calculate volatility
atr_15m = calc_atr(klines_15m, period=14)
atr_pct = (atr_15m / current_price) * 100  # ATR as % of price

# 2. Query max leverage for the pair
params = sign({"symbol": symbol, "timestamp": int(time.time() * 1000), "recvWindow": 10000})
r = requests.get(f"{BASE_URL}/fapi/v1/leverageBracket", params=params, headers=headers)
brackets = r.json()[0]['brackets']
max_leverage = brackets[0]['initialLeverage']

# 3. Calculate appropriate leverage based on volatility
calculated_lev = int(min(max_leverage, max(10, 2 / atr_pct * 10)))

# Volatility tiers:
# ATR% > 2%  (shitcoin, meme, lowcap)  → 10-20x (LOW)
# ATR% 1-2%  (midcap altcoin)           → 20-50x (MEDIUM)
# ATR% < 1%  (large cap BTC/ETH/BNB)    → 50x-MAX (HIGH)

leverage = calculated_lev

# 4. Set leverage
params = sign({"symbol": symbol, "leverage": leverage, "timestamp": int(time.time() * 1000)})
requests.post(f"{BASE_URL}/fapi/v1/leverage", params=params, headers=headers)

# 5. Set margin type to ISOLATED
params = sign({"symbol": symbol, "marginType": "ISOLATED", "timestamp": int(time.time() * 1000)})
requests.post(f"{BASE_URL}/fapi/v1/marginType", params=params, headers=headers)
# Note: returns -4046 if already ISOLATED — this is fine, not an error

# 6. Calculate quantity with dynamic leverage
margin = wallet_balance * 0.02  # 2% of wallet
notional = margin * leverage
quantity = round(notional / current_price, qty_precision)
```

**Typical leverages by tier:**
| Volatility | ATR% | Examples | Leverage |
|---|---|---|---|
| 🟢 Low | <1% | BTC, ETH, BNB | 50x - MAX |
| 🟡 Medium | 1-2% | DOGE, NEAR, XRP, AIOT | 20-50x |
| 🔴 High | >2% | Meme coins, new listings, lowcap | 10-20x |

**Why dynamic is better than always-max:**
- Volatile tokens with max leverage → SL too tight → instant stop-out (TAGUSDT lesson)
- Stable tokens with low leverage → wasted profit potential
- Dynamic leverage ensures SL has proportional breathing room regardless of token volatility

**User preference (the user):** Initially chose "max leverage per pair" but after TAGUSDT got instantly SL'd, agreed to dynamic volatility-based leverage. The principle remains: maximize profit potential while keeping SL viable. Report leverage choice in output: "Leverage: {lev}x (ATR: {atr_pct}%, Volatilitas: {tier})"

## FibStruct Engine v2 — Updated June 2026

Engine path: `/home/ubuntu/fibstruct_engine.py`
State file: `/home/ubuntu/fibstruct_state.json`
Margin: 5% per trade (MARGIN_PCT = 0.05) — user preference June 2026
Min score: 4/5, Min R:R: 1:2
Max positions: 3, Max same direction: 3
Volume filter: $10M minimum 24h volume (user said $50M was too strict — blocked too many altcoins)

### Improvements from v1:
1. **News check** before entry (web scrape @marketfeed + CryptoCompare)
- **BTC direction filter** (4H/1H analysis required)
4. **Weekend filter** (Sat/Sun: monitor only, no new entries)
5. **Partial TP** (30% at TP1, 40% at TP2, 30% at TP3)
6. **Direction balance** (max 3 LONG or 3 SHORT at a time)
7. **Token news check** (skip if unlock/hack/legal risk)
8. **Improved logging** (Indonesian, emoji-rich)
Volume filter: $10M minimum (adjusted from $50M per user request)

### Non-Traditional Pairs (Stock Perpetuals)
Binance Futures lists non-crypto perpetuals like SKHYNIXUSDT (Samsung/Hynix stock-backed). These may have lower liquidity, wider spreads, and follow TradFi trading hours. When scan engine picks these up, verify volume ≥$50M before entering. Prefer well-known crypto pairs (BTC, ETH, SOL, XRP) when unsure.

### Deployment:
```bash
# Kill any existing instances first
pkill -f fibstruct_engine 2>/dev/null; sleep 1

# Clear log to avoid apparent duplication from old content
> /home/ubuntu/fibstruct.log

# Start daemon in screen (MUST source .env for API keys)
screen -dmS fibstruct bash -c 'cd /home/ubuntu && export PYTHONUNBUFFERED=1 && source .hermes/.env && python3 -u fibstruct_engine.py >> fibstruct.log 2>&1'

# Verify single process (expect 3 lines: SCREEN + bash + python3)
ps aux | grep fibstruct_engine | grep -v grep

# Check logs
tail -f /home/ubuntu/fibstruct.log

# Stop daemon
screen -S fibstruct -X quit
pkill -f fibstruct_engine
```

**PITFALL: Log duplication on restart** — If you restart without clearing the log file, old content persists and output APPEARS doubled (every line shows twice). Always `> /home/ubuntu/fibstruct.log` before restart. The `uniq` command also helps diagnose: `tail -30 fibstruct.log | uniq`.

**PITFALL: Multiple instances** — `pkill -f fibstruct_engine` before restart. Multiple instances cause duplicate log entries AND duplicate order attempts. Verify with `ps aux | grep fibstruct_engine | grep -v grep` — should show exactly 3 lines (SCREEN + bash + python3).

**PITFALL: Engine uses env vars** — The engine reads `os.environ.get('BINANCE_API_KEY')`. When API keys change, update `~/.hermes/.env` only — no need to edit the engine file. Test with: `source ~/.hermes/.env && python3 -c "import os; print(os.environ.get('BINANCE_API_KEY', 'NOT SET'))"`.

### Watchdog cronjob (every 5 min):
Use `no_agent: true` + bash script for lightweight watchdog. Silent when daemon alive, reports only on restart.

```bash
#!/bin/bash
if ! screen -ls | grep -q fibstruct; then
    echo "$(date '+%H:%M:%S') ⚠️ FibStruct daemon DEAD — restarting..."
    > /home/ubuntu/fibstruct.log  # Clear log on restart
    screen -dmS fibstruct bash -c 'cd /home/ubuntu && export PYTHONUNBUFFERED=1 && source .hermes/.env && python3 -u fibstruct_engine.py >> fibstruct.log 2>&1'
    sleep 3
    if ps aux | grep -q fibstruct_engine; then
        echo "✅ Daemon restarted"
    else
        echo "❌ Restart failed"
    fi
else
    exit 0  # Silent when alive
fi
```

Create with: `cronjob action=create no_agent=true script="watchdog.sh" schedule="*/5 * * * *"`

**PITFALL: Cronjob `script` parameter MUST be a filename, NOT inline code.**
The `script` parameter is resolved as a path relative to `~/.hermes/scripts/`. Passing inline bash code as the script value causes the scheduler to interpret it as a filename (e.g., `#!/bin/bash` becomes `/home/ubuntu/.hermes/scripts/#!/bin/bash`), which fails with "Script not found". Always save the script to a `.sh` file in `~/.hermes/scripts/` first, then reference just the filename.

```bash
# ✅ CORRECT: Save script file first
write_file("~/.hermes/scripts/watchdog.sh", bash_content)
cronjob(action='create', script='watchdog.sh', no_agent=True, schedule='*/5 * * * *')

# ❌ WRONG: Inline script content
cronjob(action='create', script='#!/bin/bash\nif ! screen...', no_agent=True)
```

This applies to ALL `no_agent: true` cronjobs — the script is always a file reference, never inline content.

## Pitfalls

### CRITICAL: XAUUSDT (Commodity Pairs) — No Conditional Orders via API
- XAUUSDT and potentially other commodity pairs on Binance Futures return error `-4120: "Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."` for ALL conditional order types (STOP_MARKET, TAKE_PROFIT_MARKET, STOP, TAKE_PROFIT, TRAILING_STOP_MARKET)
- This affects both `/fapi/v1/order` and `/fapi/v1/batchOrders` endpoints
- The Algo Order endpoint (`/sapi/v1/algo/futures/`) does NOT support SL/TP either — it's for TWAP/VP execution only
- **Workaround:** User must set TP/SL manually from the Binance app/web interface
- **Alternative:** Set up a polling monitor that checks mark price and executes a MARKET SELL when price hits SL level (MARKET orders DO work for XAUUSDT)
- LIMIT and MARKET orders work fine for XAUUSDT — only conditional/stop orders are blocked
- Discovered May 2026 on PROD (not a testnet limitation)

### CRITICAL: XAUUSDT Price Differs from Spot Gold
- Binance Futures XAUUSDT trades at ~$4,700+ (May 2026), NOT the same as spot gold (~$3,385 from Kitco/Investing.com)
- Always check the actual Binance Futures price via API or `document.title` on the futures page, not external gold price sources
- The price difference is due to Binance's contract specification (likely 1 XAU = different unit or premium)
- When user mentions XAU price, verify against Binance Futures directly: `GET /fapi/v1/ticker/price?symbol=XAUUSDT`

### CRITICAL: binance-cli Profiles Are Volatile
- `binance-cli profile` configs stored in `~/.config/binance-cli/config.toml` can disappear between sessions
- **Preferred approach**: Use environment variables (`BINANCE_API_KEY`, `BINANCE_SECRET_KEY`, `BINANCE_API_ENV`) + direct Python HMAC-signed API calls
- Python approach is more reliable and doesn't depend on profile state
- Always check `env | grep -i binance` first to find existing credentials

### CRITICAL: Testnet Resets / API Key Expiration
- Binance Testnet periodically resets balances and positions to $0
- API keys can expire or become invalid without warning (error `-2015`)
- If balance shows $0 and no positions exist, the testnet likely reset — user needs to:
  1. Re-deposit testnet funds via Binance Testnet faucet
  2. Possibly generate new API keys from testnet.binancefuture.com
- If one endpoint works (e.g., `/fapi/v2/account`) but another fails with `-2015` (e.g., `/fapi/v1/openOrders`), the key may have partial permissions or be in a degraded state — regenerate

### CRITICAL: Multiple API Key Sources — Verify Which Is Active
- Keys may exist in BOTH `env` vars AND `~/.hermes/.env` — they can be DIFFERENT keys
- **PROD vs TESTNET keys are DIFFERENT!** env vars may have testnet keys while user provides prod keys separately
- Always verify which key actually works before trading:
```python
# Test both keys against account endpoint
params = {'timestamp': int(time.time() * 1000)}
# sign and GET /fapi/v2/account — the one that returns balance is correct
```
- Error `-2015: Invalid API-key, IP, or permissions` means wrong key, not permission issue
- Priority: check `env | grep BINANCE` first, then `cat ~/.hermes/.env | grep BINANCE`
- **If user provides new keys in chat:** Use them directly in the script (hardcoded), don't assume env vars are updated. The env vars stored on VPS are for TESTNET; user's real account keys are provided ad-hoc.

### CRITICAL: PROD API Keys (Real Account)
- User's PROD keys are provided per-session (not stored in env vars permanently)
- Base URL for PROD: `https://fapi.binance.com`
- Base URL for TESTNET: `https://testnet.binancefuture.com`
- When user says "cek akun real" or "binance futures real" → use PROD base URL with user-provided keys
- The env vars (`BINANCE_API_KEY` in `.env`) are TESTNET keys — they return -2015 on prod endpoints

### CRITICAL: Commodity Pairs (XAUUSDT) Do NOT Support Conditional Orders on PROD
- XAUUSDT and similar commodity perpetuals return `-4120` for STOP_MARKET, TAKE_PROFIT_MARKET, etc. even on PROD
- User must set TP/SL via Binance app/web UI manually
- API can only do MARKET and LIMIT orders for these pairs
- Workaround: polling script that market-closes when price breaches SL
- See `references/testnet-limitations.md` for full details

### CRITICAL: XAUUSDT Price ≠ Spot Gold (XAU/USD)
- Binance Futures XAUUSDT perpetual trades at ~$4,700+ (May 2026)
- Spot gold from Kitco/Investing.com shows ~$3,385
- These are COMPLETELY DIFFERENT prices — always check Binance Futures directly
- When user says "XAU price is X", trust them over external spot gold sources
- Use `document.title` from `https://www.binance.com/en/futures/XAUUSDT` or API `/fapi/v1/ticker/price?symbol=XAUUSDT` for accurate price

### CRITICAL: Testnet Does NOT Support Conditional Orders
- Error: `"Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."`
- This affects: STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET
- These order types ARE listed in exchangeInfo but CANNOT be placed on testnet
- The Algo Order endpoint (`new-algo-order`) also fails with "Invalid algoType" on testnet
- **Workaround**: Use cron job to monitor and manually close positions when price hits SL/TP levels
- **On PROD**: All conditional orders work normally via `/fapi/v1/order` — **EXCEPT for commodity pairs (XAUUSDT)**

### CRITICAL: XAUUSDT (Gold) Does NOT Support Conditional Orders via API (PROD)
- Error: `{"code":-4120,"msg":"Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."}`
- Affects ALL conditional order types: STOP_MARKET, TAKE_PROFIT_MARKET, STOP, TAKE_PROFIT
- Also fails via batch orders (`/fapi/v1/batchOrders`)
- The "Algo Order API" endpoint (`/sapi/v1/algo/futures/newOrderVp`) is for TWAP/VP execution, NOT for SL/TP
- **This is a PROD limitation specific to commodity pairs like XAUUSDT**
- **Workaround**: User must set SL/TP manually from the Binance app/web UI, OR use a polling monitor script that executes MARKET SELL when price hits SL level
- MARKET and LIMIT orders DO work normally for XAUUSDT via API

### Node.js Version
- `binance-cli` requires Node 22+ (uses `styleText` from `node:util`)
- Always run `source ~/.nvm/nvm.sh && nvm use 22` before any binance-cli command

### Algo Order Parameter
- `new-algo-order` requires `--algo-type` parameter (e.g., VP, TWAP for algo orders)
- For conditional orders on prod, use `new-order` with type STOP_MARKET/TAKE_PROFIT_MARKET instead

### Margin Type Already Set
- `change-margin-type` returns "No need to change margin type" if already correct — this is not an error

### Quantity Precision
- Each symbol has different quantity precision requirements
- Check via `exchangeInfo` endpoint for `quantityPrecision` field

## Cancel Open Orders

```python
# Cancel specific order
params = sign({'symbol': 'DOGEUSDT', 'orderId': order_id, 'timestamp': int(time.time() * 1000)})
resp = requests.delete(f"{BASE_URL}/fapi/v1/order", params=params, headers=headers)

# Cancel ALL open orders for a symbol
params = sign({'symbol': 'DOGEUSDT', 'timestamp': int(time.time() * 1000)})
resp = requests.delete(f"{BASE_URL}/fapi/v1/allOpenOrders", params=params, headers=headers)

# List open orders first
params = sign({'symbol': 'DOGEUSDT', 'timestamp': int(time.time() * 1000)})
resp = requests.get(f"{BASE_URL}/fapi/v1/openOrders", params=params, headers=headers)
```

**Note:** If limit order already filled, it won't appear in openOrders — check position instead via `/fapi/v2/account`.

## XAUUSDT (Gold) Perpetual — Special Notes

**CRITICAL:** Binance Futures XAUUSDT trades at a DIFFERENT price than spot gold (XAU/USD from Kitco/Investing.com). As of May 2026:
- Binance XAUUSDT Perp: ~$4,726
- Spot gold (Kitco/Investing.com): ~$3,385

**DO NOT** use spot gold prices from Kitco, Investing.com, TradingView spot, or Forex Factory for Binance XAUUSDT analysis. Always check the actual Binance Futures price via:
- `https://www.binance.com/en/futures/XAUUSDT`
- API: `GET /fapi/v1/ticker/price?symbol=XAUUSDT`
- Or browser console: `document.title` on the Binance Futures page

**NFP (Nonfarm Payrolls) Trading on XAUUSDT:**
- NFP releases at 19:30 WIB (12:30 UTC) — first Friday of month
- Typical XAUUSDT move during NFP: 1-3% ($47-$142 at $4,726)
- Whipsaw pattern: often spikes OPPOSITE direction first (liquidity grab), then moves in "real" direction
- Spread widens significantly at release moment
- Safe play: Limit order at key support (EMA99/demand zone) to catch the whipsaw dip, entry 1-2 min after release
- Aggressive play: Market order at release (risk whipsaw + wide spread)
- With $28 margin at 20x: each 1% move = ~$5.60 P&L

**Leverage for XAUUSDT (news events):**
- 20x is reasonable for NFP with small account ($28)
- 50x+ is dangerous — NFP can swing 2-3% instantly = liquidation
- ALWAYS use ISOLATED margin (not Cross) for news trading — limits loss to margin only

## Intraday TP/SL Calculation (ATR-Based)

For futures intraday positions, calculate SL/TP from 1H and 15M data — NOT daily:

```python
# Fetch 1H and 15M klines
atr_1h = calc_atr(highs_1h, lows_1h, closes_1h, period=14)
atr_15m = calc_atr(highs_15m, lows_15m, closes_15m, period=14)
recent_high_1h = max(highs_1h[-10:])  # 10-candle swing high
recent_low_1h = min(lows_1h[-10:])    # 10-candle swing low
recent_low_15m = min(lows_15m[-15:])  # 15-candle swing low

# LONG position:
sl = recent_low_15m - atr_15m * 0.3   # Below swing low + buffer
tp1 = min(recent_high_1h, price + atr_1h * 1.0)  # 1x ATR or swing high
tp2 = price + atr_1h * 1.8            # 1.8x ATR
tp3 = price + atr_1h * 2.5            # 2.5x ATR

# SHORT position:
sl = recent_high_15m + atr_15m * 0.3  # Above swing high + buffer
tp1 = max(recent_low_1h, price - atr_1h * 1.0)
tp2 = price - atr_1h * 1.8
tp3 = price - atr_1h * 2.5
```

**Key principle:** SL should be 0.5-3% from entry (tight for intraday). If calculated SL is wider than 3%, reduce leverage or skip the trade.

## Partial TP Strategy

Split position into 3 tranches:
- TP1 (30% of qty): Conservative target (1x ATR / swing level)
- TP2 (40% of qty): Medium target (1.8x ATR)
- TP3 (20% of qty): Aggressive target (2.5x ATR)
- Remaining 10%: Trailing stop (2% distance)
- After TP1 hit: Move SL to breakeven (entry price)

**RSI(3) Engine Config (as of May 2026):**
- MAX_POSITIONS = 10 (user increased from 5)
- MAX_SAME_DIRECTION = 6 (user increased from 3)
- Engine path: `/home/ubuntu/rsi3_engine.py`
- State file: `/home/ubuntu/rsi3_state.json`

**When to update TP/SL:** If positions were opened with daily TF analysis but are futures (intraday), recalculate TP/SL using 1H+15M ATR method above. Daily TP targets are too far for leveraged intraday positions.

## Weekday/Weekend Trading Filter

Since BTC ETF approval, crypto markets follow TradFi patterns. Weekend volume is 50-70% lower, spreads wider, signals less reliable.

**Implementation in cronjob:**
```python
import datetime
day = datetime.datetime.now().weekday()  # 0=Mon, 6=Sun
is_weekend = day >= 5  # Saturday=5, Sunday=6

if is_weekend:
    # MONITOR ONLY — no new entries
    # Exception: DANGER news + SHORT score >= 75, or liquidity sweep + score >= 80
    allow_new_entry = False
    if risk_rating == 'danger' and direction == 'SHORT' and score >= 75:
        allow_new_entry = True
    if has_liquidity_sweep and score >= 80:
        allow_new_entry = True
else:
    allow_new_entry = True
```

**Preferred entry days:** Monday (institutional open), Wednesday (rebalancing), Friday (options expiry).

## Cron Monitoring Template

For testnet (no auto SL/TP), set up cron job (every **15 minutes** — 30m is too slow for leveraged positions) that:
1. **Analyzes BTC** via AITS (`analyze_aits("BTCUSDT")`) for market direction
2. **Checks news** from @marketfeed, CryptoCompare, CMC Fear & Greed
3. Checks ALL active positions via `/fapi/v2/account` (positionAmt != 0)
4. Checks ALL open/pending limit orders via `/fapi/v1/openOrders`
5. **Re-analyzes each position** using AITS scoring — auto-close if score < 40 or CHoCH reversal
6. Fetches current prices, compares against SL/TP levels
7. Executes market close if SL breached
8. Executes partial close (30%) if TP1 hit, moves SL to breakeven
9. **Scans for new entries** if positions < 5 using `scan_and_execute()`
10. Reports everything in compact format

**AITS Integration in Cronjob:**
The AITS engine script lives at `/home/ubuntu/aits_engine.py`. The cronjob imports it:
```python
import sys
sys.path.insert(0, '/home/ubuntu')
from aits_engine import analyze_aits, score_setup, generate_entry, scan_and_execute
```

**All actions are AUTO-EXECUTED — no asking for confirmation:**
- SL hit → close immediately
- TP1 hit → partial close 30%, SL to breakeven
- TP2 hit → partial close 40%
- TP3 hit → close remaining 30%
- Position invalid (score < 40) → close immediately
- Market DANGER → cut loss LONG positions in minus
- Setup found (score ≥ 60) → execute entry immediately

**Cron prompt should include:**
- All SL/TP levels for each position (use intraday ATR-based levels, not daily)
- Partial TP rules (30% at TP1, 40% at TP2, 30% at TP3)
- Trailing SL rule (after TP1 → SL moves to entry)
- Max drawdown rule (8% total → stop trading)
- Alert threshold (warn if position within 0.3% of SL)
- Open order tracking (report if limit orders filled since last check)

## News-Based Risk Management in Cronjob

Integrate global news monitoring INTO the portfolio cron to auto-protect against sudden market wicks from geopolitical/macro events.

**Architecture:** Single cronjob that does BOTH news analysis + position monitoring. Requires `terminal` + `web` toolsets enabled.

**News sources to check (free, no auth):**
- **Telegram @marketfeed (HIGHEST PRIORITY — fastest real-time):** Scrape via `https://t.me/s/marketfeed` — read latest 20 posts. Covers Trump statements, geopolitics, Fed decisions, macro data, market closes, breaking events. 34K subscribers, updates within seconds of events. This is the closest thing to a Bloomberg terminal for free. Parse the HTML for StaticText content of recent posts.
- CryptoCompare News API: `https://min-api.cryptocompare.com/data/v2/news/?lang=EN&sortOrder=latest`
- **Fear & Greed Index (IMPORTANT — use correct source):**
  - ✅ **CoinMarketCap (PREFERRED):** Scrape `https://coinmarketcap.com/charts/fear-and-greed-index/` — extract score via regex: `re.findall(r'"score"\s*:\s*(\d+)', r.text)[0]`. Returns accurate real-time value (e.g., 44 Neutral).
  - ✅ **cfgi.io (BACKUP):** Scrape `https://cfgi.io/bitcoin-fear-greed-index/` — look for "Now" value in Historical Values section.
  - ❌ **api.alternative.me — DO NOT USE!** Returns stale/delayed data (showed 26 when real value was 44). User confirmed this is inaccurate.
  - Classification from score: ≤20 Extreme Fear, ≤40 Fear, ≤60 Neutral, ≤80 Greed, >80 Extreme Greed
- Google News RSS: `https://news.google.com/rss/search?q=crypto+market&hl=en`
- CryptoPanic (free tier): `https://cryptopanic.com/api/free/v1/posts/?auth_token=free&filter=hot`

**Risk Rating System:**
- 🟢 SAFE — No dangerous news, positions run normally
- 🟡 CAUTION — Notable news (e.g., regulatory rumors, minor geopolitical tension) — tighten mental SL
- 🔴 DANGER — High-impact event confirmed (war escalation, major hack, bank collapse, surprise Fed action, stablecoin depeg) — **AUTO CUT LOSS all LONG positions currently in minus; SHORT positions in profit → HOLD (they benefit from downturn)**

**CRITICAL PRINCIPLE: TECHNICAL = DIRECTION, MARKET = FILTER**

The market risk rating does NOT determine trade direction. It only FILTERS which technically-valid setups get executed:

- 🟢 SAFE → Execute ALL valid setups (LONG and SHORT per technical analysis)
- 🟡 CAUTION → Execute all valid setups; if multiple candidates are equally strong, PRIORITIZE SHORT setups. LONG still allowed if score is 4/4.
- 🔴 DANGER → Execute ONLY setups where technical analysis shows SHORT. SKIP all LONG setups regardless of score. But NEVER short just because market is dangerous without technical confirmation!

**WRONG:** "Market is DANGER → open SHORT positions everywhere"
**RIGHT:** "Market is DANGER → only execute entries where 4H/1H/15M/5M technically align SHORT"

The user explicitly corrected this: don't blindly short in danger or blindly long in safe. Always let the multi-TF technical analysis determine direction first, then use market condition as a go/no-go filter.

**DANGER triggers (auto cut-loss):**
- Active military conflict escalation (Iran/Israel, Russia/Ukraine, China/Taiwan)
- Major exchange hack (>$100M)
- Systemic bank/institution collapse
- Surprise Fed emergency action
- Stablecoin depeg (USDT, USDC)
- Government crypto ban in major market
- Whale dump >$500M in 1 hour

**Auto cut-loss logic on DANGER:**
```python
# Only cut positions that are currently LOSING money
for pos in positions:
    if float(pos['unrealizedProfit']) < 0:
        # Market close the losing position
        side = 'SELL' if float(pos['positionAmt']) > 0 else 'BUY'
        close_order = api_request('POST', '/fapi/v1/order', {
            'symbol': pos['symbol'], 'side': side,
            'type': 'MARKET', 'quantity': abs(float(pos['positionAmt']))
        })
# Positions in profit: let them run but report tightened SL recommendation
```

**Cronjob output format (4 sections):**
1. 📰 BERITA & SENTIMEN MARKET — Risk rating + headlines + Fear & Greed
2. 📊 PORTFOLIO STATUS — Balance, positions table with PnL
3. ⚡ AKSI YANG DIAMBIL — Auto cut-loss actions or "Tidak ada aksi"
4. 💡 REKOMENDASI — Suggestions based on news + position state

**Cronjob toolsets required:** `["terminal", "web"]` — web needed for news fetching

**Important:** When user says "cancel limit order" but it's already filled, check position first via `/fapi/v2/account`. If positionAmt != 0 for that symbol, the order already executed — inform user it's now an active position.

**TP/SL update cadence:** Recalculate intraday TP/SL levels when:
- Market structure changes (new swing high/low formed on 1H)
- Position was opened with wrong TF analysis (e.g., daily TF for futures)
- ATR significantly changes (volatility expansion/contraction)

## Entry Methodology Audit

**CRITICAL:** Futures positions MUST be entered using intraday multi-TF analysis (4H → 1H → 15M → 5M). Positions opened with Daily (1D) TF analysis are considered "legacy" and should be:

1. **Identified** — Track which positions were opened with which methodology
2. **Flagged** — When user asks about methodology mismatch, check all active positions
3. **Cut loss candidates** — If a 1D-entry position is in loss, recommend cut loss since the entry precision was poor
4. **Exception** — If a 1D-entry position is in profit, it can be kept but with tightened intraday SL/TP

**Audit checklist when user asks "masih pakai TF 1D?":**
- List ALL active positions
- For each, identify entry batch/date and methodology used
- Positions from early batches (before intraday methodology was agreed) are likely 1D entries
- Recommend cut loss for losing 1D-entry positions, keep profitable ones with tight SL

## NFP / High-Impact News Trading (Manual Positions)

When user wants to trade NFP or other high-impact macro news on Binance Futures:

**Pre-Entry Analysis:**
1. Identify the news event, forecast vs previous, and expected USD impact
2. Check the ACTUAL price on Binance Futures (not spot gold from external sources)
3. Calculate EMA levels, swing lows, Fibonacci retracement for limit entry zones
4. Recommend limit buy at confluence zone (EMA99 + Fib 0.382 + swing low cluster)

**Entry Timing Strategy:**
- **Safe play:** Wait 1-2 minutes after news release for direction confirmation. NFP often whipsaws (spikes one direction then reverses). The main move lasts 15-30 minutes — plenty of time.
- **Aggressive:** Enter at news release but accept whipsaw risk
- **Limit order (BEST):** Place limit at key support BEFORE news — catches the whipsaw dip

**Leverage Guidance for News Trading (small accounts <$50):**
- 10-20x = reasonable for news events (survives 2-5% whipsaw)
- 50x = dangerous for NFP (liquidation within 1.5-2% move)
- 100x = suicide for news events

**CRITICAL REMINDERS for user:**
1. Use **ISOLATED** margin (not Cross) — protects remaining balance
2. Set SL BEFORE news hits — manual SL won't work fast enough during spike
3. NFP whipsaw can be $50-80 on gold in seconds

**Liquidation Distance Quick Calc:**
```
liq_distance_pct ≈ 100% / leverage × (1 - maintenance_margin_rate)
# Rough: 50x ≈ 1.5-2% to liquidation
# Rough: 20x ≈ 4-5% to liquidation
# Rough: 10x ≈ 9-10% to liquidation
```

## NFP / High-Impact News Trading (Manual Position)

When user wants to trade NFP or other high-impact news events manually (not via cron):

**Pre-Entry Analysis:**
1. Identify the news event, consensus forecast, and previous reading
2. Determine directional bias (e.g., NFP forecast much lower than previous = BAD USD = LONG gold)
3. Calculate limit entry using confluence: EMA99(15m) + EMA25(1h) + Fib 0.382 + swing lows = best entry zone
4. Recommend waiting 1-2 minutes AFTER news release for whipsaw to settle (explain why: spread widens, initial spike often reverses)

**Position Sizing for Small Accounts ($20-50):**
- Max recommended leverage: 20x (not 50x+)
- With 50x on NFP: liquidation distance ~1.5% — NFP can easily whipsaw 1-2% before moving in "correct" direction
- Always recommend ISOLATED margin (not Cross) — limits loss to position margin only
- SL should be set BEFORE news, not after

**TP/SL Calculation for News Trades:**
- SL: Below liquidation price or key structure (swing low)
- TP: Based on R:R from SL distance
  - Conservative: 1:1 R:R (realistic for NFP)
  - Moderate: 1:1.5 R:R
  - Aggressive: 1:2 R:R (may not fill same session)
- NFP typical XAU move: 1-2% ($47-94 on $4,700 price)

**XAUUSDT-Specific Notes:**
- Cannot set SL/TP via API (see pitfall above) — user must set manually in app
- Verify price from Binance Futures directly (differs from spot gold)
- Funding rate is typically 0% or very low on XAUUSDT

## API Key Rotation Workflow

When Binance API keys expire or become invalid (error `-2015`):

1. **Detect** — Balance shows $0 or endpoints return permission errors
2. **User provides new keys** — API key + Secret key pair
3. **Update env file:**
   ```bash
   sed -i 's/BINANCE_API_KEY=.*/BINANCE_API_KEY=<new_key>/' /home/ubuntu/.hermes/.env
   sed -i 's/BINANCE_SECRET_KEY=.*/BINANCE_SECRET_KEY=<new_secret>/' /home/ubuntu/.hermes/.env
   ```
4. **Test new keys** — Run quick account balance check
5. **Update cronjob prompt** — The cronjob has API keys hardcoded in its prompt, must update via `cronjob action=update`
6. **Verify** — Run cronjob once to confirm it works with new keys

**Important:** Both `.env` file AND cronjob prompt need updating — they store keys independently.

## Auto-Entry Cronjob Pattern (Positions < Target)

When the user wants the cronjob to automatically find and execute new entries when open positions fall below a target (e.g., 5):

**Cronjob flow:**
```
📰 News Check → 📊 Monitor Positions → 🔍 Scan Entry (if < target) → 📰 Token News Check → 🚀 Execute
```

**Key rules:**
1. Count active positions (positionAmt != 0) at start of each cron run
2. If count < target AND risk rating is NOT 🔴 DANGER → scan for new entries
3. **DIRECTION BALANCE CHECK (HARD RULE):** Count how many positions are LONG vs SHORT. Max 3 positions in same direction out of 5 total. If already 3 SHORT → next entry MUST be LONG (or skip if no valid LONG setup). Lesson: 5/5 SHORT + BTC pump = all positions lose simultaneously (-$49 total).
3. Use multi-TF intraday scoring (see crypto-altcoin-scanner skill)
4. **CHECK TOKEN-SPECIFIC NEWS BEFORE ENTRY** (see section below)
5. **SET DYNAMIC LEVERAGE** — Query `/fapi/v1/leverageBracket` for max, then calculate appropriate leverage based on ATR% volatility (see Leverage Strategy section). Do NOT blindly use max — volatile tokens need lower leverage for SL to breathe.
6. **EXECUTE immediately** — don't just recommend, actually place the order
7. Report what was opened with full details (symbol, side, leverage, SL/TP, reason)
8. If no valid setup found (score < 3/4), report "Tidak ada setup valid" — never force entry

## Token-Specific News Check (MANDATORY Before Entry)

**RULE: Teknikal bagus + fundamental jelek = NO ENTRY.**

Before executing ANY new entry, even if technical score is 4/4, MUST check token-specific news:

**Sources to check:**
- CryptoCompare token news: `https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories={token_name}`
- Web search: "{token_name} crypto news today"
- Token unlock schedules (tokenunlocks.app or news mentions)

**Volume Filter (MANDATORY — added May 2026, adjusted June 2026):**
- Minimum 24h volume: $10M USDT. Skip anything below.
- Preferred: > $200M (blue chips like ETH, SOL, XRP, BNB, DOGE, BCH)
- User explicitly said $50M was "terlalu ketat" — blocked too many altcoins from entry. $10M is the sweet spot.
- Low volume tokens (< $10M) are easily manipulated, have wide spreads, and produce unreliable technical signals
- Check via: `GET /fapi/v1/ticker/24hr` → `quoteVolume` field
- This filter alone eliminates many losing trades from thin/manipulated pairs

**Red flags that INVALIDATE technical setup:**
- 🔓 **Token Unlock** — Large unlock (>5% supply) within 7 days → SKIP (sell pressure incoming)
- 🔴 **Hack/Exploit** — Project hacked, funds stolen, security breach → SKIP
- ⚖️ **Regulasi/Legal** — SEC lawsuit, investigation, regulatory action → SKIP
- 📉 **Delisting** — Exchange removing the token → SKIP
- 🐋 **Whale Dump** — Large holder dumping (on-chain data) → SKIP
- 💀 **Project Dead** — Team abandoned, no development activity → SKIP
- 🤝 **Buy-the-rumor-sell-the-news** — Major partnership/upgrade ALREADY announced and priced in → CAUTION (reduce size)

**Token News Rating:**
- ✅ CLEAR — No negative news, safe to entry at full size
- ⚠️ RISKY — Minor concerns, entry with reduced size (50% of normal)
- ❌ SKIP — Dangerous news detected, DO NOT ENTRY regardless of technical score

**Implementation in cronjob prompt:**
```
### STEP A: CEK NEWS PER TOKEN (WAJIB SEBELUM ENTRY!)
For each candidate that passes technical analysis:
1. Fetch token-specific news
2. Check for unlock/hack/legal/delist/whale dump
3. Rate: CLEAR / RISKY / SKIP
4. If SKIP → move to next candidate
5. If CLEAR → proceed to execution
6. If RISKY → proceed but halve position size
```

**User preference:** Entry execution should happen IMMEDIATELY when a setup is found, NOT wait for the next cronjob cycle. If user asks to scan/enter, do it in the current session directly. The cronjob is a safety net, not the primary entry mechanism.

**Cronjob prompt structure for auto-entry:**
```
=== BAGIAN 1: CEK BERITA ===
(news sources + risk rating)

=== BAGIAN 2: MONITOR POSISI ===
(account info + positions + SL/TP check + auto close)

=== BAGIAN 3: AUTO SCAN ENTRY BARU (JIKA POSISI < 5) ===
- STEP A: Scan top 30 volume pairs
- STEP B: Multi-TF analysis: 4H → 1H → 15M → 5M (score >= 3/4)
- STEP C: Token-specific news check (unlock/hack/legal = SKIP)
- STEP D: Set DYNAMIC LEVERAGE per pair (ATR-based, NOT always max — see Leverage Strategy)
- STEP E: Execute with 2% margin, ISOLATED
- If DANGER → skip all new entries

=== BAGIAN 4: FORMAT OUTPUT ===
(Indonesian language, emoji-rich, 4 sections)
```

**Recommended cron frequency:** Every **15 minutes** for tight intraday monitoring. 30m is too slow for leveraged positions with tight SL. With high leverage (50-100x on large caps), SL distances are tiny — 15m ensures positions get closed before liquidation.

**PREFERRED: Daemon mode (30-second polling)** — For real-money accounts, use a persistent daemon process (via `screen`) instead of a cronjob. The daemon checks SL/TP every 30 seconds and scans for new signals every 5 minutes. A lightweight cronjob (every 5 min) acts as a watchdog to restart the daemon if it dies. This gives near-real-time SL/TP enforcement without the overhead of spawning a new process every minute.

```bash
# Start daemon
screen -dmS rsi3real bash -c 'python3 -u /path/to/daemon.py >> /path/to/log 2>&1'

# Watchdog cronjob checks if daemon is alive, restarts if dead
# Report to user ONLY on actions (entry/close/SL/TP hit) — silent otherwise
```

**User preference (the user):** Does NOT want spam reports every minute. Only notify on actual actions (new entry, SL hit, TP hit, position closed). Use "silent" suppression in cronjob when no actions occurred.

**Cronjob toolsets required:** `["terminal", "web"]` — web needed for scraping @marketfeed and other news sources.

**Dynamic SL/TP tracking:** When new positions are opened by the cronjob, their SL/TP levels must be added to the cronjob prompt (via `cronjob action=update`) so subsequent runs can monitor them. This requires updating the cronjob after each new entry.

## Real Account vs Testnet Differences

When switching from testnet to real account:

| Aspect | Testnet | Real |
|--------|---------|------|
| Balance | $5,000 (virtual) | User's actual funds |
| Risk per trade | 2% (can be aggressive) | 5% margin per trade (user preference, June 2026) |
| Max positions | 10 | 3 (FibStruct v2), max same direction: 3 |
| SL/TP API | Never works | Works for most pairs (NOT commodity pairs like XAUUSDT) |
| Monitoring | Cronjob every 1-15 min | Daemon with 30s polling |
| Reporting | Every run | Only on actions |

**Real account setup checklist:**
1. New API key with Futures permission enabled
2. IP whitelist includes VPS IP (43.159.56.39)
3. Margin type: ISOLATED (always — never CROSS on real money)
4. State file separate from testnet: `rsi3_real_state.json`
5. Daemon via screen (not cronjob) for 30s SL/TP polling
6. Watchdog cronjob every 5 min to restart daemon if dead
7. Try API SL/TP first → fallback to manual polling if -4120 error

**MANDATORY RULE: Every position MUST have SL/TP.** The cronjob must NEVER leave a position without SL/TP levels. If a new position is opened (by cronjob or manually), the SL/TP must be:
1. Calculated immediately from ATR 15M (SL=1.2x ATR, TP1=1:1.5 RR, TP2=1:2.5 RR, TP3=1:3.5 RR)
2. Reported in the output
3. Added to the cronjob prompt via update

**Lesson learned (FXS/TAG incident):** Cronjob opened positions but didn't add them to the SL/TP tracking list. User noticed positions running without protection. Fix: cronjob prompt must include instruction "Posisi baru tanpa SL/TP → HITUNG dari ATR 15M dan CATAT. Jangan biarkan posisi tanpa SL/TP!"

**Lesson learned (FIL incident — May 2026):** Cronjob opened FIL SHORT position but SL was NEVER set or tracked. It became the largest single loss (-$18) while other positions with SL were contained. Root cause: the entry execution succeeded but SL calculation/tracking step was silently skipped. Fix: Every cron run must VERIFY all positions have SL tracked — if any position lacks SL, calculate immediately and add. This is a HARD CHECK, not optional.

**RSI(3) Engine: Completed Candle vs Current Candle:** The engine uses `closes[:-1]` (last completed candle) for RSI/EMA calculation, NOT the current forming candle. When doing manual scans to compare, use the same approach — otherwise RSI values will differ and cause confusion about why the engine "missed" a signal. A signal visible on the current candle will only trigger after that candle closes.

**SL Enforcement Gap on Testnet:** With 1-minute cron polling, volatile pairs can gap past SL between polls. Observed: ONDOUSDT -$299, PLAYUSDT -$188, LABUSDT -$137 — all exceeded reasonable SL because the cron didn't catch them in time. Consider: (1) adding a max-loss-per-position hard cap (e.g., -$50 or -$75, auto-cut regardless of SL level), (2) reducing cron interval for SL checks only, or (3) running a dedicated lightweight SL-watcher process with tighter polling.

**Proactive cut-loss near SL (testnet-specific):** When a position is within 0.3% of its SL level, cut it manually rather than waiting for the next 15-min cron poll. On testnet, there are no native STOP_MARKET orders — SL is enforced by polling. A 15-minute gap means the price can blow past SL and deepen the loss before the cron catches it. Example: BNB was 0.22% from SL → manual cut saved potential additional loss from 15-min delay.

## Background Process Buffering Pitfall

When running Python scripts via `background: true` terminal commands, stdout may NOT appear in `process log` or `process poll` even though the script is running correctly. This is caused by Python's default stdout buffering in non-TTY mode.

**Fix:** Always use `flush=True` on every `print()` AND set `PYTHONUNBUFFERED=1` environment variable:
```bash
PYTHONUNBUFFERED=1 python3 /tmp/script.py
```
Or add at script top:
```python
import sys
sys.stdout.reconfigure(line_buffering=True)
```

**Lesson (May 2026 NFP session):** A time-sensitive auto-entry script appeared to produce no output for 12+ minutes because of buffering. The script was actually running fine but all output was stuck in buffer. By the time it was investigated, the trading window had passed. Always use PYTHONUNBUFFERED=1 for time-critical background scripts.

## Cronjob Delivery Fallback

When the cronjob runs successfully (`last_status: ok`) but the user doesn't see results in chat:
1. Check `last_delivery_error` — if `null`, delivery succeeded but may be delayed
2. **Direct execution fallback**: Run the monitoring script directly in the terminal session so results appear immediately inline
3. The monitoring script template (Python + HMAC signing) can be executed ad-hoc without waiting for cron schedule
4. If user says "kirim cronjob" or "jalankan cronjob" — use `cronjob action=run` first, but if results don't appear, offer to execute the script directly

## BTC Analysis as Mandatory Pre-Entry Filter

**RULE: Always analyze BTC before entering ANY altcoin position.**

Altcoins generally follow BTC's direction. Entering a LONG altcoin position while BTC is bearish (or SHORT while BTC is bullish) significantly increases risk of stop-out.

**BTC Analysis (run every cron cycle):**
```python
# Analyze BTC multi-TF (same method as altcoin analysis)
btc_results = analyze_symbol("BTCUSDT")  # 4H, 1H, 15M, 5M
btc_bull = sum(1 for r in btc_results.values() if r['direction'] == 'BULL')
btc_overall = "BULLISH" if btc_bull >= 3 else "BEARISH" if btc_bull <= 1 else "NEUTRAL"
```

**Combined BTC + Market Condition Filter Matrix:**

| BTC Direction | Market Risk | LONG Allowed? | SHORT Allowed? |
|---|---|---|---|
| BULLISH | 🟢 SAFE | ✅ Yes | ✅ Yes (per technical) |
| BULLISH | 🟡 CAUTION | ✅ Yes | ⚠️ Only if 4/4 + token has own bearish catalyst |
| BULLISH | 🔴 DANGER | ❌ Skip | ✅ Only technically-valid SHORT |
| BEARISH | 🟢 SAFE | ⚠️ Only if 4/4 | ✅ Yes |
| BEARISH | 🟡 CAUTION | ❌ Skip | ✅ Yes |
| BEARISH | 🔴 DANGER | ❌ Skip | ✅ Only technically-valid SHORT |
| NEUTRAL | Any | Per technical | Per technical |

**BTC-Altcoin correlation nuances:**
- BTC naik pelan & stabil → Altcoin ikut naik, bahkan lebih kencang (altseason)
- BTC naik kencang → Altcoin tertinggal dulu, baru nyusul
- BTC turun → Altcoin turun LEBIH PARAH (2-3x lipat)
- BTC crash → Altcoin bloodbath
- BTC sideways → Altcoin bisa pump sendiri-sendiri (rotasi)
- BTC dominance naik → Uang pindah dari altcoin ke BTC → Altcoin turun
- BTC dominance turun → Altseason

**Impact on existing positions:** When BTC direction changes, re-evaluate all positions that are now against BTC. If a SHORT position was valid when BTC was bearish but BTC flipped bullish, tighten SL immediately.

## Active Position Re-Analysis (Every Cron Run)

**RULE: Every cron run must re-analyze ALL active positions for continued validity.**

Don't just check SL/TP levels — re-run the full multi-TF technical analysis on each position to detect when the setup has invalidated.

### Basic Method (EMA/RSI/MACD scoring):
```python
for pos in active_positions:
    results = analyze_symbol(pos['symbol'])  # Full 4H/1H/15M/5M
    bull_count = sum(1 for r in results.values() if r['direction'] == 'BULL')
    bear_count = sum(1 for r in results.values() if r['direction'] == 'BEAR')
    
    if pos['side'] == 'LONG':
        still_valid = bull_count >= 2
        strong = bull_count >= 3
    else:  # SHORT
        still_valid = bear_count >= 2
        strong = bear_count >= 3
    
    against_btc = (pos['side'] == 'LONG' and btc_overall == 'BEARISH') or \
                  (pos['side'] == 'SHORT' and btc_overall == 'BULLISH')
    
    # Auto-close rules:
    if not still_valid:  # <2/4 aligned
        close_position(pos)  # Technical fully reversed
    elif not strong and against_btc:  # 2/4 + against BTC
        close_position(pos)  # Weak + wrong side of BTC
```

### AITS Method (SMC + S/D + Fibonacci — PREFERRED):
When using the AITS engine (`/home/ubuntu/aits_engine.py`), re-analysis uses the scoring system:
```python
from aits_engine import analyze_aits, score_setup
tf_results = analyze_aits(symbol)
score, factors = score_setup(tf_results, direction)

# Auto-close rules:
if score < 40:  # Setup has significantly degraded
    close_position(pos)
# Also close if 4H CHoCH detected against position direction
if tf_results['4h']['last_break'] and 'CHOCH' in tf_results['4h']['last_break'][0]:
    if (direction == 'LONG' and 'BEAR' in tf_results['4h']['last_break'][0]) or \
       (direction == 'SHORT' and 'BULL' in tf_results['4h']['last_break'][0]):
        close_position(pos)  # Structure reversal confirmed
```

**Validity ratings in output:**
- ✅ VALID — Score ≥60 (AITS) or ≥3/4 (basic), aligned with BTC
- 🟡 VALID but against BTC — Score ≥60, but opposite BTC direction (tighten SL)
- ⚠️ MELEMAH — Score 40-59 (AITS) or 2/4 (basic) (monitor closely)
- ❌ TIDAK VALID — Score <40 (AITS) or <2/4 (basic) → AUTO CLOSE

**Lesson learned (TAG incident):** TAGUSDT was held as SHORT while 4H and 1H had already flipped BULLISH. By the time it was manually reviewed, the profit had turned to loss (-$37). If re-analysis had been running, it would have been closed while still in profit (+$11). The re-analysis catches reversals BEFORE they hit SL.

## Advanced Analysis: FibStruct (Current Preferred Method — May 2026)

**See `references/fibstruct-methodology.md` for full documentation.**

FibStruct is the current preferred method for the user's real account ($106 USDT). It combines:
- Market Structure (BOS/CHoCH) on 4H/1H for direction
- Trendline on 15M for trend filter
- Fibonacci OTE (0.618-0.786) on 15M for entry zone
- Liquidity Sweep + Price Action on 5M for trigger

**Key differences from AITS:** FibStruct is simpler (4 layers vs 6), faster to scan, and uses trendline instead of VWAP/Volume Profile. Better suited for automated scanning of 200 pairs. AITS remains valid for manual deep-analysis of specific setups.

**Scoring:** 5-point system (1 per layer), minimum 4/5 for entry, minimum R:R 1:2.
**Script:** `/home/ubuntu/fibstruct_engine.py` — daemon mode with 30s SL/TP polling + 5min signal scan.
**State:** `/home/ubuntu/fibstruct_state.json`

**User preference (May 2026):** User explicitly requested this combination: "fibonacci, struktur market, liquidity & price action + trendline." Replaced RSI(3) mean reversion which had ~50% win rate and too many small losses for a $106 account.

## Advanced Analysis: AITS (Legacy Method)

**See `references/aits-methodology.md` for full documentation.**

The basic EMA/RSI/MACD method has been superseded by AITS (Advanced Institutional Trading System) which uses:
- Market Structure (BOS/CHoCH) instead of EMA for trend
- Supply & Demand Zones (Order Blocks) instead of RSI for entry
- Fibonacci OTE (0.618-0.786) for precision confluence
- Volume Profile + VWAP for institutional confirmation
- Liquidity Sweep detection for smart money entries
- CoinGlass Liquidation Heatmap for macro confirmation

**Scoring:** 0-100 system, minimum 60 for entry, minimum R:R 1:2.
**Script:** `/home/ubuntu/aits_engine.py` — import with `from aits_engine import *`

**Weekend Filter:** No new entries Sat-Sun (low volume, unreliable signals). Exception: DANGER news + SHORT ≥75, or clear liquidity sweep + score ≥80. SL/TP management continues 24/7.

## References

- `references/futures-usds.md` — Full endpoint reference
- `references/auth.md` — API key setup and security rules
- `references/position-sizing.md` — Detailed calculation examples
- `references/fear-greed-sources.md` — Fear & Greed Index source comparison (CMC preferred, alternative.me is WRONG)
- `references/news-trading-xauusdt.md` — NFP/macro news trading playbook for XAUUSDT, price discrepancy notes (Binance Perp vs spot gold), leverage guide for small accounts, whipsaw patterns
- `references/cronjob-prompt-template.md` — Complete cronjob prompt structure with 6 phases (BTC analysis, news, monitor, re-analyze, scan entry, report)
- `references/fibstruct-methodology.md` — FibStruct trading system: 4-layer confluence (Market Structure + Trendline + Fibonacci OTE + Liquidity Sweep), scoring system, SL/TP placement, daemon architecture, comparison with RSI(3)
- `references/aits-methodology.md` — AITS (Advanced Institutional Trading System) full methodology: SMC, S/D zones, Fibonacci OTE, Volume, Liquidity Sweep, Liquidation Heatmap, Weekend Filter
- `references/pre-news-limit-entry.md` — Pre-news event (NFP/CPI/FOMC) limit entry workflow: confluence-based entry levels using Binance public API klines, EMA/Fib/swing low/demand zone stacking, split order strategy for whipsaw fills
- `references/strategy-evolution.md` — Strategy evolution timeline (AITS→EMA-VWAP→BB+RSI→RSI3), backtest results, current RSI(3) parameters, TP/SL rules, CloakBrowser usage (absorbed from crypto-futures-trading-system)
- `references/testnet-limitations.md` — Testnet-specific limitations and workarounds
- `references/real-account-deployment.md` — Real account deployment notes, config, pitfalls (NFP auto-entry, buffering, margin issues)
- `references/xauusdt-commodity-pairs.md` — XAUUSDT/commodity pair quirks: price differs from spot gold, conditional orders blocked via API, workarounds, NFP trading notes
- `references/xauusdt-nfp-trading.md` — XAUUSDT gold perpetual: price discrepancy vs spot gold, NFP trading strategies, position sizing for small accounts, confluence entry method
- `references/scan-execute-pattern.md` — Scan & Execute pattern: one-shot script that scans all liquid pairs, scores with FibStruct, and batch-executes top N entries
- `scripts/scan_execute.py` — Scan & Execute: batch scan 200 pairs with FibStruct scoring, execute top N entries. Configurable MIN_VOLUME, MIN_SCORE, MARGIN_PCT, MAX_ENTRIES at top of file. Re-queries balance before each entry.
- `scripts/nfp_auto_entry.py` — News-event auto-entry script: monitors price around release, enters on confirmation, manages SL/TP (manual polling for commodity pairs). Run with PYTHONUNBUFFERED=1.
- `scripts/intraday_tp_sl_calculator.py` — ATR-based TP/SL calculator for all open positions (update pairs dict and run)
- `scripts/portfolio_monitor.py` — Direct-execution portfolio monitor (fallback when cronjob delivery fails)
- `scripts/portfolio_monitor_with_news.py` — News-integrated monitor with auto cut-loss on DANGER rating (preferred version)
- `scripts/intraday_multi_tf_scanner.py` — Multi-TF scanner (4H→1H→15M→5M) with EMA/MACD/structure scoring + ATR-based SL/TP calculator
- `scripts/testnet_multi_entry.py` — Multi-trade entry script: cancels old orders, places LIMIT entries with calculated TP/SL levels, outputs tracking data for cronjob. Modify `trades` list to configure entries.
- `scripts/news_event_auto_entry.py` — Auto-entry on high-impact news (NFP/CPI/FOMC): waits for release, confirms direction (>0.3% move), executes MARKET order, sets SL/TP (API or manual monitor fallback). Configurable for LONG/SHORT/AUTO.
- `references/smart-position-monitor.md` — Technical exit monitor pattern: multi-TF EMA/RSI analysis every 60s, auto-closes positions when setup invalidates (3+ opposing signals while in loss).
- `references/fibstruct-v2-daemon.md` — FibStruct v2 daemon deployment: screen session, watchdog cronjob pattern, log management, duplicate process detection
- `scripts/nfp_auto_entry.py` — Auto-entry script for high-impact news (NFP/CPI/FOMC). Waits for news time, monitors price, enters LONG after directional confirmation (>0.3% pump). Configurable leverage, margin, thresholds. Note: XAUUSDT SL/TP must be set manually from app (API limitation).

## Pre-News Event Limit Entry (NFP/CPI/FOMC)

**See `references/pre-news-limit-entry.md` for full workflow.**

When user wants to place limit orders ahead of high-impact macro news to catch the whipsaw dip:

1. Fetch 15m + 1h klines from Binance public API (no auth needed): `https://fapi.binance.com/fapi/v1/klines?symbol={SYMBOL}&interval=15m&limit=120`
2. Calculate EMA7/25/99 on both timeframes
3. Find swing lows (fractal-based: low < prev_low AND low < next_low)
4. Identify demand zones (bullish engulfing / hammer candles on 1h)
5. Calculate Fibonacci retracement from recent swing high→low
6. **Stack confluences** — rank price levels by how many factors converge (EMA + Fib + swing low + demand zone)
7. Place laddered limit orders: 40% at best confluence, 30% aggressive, 20% conservative, 10% deep dip
8. SL below major swing low / structure break

**Key:** The more confluences at a level, the higher probability it holds during news volatility. 3-4 confluences = high probability fill zone.

## Related Skills (Absorbed)
- `crypto-futures-trading-system` → archived, content absorbed into this skill's references/strategy-evolution.md
- `binance-trading` → archived, CLI reference content absorbed into references/binance-cli-reference.md
- `trading-toolkit-setup` → archived, setup guide absorbed into references/toolkit-setup.md
