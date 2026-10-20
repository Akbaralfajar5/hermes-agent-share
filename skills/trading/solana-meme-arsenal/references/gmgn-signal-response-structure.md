# GMGN Signal Response Structure

## `market signal` JSON Shape (as of June 2026)

Top-level is a **JSON array** (NOT an object with `data` key):

```json
[
  {
    "id": "uuid",
    "signal_type": 1,
    "signal_times": 5,
    "signal_times_by_type": {"1": 1, "6": 1, "7": 1, "10": 1, "15": 1},
    "trigger_at": 1781601600,
    "trigger_mc": 12408.525,
    "first_trigger_mc": 12408.525,
    "market_cap": 4585.7667,
    "token_address": "5mJwL...pump",
    "ath": 16072.137,
    "cur_data": {
      "top_10_holder_rate": 0.1533,
      "holder_count": 83,
      "liquidity": 6613.71
    },
    "data": {
      "address": "5mJwL...pump",
      "symbol": "KOHEN",
      "name": "Justice for Kohen Wiley",
      "market_cap": 12408.525,
      "usd_market_cap": 12408.525,
      "liquidity": 10630.92,
      "holder_count": 45,
      "top_10_holder_rate": 0.1533,
      "bundler_trader_amount_rate": 0.1898,
      "bot_degen_rate": 0.5848,
      "bot_degen_count": 59,
      "smart_degen_count": 0,
      "renowned_count": 1,
      "sniper_count": 0,
      "creator": "B4tWh...QJju",
      "creator_token_status": "creator_hold",
      "creator_balance_rate": 0,
      "creator_created_open_count": 11,
      "creator_created_count": 2374,
      "twitter_create_token_count": 0,
      "launchpad": "Pump.fun",
      "progress": 0.4051,
      "has_at_least_one_social": false,
      "twitter": "Frank_67x/status/...",
      "website": "https://...",
      "telegram": "",
      "rug_ratio": 0,
      "is_honeypot": "",
      "renounced_mint": true,
      "renounced_freeze_account": true,
      "burn_status": "burn",
      "fresh_wallet_rate": 0.2028,
      "rat_trader_amount_rate": 0,
      "entrapment_ratio": 0,
      "is_wash_trading": false
    }
  }
]
```

## Field Mapping for Pre-Filter

| Filter Need | Field Path | Notes |
|---|---|---|
| CA | `data.address` or `token_address` | Both present, prefer `data.address` |
| Symbol | `data.symbol` | |
| Market Cap | `data.usd_market_cap` | `market_cap` on item level is trigger MC, NOT current |
| Holders | `cur_data.holder_count` | Fallback: `data.holder_count` |
| Top10 | `cur_data.top_10_holder_rate` or `data.top_10_holder_rate` | |
| Liquidity | `cur_data.liquidity` or `data.liquidity` | |
| Bundler | `data.bundler_trader_amount_rate` | NOT in cur_data |
| Bot rate | `data.bot_degen_rate` | |
| Bot count | `data.bot_degen_count` | |
| Smart money | `data.smart_degen_count` | |
| KOL | `data.renowned_count` | |
| Snipers | `data.sniper_count` | |
| Creator | `data.creator` | Wallet address |
| Dev status | `data.creator_token_status` | "creator_hold" or "creator_close" |
| Dev balance | `data.creator_balance_rate` | 0.0 = sold, even if status says "hold" |
| Serial open | `data.creator_created_open_count` | >10 = serial deployer |
| Serial twitter | `data.twitter_create_token_count` | >50 = serial promoter |
| Social | `data.has_at_least_one_social` | Also check `data.twitter`, `data.website`, `data.telegram` |
| Progress | `data.progress` | 0-1, 1.0 = graduated |
| Rug ratio | `data.rug_ratio` | >0.10 = skip |
| Honeypot | `data.is_honeypot` | Empty string = no |
| Mint auth | `data.renounced_mint` | true = renounced ✅ |
| Freeze auth | `data.renounced_freeze_account` | true = renounced ✅ |
| Burn status | `data.burn_status` | "burn" = burned ✅ |
| Fresh wallet | `data.fresh_wallet_rate` | High = new wallets buying |
| Rat trader | `data.rat_trader_amount_rate` | >0.05 = suspicious |
| Wash trading | `data.is_wash_trading` | true = skip |
| ATH | `ath` | Top-level field |

## Key Gotcha: Two Different MC Values

- `item.market_cap` (top-level) = **trigger MC** (MC when signal fired)
- `data.usd_market_cap` (nested) = **current MC** at data fetch time

Use `data.usd_market_cap` for filtering. The trigger MC can be useful for "how early was this caught" analysis.

## cur_data vs data

`cur_data` contains live-updated metrics (holder count, liquidity, T10) that may differ from `data` (snapshot at signal time). For filtering, prefer `cur_data` when available, fall back to `data`.

## Parsing Pattern

```python
import json

data = json.loads(open('/tmp/signal1.json').read())  # top-level is list
for item in data:
    d = item.get('data', {})
    cur = item.get('cur_data', {})
    ca = d.get('address', '')
    if not ca.endswith('pump'):
        continue
    mc = d.get('usd_market_cap', 0)
    holders = cur.get('holder_count', 0) or d.get('holder_count', 0)
    # ... etc
```
