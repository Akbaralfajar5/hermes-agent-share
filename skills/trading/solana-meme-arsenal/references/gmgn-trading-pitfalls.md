# GMGN CLI Trading Pitfalls & Patterns

## Pitfall 1: condition-orders ≠ Real TP/SL

**Symptom:** Swap with `--condition-orders` succeeds but no strategy orders appear in `order strategy list`.

**Root cause:** The `--condition-orders` parameter on `gmgn-cli swap` is metadata only. It does NOT create server-side TP/SL orders.

**Fix:** Use separate `order strategy create` commands after the swap:
```bash
# After swap, create SL
gmgn-cli order strategy create --chain sol --from <W> --base-token <CA> --quote-token SOL \
  --order-type limit_order --sub-order-type stop_loss \
  --check-price <SL_PRICE> --open-price <ENTRY> --amount-in <AMT> \
  --slippage 15 --priority-fee 0.001 --tip-fee 0.0001 --anti-mev

# Create TP
gmgn-cli order strategy create --chain sol --from <W> --base-token <CA> --quote-token SOL \
  --order-type limit_order --sub-order-type take_profit \
  --check-price <TP_PRICE> --open-price <ENTRY> --amount-in <AMT> \
  --slippage 15 --priority-fee 0.001 --tip-fee 0.0001 --anti-mev
```

## Pitfall 2: PEM Format Required

**Symptom:** `error:1E08010C:DECODER routines::unsupported` on any signed operation.

**Root cause:** GMGN CLI uses `crypto.createPrivateKey(pem)` which expects PEM format, not base58.


## Pitfall 3: Wallet Binding Mismatch

**Symptom:** `AUTH_SIGNATURE_INVALID` even with correct PEM key.

**Root cause:** The API key is bound to a different wallet than the private key.

**Fix:** Check binding with `gmgn-cli portfolio info`. The SOL wallet must match the private key's derived address. Rebind at https://gmgn.ai/ai.

## Pitfall 4: tip-fee Required for Strategy Orders

**Symptom:** `tip_fee is required when condition_orders is provided` or similar.

**Fix:** Always include `--tip-fee 0.0001` (or higher) for SOL chain strategy orders.

## Pitfall 5: smart_trade Requires buy_low

**Symptom:** `condition_orders must contain exactly one buy_low entry`

**Root cause:** `--order-type smart_trade` expects a full trade lifecycle including entry. For post-buy TP/SL, use `--order-type limit_order` instead.

## Pitfall 6: TP check-price Validation

**Symptom:** `limit order take profit check price less than open price`

**Root cause:** For take_profit, `check-price` must be HIGHER than `open-price`. For stop_loss, it must be LOWER.

## Pitfall 7: Orders Disappear After Position Closes

**Symptom:** Strategy orders show in history as "canceled" after selling.

**Root cause:** When a position is fully closed (by TP, SL, or manual sell), all related strategy orders are auto-canceled. This is expected behavior.

## Pitfall 8: Old condition-orders Create Ghost Orders

**Symptom:** `order strategy list` shows orders with wrong amounts (e.g., 136399786273 vs 136399).

**Root cause:** The original swap's `--condition-orders` creates low-priority server orders that persist even after manual strategy orders are created.

**Fix:** Cancel old orders by ID, or let them auto-cancel when position closes.

## Pattern: Auto-Trader Architecture

```
1. Scan (gmgn-cli market signal) → pre-filter
2. Deep dive (token info + security + RugCheck) → score
3. Execute buy (gmgn-cli swap) → get output_amount
4. Calculate entry_price = input_lamports / output_amount
5. Create SL (order strategy create --sub-order-type stop_loss)
6. Create TP (order strategy create --sub-order-type take_profit)
7. Track position (save to positions.json)
8. Monitor & learn (check closed positions, analyze wins/losses)
```

## Pattern: Trade Lessons (Learn from Losses)

When a position closes at a loss, analyze:
1. Holder concentration (T10, Top1/Top5 from RugCheck)
2. Bundler/bot activity
3. Dev behavior (sold? serial deployer?)
4. Volume trends (sells > buys?)
5. What warning signs were missed

Send educational summary to user via Telegram bot.
