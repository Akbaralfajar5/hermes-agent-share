#!/bin/bash
# Single-instance MCP miner with lock file and on-chain verification
# Usage: ./mine-single.sh
# Config: Edit .env for MINT_ADDRESS, RPC_URL, etc.

LOCK_FILE="/tmp/mcp-miner.lock"
LOG_FILE="$HOME/mining.log"
MAX_SLOTS=10  # Adjust based on project limits

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

# Create lock file
echo $$ > "$LOCK_FILE"

# Cleanup on exit
trap "rm -f $LOCK_FILE" EXIT

# Load environment
cd ~/mcp-minter  # Adjust to your project directory
export $(grep -v '^#' .env | xargs)

echo "🚀 MCP Auto Miner Started (PID: $$)" | tee -a "$LOG_FILE"
echo "💼 Wallet: $MINT_ADDRESS" | tee -a "$LOG_FILE"
echo "🎯 Target: $MAX_SLOTS slots" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

minted_count=0

while [ $minted_count -lt $MAX_SLOTS ]; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] Attempting mint #$((minted_count + 1))/$MAX_SLOTS..." | tee -a "$LOG_FILE"
    
    output=$(npm run mint 2>&1)
    
    if echo "$output" | grep -q "minted"; then  # Adjust grep pattern to match your mint script output
        tx=$(echo "$output" | grep "tx:" | awk '{print $2}')
        
        # Wait for TX to be mined
        sleep 5
        
        # Verify on-chain (adjust contract address and method)
        balance=$(cast call $TOKEN_ADDRESS "balanceOf(address)(uint256)" $MINT_ADDRESS --rpc-url $RPC_URL)
        balance_human=$(python3 -c "print(int('$balance') / 1e18)")  # Adjust decimals if needed
        
        # Calculate expected balance (adjust mint amount per slot)
        expected_balance=$(echo "$((minted_count + 1)) * 25500" | bc)
        
        if [ "$balance_human" == "$expected_balance" ]; then
            minted_count=$((minted_count + 1))
            echo "[$timestamp] ✅ CONFIRMED on-chain! Slot $minted_count/$MAX_SLOTS | TX: $tx" | tee -a "$LOG_FILE"
            echo "[$timestamp] 💰 Balance: $balance_human tokens" | tee -a "$LOG_FILE"
            
            # Random cooldown to avoid rate limits
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
        
        # Server error = wait longer
        if echo "$error" | grep -qE "(500|502|503)"; then
            echo "[$timestamp] ⏳ Server error, waiting 45s..." | tee -a "$LOG_FILE"
            sleep 45
        else
            echo "[$timestamp] ⏳ Retrying in 25s..." | tee -a "$LOG_FILE"
            sleep 25
        fi
    fi
done

echo "" | tee -a "$LOG_FILE"
echo "🎉 MINING COMPLETE!" | tee -a "$LOG_FILE"
echo "✅ Minted $minted_count slots" | tee -a "$LOG_FILE"
echo "💰 Final balance: $(cast call $TOKEN_ADDRESS "balanceOf(address)(uint256)" $MINT_ADDRESS --rpc-url $RPC_URL | python3 -c "import sys; print(int(sys.stdin.read().strip()) / 1e18)") tokens" | tee -a "$LOG_FILE"
