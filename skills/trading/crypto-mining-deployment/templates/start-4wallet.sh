#!/bin/bash
# 4-wallet x 1-GPU miner startup script for $HASH mining
# Each wallet gets its own GPU and independent challenge (4x lottery tickets)
# Fill in: RPC, and 4x PRIVATE_KEY values
# Requires: screen, node, hash-miner-v4 binary, miner-gpu-v3.js

RPC="https://rpc.ankr.com/eth/YOUR_ANKR_KEY"  # Ankr Premium recommended for multi-wallet

# Kill any existing miner processes
pkill -f "node miner" 2>/dev/null
for s in hash-gpu hash-w1 hash-w2 hash-w3 hash-w4; do screen -S $s -X quit 2>/dev/null; done
sleep 3

# Wallet 1 - GPU 0
screen -dmS hash-w1 bash -c "cd /root/hash-miner && PRIVATE_KEY=0xPK1 RPC_URL=$RPC NUM_GPUS=1 GPU_OFFSET=0 node miner-gpu-v3.js >> miner-w1.log 2>&1"

# Wallet 2 - GPU 1
screen -dmS hash-w2 bash -c "cd /root/hash-miner && PRIVATE_KEY=0xPK2 RPC_URL=$RPC NUM_GPUS=1 GPU_OFFSET=1 node miner-gpu-v3.js >> miner-w2.log 2>&1"

# Wallet 3 - GPU 2
screen -dmS hash-w3 bash -c "cd /root/hash-miner && PRIVATE_KEY=0xPK3 RPC_URL=$RPC NUM_GPUS=1 GPU_OFFSET=2 node miner-gpu-v3.js >> miner-w3.log 2>&1"

# Wallet 4 - GPU 3
screen -dmS hash-w4 bash -c "cd /root/hash-miner && PRIVATE_KEY=0xPK4 RPC_URL=$RPC NUM_GPUS=1 GPU_OFFSET=3 node miner-gpu-v3.js >> miner-w4.log 2>&1"

echo "4 wallet x 1 GPU started!"
sleep 2
screen -list
