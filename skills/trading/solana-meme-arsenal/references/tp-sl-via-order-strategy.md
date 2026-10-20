# TP/SL via `order strategy create` — Best Practice (June 2026)

## Why NOT `--condition-orders`

| Issue | Detail |
|-------|--------|
| `loss_stop` silently ignored | GMGN CLI accepts `loss_stop` in `--condition-orders` but does NOT create the SL order. Swap succeeds, position is UNPROTECTED. |
| `profit_stop` creates STMix | TP works but creates an STMix order that can't be modified. To change TP, must cancel entire STMix and recreate. |
| Can't verify easily | `order get` only returns swap confirmation, not strategy status. Must query both STMix + LimitOrder groups. |

## Best Practice: Plain Swap + Separate Orders

### Step 1: Plain swap
```bash
gmgn-cli swap --chain sol --from <WALLET> \
  --input-token SOL --output-token <CA> \
  --amount <LAMPORTS> --slippage 10 \
  --anti-mev --priority-fee 0.001 --tip-fee 0.0001 --raw
```

### Step 2: Get token amount
- Try `swap_result.report.output_amount` or `swap_result.report.base_amount`
- Fallback: `order quote` (wait 3s for tx confirmation first)
- Last resort: `portfolio holdings`

### Step 3: Create SL
```bash
gmgn-cli order strategy create --chain sol --from <WALLET> \
  --base-token <CA> --quote-token SOL \
  --order-type limit_order --sub-order-type stop_loss \
  --check-price <entry_price * 0.65> \
  --open-price <entry_price> \
  --amount-in <token_amount> \
  --slippage 15 --priority-fee 0.001 --tip-fee 0.0001 --anti-mev \
  --expire-in 604800 --raw
```

### Step 4: Create TP
```bash
gmgn-cli order strategy create --chain sol --from <WALLET> \
  --base-token <CA> --quote-token SOL \
  --order-type limit_order --sub-order-type take_profit \
  --check-price <entry_price * 2.0> \
  --open-price <entry_price> \
  --amount-in <token_amount> \
  --slippage 15 --priority-fee 0.001 --tip-fee 0.0001 --anti-mev \
  --expire-in 604800 --raw
```

### Step 5: Verify
```bash
gmgn-cli order strategy list --chain sol --group-tag LimitOrder
# Expect: stop_loss (running) + take_profit (running)
```

## Pitfalls
- `--amount-in` must be exact token amount (NOT lamports, NOT percent)
- `--expire-in 604800` = 7 days (default is shorter, may expire before TP hit)
- Both `--priority-fee` and `--tip-fee` required on SOL chain
- `take_profit` check-price MUST be > `open-price` (error otherwise)
- `stop_loss` check-price MUST be < `open-price` (error otherwise)
- If swap response lacks `output_amount`, use multi-field fallback: `output_amount` → `base_amount` → `amount_out` → quote API

## Verified Working (June 16, 2026)
- bully SL: order_id `48eca482-...` → running ✅
- cursor SL: order_id `4aae391a-...` → running ✅
- bully TP: order_id `70f17e9b-...` → running ✅
- cursor TP: order_id `fd33d43b-...` → running ✅
- petin SL: order_id `d1bd802e-...` → running ✅
