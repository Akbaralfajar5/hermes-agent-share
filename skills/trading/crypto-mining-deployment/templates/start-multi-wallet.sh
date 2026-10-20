#!/bin/bash
# start-multi-wallet.sh
# Optimal config: 2 GPU per wallet = 2 wallets per VPS
# Tested May 2026: 1 GPU/wallet (4 wallets) was SLOWER than 4 GPU/wallet (1 wallet)
# Sweet spot: 2 GPU/wallet = ~11.8 GH/s per wallet, 2 independent challenges
#
# Usage: RPC=https://... bash start-multi-wallet.sh
# Or edit WALLET1_PK, WALLET2_PK, RPC below and run directly

RPC="${RPC:-https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY}"
WALLET1_PK="${WALLET1_PK:-0xYOUR_WALLET1_PRIVATE_KEY}"
WALLET2_PK="${WALLET2_PK:-0xYOUR_WALLET2_PRIVATE_KEY}"
LOG_DIR="${LOG_DIR:-/root/hash-miner}"

# Kill all old instances
pkill -f "node miner" 2>/dev/null
for s in hash-gpu hash-w1 hash-w2 hash-w3 hash-w4; do
  screen -S $s -X quit 2>/dev/null
done
sleep 2

# Wallet 1 - GPU 0+1 (2 GPUs)
screen -dmS hash-w1 bash -c "cd $LOG_DIR && PRIVATE_KEY=$WALLET1_PK RPC_URL=$RPC NUM_GPUS=2 GPU_OFFSET=0 node miner-gpu-v3.js >> miner-w1.log 2>&1"

# Wallet 2 - GPU 2+3 (2 GPUs)
screen -dmS hash-w2 bash -c "cd $LOG_DIR && PRIVATE_KEY=$WALLET2_PK RPC_URL=$RPC NUM_GPUS=2 GPU_OFFSET=2 node miner-gpu-v3.js >> miner-w2.log 2>&1"

echo "2 wallet instances started (2 GPU each)!"
screen -list

echo ""
echo "Monitor:"
echo "  tail -f $LOG_DIR/miner-w1.log"
echo "  tail -f $LOG_DIR/miner-w2.log"
echo ""
echo "Check mints:"
echo "  grep 'MINED' $LOG_DIR/miner-w*.log"
