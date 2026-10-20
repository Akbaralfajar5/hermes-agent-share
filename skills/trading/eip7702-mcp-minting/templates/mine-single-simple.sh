#!/bin/bash
# Single-instance ROT miner with lock file (simplified version without on-chain verification)
# Based on production session May 10, 2026
# Usage: ./mine-single-simple.sh

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

# Create lock file
echo $$ > "$LOCK_FILE"

# Cleanup on exit
trap "rm -f $LOCK_FILE" EXIT

# Run miner
cd ~/rot-minter-new
export $(grep -v '^#' .env | xargs)

echo "🚀 ROT Auto Miner Started (PID: $$)" | tee -a "$LOG_FILE"
echo "💼 Wallet: $MINT_ADDRESS" | tee -a "$LOG_FILE"
echo "🎯 Current: 8/10 slots (need 2 more)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

minted_count=0
MAX_SLOTS=2  # Need 2 more to reach 10

while [ $minted_count -lt $MAX_SLOTS ]; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] Attempting mint #$((minted_count + 1))/2..." | tee -a "$LOG_FILE"
    
    output=$(npm run mint 2>&1)
    
    if echo "$output" | grep -q "minted 25,500"; then
        minted_count=$((minted_count + 1))
        tx=$(echo "$output" | grep "tx:" | awk '{print $2}')
        balance=$(echo "$output" | grep "ROT balance:" | awk '{print $3}')
        
        echo "[$timestamp] ✅ SUCCESS! Slot $((8 + minted_count))/10 | TX: $tx" | tee -a "$LOG_FILE"
        echo "[$timestamp] 💰 Balance: $balance ROT" | tee -a "$LOG_FILE"
        
        # Random cooldown 10-15s
        cooldown=$((10 + RANDOM % 6))
        echo "[$timestamp] ⏸️  Cooldown ${cooldown}s..." | tee -a "$LOG_FILE"
        sleep $cooldown
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
echo "✅ Minted 2 more slots (total: 10/10)" | tee -a "$LOG_FILE"
echo "💰 Final balance: $((204000 + minted_count * 25500)) ROT" | tee -a "$LOG_FILE"
