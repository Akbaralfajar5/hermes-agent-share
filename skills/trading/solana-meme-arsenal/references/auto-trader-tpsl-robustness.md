# Auto-Trader TP/SL Robustness — Lessons Learned (June 2026)

## Critical Finding: `loss_stop` Does NOT Work in `--condition-orders`

**Verified across multiple tokens (Coco, USAGIRL, Kohen, DOPAMINE, petin):**
- `profit_stop` in `--condition-orders` → ✅ WORKS (STMix created with profit stops)
- `loss_stop` in `--condition-orders` → ❌ SILENTLY IGNORED (swap succeeds, STMix created, but NO stop-loss)

The GMGN CLI accepts the full condition_orders JSON without error, but `loss_stop` entries are never actually registered on the GMGN server.

## Correct Pattern

```python
# Step 1: Swap with TP only
condition_orders = json.dumps([
    {"order_type": "profit_stop", "side": "sell", "price_scale": "150", "sell_ratio": "100"},  # +50% TP
])
swap_result = run_cmd(f"gmgn-cli swap ... --condition-orders '{condition_orders}' --raw")

# Step 2: Wait for tx confirmation
time.sleep(3)

# Step 3: Create SL separately via order strategy create
entry_price_sol = TRADE_AMOUNT / token_amount
sl_price = entry_price_sol * 0.65
sl_cmd = (
    f"gmgn-cli order strategy create --chain sol --from {WALLET} "
    f"--base-token {ca} --quote-token {SOL_MINT} "
    f"--order-type limit_order --sub-order-type stop_loss "
    f"--check-price {sl_price:.20f} --open-price {entry_price_sol:.20f} "
    f"--amount-in {int(token_amount)} --slippage 15 "
    f"--priority-fee 0.001 --tip-fee 0.0001 --anti-mev "
    f"--expire-in 604800 --raw"
)
sl_result = run_cmd(sl_cmd)
```

## Verification After Buy

Always verify both orders exist:

```python
# Check TP (STMix)
stmix = json.loads(run_cmd(f"gmgn-cli order strategy list --chain sol --from {WALLET} --group-tag STMix --base-token {ca}"))
has_tp = stmix.get("total", 0) > 0

# Check SL (LimitOrder)
limit = json.loads(run_cmd(f"gmgn-cli order strategy list --chain sol --from {WALLET} --group-tag LimitOrder --base-token {ca}"))
has_sl = any(o.get("sub_order_type") == "stop_loss" for o in limit.get("list", []))
```

## output_amount Fallback Chain

GMGN swap response may not include `output_amount` at top level. Fallback chain:

1. `swap_result.get("output_amount")`
2. `swap_result.get("data", {}).get("output_amount")`
3. Wait 3s → `gmgn-cli portfolio holdings` → find token balance
4. `gmgn-cli order quote` → estimated output

## User Default Config

- TP: +50% sell 100% (single tier, NOT multi-tier)
- SL: -35% sell 100%
- Entry: 0.1 SOL per trade
- Filter: Grade B+ (score ≥ 60)
