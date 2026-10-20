#!/bin/bash
# start-4gpu.sh — 4 EQM miner instances, each on a different GPU
# Each instance uses EQM_GPU_ID env var to select its GPU.
# All instances share the same wallet (same challenge, different nonce search).

source $HOME/.cargo/env
cd /root/equium

# Kill all old instances
for s in eqm-gpu eqm-gpu0 eqm-gpu1 eqm-gpu2 eqm-gpu3 eqm-miner; do
  screen -S $s -X quit 2>/dev/null
done
pkill -f equium 2>/dev/null
sleep 3

RPC="https://mainnet.helius-rpc.com/?api-key=YOUR_HELIUS_KEY"
KEYPAIR="/root/.config/solana/eqm-keypair.json"
# 4 threads per instance = batch of 4 nonces per GPU call
THREADS=4

for GPU_ID in 0 1 2 3; do
  LOG="/root/eqm-gpu${GPU_ID}.log"
  screen -dmS eqm-gpu${GPU_ID} bash -c "
    cd /root/equium
    source \$HOME/.cargo/env
    EQM_GPU_ID=${GPU_ID} ./target/release/equium-gpu-miner mine \
      --rpc-url '${RPC}' \
      --keypair ${KEYPAIR} \
      --threads ${THREADS} \
      2>&1 | tee ${LOG}
  "
  echo "Started GPU${GPU_ID} -> screen eqm-gpu${GPU_ID}, log ${LOG}"
done

sleep 5
screen -list
echo ""
echo "Monitor: tail -f /root/eqm-gpu0.log"
echo "Check GPU: nvidia-smi --query-gpu=index,utilization.gpu,power.draw --format=csv,noheader"
