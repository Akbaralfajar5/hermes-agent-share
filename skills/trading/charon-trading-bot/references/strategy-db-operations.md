# Charon Strategy Database Operations

## Query All Strategies with Full Config

```python
import sqlite3, json

db = sqlite3.connect('/home/ubuntu/charon/charon.sqlite')
db.row_factory = sqlite3.Row

for row in db.execute("SELECT * FROM strategies ORDER BY name"):
    name = row['name']
    enabled = row['enabled']
    config = json.loads(row['config_json'])
    
    print(f"\n{'='*55}")
    print(f"📊 {name} — {'✅ ENABLED' if enabled else '❌ DISABLED'}")
    print(f"{'='*55}")
    
    print("\n📈 Entry Filters:")
    print(f"  • Entry Mode: {config.get('entry_mode')}")
    print(f"  • Min Source Count: {config.get('min_source_count')}")
    print(f"  • Token Age Max: {config.get('token_age_max_ms', 0) / 3600000:.1f} hours")
    print(f"  • MCap: ${config.get('min_mcap_usd', 0):,} - ${config.get('max_mcap_usd', 0):,}")
    print(f"  • ATH Distance: {config.get('max_ath_distance_pct', 0)}%")
    print(f"  • Min Holders: {config.get('min_holders', 0)}")
    print(f"  • Max Top20 Holder: {config.get('max_top20_holder_percent', 0)}%")
    
    print("\n💰 Fee Requirements:")
    print(f"  • Require Fee Claim: {config.get('require_fee_claim', False)}")
    print(f"  • Min Fee Claim: {config.get('min_fee_claim_sol', 0)} SOL")
    print(f"  • Min GMGN Total Fee: {config.get('min_gmgn_total_fee_sol', 0)} SOL")
    
    print("\n📊 Trending Filters:")
    print(f"  • Min Volume: ${config.get('trending_min_volume_usd', 0):,}")
    print(f"  • Min Swaps: {config.get('trending_min_swaps', 0)}")
    print(f"  • Max Rug Ratio: {config.get('trending_max_rug_ratio', 0) * 100:.0f}%")
    print(f"  • Max Bundler Rate: {config.get('trending_max_bundler_rate', 0) * 100:.0f}%")
    
    print("\n🎯 Position & Exit:")
    print(f"  • Position Size: {config.get('position_size_sol', 0)} SOL")
    print(f"  • Max Open Positions: {config.get('max_open_positions', 0)}")
    print(f"  • TP: +{config.get('tp_percent', 0)}%")
    print(f"  • SL: {config.get('sl_percent', 0)}%")
    trailing = f"✅ {config.get('trailing_percent', 0)}%" if config.get('trailing_enabled') else "❌ Off"
    print(f"  • Trailing: {trailing}")
    partial = f"✅ Sell {config.get('partial_tp_sell_percent', 0)}% at +{config.get('partial_tp_at_percent', 0)}%" if config.get('partial_tp') else "❌ Off"
    print(f"  • Partial TP: {partial}")
    
    print("\n🤖 LLM:")
    print(f"  • Use LLM: {'✅' if config.get('use_llm') else '❌'}")
    print(f"  • Min Confidence: {config.get('llm_min_confidence', 0)}%")

db.close()
```

## Update Single Strategy Setting

```python
import sqlite3, json

db = sqlite3.connect('/home/ubuntu/charon/charon.sqlite')

# Strategy names in DB (with spaces/caps): 'Degen', 'Dip Buy', 'Smart Money', 'Sniper'
strategy_name = 'Degen'

# Get current config
cursor = db.execute("SELECT config_json FROM strategies WHERE name = ?", [strategy_name])
row = cursor.fetchone()
config = json.loads(row[0])

# Update desired field
config['min_holders'] = 50  # example

# Save back
db.execute("UPDATE strategies SET config_json = ? WHERE name = ?", [json.dumps(config), strategy_name])
db.commit()

# Verify
cursor = db.execute("SELECT config_json FROM strategies WHERE name = ?", [strategy_name])
new_config = json.loads(cursor.fetchone()[0])
print(f"✅ {strategy_name} min_holders updated: {new_config['min_holders']}")

db.close()
```

## Enable/Disable Strategy

```python
import sqlite3

db = sqlite3.connect('/home/ubuntu/charon/charon.sqlite')

# Enable
db.execute("UPDATE strategies SET enabled = 1 WHERE name = 'Smart Money'")

# Disable
db.execute("UPDATE strategies SET enabled = 0 WHERE name = 'Sniper'")

db.commit()
db.close()
```

## Common Config Keys

| Key | Type | Description |
|-----|------|-------------|
| entry_mode | string | 'immediate' or 'wait_for_dip' |
| min_source_count | int | Min signal sources required |
| token_age_max_ms | int | Max token age in milliseconds |
| min_mcap_usd | int | Minimum market cap USD |
| max_mcap_usd | int | Maximum market cap USD |
| max_ath_distance_pct | int | Max % below ATH (negative = must be below) |
| min_holders | int | Minimum holder count |
| max_top20_holder_percent | int | Max % held by top 20 |
| require_fee_claim | bool | Require fee claim |
| min_fee_claim_sol | float | Min fee claim in SOL |
| min_gmgn_total_fee_sol | float | Min GMGN total fee |
| trending_min_volume_usd | int | Min trending volume |
| trending_min_swaps | int | Min swap count |
| trending_max_rug_ratio | float | Max rug ratio (0-1) |
| trending_max_bundler_rate | float | Max bundler rate (0-1) |
| position_size_sol | float | Position size in SOL |
| max_open_positions | int | Max concurrent positions |
| tp_percent | int | Take profit % |
| sl_percent | int | Stop loss % (negative) |
| trailing_enabled | bool | Enable trailing stop |
| trailing_percent | int | Trailing stop % |
| partial_tp | bool | Enable partial TP |
| partial_tp_at_percent | int | Trigger partial at % |
| partial_tp_sell_percent | int | Sell % of position |
| max_hold_ms | int | Max hold time (0=unlimited) |
| use_llm | bool | Use LLM for analysis |
| llm_min_confidence | int | Min LLM confidence % |
