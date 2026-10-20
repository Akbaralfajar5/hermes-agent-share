# Intraday Futures Workflow

## Timeframe Rules (User-Corrected)

Futures trading is NOT swing trading. Use lower timeframes for tight SL and quick profit.

| Step | TF | Purpose |
|------|-----|---------|
| 1. Trend | **4H** | Determine long/short bias (EMA7 vs EMA21, MACD) |
| 2. Confirm | **1H** | Must align with 4H direction |
| 3. Entry | **15M / 5M** | Precise entry on pullback |

**Rule: ALL three TFs must align.** If 4H is bullish but 1H/15M are bearish, WAIT — don't force entry.

## Scanning Algorithm (25+ tokens)

```python
# For each token, score on 4H + 1H + 15M
long_score = 0
if e7_4h > e21_4h: long_score += 2   # 4H trend (weight 2)
if macd_4h > 0: long_score += 1       # 4H momentum
if e7_1h > e21_1h: long_score += 2   # 1H confirm (weight 2)
if macd_1h > 0: long_score += 1       # 1H momentum
if rsi_4h < 65: long_score += 1       # Not overbought
if rsi_1h < 60: long_score += 1       # Room to run
if 40 < rsi_15 < 55: long_score += 1  # 15M pullback = ideal entry

# Score 7+/9 = strong setup
```

Short scoring mirrors this with inverted conditions.

## Position Sizing (Intraday)

```
Balance = total USDT
Risk = 2-3% of balance
SL distance = 2x ATR(14) on 15M timeframe (~1-2% from entry)
Position notional = Risk / SL_distance_pct
Margin = Position notional / Leverage
Quantity = Position notional / Entry price
```

### Example
- Balance: $5,000
- Risk 3%: $150
- 15M ATR: $0.005 on a $1.00 token = 0.5% per ATR
- SL = 2x ATR = 1.0% below entry
- Position = $150 / 0.01 = $15,000 notional
- At 20x leverage: $750 margin

## SL/TP Placement (ATR-Based)

| Level | Distance | R:R |
|-------|----------|-----|
| SL | 2x ATR below/above entry | — |
| TP1 | 2x ATR (= 1:1 R:R) | Partial close 50% |
| TP2 | 4x ATR (= 1:2 R:R) | Close remaining 50% |
| TP3 | 6x ATR (= 1:3 R:R) | Optional runner |

After TP1 hit → move SL to breakeven.

## Testnet Limitations

Binance testnet does NOT support:
- `STOP_MARKET` orders
- `TAKE_PROFIT_MARKET` orders
- Algo conditional orders

Error: `"Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."` — and Algo endpoint also fails on testnet.

**Workaround:** Use cron job to monitor positions every 30 min and execute market close orders when SL/TP levels are breached.

## Tokens to Scan (Futures-Available)

Confirmed available on Binance Futures testnet:
DOGEUSDT, SOLUSDT, XRPUSDT, ADAUSDT, AVAXUSDT, LINKUSDT, DOTUSDT,
NEARUSDT, FILUSDT, APTUSDT, ARBUSDT, OPUSDT, SUIUSDT, SEIUSDT,
PENDLEUSDT, TAOUSDT, INJUSDT, COMPUSDT, AAVEUSDT, LTCUSDT, ETCUSDT,
ATOMUSDT, FTMUSDT, RUNEUSDT, WIFUSDT

NOT available on testnet: PEPEUSDT, MATICUSDT, RAYUSDT
