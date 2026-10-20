# Charon Default Strategy Settings

Quick reference for all 4 built-in strategies.

## Sniper (default enabled)

```
Entry Mode: immediate
Token Age Max: 1 hour
MCap: $7,000 - $200,000
ATH Distance: 0%
Min Holders: 0
Max Top20 Holder: 100%
Require Fee Claim: true
Min Fee Claim: 0.5 SOL
Min GMGN Total Fee: 10 SOL
Max Rug Ratio: 30%
Max Bundler Rate: 50%
Position Size: 0.1 SOL
Max Open Positions: 3
TP: +50% | SL: -25%
Trailing: 20%
Partial TP: off
LLM: enabled, min 50% confidence
```

## Dip Buy

```
Entry Mode: wait_for_dip
Token Age Max: 24 hours
MCap: $25,000 - $500,000
ATH Distance: -40% (must be 40% below ATH)
Min Holders: 0
Max Top20 Holder: 100%
Max Rug Ratio: 30%
Max Bundler Rate: 50%
Position Size: 0.05 SOL
Max Open Positions: 3
TP: +30% | SL: -20%
Trailing: 15%
Partial TP: off
LLM: enabled, min 60% confidence
```

## Smart Money

```
Entry Mode: immediate
Token Age Max: 24 hours
MCap: $10,000 - $1,000,000
ATH Distance: 0%
Min Holders: 1,000
Max Top20 Holder: 50%
Trending Min Volume: $5,000
Trending Min Swaps: 100
Max Rug Ratio: 20%
Max Bundler Rate: 30%
Position Size: 0.1 SOL
Max Open Positions: 3
TP: +100% | SL: -25%
Trailing: off
Partial TP: sell 50% at +100%
LLM: enabled, min 70% confidence
```

## Degen

```
Entry Mode: immediate
Token Age Max: 1 hour
MCap: $5,000 - $100,000
ATH Distance: 0%
Min Holders: 0
Max Top20 Holder: 100%
Max Rug Ratio: 50%
Max Bundler Rate: 70%
Position Size: 0.05 SOL
Max Open Positions: 5
TP: +30% | SL: -15%
Trailing: 10%
Partial TP: off
LLM: disabled
```

## Telegram Commands

Enable/disable:
```
/stratenable sniper
/stratdisable sniper
```

Modify settings:
```
/stratset sniper tp_percent 75
/stratset sniper max_mcap_usd 500000
/stratset sniper sl_percent -30
/stratset smart_money min_holders 500
```

Available keys:
- tp_percent, sl_percent
- position_size_sol, max_open_positions
- min_mcap_usd, max_mcap_usd
- min_holders, max_top20_holder_percent
- trailing_enabled, trailing_percent
- partial_tp, partial_tp_at_percent, partial_tp_sell_percent
- max_hold_ms
- use_llm, llm_min_confidence
- min_source_count
- require_fee_claim, min_fee_claim_sol, min_gmgn_total_fee_sol
- max_ath_distance_pct
- token_age_max_ms
- trending_min_volume_usd, trending_min_swaps
- trending_max_rug_ratio, trending_max_bundler_rate
