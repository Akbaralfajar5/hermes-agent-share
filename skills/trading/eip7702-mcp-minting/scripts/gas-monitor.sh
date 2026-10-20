#!/bin/bash
# Gas monitor for EIP-7702 MCP minting projects
# Notifies when gas drops below target for relayer to process mints
# Usage: ./gas-monitor.sh [target_gwei] [check_interval_seconds]

export PATH="$HOME/.foundry/bin:$PATH"
RPC="${RPC_URL:-https://ethereum-rpc.publicnode.com}"
TARGET_GWEI="${1:-4.21}"
INTERVAL="${2:-60}"
TELEGRAM_NOTIFY="${TELEGRAM_NOTIFY:-true}"

echo "=== Gas Monitor Started ==="
echo "Target: < ${TARGET_GWEI} gwei"
echo "Check interval: ${INTERVAL}s"
echo "RPC: $RPC"
echo ""

while true; do
  BASE_FEE=$(cast base-fee --rpc-url "$RPC" 2>/dev/null)
  if [ -z "$BASE_FEE" ] || [ "$BASE_FEE" = "0" ]; then
    echo "$(date '+%H:%M:%S'): RPC error, retrying..."
    sleep 10
    continue
  fi
  
  GWEI=$(python3 -c "print(f'{int(${BASE_FEE}) / 1e9:.2f}')")
  
  if python3 -c "exit(0 if float('$GWEI') < float('$TARGET_GWEI') else 1)"; then
    echo ""
    echo "🚨 GAS LOW: ${GWEI} gwei < ${TARGET_GWEI} gwei — MINT NOW!"
    echo "$(date)"
    
    # Send Telegram notification if hermes is available
    if [ "$TELEGRAM_NOTIFY" = "true" ]; then
      echo "⛽ GAS ALERT: ${GWEI} gwei (< ${TARGET_GWEI}). Open Claude.ai and type 'mint me 9 slots' NOW!" 
    fi
    break
  fi
  
  echo "$(date '+%H:%M:%S'): ${GWEI} gwei (waiting for < ${TARGET_GWEI})"
  sleep "$INTERVAL"
done
