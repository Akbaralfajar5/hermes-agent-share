# MEXC API Reference for Spot Scanning

## Base URL
`https://api.mexc.com/api/v3`

## Endpoints Used

### 24hr Ticker
```
GET /ticker/24hr
```
Returns all pairs. No auth needed. ~2400 pairs total.

Fields: `symbol`, `lastPrice`, `priceChangePercent`, `quoteVolume`, `highPrice`, `lowPrice`, `openPrice`

### Klines (Candlesticks)
```
GET /klines?symbol={SYMBOL}&interval={INTERVAL}&limit={LIMIT}
```
- Intervals: `1m`, `5m`, `15m`, `30m`, `60m`, `4h`, `1d`, `1W`, `1M`
- Max limit: 1000
- **IMPORTANT**: Quote volume is at index 7 (differs from Binance which uses index 5 for base volume)
- Array format: `[openTime, open, high, low, close, volume, closeTime, quoteVolume]`

## Filtering Tips

### Exclude leveraged tokens
```python
skip_suffixes = ['3L', '3S', '2L', '2S', '4L', '4S', '5L', '5S']
if any(base.endswith(x) for x in skip_suffixes):
    continue
```

### Exclude stablecoins
```python
stables = ['USDC', 'BUSD', 'DAI', 'TUSD', 'FDUSD', 'USD1', 'USDE', 'EUR']
```

### Volume thresholds
- For gem hunting: $200K+ daily volume (MEXC has many low-vol pairs)
- For swing trading: $500K+ 
- For day trading: $1M+

## Rate Limits
- No strict published limit for public endpoints
- In practice, ~20 requests/second works fine
- Klines endpoint is fast and reliable

## MEXC vs Binance Differences
1. MEXC has WAY more pairs (2400+ vs ~600 on Binance)
2. Many micro-cap tokens only on MEXC (not Binance/Gate)
3. Volume data can be inflated (wash trading more common)
4. Kline index 7 = quoteVolume (Binance: index 7 = quoteAssetVolume, same thing)
5. No mcap data in ticker — must cross-reference CoinGecko for mcap filtering

## Cross-Reference Pattern
When scanning MEXC, cross-check interesting finds:
```python
# Check if also on Binance (safer, more liquid)
binance_resp = requests.get("https://api.binance.com/api/v3/exchangeInfo")
binance_symbols = {s['baseAsset'] for s in binance_resp.json()['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING'}

# Check Gate.io
gate_resp = requests.get("https://api.gateio.ws/api/v4/spot/tickers")
gate_pairs = {t['currency_pair'].replace('_USDT', '') for t in gate_resp.json() if '_USDT' in t['currency_pair']}
```

## Narrative Token Categories (MEXC-specific gems)
These tokens are often MEXC-exclusive or MEXC-first:
- AI Agents: ELIZAOS, SWARMS, ZEREBRO, GRIFFAIN, COOKIE, ARC
- AI Infra: AIX, CHIP, ALCH, UAI (UnifAI Network - MCap #428, also on Gate.io)
- Gaming: MOGU, 9BIT, PLAY
- Privacy: ZANO
- BTC ecosystem: BSB

**Removed (May 2026):** PSAI — delisted from MEXC (ST tag → delist May 9 2026). Was only on MEXC, no DEX liquidity. Total loss for holders.

## LRC (Loopring) Pattern Notes (May 2026)
- Ethereum L2 ZK-Rollup, established project
- Listed on: Binance, Coinbase, Kraken, OKX, Gate.io, MEXC (6+ exchanges = very safe)
- Narrative: Layer 2 / ZK (solid but not "hot" — more of a technical bounce play)
- When it shows 5x+ volume spike at oversold RSI + bottom of range = high conviction bounce
- Typical R:R at support: 1:3 to 1:4
- Price range May 2026: ~$0.018-0.024

## ENM Warning (May 2026)
- Dropped -83% from 20-bar high ($0.091 → $0.016)
- Could NOT be found on CoinGecko or DexScreener under "ENM"
- Despite $4.29M volume, fundamentals unverifiable
- SKIPPED per PSAI lesson: unverified project + massive decline = avoid
