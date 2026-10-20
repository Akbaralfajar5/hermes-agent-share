# Post-Buy TP/SL Verification Pattern

## Problem
GMGN CLI's `swap` command uses `--condition-orders` for TP/SL, but this is **best-effort** — if strategy creation fails, the swap still succeeds and the position is left unprotected. Additionally, `loss_stop` in `--condition-orders` is silently ignored (only `profit_stop` works). This means positions can end up with:
- No TP/SL at all (strategy creation failed)
- TP only, no SL (loss_stop silently dropped)
- SL only (if created separately via `order strategy create`)

## How to Check

### Step 1: Check STMix group (condition_orders from swap)
```bash
gmgn-cli order strategy list --chain sol --from <WALLET> --group-tag STMix --base-token <CA> --raw
```
- `total > 0` → position has strategy orders
- Check `condition_orders[]` array for `profit_stop` (TP) and `loss_stop` (SL)
- Note: `loss_stop` in STMix is often empty even when specified in swap — this is the silent-ignore bug

### Step 2: Check LimitOrder group (standalone orders)
```bash
gmgn-cli order strategy list --chain sol --from <WALLET> --group-tag LimitOrder --base-token <CA> --raw
```
- `total > 0` → position has standalone TP/SL orders
- Check `sub_order_type`: `stop_loss` (SL) or `take_profit` (TP)

### Step 3: If BOTH empty → UNPROTECTED
Create TP and SL manually:
```bash
# Get entry price from portfolio
gmgn-cli portfolio holdings --wallet <WALLET> --chain sol --raw
# → use accu_cost / accu_amount for entry_price_per_token

# Get token balance (raw)
# → use balance * 10^decimals

# Create SL at -35%
gmgn-cli order strategy create --chain sol --from <WALLET> \
  --base-token <CA> --quote-token So11111111111111111111111111111111111111112 \
  --order-type limit_order --sub-order-type stop_loss \
  --check-price $(python3 -c "print($ENTRY * 0.65)") \
  --open-price $ENTRY \
  --amount-in $BALANCE \
  --slippage 15 --priority-fee 0.001 --tip-fee 0.0001 --anti-mev \
  --expire-in 604800 --raw

# Create TP at +50%
gmgn-cli order strategy create --chain sol --from <WALLET> \
  --base-token <CA> --quote-token So11111111111111111111111111111111111111112 \
  --order-type limit_order --sub-order-type take_profit \
  --check-price $(python3 -c "print($ENTRY * 1.5)") \
  --open-price $ENTRY \
  --amount-in $BALANCE \
  --slippage 15 --priority-fee 0.001 --tip-fee 0.0001 --anti-mev \
  --expire-in 604800 --raw
```

## Critical: `order get` ≠ TP/SL Status
`order get --order-id <id>` returns the BUY swap confirmation only:
```json
{
  "status": "confirmed",
  "hash": "...",
  "order_id": "...",
  "report": { "input_amount": "...", "output_amount": "..." }
}
```
This does NOT include TP/SL strategy information. The `order_id` from `swap` is the swap order ID, NOT the strategy order ID. Always use `order strategy list` to check TP/SL.

## Real-World Example (June 16, 2026)
9 positions found in `positions.json`. After checking GMGN:
- 3 had active strategy orders (petin SL, bully TP, cursor TP)
- 6 had NO strategy orders at all (POTM, Athlos, DOPAMINE, USAGIRL, Coco, Watermelon)
- Of the 3 with orders, only 1 had SL (petin via LimitOrder)
- The other 2 (bully, cursor) had TP only via STMix — no SL

**Root cause:** Auto-trader created buys with `--condition-orders` for TP, but `loss_stop` was silently ignored. And the separate `order strategy create` for SL either wasn't called or failed silently.

## Prevention: Auto-Trader Post-Buy Hook
Add to auto-trader script after every buy:
```python
# After swap succeeds, wait 3s, then verify
time.sleep(3)

# Check both groups
stmix = gmgn_list_strategy(chain="sol", group_tag="STMix", base_token=ca)
limit_orders = gmgn_list_strategy(chain="sol", group_tag="LimitOrder", base_token=ca)

has_tp = False
has_sl = False

# Check STMix condition_orders
for order in stmix.get("list", []):
    for cond in order.get("condition_orders", []):
        if cond.get("order_type") == "profit_stop":
            has_tp = True
        if cond.get("order_type") == "loss_stop":
            has_sl = True

# Check LimitOrder standalone orders
for order in limit_orders.get("list", []):
    if order.get("sub_order_type") == "take_profit":
        has_tp = True
    if order.get("sub_order_type") == "stop_loss":
        has_sl = True

# Create missing orders
if not has_sl:
    create_sl_order(ca, entry_price, token_balance)
if not has_tp:
    create_tp_order(ca, entry_price, token_balance)
```
