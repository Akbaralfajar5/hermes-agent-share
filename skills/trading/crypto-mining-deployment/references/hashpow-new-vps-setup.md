# New VPS Setup Workflow for $HASH Mining

## MANDATORY FIRST CHECK: CUDA Init Verification

**Run this BEFORE anything else.** Takes 2 seconds. Saves hours of wasted mining on broken containers.

```bash
python3 -c "
import ctypes
cuda = ctypes.CDLL('libcuda.so')
r = cuda.cuInit(0)
print(f'cuInit: {r}')  # MUST be 0 (success)
count = ctypes.c_int(0)
cuda.cuDeviceGetCount(ctypes.byref(count))
print(f'Device count: {count.value}')  # MUST match nvidia-smi GPU count
"
```

**If `cuInit != 0` or `Device count == 0` → DESTROY INSTANCE IMMEDIATELY.** Do not compile, do not start miners. This is a Vast.ai host configuration issue — the container has no GPU passthrough. Cannot be fixed from inside. Confirmed pattern: VPS2 (8× RTX 5090, May 2026) had `cuInit: 999, Device count: 0` — all mining was fake CPU fallback showing inflated hashrate numbers.

**If `cuInit == 0` and `Device count == N` → proceed with setup.**

## Prerequisites Check
```bash
# Check what's already available
node --version       # need v18+
nvcc --version       # need CUDA
which git screen     # need both
nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader
```

## Step 1: Install missing tools
```bash
apt-get install -y screen  # often missing on Vast.ai base images

# Node.js is NOT pre-installed on CUDA 13.x base images (Vast.ai 2026)
# Check first: node --version
# If missing, install via nodesource:
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
node --version  # should show v20.x
```

## Step 2: Clone repo and install deps
```bash
cd /root
cd hash-miner
npm install
```

## Step 3: Copy miner-gpu-v3.js from existing VPS
# This file is NOT in the GitHub repo — must copy manually
# Keep a cached copy at /tmp/miner-gpu-v3.js on the Hermes host for fast deployment
```bash
# From Hermes host (if cached):
scp -P <NEW_PORT> /tmp/miner-gpu-v3.js root@<NEW_HOST>:/root/hash-miner/

# If cache is stale, refresh from a running VPS first:
scp -P <OLD_PORT> root@<OLD_HOST>:/root/hash-miner/miner-gpu-v3.js /tmp/
scp -P <NEW_PORT> /tmp/miner-gpu-v3.js root@<NEW_HOST>:/root/hash-miner/
```

## Step 4: Compile CUDA binary
```bash
cd /root/hash-miner

# Check GPU compute capability first
nvidia-smi --query-gpu=compute_cap --format=csv,noheader

# Compile for detected arch (sm_XX where XX = compute_cap without dot)
# RTX 20xx (Turing): sm_75
# RTX 30xx / A5000 / A6000: sm_86
# RTX 40xx: sm_89
# RTX 50xx / Blackwell / RTX PRO 6000: sm_120
nvcc -O3 -arch=sm_<XX> -o hash-miner-v4 hash_miner_v4.cu
ls -lh hash-miner-v4  # verify binary exists
```

## Step 5: Start miner

### Single instance (≤4 GPUs)
```bash
screen -S hash-gpu -dm bash -c 'cd /root/hash-miner && set -a && source .env && set +a && NUM_GPUS=4 GPU_OFFSET=0 node miner-gpu-v3.js 2>&1 | tee miner-gpu.log'
```

### Multi-instance (>4 GPUs, e.g. 16x RTX 5090)
Run one screen per 4 GPUs using GPU_OFFSET. Confirmed working May 12 2026 on 16× RTX 5090:
```bash
for OFFSET in 0 4 8 12; do
  screen -S hash-g${OFFSET} -dm bash -c "cd /root/hash-miner && set -a && source .env && set +a && NUM_GPUS=4 GPU_OFFSET=${OFFSET} node miner-gpu-v3.js 2>&1 | tee miner-g${OFFSET}.log"
  sleep 2
done
screen -ls  # should show 4 sessions
```

### Original step (single-wallet mode — current standard)
```bash
# Inline env var in screen command — no .env file needed
# Use Ankr Premium RPC for reliability (no TIMEOUT errors)
ANKR_RPC="https://rpc.ankr.com/eth/923821b85ed523a84a04ab4af6dfe0ab4e46244b69418fefae48edf52b64e210"

# Update RPC in script first (default is publicnode which can timeout)
sed -i "s|https://ethereum.publicnode.com|$ANKR_RPC|g" miner-gpu-v3.js

screen -dmS hash-gpu bash -c "cd /root/hash-miner && PRIVATE_KEY=0x<PK> node miner-gpu-v3.js 2>&1 | tee miner-gpu.log"
sleep 6
cat miner-gpu.log | tail -15
```

## Step 6: Verify running
```bash
screen -list  # should show hash-gpu (Detached)
cat miner-gpu.log | tail -5  # should show MH/s lines
```

## One-liner full setup (for fast deployment)
```bash
# Run on new VPS after SSH in:
apt-get install -y screen 2>&1 | tail -1 && \
curl -fsSL https://deb.nodesource.com/setup_20.x | bash - 2>&1 | tail -1 && \
apt-get install -y nodejs 2>&1 | tail -1 && \
cd hash-miner && npm install 2>&1 | tail -2 && \
ARCH=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1 | tr -d '.') && \
nvcc -O3 -arch=sm_${ARCH} -o hash-miner-v4 hash_miner_v4.cu 2>&1 | tail -2 && \
ls -lh hash-miner-v4
# Then scp miner-gpu-v3.js and start screen
```

## GPU Hashrate Benchmarks (keccak256)
- RTX 5090: **~5.9–5.97 GH/s per GPU** ✅ Best choice (sm_120 on Blackwell) — 2× = ~12 GH/s, 8× = ~47 GH/s, 16× = ~94 GH/s. Confirmed May 12 2026 on Vast.ai (16× RTX 5090, CUDA 13.x, all 100% util, ~500W each). Note: raw binary benchmark shows ~400–850 GH/s but this is a `time()` resolution artifact — use Node.js wrapper hashrate for economics.
- RTX 4090: ~4.4–4.5 GH/s/GPU ✅ Excellent (sm_89) — 4× = ~17.8 GH/s total
- RTX 4070 SUPER: ~1.85 GH/s/GPU ✅ Good value (sm_89, 2× = ~3.7 GH/s)
- RTX PRO 6000 Blackwell: ~1.56 GH/s/GPU ✅ (sm_120, 4× = ~6.2 GH/s) — expensive
- RTX 5070 Ti: ~2.15 GH/s ⚠️ Blackwell sm_120, supplemental only
- RTX 5070: ~1.4 GH/s ⚠️ Blackwell sm_120, supplemental only
- RTX 5060 Ti: ~1.0-1.15 GH/s ⚠️ Blackwell sm_120, supplemental only
- RTX 2060: ~730 MH/s/GPU ⚠️ Turing sm_75, 4× = ~2.9 GH/s — cheap but slow
- RTX A5000: ~1.4 GH/s ❌ Avoid — memory bandwidth bottleneck
- RTX 3060 Ti: ~3-4 GH/s ⚠️ Marginal (sm_86)

## CUDA arch flags by GPU generation
| Compute Cap | GPU Examples | Flag |
|-------------|-------------|------|
| 7.5 | RTX 2060, RTX 2080 Ti | sm_75 |
| 8.6 | RTX 3090, RTX 3080, A5000, A6000 | sm_86 |
| 8.9 | RTX 4090, RTX 4070 SUPER, RTX 4070 | sm_89 |
| 12.0 | RTX 5090, RTX 5070 Ti, RTX 5070, RTX 5060 Ti, RTX PRO 6000 | sm_120 |

Always confirm: `nvidia-smi --query-gpu=compute_cap --format=csv,noheader`

## RPC Configuration
- **Ankr Premium** (user's key): `https://rpc.ankr.com/eth/923821b85ed523a84a04ab4af6dfe0ab4e46244b69418fefae48edf52b64e210`
  - Required for multi-wallet or multi-VPS setups — public RPCs timeout under load
  - **Known issue (May 2026):** Ankr Premium can have brief outages causing TIMEOUT loops across all VPS simultaneously. When this happens, switch to dRPC immediately.
- **dRPC** (user's key): `https://lb.drpc.live/ethereum/AuchdA0wR03lp6HZlnn8J5yMGaWXTCAR8aFDtiKh6MJI`
  - Confirmed stable alternative to Ankr — tested May 2026 with 7 VPS simultaneously
  - Switch to this when Ankr has TIMEOUT issues
- **Fallback reads only**: `https://rpc.mevblocker.io`, `https://ethereum.publicnode.com`
- **Flashbots fast** (dual-broadcast): `https://rpc.flashbots.net/fast`
  - Used for MEV protection and faster block inclusion
  - Tx is signed once, broadcast to Ankr/dRPC + Flashbots in parallel

## EPOCH_CHANGED + TIMEOUT Loop — Emergency Fix

When all VPS simultaneously show `EPOCH_CHANGED` + `TIMEOUT: refreshing challenge`, the RPC is down and epoch keeps rotating before the miner can recover.

Fix sequence:
1. Restart all miners first (often resolves transient RPC hiccup)
2. If TIMEOUT persists after restart, switch RPC to dRPC
3. Bulk RPC swap: `sed -i 's|OLD_RPC_URL|NEW_RPC_URL|g' /root/hash-miner/miner-gpu-v3.js`
4. Restart miners again after RPC swap

## Competition Analysis Before Starting

Before renting or starting miners, check if competition is worth it:

```bash
node -e "
const {ethers} = require('ethers');
const p = new ethers.JsonRpcProvider('https://rpc.mevblocker.io', 1, {staticNetwork:true});
async function main() {
  const latest = await p.getBlockNumber();
  const logs = await p.getLogs({
    address: '0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc',
    fromBlock: '0x' + (latest - 2000).toString(16), toBlock: 'latest'
  });
  const miners = {};
  for (const l of logs) {
    const miner = '0x' + (l.topics[1]||'').slice(-40);
    miners[miner] = (miners[miner]||0) + 1;
  }
  const sorted = Object.entries(miners).sort((a,b)=>b[1]-a[1]);
  const diff = await p.call({to:'0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc', data:'0x5c062d6c'});
  const d = BigInt(diff);
  const exp = Number((2n**256n)/d);
  console.log('Total mints/2000 blocks:', logs.length, '| Avg:', (logs.length/2000).toFixed(2)+'/block');
  console.log('Difficulty:', '0x'+d.toString(16).slice(0,16)+'...');
  console.log('Expected nonces/mint:', (exp/1e12).toFixed(1)+'T');
  console.log('TOP 5:');
  for (const [m,c] of sorted.slice(0,5)) console.log(m, '|', c, 'mints');
}
main().catch(console.error);
"
```

**Stop/don't start if:**
- Top 1-2 miners hold >40% of all mints (farm dominance)
- Difficulty > `0x000000000000ffff` (48-bit, ~280T nonces) at your hashrate
- `0xac7b5d...` (contract address) appears in top miners — dev is mining, difficulty will stay high

**Confirmed May 2026:** At difficulty `0x3fffffffffffffff` (62-bit, ~1,125T nonces), even 84 GH/s (16× RTX 5090) only gets ~1 mint per 3.7 hours. Not worth it. Stopped VPS and waited for difficulty retarget.

## Vast.ai SSH Key Notes
- Add SSH key via Vast.ai dashboard (instance settings), not just authorized_keys
- Dashboard method persists across reboots
- New instances may take 1-3 min to boot — retry if "Connection refused"
- User-stopped instances also return "Connection refused" — ask user before diagnosing

## Multi-VPS Same Wallet
- Running same wallet on multiple VPS is safe and additive
- Contract does not block; even nonce collisions both land
- No need to fund extra wallets — just use same PK on all VPS
- Total hashrate = sum of all VPS hashrates

## Gas Fee Tuning (confirmed May 2026)
- **Preferred setting: 10 gwei** for both `maxFeePerGas` bump and `maxPriorityFeePerGas`
- Successful competing miners observed using **0.3–1.0 gwei** — gas is NOT the bottleneck
- Block slots (10/block cap) fill based on **who submits first**, not who pays most gas
- Raising to 25 gwei did NOT improve mint rate vs 10 gwei
- Latency (RPC speed, network proximity to validators) matters more than gas price
- Flashbots fast endpoint helps more than high gas — routes tx directly to builders
- Update all VPS at once:
```bash
for VPS in "PORT:IP:NAME"; do
  PORT=$(echo $VPS | cut -d: -f1); IP=$(echo $VPS | cut -d: -f2)
  ssh -o StrictHostKeyChecking=no -p $PORT root@$IP "
    sed -i 's/parseUnits(\\\"OLD\\\", \\\"gwei\\\")/parseUnits(\\\"10\\\", \\\"gwei\\\")/g' /root/hash-miner/miner-gpu-v3.js
    screen -S hash-gpu -X quit; sleep 1
    screen -dmS hash-gpu bash -c 'cd /root/hash-miner && PRIVATE_KEY=\$PK node miner-gpu-v3.js 2>&1 | tee miner-gpu.log'
  "
done
```

## CPU Miner Setup (bonus free hashrate)

Run alongside GPU miners to use idle CPU cores. Negligible vs GPU but zero extra cost.

```bash
# Install from GitHub
cd /root && git clone https://github.com/mrfunntastiic/hash256-cli.git
cd hash256-cli && npm install

# Copy multi-thread version from Hermes skill templates
# (or use the single-thread miner.js from the repo)

# Start with all CPU cores
CORES=$(nproc)
screen -dmS cpu-miner bash -c "cd /root/hash256-cli && PRIVATE_KEY=0x<PK> RPC_URL=<RPC> NUM_THREADS=$CORES node miner-multi.js 2>&1 | tee cpu.log"
```

**Expected hashrates:**
- 144 CPU cores (Vast.ai XEON): ~1.5 MH/s
- 384 CPU cores (Vast.ai XEON): ~1.6 MH/s
- Contribution to total: ~3 MH/s vs ~56 GH/s GPU = 0.005% — symbolic but free

**Note:** CPU miner uses same wallet as GPU miner — no extra ETH funding needed.
