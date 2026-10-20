# Position Sizing Reference

## Formula

```
risk_amount = balance × risk_pct
sl_distance_pct = |entry_price - sl_price| / entry_price
position_notional = risk_amount / sl_distance_pct
margin_needed = position_notional / leverage
quantity = position_notional / entry_price
liquidation_price ≈ entry × (1 - 1/leverage + maint_margin_ratio)  # for LONG
liquidation_price ≈ entry × (1 + 1/leverage - maint_margin_ratio)  # for SHORT
```

## Worked Example: INJ LONG

```
Balance:        $5,000
Risk:           3% = $150
Entry:          $3.654
Stop Loss:      $3.18
Leverage:       25x

SL Distance:    (3.654 - 3.18) / 3.654 = 13.0%
Position Size:  $150 / 0.13 = $1,156
Margin Needed:  $1,156 / 25 = $46.25
Quantity:       $1,156 / $3.654 = 316 INJ
Liq. Price:     ~$3.58 (2% maint margin)
```

## Leverage Brackets (Binance)

Higher notional = lower max leverage. Always check:
```bash
binance-cli futures-usds notional-and-leverage-brackets --symbol INJUSDT
```

Typical brackets:
| Notional | Max Leverage |
|----------|-------------|
| 0-5K     | 25x         |
| 5K-50K   | 20x         |
| 50K-1.6M | 10x         |
| 1.6M+    | 5x or less  |

## Risk Rules

- Max 2-3% risk per trade
- Max 3 concurrent positions
- 8% portfolio drawdown = stop trading for the day
- After TP1 hit, move SL to breakeven
- Never risk more than 15% of portfolio across all positions
