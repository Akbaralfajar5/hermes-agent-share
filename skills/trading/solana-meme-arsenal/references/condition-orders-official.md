# condition_orders Official GMGN Approach

**Source:** GMGN Skills (`GMGNAI/gmgn-skills`) — `gmgn-swap` skill, installed June 2026.

## condition_orders on swap (PREFERRED)

Both `profit_stop` and `loss_stop` work in `--condition-orders` on the swap command. This is the official, atomic approach.

### price_scale semantics (OFFICIAL)

From GMGN skill docs:

| order_type | price_scale meaning | Example |
|---|---|---|
| `profit_stop` | Gain % from entry | `"50"` = +50% (triggers at 1.5× entry) |
| `loss_stop` | Drop % from entry | `"35"` = -35% (triggers at 0.65× entry) |
| `profit_stop_trace` | Gain % from entry (trailing) | `"100"` = +100% with drawdown callback |
| `loss_stop_trace` | Drop % from entry (trailing) | `"50"` = -50% with drawdown callback |

### Full condition_orders JSON schema

```json
[
  {"order_type": "profit_stop", "side": "sell", "price_scale": "50", "sell_ratio": "100"},
  {"order_type": "loss_stop", "side": "sell", "price_scale": "35", "sell_ratio": "100"}
]
```

Fields:
- `order_type`: `profit_stop` | `loss_stop` | `profit_stop_trace` | `loss_stop_trace`
- `side`: always `"sell"`
- `price_scale`: gain/drop % as string
- `sell_ratio`: % of position to sell (string)
- `drawdown_rate`: (trailing only) callback % from peak

### Multi-TP example

```json
[
  {"order_type": "profit_stop", "side": "sell", "price_scale": "100", "sell_ratio": "50"},
  {"order_type": "profit_stop", "side": "sell", "price_scale": "300", "sell_ratio": "100"},
  {"order_type": "loss_stop", "side": "sell", "price_scale": "65", "sell_ratio": "100"}
]
```

With `--sell-ratio-type hold_amount`: second TP fires on remaining 50%.

### Command

```bash
gmgn-cli swap --chain sol --from <WALLET> \
  --input-token So11111111111111111111111111111111111111112 \
  --output-token <CA> --amount <LAMPORTS> --slippage 10 \
  --anti-mev --priority-fee 0.001 --tip-fee 0.0001 \
  --condition-orders '<JSON>' --raw
```

### Verify

Check `strategy_order_id` in swap response. Then:
```bash
gmgn-cli order strategy list --chain sol --group-tag STMix --base-token <CA>
```

Should show `condition_orders[]` with both entries.

## Fallback: order strategy create (existing positions only)

⚠️ **CRITICAL LIMITATIONS:**
1. **Only 1 LimitOrder per token** — cannot have both TP and SL
2. **NEVER use `--expire-in`** — causes phantom orders
3. **`--open-price` REQUIRED** — without it, SL fails silently
4. **Use actual balance** from `portfolio holdings`, not quote amount

## Why old sessions said "loss_stop silently ignored"

Multiple factors:
1. `--expire-in 604800` was used → phantom orders
2. Amount from quote exceeded actual balance → silent rejection
3. SL trigger price already passed → GMGN auto-cancels
4. Possible API changes between sessions

**Current status (June 2026):** Both profit_stop and loss_stop work correctly in condition_orders.
