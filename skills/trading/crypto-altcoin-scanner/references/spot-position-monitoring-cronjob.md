# Spot Position Monitoring via Cronjob

## Purpose
Monitor multiple spot positions (Binance + MEXC) and alert on SL/TP hits or significant moves.

## Pattern
Add spot positions to existing cronjob rather than creating new ones. Consolidate monitoring into a single job that checks all positions.

## Implementation (May 2026)

### Cronjob Structure
```
Name: Spot Monitor: [COIN1] + [COIN2] + [COIN3] + [COIN4]
Schedule: every 120m (2 hours)
Enabled toolsets: web, terminal
```

### Prompt Template
```
Monitor N spot positions and alert on significant moves:

POSITION 1: [SYMBOL] on [EXCHANGE]
- Entry: $X.XX
- Position: $XXX (XX.XX tokens)
- SL: $X.XX (-X.XX%)
- TP1: $X.XX (+X.XX%) - close 50%
- TP2: $X.XX (+X.XX%) - close remaining 50%
- Alert if: Price hits SL, TP1, or TP2

[Repeat for each position]

Tasks:
1. Check current prices for all positions
2. For each position: Check if price hit SL, TP1, or TP2
3. Calculate current P&L
4. Report ONLY if there's an alert or significant move

Use Binance API:
```bash
curl -sf "https://api.binance.com/api/v3/ticker/price?symbol=MOVRUSDT"
```

For MEXC, use web scraping or skip if API unavailable.

Report format:
```
🚨 SPOT ALERT

[Coin] [Current Price]
Entry: $X.XX | Current: $X.XX
P&L: +X.XX% ($+XX.XX)
Status: [Approaching TP1 / Hit SL / etc]
```
```

### Alert Thresholds
- 🚨 **SL HIT**: Price <= SL price
- 🎯 **TP1 HIT**: Price >= TP1 price
- 🎯 **TP2 HIT**: Price >= TP2 price
- ⚠️ **APPROACHING SL**: Price within 5% of SL
- ✅ **NEAR TP1**: Price within 5% of TP1

### Python Monitoring Script
```python
import requests
from datetime import datetime

# Get current price
resp = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT", timeout=10)
current_price = float(resp.json()['price'])

# Calculate P&L
pnl_pct = ((current_price - entry_price) / entry_price) * 100
pnl_usd = capital * (pnl_pct / 100)

# Check alerts
if current_price <= sl_price:
    print("🚨 ALERT: SL HIT!")
elif current_price >= tp2_price:
    print("🎯 ALERT: TP2 HIT!")
elif current_price >= tp1_price:
    print("🎯 ALERT: TP1 HIT!")
elif current_price <= sl_price * 1.05:
    print("⚠️ WARNING: Approaching SL (within 5%)")
elif current_price >= tp1_price * 0.95:
    print("✅ NEAR TP1 (within 5%)")
else:
    print("✅ Position OK")
```

### Adding New Positions
Use `cronjob update` to modify existing monitoring job:

```python
# Example: Adding MOVR and BICO to existing UAI + GOBLIN monitor
cronjob(action="update", 
        job_id="a9cb40f0ecb7",
        name="Spot Monitor: UAI + GOBLIN + MOVR + BICO",
        prompt="[Updated prompt with 4 positions]")
```

### Manual Check Command
```bash
python3 << 'EOF'
import requests

# MOVR
movr_resp = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=MOVRUSDT", timeout=10)
movr_price = float(movr_resp.json()['price'])
movr_entry = 2.648
movr_capital = 225
movr_pnl_pct = ((movr_price - movr_entry) / movr_entry) * 100
movr_pnl_usd = movr_capital * (movr_pnl_pct / 100)

print(f"MOVR: ${movr_price:.4f} | P&L: {movr_pnl_pct:+.2f}% (${movr_pnl_usd:+.2f})")
EOF
```

## Pitfalls

### MEXC API Unavailable
MEXC doesn't have reliable public API. Options:
1. Skip MEXC positions in automated monitoring
2. Use web scraping (fragile, breaks often)
3. Manual check via exchange website

### Missing Entry Price
If entry price unknown:
- Check exchange order history
- Ask user for entry price
- Set entry = current price (start tracking from now)

### Position Size Calculation
For accurate P&L:
```python
# Method 1: From capital
quantity = capital / entry_price

# Method 2: From quantity (if known)
capital = quantity * entry_price
```

### Silent Runs
Cronjob should return `[SILENT]` if no alerts to avoid spam. Only report when:
- SL/TP hit
- Approaching SL/TP (within 5%)
- Significant move (>10% in 2h for volatile coins)

## Related
- See `binance-futures-trading` skill for futures position monitoring
