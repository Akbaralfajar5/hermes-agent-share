# FibStruct v2 Daemon Deployment Guide

## Architecture

```
┌─────────────────────────────────────┐
│  screen session: fibstruct          │
│  ┌───────────────────────────────┐  │
│  │  fibstruct_engine.py          │  │
│  │  - Scan every 5 min           │  │
│  │  - SL/TP check every 30s      │  │
│  │  - News filter                │  │
│  │  - BTC direction filter       │  │
│  │  - Weekend filter             │  │
│  │  - Partial TP execution       │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         ↕ (watches)
┌─────────────────────────────────────┐
│  watchdog cronjob (every 5 min)     │
│  no_agent: true, script-based       │
│  - Checks if screen exists          │
│  - Restarts if dead                 │
│  - Silent when alive (exit 0)       │
│  - Reports only on restart          │
└─────────────────────────────────────┘
```

## Deployment Steps

### 1. Prepare environment
```bash
# Ensure API keys are in .env
cat ~/.hermes/.env | grep BINANCE

# Test API connection
source ~/.hermes/.env && python3 -c "
import os, hmac, hashlib, time, requests
from urllib.parse import urlencode
k = os.environ['BINANCE_API_KEY']
s = os.environ['BINANCE_SECRET_KEY']
p = {'timestamp': int(time.time()*1000), 'recvWindow': 10000}
qs = urlencode(p)
p['signature'] = hmac.new(s.encode(), qs.encode(), hashlib.sha256).hexdigest()
r = requests.get('https://fapi.binance.com/fapi/v2/account', params=p, headers={'X-MBX-APIKEY': k})
d = r.json()
print(f'Balance: {d[\"totalWalletBalance\"]} USDT')
print(f'Positions: {len([x for x in d[\"positions\"] if float(x[\"positionAmt\"]) != 0])}')
"
```

### 2. Kill any existing instances
```bash
pkill -f fibstruct_engine 2>/dev/null
sleep 1
# Verify killed
ps aux | grep fibstruct_engine | grep -v grep
# Should return nothing
```

### 3. Clear old log (prevents apparent duplication)
```bash
> /home/ubuntu/fibstruct.log
```

### 4. Start daemon in screen
```bash
screen -dmS fibstruct bash -c '
  cd /home/ubuntu
  export PYTHONUNBUFFERED=1
  source .hermes/.env
  python3 -u fibstruct_engine.py >> fibstruct.log 2>&1
'
```

### 5. Verify single process
```bash
ps aux | grep fibstruct_engine | grep -v grep
# Should show exactly 3 lines:
# 1. SCREEN -dmS fibstruct
# 2. bash -c ...
# 3. python3 -u fibstruct_engine.py
```

### 6. Create watchdog cronjob
```bash
# Save watchdog script to ~/.hermes/scripts/fibstruct_watchdog.sh
# Then create cronjob:
# cronjob(action='create', no_agent=True, script='fibstruct_watchdog.sh', schedule='*/5 * * * *')
```

## Watchdog Script

```bash
#!/bin/bash
# ~/.hermes/scripts/fibstruct_watchdog.sh
# Silent when daemon alive, reports only on restart

if ! screen -ls | grep -q fibstruct; then
    echo "$(date '+%H:%M:%S') ⚠️ FibStruct daemon DEAD — restarting..."
    > /home/ubuntu/fibstruct.log  # Clear log on restart
    screen -dmS fibstruct bash -c 'cd /home/ubuntu && export PYTHONUNBUFFERED=1 && source .hermes/.env && python3 -u fibstruct_engine.py >> fibstruct.log 2>&1'
    sleep 3
    if ps aux | grep -q fibstruct_engine; then
        echo "✅ Daemon restarted"
    else
        echo "❌ Restart failed"
    fi
else
    exit 0  # Silent when alive — cronjob won't report
fi
```

## Common Operations

### Check daemon status
```bash
screen -ls | grep fibstruct
tail -5 /home/ubuntu/fibstruct.log
```

### View live logs
```bash
tail -f /home/ubuntu/fibstruct.log
```

### Restart daemon (clean)
```bash
pkill -f fibstruct_engine 2>/dev/null
sleep 1
> /home/ubuntu/fibstruct.log
screen -dmS fibstruct bash -c 'cd /home/ubuntu && export PYTHONUNBUFFERED=1 && source .hermes/.env && python3 -u fibstruct_engine.py >> fibstruct.log 2>&1'
```

### Stop daemon completely
```bash
screen -S fibstruct -X quit
pkill -f fibstruct_engine
```

### Reattach to screen (interactive)
```bash
screen -r fibstruct
# Detach: Ctrl+A, then D
```

## Pitfalls

### PITFALL: Log duplication on restart
If you restart without clearing the log file, old content persists and output APPEARS doubled. Always `> /home/ubuntu/fibstruct.log` before restart. Quick diagnosis: `tail -30 fibstruct.log | uniq`.

### PITFALL: Multiple instances
Always `pkill -f fibstruct_engine` before restart. Multiple instances cause duplicate log entries AND duplicate order attempts. Verify with `ps aux | grep fibstruct_engine | grep -v grep` — should show exactly 3 lines.

### PITFALL: Engine reads API keys from env vars
The engine uses `os.environ.get('BINANCE_API_KEY')`. When API keys change, update `~/.hermes/.env` only — no need to edit the engine file. Test: `source ~/.hermes/.env && python3 -c "import os; print(os.environ.get('BINANCE_API_KEY', 'NOT SET'))"`.

### PITFALL: Cronjob script parameter
The `script` parameter in cronjob MUST be a filename (relative to `~/.hermes/scripts/`), NOT inline code. Passing inline bash like `#!/bin/bash\nif...` causes "Script not found" because the scheduler treats it as a path. Always save to file first.

### PITFALL: PYTHONUNBUFFERED
Without `PYTHONUNBUFFERED=1`, Python buffers stdout in non-TTY mode (screen sessions). Log output appears delayed or missing. Always set the env var or use `python3 -u`.

## Config Reference (FibStruct v2)

| Parameter | Value |
|-----------|-------|
| MARGIN_PCT | 0.05 (5%) |
| MAX_POSITIONS | 3 |
| MAX_SAME_DIRECTION | 3 |
| Min confluence score | 4/5 |
| Min R:R | 1:2 |
| SL/TP check interval | 30s |
| Signal scan interval | 5 min |
| Volume filter | $50M minimum |
| Weekend | Monitor only, no new entries |
| News check | @marketfeed + CryptoCompare |
| BTC filter | 4H/1H direction required |
| Partial TP | 30% TP1, 40% TP2, 30% TP3 |
