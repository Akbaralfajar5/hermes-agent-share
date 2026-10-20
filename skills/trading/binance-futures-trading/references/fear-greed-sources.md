# Fear & Greed Index — Source Comparison

## Verified 2026-05-02 by user the user

### ✅ CoinMarketCap (PREFERRED — use this)
- **URL:** `https://coinmarketcap.com/charts/fear-and-greed-index/`
- **Method:** Scrape HTML, extract via regex
- **Code:**
  ```python
  import requests, re
  r = requests.get("https://coinmarketcap.com/charts/fear-and-greed-index/",
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    timeout=15)
  score = int(re.findall(r'"score"\s*:\s*(\d+)', r.text)[0])
  ```
- **Classification from score:**
  - ≤20: Extreme Fear
  - ≤40: Fear
  - ≤60: Neutral
  - ≤80: Greed
  - >80: Extreme Greed
- **Accuracy:** ✅ Matched user's live CoinMarketCap app screenshot (44 Neutral)
- **Latency:** Real-time

### ✅ cfgi.io (BACKUP)
- **URL:** `https://cfgi.io/bitcoin-fear-greed-index/`
- **Method:** Scrape, look for "Now" value in Historical Values
- **Note:** Shows BTC-specific F&G (61 Greed on same day CMC showed 44 Neutral for overall crypto)
- **Useful for:** BTC-specific sentiment, breakdown by component (Price Score, Volatility, Volume, Impulse, Technical, Social, Dominance, Search, Whales, Order Book)

### ❌ api.alternative.me (DO NOT USE)
- **URL:** `https://api.alternative.me/fng/`
- **Method:** JSON API
- **Problem:** Returns STALE/DELAYED data
- **Evidence:** Returned 26 (Fear) when real value was 44 (Neutral) — confirmed by user checking CoinMarketCap directly
- **Time until update field** showed ~1800 seconds but data was hours behind
- **DO NOT USE for trading decisions**

### ❌ CoinGlass API
- **URL:** `https://open-api-v3.coinglass.com/api/index/fear-greed-history`
- **Problem:** Requires API key (returns error 30001)
- **Not usable without paid subscription**

### ❌ CoinMarketCap API (direct)
- **URL:** `https://api.coinmarketcap.com/data-api/v3/fear-greed/latest`
- **Problem:** Returns 404
- **Pro API endpoint requires authentication**
