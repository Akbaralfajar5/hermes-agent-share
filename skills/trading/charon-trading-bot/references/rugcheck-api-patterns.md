# RugCheck API Patterns & Pitfalls

## API Endpoint

```
GET https://api.rugcheck.xyz/v1/tokens/{mint}/report
```

Returns JSON with token security analysis. Key fields for trading bot scoring:

```json
{
  "topHolders": [{"address": "...", "pct": 12.5, "amount": "...", "owner": "...", "insider": false}],
  "risks": [{"name": "Low Liquidity"}, "High Concentration", {"name": "Mint Authority"}],
  "mint": "...",
  "tokenProgram": "...",
  "creator": "...",
  "creatorBalance": 0
}
```

## Critical Pitfall: `risks` Array Mixed Types

**The `risks` array can contain BOTH dicts AND plain strings.** This is not documented.

```python
# ❌ BREAKS when risks item is a plain string
rugcheck_risks = [r.get("name", "") for r in rugcheck.get("risks", [])]
# → AttributeError: 'str' object has no attribute 'get'

# ✅ CORRECT — handle both types
rugcheck_risks = [
    r.get("name", "") if isinstance(r, dict) else str(r)
    for r in rugcheck.get("risks", [])
]
```

This error is deceptive because:
- It only fires for SOME tokens (those with string-type risk items)
- It survives basic type guards on the parent `rugcheck` dict (the dict itself is fine, its nested array items are the problem)
- Clearing `.pyc` cache doesn't help (it's not a caching issue)
- Basic error message `'str' object has no attribute 'get'` doesn't indicate which `.get()` call failed

**Debug technique**: Use `exc_info=True` in the except block to get the full traceback with line numbers. The basic error message is misleading — it points to the symptom, not the cause.

```python
# ❌ Basic error logging — misleading
except Exception as e:
    log.error(f"Analysis error: {e}")

# ✅ Full traceback — shows exact line and nested cause
except Exception as e:
    log.error(f"Analysis error: {e}", exc_info=True)
```

## `topHolders` Array

Always present as a list of dicts. Each dict has:
- `pct` — percentage (0-100 scale, NOT 0-1)
- `amount` — raw token amount (string)
- `uiAmount` — human-readable amount
- `owner` — wallet address
- `insider` — boolean
- `address` — token account address

Sort by `pct` descending to find top holder concentration:

```python
holders = rugcheck.get("topHolders", [])
if holders:
    sorted_h = sorted(holders, key=lambda h: h.get("pct", 0), reverse=True)
    top1_pct = sorted_h[0].get("pct", 0)  # Already 0-100, do NOT multiply by 100
```

**Pitfall**: `pct` is already 0-100. Do NOT multiply by 100 (was a previous bug that showed 2069% for Top1 holder).

## Defensive Coding Pattern for External APIs

When consuming external API responses in scoring/analysis functions, always add type guards at the function entry:

```python
def analyze_token(mint, signal, info, security, rugcheck, ...):
    try:
        # Type guards — external APIs can return unexpected types
        if not isinstance(signal, dict): signal = {}
        if not isinstance(info, dict): info = {}
        if not isinstance(security, dict): security = {}
        if not isinstance(rugcheck, dict): rugcheck = {}
        # ... rest of analysis
```

This prevents cascading failures when GMGN CLI returns a string/list instead of expected dict (e.g., malformed JSON, API changes, rate limit responses).

## GMGN CLI Swap Notes

### `--condition-orders` for TP/SL

```bash
gmgn-cli swap --chain sol \
  --input-token SOL --output-token <mint> \
  --amount <lamports> --from <wallet> \
  --priority-fee 100000 --tip-fee 100000 \
  --slippage 30 \
  --condition-orders '[{"order_type":"profit_stop","side":"sell","price_scale":"30","sell_ratio":"100"},{"order_type":"loss_stop","side":"sell","price_scale":"50","sell_ratio":"100"}]'
```

**Known issues** (GMGN CLI limitations, not code bugs):
- `No strategy_order_id in swap response` — TP/SL may not be set on GMGN side. This warning appears on every swap.
- `Swap tx: unknown` — transaction hash not returned. Cannot verify on-chain.
- `--expire-in` causes phantom orders — do NOT use.
- `--priority-fee` and `--tip-fee` are REQUIRED when using `--condition-orders`.

### `--chain` Position

`--chain` must be on the SUBCOMMAND, not global:

```bash
# ❌ Wrong
gmgn-cli --chain sol swap ...

# ✅ Correct
gmgn-cli swap --chain sol ...
```

## Trading Bot Notification Patterns

User preference for Solana meme trading bots:
- **Silent analysis** — do NOT send analysis messages to Telegram for every token scanned
- **Notify only on BUY/SELL** — one concise message per trade execution
- **No startup messages** — don't send "Bot started!" notifications
- **Menu should match auto-scan** — manual scan button triggers same scan+analyze+buy flow as automatic loop

Example buy notification (concise):
```
🛒 {SYMBOL} dibeli!
Score: {score} | MC: ${mc}
Amount: {amount} SOL
TP: +30% | SL: -50%
Strategy: {id or 'N/A'}
```
