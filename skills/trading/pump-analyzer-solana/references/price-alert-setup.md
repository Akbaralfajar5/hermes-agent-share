# Price Alert Setup Pattern

When user asks "kasih tau kalau turun ke $XXK" or "alert me at support level", set up automated price monitoring with Hermes cronjobs.

## Pattern (from session: Goyim token)

### 1. Create Simple Alert Checker Script

```python
#!/usr/bin/env python3
"""
Simple price alert - Check via cronjob
"""
import sys

# Alert levels (market cap in USD)
ALERTS = {
    "$380K (Primary Entry)": 380000,
    "$350K (Secondary Entry)": 350000,
    "$320K (Strong Support)": 320000,
    "$280K (Major Support)": 280000,
    "$240K (Stop Loss Zone)": 240000,
}

LAST_ALERT_FILE = "/home/ubuntu/pump-monitor/token_last_price.txt"
CA = "TOKEN_CA_HERE"

def get_last_price():
    try:
        with open(LAST_ALERT_FILE, 'r') as f:
            return float(f.read().strip())
    except:
        return 999999  # Start high

def save_price(price):
    with open(LAST_ALERT_FILE, 'w') as f:
        f.write(str(price))

# Accept price as argument (cronjob will fetch and pass it)
if len(sys.argv) > 1:
    current_price = float(sys.argv[1])
else:
    print("Usage: python3 check-price.py <current_price>")
    sys.exit(0)

last_price = get_last_price()

# Check if crossed any alert level (going down)
for level_name, target in sorted(ALERTS.items(), key=lambda x: x[1], reverse=True):
    if last_price > target >= current_price:
        # Crossed this level!
        print(f"ALERT:{level_name}:{current_price}")
        save_price(current_price)
        sys.exit(0)

# No alert, just update price
save_price(current_price)
print(f"NO_ALERT:{current_price}")
```

### 2. Create Cronjob with Fetch + Check Logic

```bash
hermes cronjob create \
  --name "Token Price Alert Monitor" \
  --schedule "every 2m" \
  --prompt "
Monitor token price and alert when it reaches support levels.

Steps:
1. Fetch current market cap from RugCheck API
2. Check if price crossed any alert level
3. If alert triggered, send notification

\`\`\`bash
# Fetch current price
CA=\"TOKEN_CA_HERE\"
PRICE=\$(curl -s \"https://api.rugcheck.xyz/v1/tokens/\${CA}/report\" | jq -r '.totalMarketLiquidity // 0' 2>/dev/null)

# Check if valid price
if [ -z \"\$PRICE\" ] || [ \"\$PRICE\" = \"0\" ] || [ \"\$PRICE\" = \"null\" ]; then
  echo \"Failed to fetch price\"
  exit 0
fi

# Check alerts
RESULT=\$(python3 ~/pump-monitor/check-price.py \"\$PRICE\" 2>&1)

# If alert triggered, format and send message
if echo \"\$RESULT\" | grep -q \"^ALERT:\"; then
  LEVEL=\$(echo \"\$RESULT\" | cut -d: -f2)
  CURRENT=\$(echo \"\$RESULT\" | cut -d: -f3)
  
  # Format price
  PRICE_K=\$(echo \"scale=0; \$CURRENT / 1000\" | bc)
  
  echo \"🔔 **TOKEN PRICE ALERT!**\"
  echo \"\"
  echo \"**Level Reached:** \$LEVEL\"
  echo \"**Current Price:** \\\$\${PRICE_K}K\"
  echo \"\"
  echo \"**CA:**\"
  echo \"\\\`\${CA}\\\`\"
  echo \"\"
  echo \"**QUICK ACTION:**\"
  echo \"Trade: https://pump.fun/\${CA}\"
  echo \"Chart: https://dexscreener.com/solana/\${CA}\"
  echo \"\"
  echo \"⚠️ **Verify volume & holders before entry!**\"
fi
\`\`\`
"
```

### 3. Test Manually

```bash
# Test with different prices to verify logic
python3 ~/pump-monitor/check-price.py 433000  # Above all alerts → NO_ALERT
python3 ~/pump-monitor/check-price.py 375000  # Below $380K → ALERT
python3 ~/pump-monitor/check-price.py 375000  # Same level again → NO_ALERT (already alerted)
python3 ~/pump-monitor/check-price.py 315000  # Below $320K → ALERT (new level)
```

## Key Design Decisions

### Why Simple Script + Cronjob (Not Long-Running Process)

**Tried:** Long-running Python script with while loop
**Problem:** 
- Hard to debug (no output visible)
- Crashes silently
- Resource leak over time
- Can't see what's happening

**Solution:** Simple script + cronjob
**Benefits:**
- Each run is independent (no state leaks)
- Cronjob logs visible in Hermes
- Easy to test manually
- Automatic restart if fails
- Can see exactly what's happening

### Why RugCheck API (Not Pump.fun)

**Pump.fun API:** Returns inconsistent data, sometimes blocked by Cloudflare
**RugCheck API:** Reliable, consistent, no auth needed, includes market cap directly

### Why "Crossed Level" Logic (Not "Below Level")

**Bad:** Alert every time price is below $380K
**Result:** Spam alerts every 2 minutes while price is at $370K

**Good:** Alert only when price CROSSES from above to below $380K
**Result:** One alert per level, then silent until next level

**Implementation:**
```python
if last_price > target >= current_price:
    # Crossed from above to below
    alert()
```

### Why Multiple Alert Levels (Not Just One)

User wants to know about:
1. Primary entry ($380K) - best risk/reward
2. Secondary entry ($350K) - still good
3. Strong support ($320K) - better entry
4. Major support ($280K) - best entry
5. Stop loss zone ($240K) - don't enter, wait for bounce

Each level has different entry setup (SL, TP, position size), so separate alerts needed.

## Alert Message Format

**Good format (from session):**
```
🔔 **TOKEN PRICE ALERT!**

**Level Reached:** $380K (Primary Entry)
**Current Price:** $380K

**CA:**
`9S8edqWxoWz5LYLnxWUmWBJnePg35WfdYQp7HQkUpump`

**QUICK ACTION:**
Trade: https://pump.fun/[CA]
Chart: https://dexscreener.com/solana/[CA]

⚠️ **Verify volume & holders before entry!**
```

**Why this format:**
- Emoji for attention (🔔)
- Level name for context
- CA in code block for easy copy
- Direct links for quick action
- Warning to verify (prevent FOMO)

**Bad format:**
```
Price is now $380K
```
(No context, no action, no links)

## Troubleshooting

### No Alerts Received

1. Check cronjob status: `hermes cronjob list`
2. Check if price actually reached level (verify on pump.fun)
3. Check last price file: `cat ~/pump-monitor/token_last_price.txt`
4. Test script manually: `python3 check-price.py 375000`

### False Alerts

1. API might return wrong data (RugCheck vs pump.fun discrepancy)
2. Verify on pump.fun manually before acting
3. Add validation: reject if price change >50% in 2 minutes (likely API error)

### Alert Spam

1. Check "crossed level" logic is working (should only alert once per level)
2. Check last_price file is being saved correctly
3. Add cooldown: don't alert same level within 10 minutes

## User Management Commands

**Stop alerts:**
```bash
hermes cronjob remove [job_id]
```

**Pause alerts:**
```bash
hermes cronjob pause [job_id]
```

**Resume alerts:**
```bash
hermes cronjob resume [job_id]
```

**Check status:**
```bash
hermes cronjob list
```

Or user can just say: "Stop [token] alerts" and agent handles it.

## When to Use This Pattern

✅ **Use when:**
- User asks "kasih tau kalau turun ke $XXK"
- User asks "alert me at support level"
- User wants to wait for specific price before entry
- User wants hands-off monitoring

❌ **Don't use when:**
- User wants real-time tick-by-tick updates (use WebSocket dashboard instead)
- User wants to monitor 10+ tokens (too many cronjobs, use dashboard)
- User wants complex conditions (use full bot with screening logic)

## Related Patterns

- **Dashboard monitoring:** For real-time visual feed (see `scripts/deploy-dashboard.sh`)
- **Jupiter limit orders:** For automated TP/SL execution (see "Exit Strategy" section)
