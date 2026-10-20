# Entry Zone Calculation for Pumped Tokens

Use when user asks "entry di berapa?" or "good entry level?" for tokens already on pump.fun bonding curve.

## When to Use

Token is on pump.fun bonding curve, has already pumped significantly from launch, and the user wants specific buy zones.

## Core Method: Launch → Current Fibonacci

### Step 1: Get Current Metrics

From DexScreener pair data:
- `priceUsd` — current price
- `priceChange.h24` — all-time change (for tokens < 24h old, this IS the launch price)
- `priceChange.h1` — 1h change for natural support level
- `priceChange.m5` — 5m change for momentum check
- `txns.m5.buys / sells` — short-term B/S ratio

### Step 2: Calculate Launch Price

```python
launch_price = current_price / (1 + chg_24h / 100)
```

For pump.fun tokens < 24h old, the 24h change IS the total pump from launch.

### Step 3: Fibonacci Retracement

```python
high = current_price
low = launch_price
diff = high - low

fib_levels = {
    "S1 (Aggressive)":  0.236,  # shallow dip, first buy zone
    "S2 (Balanced)":    0.382,  # standard pullback, main entry ⭐
    "S3 (Safe)":        0.5,    # half retrace, last entry
    "Emergency":        0.618,  # deep retrace
    "Broken":           0.786,  # max pullback, below this = dead
}

for label, fib in fib_levels.items():
    entry_price = high - diff * fib
    entry_fdv = current_fdv * (entry_price / current_price)
```

### Step 4: Position Sizing

```
S1: 40% — aggressive first entry
S2: 40% — main entry ⭐ (best risk/reward)
S3: 20% — last add

Stop Loss: 15% below S3 (break = momentum dead)
```

### Step 5: Momentum Status Check

```python
chg_5m = priceChange.m5
bs_5m = buys_5m / max(sells_5m, 1)

if chg_5m > 10 and bs_5m > 2:
    status = "⛔ MASIH PUMPING KERAS — WAIT"
elif chg_5m > 3:
    status = "⚠️ MASIH NAIK — TUNGGU KOREKSI"
elif chg_5m < -2:
    status = "📉 SUDAH KOREKSI — pantau support"
else:
    status = "✅ SIDEWAYS — bisa mulai akumulasi"
```

## Output Format

Always present as a clean table + risk management:

```
| Level | Harga | FDV | Drop | Alokasi |
|-------|-------|-----|------|---------|
| S1 | $X | $X | -X% | 40% |
| S2 ⭐ | $X | $X | -X% | 40% |
| S3 | $X | $X | -X% | 20% |

Stop Loss: $X (below S3)
TP1: +50%, TP2: +100%, TP3: +200%
```

## Pitfalls

- **Don't calculate from DexScreener "launch price"** — pump.fun bonding curve tokens don't have an explicit launch price in the API. Derive it from 24h change.
- **Bonding curve LP = $0 is NORMAL** — don't flag it as "thin LP." The bonding curve IS the liquidity mechanism on pump.fun.
- **Top1 30-45% on pump.fun is usually the bonding curve address** — don't flag as whale risk unless it's a regular wallet.
- **Tokens < 2h old have unreliable support** — fib levels are approximate. Use wider stops.
