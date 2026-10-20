# Crypto Narrative Analysis Workflow

## Purpose
Identify hot crypto narratives from trending coins and categorize candidates by sector/theme for better fundamental context.

## When to Use
- User asks "narasi apa yang bagus sekarang" or "what narratives are hot"
- After technical screening, to provide fundamental context
- To understand why certain tokens are pumping

## Data Source
CoinGecko Trending API (free, no key needed):
```bash
curl -sf "https://api.coingecko.com/api/v3/search/trending"
```

Returns top 10-15 trending coins with:
- Name, symbol, market cap rank
- 24h price change
- Market cap

## Categorization Logic

```python
import requests

resp = requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=10)
trending = resp.json()

narratives = {}

for coin in trending['coins'][:15]:
    item = coin['item']
    name = item['name'].lower()
    symbol = item['symbol'].lower()
    
    # Categorize by keywords in name
    if any(x in name for x in ['real world', 'ondo', 'rwa']):
        narratives['RWA (Real World Assets)'] = narratives.get('RWA (Real World Assets)', []) + [item['symbol'].upper()]
    elif any(x in name for x in ['ai', 'bittensor', 'render', 'fetch']):
        narratives['AI'] = narratives.get('AI', []) + [item['symbol'].upper()]
    elif any(x in name for x in ['layer', 'sui', 'aptos', 'sei']):
        narratives['Layer-1 Alt'] = narratives.get('Layer-1 Alt', []) + [item['symbol'].upper()]
    elif any(x in name for x in ['privacy', 'zcash', 'monero']):
        narratives['Privacy'] = narratives.get('Privacy', []) + [item['symbol'].upper()]
    elif any(x in name for x in ['depin', 'network', 'infrastructure', 'constellation', 'moonriver']):
        narratives['DePIN'] = narratives.get('DePIN', []) + [item['symbol'].upper()]
    elif any(x in name for x in ['meme', 'doge', 'shib', 'pepe', 'wojak', 'pengu']):
        narratives['Meme'] = narratives.get('Meme', []) + [item['symbol'].upper()]
    elif any(x in name for x in ['internet computer', 'icp']):
        narratives['Web3 Infrastructure'] = narratives.get('Web3 Infrastructure', []) + [item['symbol'].upper()]
    elif any(x in name for x in ['gaming', 'game', 'nft', 'treasure', 'magic']):
        narratives['Gaming/NFT'] = narratives.get('Gaming/NFT', []) + [item['symbol'].upper()]
    elif any(x in name for x in ['wallet', 'account', 'biconomy']):
        narratives['Web3 Infrastructure'] = narratives.get('Web3 Infrastructure', []) + [item['symbol'].upper()]
```

## Output Format

```
🔥 HOT NARRATIVES (from trending coins):

📌 **RWA (Real World Assets)**
   Coins: ONDO, POLYX
   Strength: 🔥🔥

📌 **DePIN**
   Coins: DAG, FIL, MOVR
   Strength: 🔥🔥🔥

📌 **Layer-1 Alt**
   Coins: SUI, ICP
   Strength: 🔥🔥
```

Strength = number of coins in that narrative (more coins = hotter narrative).

## Narrative Leaders (May 2026)

Check Binance 24h performance for narrative leaders:

```python
leaders = {
    'ONDO': 'RWA',
    'ICP': 'Web3 Infra', 
    'DAG': 'DePIN',
    'SUI': 'Layer-1 Alt',
    'ZEC': 'Privacy',
    'TAO': 'AI'
}

for symbol, narrative in leaders.items():
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
    r = requests.get(url, timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"✅ {symbol:6} ({narrative:15}) +{float(data['priceChangePercent']):6.2f}%  Vol: ${float(data['quoteVolume'])/1e6:.0f}M")
```

## Integration with Scanner

1. Run technical scanner first (EMA/RSI/score filtering)
2. After getting candidates, run narrative analysis
3. Present results grouped by narrative for context
4. User can choose based on technical + narrative alignment

## Pitfalls

- **Don't filter by narrative first** — technical quality comes first, narrative is context
- **Trending ≠ good entry** — many trending coins are already overbought
- **Narrative rotation** — hot narratives change monthly, update keyword list
- **False categorization** — some coins fit multiple narratives, pick primary

## Related
- See `references/hot-narratives-2026-05.md` for detailed narrative descriptions
