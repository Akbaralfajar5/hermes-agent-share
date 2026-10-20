# Duplicate Process Prevention & TX Verification

**Session**: May 10, 2026 - brainrot.dog $ROT minting  
**Problem**: Script claimed 10/10 slots minted but only 8 confirmed on-chain  
**Root causes**: (1) Duplicate script instances running, (2) MCP relayer returns TX hash even when TX reverts

## Symptoms

```
[2026-05-10 10:32:21] ✅ SUCCESS! Minted slot #7 | TX: 0xd641ba...67dd4a
[2026-05-10 10:34:40] ✅ SUCCESS! Minted slot #8 | TX: 0x56b1fc...c451e8
[2026-05-10 10:34:58] ✅ SUCCESS! Slot #4 minted  # ← Duplicate instance
[2026-05-10 10:35:52] ✅ SUCCESS! Slot #4 minted  # ← Still stuck at slot 4
[2026-05-10 10:36:47] ✅ SUCCESS! Slot #4 minted
[2026-05-10 10:37:44] ✅ SUCCESS! Slot #4 minted
[2026-05-10 10:38:37] ✅ SUCCESS! Minted slot #9 | TX: 0x66743a...7760b
[2026-05-10 10:39:40] ✅ SUCCESS! Minted slot #10 | TX: 0x106ee1...a286a8
```

**Actual on-chain state**:
```
$ROT balance: 204,000 ROT
slots used: 8/10
slots remaining: 2
```

**Diagnosis**:
- 2 script instances running (one stuck at slot 4, one progressing)
- Last 2 TXs (slot #9, #10) got TX hashes but reverted on-chain
- No lock file to prevent duplicate launches

## Solution 1: Lock File Pattern

```bash
#!/bin/bash
# Single-instance miner with lock file

LOCK_FILE="/tmp/rot-miner.lock"
LOG_FILE="$HOME/rot-minter-new/mining.log"

# Check if already running
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Miner already running (PID: $PID)"
        exit 1
    else
        echo "Stale lock file found, removing..."
        rm -f "$LOCK_FILE"
    fi
fi

# Create lock file with current PID
echo $$ > "$LOCK_FILE"

# Cleanup on exit (normal or signal)
trap "rm -f $LOCK_FILE" EXIT

# Run miner logic...
cd ~/rot-minter-new
export $(grep -v '^#' .env | xargs)

echo "🚀 ROT Auto Miner Started (PID: $$)" | tee -a "$LOG_FILE"
# ... rest of mining loop
```

**Key points**:
- Check for existing lock file + verify PID still running
- Remove stale locks (PID no longer exists)
- Use `trap` to cleanup lock on exit (Ctrl+C, kill, normal exit)
- Log PID in startup message for debugging

## Solution 2: On-Chain Verification After "Success"

**Problem**: MCP relayer returns TX hash immediately, but TX can revert later (nonce conflict, gas spike, contract revert).

**Pattern**:
```bash
while [ $minted_count -lt $MAX_SLOTS ]; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] Attempting mint #$((minted_count + 1))/$MAX_SLOTS..." | tee -a "$LOG_FILE"
    
    output=$(npm run mint 2>&1)
    
    if echo "$output" | grep -q "minted 25,500"; then
        tx=$(echo "$output" | grep "tx:" | awk '{print $2}')
        
        # DON'T trust the output alone - verify on-chain
        sleep 5  # Wait for TX to be mined
        
        balance=$(cast call $TOKEN "balanceOf(address)(uint256)" $WALLET --rpc-url $RPC)
        balance_human=$(python3 -c "print(int('$balance') / 1e18)")
        
        expected_balance=$(echo "$((minted_count + 1)) * 25500" | bc)
        
        if [ "$balance_human" == "$expected_balance" ]; then
            minted_count=$((minted_count + 1))
            echo "[$timestamp] ✅ CONFIRMED on-chain! Slot $minted_count/$MAX_SLOTS | TX: $tx" | tee -a "$LOG_FILE"
            echo "[$timestamp] 💰 Balance: $balance_human ROT" | tee -a "$LOG_FILE"
            
            # Random cooldown
            cooldown=$((10 + RANDOM % 6))
            echo "[$timestamp] ⏸️  Cooldown ${cooldown}s..." | tee -a "$LOG_FILE"
            sleep $cooldown
        else
            echo "[$timestamp] ❌ TX reverted - balance unchanged (expected $expected_balance, got $balance_human)" | tee -a "$LOG_FILE"
            echo "[$timestamp] ⏳ Retrying in 25s..." | tee -a "$LOG_FILE"
            sleep 25
        fi
    else
        error=$(echo "$output" | grep -E "error:" | head -1)
        echo "[$timestamp] ❌ Failed: $error" | tee -a "$LOG_FILE"
        
        if echo "$error" | grep -qE "(500|502|503)"; then
            echo "[$timestamp] ⏳ Server error, waiting 45s..." | tee -a "$LOG_FILE"
            sleep 45
        else
            echo "[$timestamp] ⏳ Retrying in 25s..." | tee -a "$LOG_FILE"
            sleep 25
        fi
    fi
done
```

**Key points**:
- Sleep 5s after "success" to let TX be mined
- Query actual on-chain balance with `cast call`
- Compare with expected balance (previous + mint amount)
- Only increment counter if balance matches expectation
- If balance unchanged, treat as failure and retry same slot

## Verification Commands

```bash
# Check for duplicate processes
ps aux | grep -E "(auto-mine|mint-rot)" | grep -v grep

# Should show only:
# 1 bash process (auto-mine.sh)
# 1 node process (mint-rot.mjs)

# Check lock file
ls -la /tmp/rot-miner.lock
cat /tmp/rot-miner.lock  # Should show PID of running miner

# Verify on-chain state
cd ~/rot-minter-new
node -e "
const address = '0xE384866275Ab25321DC03BE915CfD6798Ef3F03e';
const response = await fetch('https://www.brainrot.dog/api/mcp', {
  method: 'POST',
  headers: { 
    'content-type': 'application/json',
    'accept': 'application/json, text/event-stream'
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: Date.now(),
    method: 'tools/call',
    params: { name: 'check_wallet', arguments: { address } }
  })
});
const text = await response.text();
const dataLine = text.split('\n').find(l => l.startsWith('data: '));
if (dataLine) {
  const payload = JSON.parse(dataLine.slice(6));
  console.log(payload.result.content[0].text);
}
"
```

## Lessons Learned

1. **Always use lock files** for long-running automated processes
2. **Never trust relayer "success" messages** - verify on-chain state
3. **Kill all instances** before restarting: `pkill -9 -f "mint-rot" && pkill -9 -f "auto-mine"`
4. **Clean up lock files** before restart: `rm -f /tmp/rot-miner.lock`
5. **Monitor process count**: `ps aux | grep mint` should show exactly 1 bash + 1 node
6. **User frustration signals**: "baru 4 yang masuk" (only 4 confirmed) = verification gap, "ada duplicate runs" = lock file missing

## Related Issues

- See `mcp-retry-patterns.md` for exponential backoff on 500/502/503 errors
- See `brainrot-dog-rot-minter.md` for full session context (RPC selection, delegation, MCP setup)
