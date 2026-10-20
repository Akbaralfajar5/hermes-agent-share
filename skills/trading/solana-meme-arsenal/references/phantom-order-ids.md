# Phantom Order IDs — GMGN API Bug

## Problem
`order strategy create` returns `{"order_id": "xxx", "is_update": false}` (HTTP 200) but the order does NOT actually exist on GMGN servers. Querying `order get --order-id xxx` returns HTTP 404 "order not found". The strategy list also doesn't show it.

## When It Happens
- Most common for **SL orders** created immediately after TP orders (race condition)
- Can happen for any order type but SL is most affected
- Timing: creating SL within 1 second of TP increases phantom rate

## Detection
```bash
# After creating each order, verify it exists:
gmgn-cli order strategy list --chain sol --group-tag LimitOrder --raw
# Parse JSON, check if order_id is in the list
```

## Prevention (Auto-Trader)
```python
def _verify_order_exists(order_id):
    """Verify an order actually exists on GMGN (not just returned order_id)"""
    import time as _t
    _t.sleep(2)  # Wait for order to propagate
    raw = run_cmd(f"gmgn-cli order strategy list --chain {CHAIN} --group-tag LimitOrder --raw")
    try:
        data = json.loads(raw)
        for o in data.get("list", []):
            if o.get("order_id") == order_id:
                return True
    except:
        pass
    return False
```

## Fix
1. Wait 2-3 seconds after TP creation before creating SL
2. Verify each order with `order strategy list` after creation
3. If phantom detected → retry SL creation with 3s delay
4. Report `PHANTOM: <order_id>` instead of `✅` in notifications

## Real Example (June 16, 2026)
- CRYPTO token buy succeeded
- TP created: order_id `2893370e-ffd9-48...` → verified ✅
- SL created: order_id `e1e85335-777b-4e...` → returned success BUT 404 on query
- Manual SL creation needed: order_id `b10958db-118c-4d...` → verified ✅
