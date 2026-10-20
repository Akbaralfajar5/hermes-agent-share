---
name: superagent-governor
description: Spend Governor — circuit breaker for all on-chain transactions. Cap per-tx/daily/session, auto-HALT, MEV protection via private relay. SUPERAGENT v4.0.
---

# superagent-governor — Spend Governor + MEV

Circuit breaker untuk SEMUA transaksi yang nyentuh dana. Bukan sekadar prompt safety — di-enforce di kode.

Scripts: `~/superagent-v4/skills/hermes/scripts/{governor,mev}.py`
Reference: `~/superagent-v4/skills/hermes/references/governor.md`

## Governor Flow

Setiap tx harus lewat:
```
simulate → gas sanity check → daily cap check → session cap check
→ slippage guard → kill-switch check → (MEV: private relay) → sign → broadcast
```

Kalau salah satu gate gagal → tx ditolak dengan reason code.

## Quick Usage

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/superagent-v4/skills/hermes/scripts"))
from governor import Governor

gov = Governor(db=os.environ.get("HERMES_GOVERNOR_DB", "~/.hermes/governor.db"))

# Check before sending
ok, reason = gov.check_tx(
    value_usd=150,
    gas_estimate_wei=100000,
    slippage_pct=2.0,
    wallet="0x...your..."
)
if not ok:
    print(f"BLOCKED: {reason}")  # e.g. "daily cap exceeded ($2100/$2000)"
    return

# Record after successful tx
gov.record_tx(tx_hash="0x...", value_usd=150, wallet="0x...your...")
```

## Cap Configuration

```bash
HERMES_MAX_TX_USD=500        # max per-tx value
HERMES_DAILY_CAP_USD=2000    # max 24h cumulative
HERMES_SESSION_CAP_USD=1000  # max per-session cumulative
HERMES_MAX_SLIPPAGE_PCT=5    # reject swaps above this
HERMES_MAX_GAS_MULTIPLE=4    # gas > 4x baseline = HALT
HERMES_MAX_TX_PER_MIN=12     # runaway protection
HERMES_REQUIRE_SIM=1         # 1=require simulation before sign
```

## Emergency Kill-Switch

```bash
touch ~/.hermes/HALT    # Governor checks this → all tx rejected immediately
rm ~/.hermes/HALT       # Resume
```

## MEV Protection

Swap & snipe otomatis lewat private relay (Flashbots/MEV Blocker untuk Ethereum):

```bash
HERMES_PRIVATE_RPC=     # custom private relay endpoint (kosong = default Flashbots)
```

```python
from mev import send_private
tx_hash = send_private(
    signed_tx=raw_signed_tx,
    rpc_url=os.environ.get("RPC_EVM_ETHEREUM"),
    private_relay_url=os.environ.get("HERMES_PRIVATE_RPC")
)
# Falls back to public mempool WITH WARNING if private relay unavailable
```

## Hard Limits (Self-Improve CANNOT Touch)

- Governor config & cap values → FROZEN
- Kill-switch mechanism → FROZEN
- `governor.py`, `mev.py`, `security.md` → FROZEN
