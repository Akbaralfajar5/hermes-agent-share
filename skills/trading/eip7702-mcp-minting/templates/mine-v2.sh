#!/bin/bash
# ROT Miner v2 - uses brainrot.dog MCP API v2 (check_wallet, mint, check_mint_status)
# Works with new API as of May 2026
#
# USAGE: Set ADDRESS below, then: chmod +x mine-v2.sh && bash mine-v2.sh
# PITFALL: MCP v2 success response is "minted 25,500 $ROT to 0x..." NOT "tx: 0x..."
#          Always parse text content first, then check for "minted 25,500" OR "tx:"
# PITFALL: After ETH top-up, restart miner — running process won't detect new balance
# PITFALL: Use on-chain slot count after success, not local counter (prevents drift)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="mining.log"
ADDRESS="0xYOUR_ADDRESS_HERE"
MCP_URL="https://www.brainrot.dog/api/mcp"
TARGET_SLOTS=10

mcp_call() {
    local tool=$1
    local args=$2
    curl -s -X POST "$MCP_URL" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"$tool\",\"arguments\":$args},\"id\":1}" \
        | grep '^data:' | sed 's/^data: //'
}

get_slots() {
    result=$(mcp_call "check_wallet" "{\"address\":\"$ADDRESS\"}")
    echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['content'][0]['text'])" 2>/dev/null | grep "slots used:" | awk '{print $3}'
}

echo "🚀 ROT Miner v2 Started" | tee -a $LOG_FILE
echo "💼 Wallet: $ADDRESS" | tee -a $LOG_FILE
echo "🎯 Target: $TARGET_SLOTS slots (255,000 ROT)" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

attempt=0
# Always initialize from on-chain, never hardcode
current_slots=$(get_slots)
[ -z "$current_slots" ] && current_slots=0

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Current slots: $current_slots/$TARGET_SLOTS" | tee -a $LOG_FILE

while [ "$current_slots" -lt "$TARGET_SLOTS" ]; do
    attempt=$((attempt + 1))
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] 🔄 Attempt #$attempt | Slots: $current_slots/$TARGET_SLOTS" | tee -a $LOG_FILE

    result=$(mcp_call "mint" "{\"address\":\"$ADDRESS\"}")

    # IMPORTANT: Parse text content first, THEN check for success
    # MCP v2 success format: "minted 25,500 $ROT to 0x...\ntx: 0x...\n..."
    # NOT just "tx: 0x..." — must check for "minted 25,500" OR "tx:"
    text=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['content'][0]['text'])" 2>/dev/null)

    if echo "$text" | grep -q "minted 25,500\|tx:"; then
        tx=$(echo "$text" | grep "tx:" | awk '{print $2}')
        echo "[$timestamp] ✅ SUCCESS! TX: $tx" | tee -a $LOG_FILE
        echo "[$timestamp] 💰 $text" | tee -a $LOG_FILE
        # Re-query on-chain for accurate slot count (prevents counter drift)
        new_slots=$(get_slots)
        [ -n "$new_slots" ] && current_slots=$new_slots || current_slots=$((current_slots + 1))
        attempt=0
        sleep 3
    elif echo "$result" | grep -q "job_id"; then
        job_id=$(echo "$text" | grep "job_id:" | awk '{print $2}')
        echo "[$timestamp] ⏳ Queued! job_id: $job_id - checking status..." | tee -a $LOG_FILE
        sleep 5
        status_result=$(mcp_call "check_mint_status" "{\"job_id\":\"$job_id\"}")
        status_text=$(echo "$status_result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['content'][0]['text'])" 2>/dev/null)
        if echo "$status_text" | grep -q "completed"; then
            echo "[$timestamp] ✅ Job completed!" | tee -a $LOG_FILE
            new_slots=$(get_slots)
            [ -n "$new_slots" ] && current_slots=$new_slots || current_slots=$((current_slots + 1))
            attempt=0
        fi
    else
        echo "[$timestamp] ❌ $text" | tee -a $LOG_FILE
        # Cooldown every 10 failures
        if [ $((attempt % 10)) -eq 0 ]; then
            echo "[$timestamp] ⏳ Cooldown 10s..." | tee -a $LOG_FILE
            sleep 10
        else
            sleep 2
        fi
    fi
done

echo "" | tee -a $LOG_FILE
echo "🎉 MINING COMPLETE! $current_slots/$TARGET_SLOTS slots = $((current_slots * 25500)) ROT" | tee -a $LOG_FILE
