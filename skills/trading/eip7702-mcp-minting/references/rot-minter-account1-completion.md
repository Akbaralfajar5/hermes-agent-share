# ROT Minter Account #1 Completion Session (May 10, 2026)

## Context
- User: the user
- Project: brainrot.dog $ROT token
- Wallet: 0xE384866275Ab25321DC03BE915CfD6798Ef3F03e
- Initial state: 4/10 slots minted (102K ROT)
- Goal: Complete remaining 6 slots to reach 10/10 (255K ROT)

## Problem
Script was "retry terus" (retrying infinitely) on MCP 500/502/503 errors with no progress.

## Root Causes Identified

### 1. Unlimited Retries
- Config had `MAX_RETRIES=0` (unlimited)
- Fixed delay `RETRY_DELAY_MS=15000` hammered failing endpoint
- Script never gave up, just kept retrying same error every 15s

### 2. No Exponential Backoff
- Every retry used same 15s delay
- Didn't give overloaded MCP server time to recover
- Contributed to server staying overloaded

### 3. Duplicate Process Spawning
- Multiple script instances running simultaneously
- Caused nonce collisions and incorrect slot counting
- Logs showed duplicate "🚀 ROT Auto Miner Started" headers
- Balance stuck despite "success" messages

### 4. TX Success ≠ On-Chain Confirmation
- MCP relayer returned TX hash + "SUCCESS" even when TX reverted
- Script trusted relayer response without verifying on-chain state
- Result: Script thought it minted 10 slots, but only 4 actually confirmed

## Solutions Implemented

### 1. Exponential Backoff
```javascript
// In mint-rot.mjs callToolWithRetry()
const backoffDelay = retryDelayMs * Math.pow(2, attempt - 1);
// Progression: 20s → 40s → 80s → 160s → 320s
```

### 2. Bounded Retries
```bash
# In .env
MAX_RETRIES=5  # Changed from 0 (unlimited)
RETRY_DELAY_MS=20000  # Increased from 15000
```

### 3. Smart Cooldown in Shell Script
```bash
# In auto-mine.sh
if echo "$error" | grep -qE "(500|502|503)"; then
    echo "Server error, waiting 30s..."
    sleep 30
else
    echo "Retrying in 20s..."
    sleep 20
fi

# After success
cooldown=$((8 + RANDOM % 5))  # Random 8-12s
sleep $cooldown
```

### 4. Lock File Pattern
```bash
# In mine-single.sh
LOCK_FILE="/tmp/rot-miner.lock"

if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Miner already running (PID: $PID)"
        exit 1
    fi
fi

echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT
```

### 5. On-Chain Verification (Recommended but not implemented in this session)
```bash
# After "success" message, verify actual state
balance=$(cast call $TOKEN "balanceOf(address)(uint256)" $WALLET --rpc-url $RPC)
if [ "$balance" -eq "$expected_balance" ]; then
    echo "✅ CONFIRMED on-chain"
    minted_count=$((minted_count + 1))
else
    echo "❌ TX reverted - balance unchanged"
    # Don't increment counter, retry this slot
fi
```

## Results

### First Run (10:24 - 10:39)
- Script claimed: 10/10 slots (255K ROT)
- Actual on-chain: 4/10 slots (102K ROT)
- 6 TXs reverted despite "SUCCESS" logs

### Second Run (10:42 - 11:51)
- Multiple duplicate processes spawned
- Logs showed overlapping attempts
- Balance stuck at 102K → 204K → 229.5K
- Final: 9/10 slots confirmed

### Manual Completion (11:52)
- Killed all duplicate processes
- Single manual mint: `npm run mint`
- TX: `0xb4b294ab8ebf071b39df5cd0d1a8ea81ad6fcf09b1fa79da990c14d3963731d1`
- Final state: 10/10 slots (255K ROT) ✅

## Key Learnings

### User Frustration Signals
- "retry terus" = immediate action needed, not "wait it out"
- "baru 4 yang masuk" when script claims 10 = verification gap
- "STOP" repeatedly = use nuclear options immediately

### Production Miner Requirements
1. **Lock file** to prevent duplicate instances
2. **Exponential backoff** (not fixed delay)
3. **Bounded retries** (not unlimited)
4. **On-chain verification** after every "success"
5. **Smart cooldown** (longer for server errors, random jitter for success)

### MCP Relayer Behavior
- Returns TX hash immediately upon submission
- Does not wait for TX confirmation
- "SUCCESS" message ≠ on-chain confirmation
- TXs can revert due to:
  - Nonce collisions (duplicate processes)
  - Gas issues
  - Contract state changes
  - Relayer queue resets (409 errors)

### Shell Script Patterns
```bash
# Detect server errors
if echo "$error" | grep -qE "(500|502|503)"; then
    # Longer wait
fi

# Random jitter
cooldown=$((8 + RANDOM % 5))

# Lock file with stale check
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        exit 1  # Already running
    else
        rm -f "$LOCK_FILE"  # Stale lock
    fi
fi
```

## Files Modified
- `~/rot-minter-new/.env` - MAX_RETRIES, RETRY_DELAY_MS
- `~/rot-minter-new/mint-rot.mjs` - Exponential backoff in callToolWithRetry
- `~/rot-minter-new/auto-mine.sh` - Smart cooldown, server error detection
- `~/rot-minter-new/mine-single.sh` - NEW: Lock file + single-instance pattern

## Recommended Template
Use `mine-single.sh` as production template:
- Lock file prevents duplicates
- Tracks actual slots needed (not hardcoded 10)
- Better error messages
- Cleaner logging

## Time Investment
- Total session: ~1.5 hours (10:20 - 11:52)
- Debugging: ~45 min (identifying duplicate processes, TX revert pattern)
- Implementation: ~30 min (exponential backoff, lock file, smart cooldown)
- Completion: ~15 min (manual mint after cleanup)

## Success Metrics
- ✅ 10/10 slots minted (255,000 ROT)
- ✅ No more infinite retry loops
- ✅ Single-instance enforcement working
- ⚠️ Still missing on-chain verification (future improvement)
