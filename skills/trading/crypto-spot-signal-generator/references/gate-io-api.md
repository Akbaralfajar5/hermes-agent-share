# Gate.io API Reference

## Endpoints Used

### Spot Tickers (24h data)
```
GET https://api.gateio.ws/api/v4/spot/tickers
```

Returns array of ticker objects:
```json
{
  "currency_pair": "BTC_USDT",
  "last": "80000.00",
  "lowest_ask": "80001.00",
  "highest_bid": "79999.00",
  "change_percentage": "2.5",
  "base_volume": "1234.56",
  "quote_volume": "98765432.10",
  "high_24h": "81000.00",
  "low_24h": "78000.00",
  "etf_leverage": null
}
```

**Key fields**:
- `currency_pair`: Trading pair (e.g., "B_USDT")
- `last`: Current price
- `change_percentage`: 24h change as string percentage
- `quote_volume`: 24h volume in quote currency (USDT)
- `high_24h` / `low_24h`: 24h price range

### Currency Info
```
GET https://api.gateio.ws/api/v4/spot/currencies/{currency}
```

Returns token metadata:
```json
{
  "currency": "B",
  "name": "BUILDon",
  "name_cn": "N/A",
  "chain": "BSC",
  "delisted": false,
  "trade_status": "tradable",
  "withdraw_disabled": false,
  "deposit_disabled": false
}
```

### Candlesticks (BROKEN - DO NOT USE)
```
GET https://api.gateio.ws/api/v4/spot/candlesticks
```

**Known Issues**:
- Returns 8 columns but pandas expects 7
- Timestamp format causes "year out of range" errors
- Column structure: `[timestamp, volume, close, high, low, open, amount, ?]`
- Timestamp appears to be in wrong format (not standard Unix ms)

**Error Example**:
```
Error: 7 columns passed, passed data had 8 columns
Error: year 1776441600 is out of range
```

**Workaround**: Use ticker endpoint only, calculate support/resistance from 24h high/low.

## Altcoin Scanning Pattern

```python
import requests

url = "https://api.gateio.ws/api/v4/spot/tickers"
response = requests.get(url, timeout=10)
tickers = response.json()

candidates = []
for ticker in tickers:
    if ticker['currency_pair'].endswith('_USDT'):
        try:
            change = float(ticker['change_percentage'])
            volume = float(ticker['quote_volume'])
            last = float(ticker['last'])
            high = float(ticker['high_24h'])
            low = float(ticker['low_24h'])
            
            # Filter criteria
            if 5 <= change <= 30 and volume > 500_000:
                # Calculate position in 24h range
                if high > low:
                    position = ((last - low) / (high - low)) * 100
                else:
                    position = 50
                
                if position < 70:  # Not near top
                    candidates.append({
                        'symbol': ticker['currency_pair'].replace('_USDT', ''),
                        'price': last,
                        'change_24h': change,
                        'volume_24h': volume,
                        'high_24h': high,
                        'low_24h': low,
                        'price_position': position
                    })
        except:
            continue

# Sort by volume (liquidity priority)
candidates.sort(key=lambda x: x['volume_24h'], reverse=True)
```

## Rate Limits

Gate.io public API:
- No authentication required for public endpoints
- Rate limit: ~900 requests per minute
- No IP restrictions for public data

## Comparison: Gate.io vs Binance

| Feature | Gate.io | Binance |
|---------|---------|---------|
| Low-cap altcoins | ✅ Excellent | ❌ Limited |
| Liquidity | ⚠️ Variable | ✅ High |
| API reliability | ⚠️ Some issues | ✅ Stable |
| Candlestick data | ❌ Broken | ✅ Works |
| Ticker data | ✅ Works | ✅ Works |
| User safety | ⚠️ Lower | ✅ Higher |

**Strategy**: 
- Use Gate.io for altcoin discovery
- Cross-check with Binance if coin is listed there
- Prefer Binance-listed coins for larger positions
- Gate.io-only coins = max 2-5% portfolio
