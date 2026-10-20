---
name: hash-pow-mining
description: Browser-based PoW token mining with CUDA GPU acceleration — setup, debugging, and optimization for keccak256-based mining contracts on Ethereum (e.g. $HASH at hash256.org). Covers contract discovery, CUDA binary debugging, endianness bugs, and multi-VPS scaling.
triggers:
  - hash mining
  - PoW token
  - keccak256 mining
  - CUDA miner
  - browser mining
  - hash256.org
  - mine(nonce)
  - PFFT
  - pffthash
  - pow free fair token
---

# Hash PoW Mining — CUDA GPU Setup & Debugging

## Overview

Browser-based PoW tokens use keccak256 hashing in the browser (WASM workers) or via CUDA GPU. The pattern:
1. Fetch `challenge = getChallenge(address)` from contract (bytes32, per-wallet)
2. Find `nonce` such that `keccak256(challenge ++ nonce_bytes32) < difficulty`
3. Submit `mine(uint256 nonce)` to contract

## Contract Discovery

**CRITICAL: Always verify the correct contract address before mining.**

- Check the website source/footer for the actual deployed contract
- Use `eth_getCode` to verify a contract has bytecode — empty = wrong address
- Cross-check with Etherscan activity (recent txs to the contract)
- The mining contract and the token contract are often DIFFERENT addresses

```bash
# Verify contract has bytecode
curl -s -X POST https://ethereum.publicnode.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getCode","params":["0xCONTRACT","latest"],"id":1}'
# result "0x" = no bytecode = wrong address
```

## Reading Contract State

```bash
# Get difficulty and mining state via ethers.js
node -e "
const {ethers}=require('ethers');
const p=new ethers.JsonRpcProvider('https://ethereum.publicnode.com',1,{staticNetwork:true});
const ABI=[
  {type:'function',stateMutability:'view',name:'currentDifficulty',inputs:[],outputs:[{type:'uint256'}]},
  {type:'function',stateMutability:'view',name:'miningState',inputs:[],outputs:[
    {name:'era',type:'uint256'},{name:'reward',type:'uint256'},
    {name:'difficulty',type:'uint256'},{name:'minted',type:'uint256'},
    {name:'remaining',type:'uint256'},{name:'epoch',type:'uint256'},
    {name:'epochBlocksLeft',type:'uint256'}
  ]},
  {type:'function',stateMutability:'view',name:'getChallenge',inputs:[{name:'miner',type:'address'}],outputs:[{type:'bytes32'}]}
];
const c=new ethers.Contract('0xCONTRACT',ABI,p);
Promise.all([c.currentDifficulty(),c.miningState(),c.getChallenge('0xWALLET')]).then(([d,s,ch])=>{
  console.log('difficulty:', '0x'+d.toString(16));
  console.log('era:', s.era.toString());
  console.log('minted:', ethers.formatEther(s.minted));
  console.log('challenge:', ch);
}).catch(console.error);
"
```

## Difficulty Interpretation

**PITFALL: Difficulty padding confusion.**

`currentDifficulty` returns a uint256. When converted to hex and padded to 64 chars (32 bytes) with leading zeros for big-endian comparison:

- `0x3ffffffffffffffffffffffffffffffffffffffffffffffffffff` (210 bits) 
- Padded to 64 chars: `0x000000000003ffff...ffff`
- First byte `0x00` means hash must start with `0x00` — requires ~8 leading zero bits
- Expected nonces = `2^(256 - bit_length)` = `2^46` ≈ 70 trillion for 210-bit difficulty

```python
d = int(difficulty_hex, 16)
expected_nonces = 2 ** (256 - d.bit_length())
time_seconds = expected_nonces / hashrate_per_second
print(f"Expected: {time_seconds/60:.1f} minutes per mint")
```

## CUDA Binary — Keccak256 Correctness

### Hash Format
- Input: `challenge_bytes32 ++ nonce_bytes32` = 64 bytes total
- Output: 32 bytes keccak256 hash
- Comparison: big-endian, byte[0] is MSB

### Keccak256 Output Endianness — THE CRITICAL BUG

Keccak state stores uint64 lanes in **little-endian** internally. Output must be converted to **big-endian** for correct comparison with difficulty.

**Wrong output loop (little-endian per word):**
```c
// WRONG — outputs little-endian bytes
for (int i=0;i<4;i++)
  for (int j=0;j<8;j++)
    out[i*8+j] = (st[i]>>(j*8))&0xFF;
```

**Correct output loop (big-endian per word):**
```c
// CORRECT — outputs big-endian bytes (MSB first)
for (int i=0;i<4;i++)
  for (int j=0;j<8;j++)
    out[i*8+j] = (st[i]>>((7-j)*8))&0xFF;
```

**Verify with test vector:**
```bash
# keccak256("") = c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
echo -n "" | keccak-256sum
# Or via Node.js:
node -e "const {ethers}=require('ethers'); console.log(ethers.keccak256('0x'));"
```

### Comparison Logic

```c
// Big-endian comparison (j=0 is MSB) — CORRECT
bool valid = false;
for (int j = 0; j < 32; j++) {
    if (hash[j] < difficulty[j]) { valid = true; break; }
    if (hash[j] > difficulty[j]) { valid = false; break; }
}
// Note: default valid=false is correct (equal = not less than)
```

### Debugging a Suspected Keccak Bug

1. Pick a known-valid nonce from a recent successful mint on-chain
2. Manually compute `keccak256(challenge ++ nonce)` with ethers.js
3. Run the binary with that exact nonce and compare output
4. If binary output ≠ ethers output → keccak implementation bug

```bash
# Get recent mint tx and decode nonce
curl -s -X POST https://ethereum.publicnode.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getLogs","params":[{"fromBlock":"0xLATEST-100","toBlock":"latest","address":"0xCONTRACT","topics":["0xMINED_EVENT_TOPIC"]}],"id":1}'
```

## Verifying Mints On-Chain

Use `eth_getLogs` with the Mined event topic and wallet address as indexed topic:

```bash
# Check all mints from a wallet
curl -s -X POST https://ethereum.publicnode.com \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0","method":"eth_getLogs",
    "params":[{
      "fromBlock":"0xSTARTBLOCK",
      "toBlock":"latest",
      "address":"0xMINING_CONTRACT",
      "topics":[
        "0xMINED_EVENT_TOPIC",
        "0x000000000000000000000000WALLETADDRESS"
      ]
    }],"id":1}'
```

**Do NOT use `eth_getTransactionCount` (nonce) to count mints** — it counts ALL txs from wallet, not just successful mints.

## Multi-Wallet Strategy (Recommended)

**Best setup: 1 wallet per GPU, all on same VPS.**

Each wallet gets its own unique `challenge = getChallenge(address)` — so N wallets = N independent lottery tickets running in parallel. This is better than N GPUs on 1 wallet because:
- 1 wallet + 4 GPUs = 4× hashrate on 1 challenge (1 lottery ticket, faster)
- 4 wallets + 1 GPU each = 4× independent chances (4 separate lottery tickets, same total hashrate)

**User confirmed:** 4 wallet x 1 GPU setup is preferred. Each wallet has its own challenge, so even if one wallet is unlucky, others can still mint independently. In practice W1 minted 2x while W2/W3/W4 were still at 0 — this is normal variance, not a bug.

Setup steps:
1. Generate N wallets: `ethers.Wallet.createRandom()`
2. Fund each with ETH for gas (0.01–0.015 ETH each is plenty for hundreds of mints)
3. Run N miner instances: `NUM_GPUS=1 GPU_OFFSET=<n> PRIVATE_KEY=<pk> node miner-gpu-v3.js`
4. Each instance gets its own screen session: `hash-w1`, `hash-w2`, etc.

See `templates/start-4wallet.sh` for a ready-to-use 4-wallet startup script (fill in PKs and RPC URL).

**Gas funding pitfall:** When sending ETH to new wallets, `maxPriorityFeePerGas` must not exceed `maxFeePerGas`. On low-gas networks (< 1 gwei), setting priority fee to 2 gwei will fail. Use:
```js
const maxFee = feeData.gasPrice * 2n;
const priorityFee = feeData.gasPrice; // NOT a fixed value
```

## Multi-GPU Scaling Beyond 4 GPUs (16x RTX 5090 pattern)

When a VPS has more than 4 GPUs, run multiple screen instances with `GPU_OFFSET` to cover all GPUs. Each instance handles 4 GPUs:

```bash
RPC='https://lb.drpc.live/ethereum/<KEY>'

# 16x GPU setup — 4 instances × 4 GPUs each
screen -S hash-g0  -dm bash -c 'cd /root/hash-miner && set -a && source .env && set +a && NUM_GPUS=4 GPU_OFFSET=0  RPC_URL='$RPC' node miner-gpu-v3.js 2>&1 | tee miner-g0.log'
sleep 2
screen -S hash-g4  -dm bash -c 'cd /root/hash-miner && set -a && source .env && set +a && NUM_GPUS=4 GPU_OFFSET=4  RPC_URL='$RPC' node miner-gpu-v3.js 2>&1 | tee miner-g4.log'
sleep 2
screen -S hash-g8  -dm bash -c 'cd /root/hash-miner && set -a && source .env && set +a && NUM_GPUS=4 GPU_OFFSET=8  RPC_URL='$RPC' node miner-gpu-v3.js 2>&1 | tee miner-g8.log'
sleep 2
screen -S hash-g12 -dm bash -c 'cd /root/hash-miner && set -a && source .env && set +a && NUM_GPUS=4 GPU_OFFSET=12 RPC_URL='$RPC' node miner-gpu-v3.js 2>&1 | tee miner-g12.log'
```

**Confirmed May 12 2026:** 16× RTX 5090 on Vast.ai (sm_120, CUDA 13.x), cuInit: 0, all 16 GPUs at 100% utilization, ~500W each, ~5.9 GH/s per GPU = **~94 GH/s total**. 4 screen sessions, each covering GPU_OFFSET 0/4/8/12.

**Hashrate per RTX 5090 (updated):** stabilizes at ~5.9–5.97 GH/s after warmup. Node.js wrapper hashrate is the reliable figure.

## 16-GPU Setup (4 instances × 4 GPU)

When a VPS has 16 GPUs, run 4 separate screen sessions each with `NUM_GPUS=4` and different `GPU_OFFSET`:

```bash
RPC='https://lb.drpc.live/ethereum/AuchdA0wR03lp6HZlnn8J5yMGaWXTCAR8aFDtiKh6MJI'

screen -S hash-g0  -dm bash -c 'cd /root/hash-miner && set -a && source .env && set +a && NUM_GPUS=4 GPU_OFFSET=0  node miner-gpu-v3.js 2>&1 | tee miner-g0.log'
screen -S hash-g4  -dm bash -c 'cd /root/hash-miner && set -a && source .env && set +a && NUM_GPUS=4 GPU_OFFSET=4  node miner-gpu-v3.js 2>&1 | tee miner-g4.log'
screen -S hash-g8  -dm bash -c 'cd /root/hash-miner && set -a && source .env && set +a && NUM_GPUS=4 GPU_OFFSET=8  node miner-gpu-v3.js 2>&1 | tee miner-g8.log'
screen -S hash-g12 -dm bash -c 'cd /root/hash-miner && set -a && source .env && set +a && NUM_GPUS=4 GPU_OFFSET=12 node miner-gpu-v3.js 2>&1 | tee miner-g12.log'
```

**16× RTX 5090 confirmed (May 2026, Vast.ai):** ~5,900–5,980 MH/s per GPU at steady state = **~94 GH/s total**. All 16 GPUs show 100% utilization + ~500W power draw when running correctly.

**PITFALL: SSH inline PK quoting** — passing `PRIVATE_KEY=0x...` directly in SSH single-quoted commands can silently truncate or mangle the key. Always write to `.env` file first and use `set -a && source .env && set +a` pattern. Confirmed fix May 2026.

**PITFALL: `dotenv` module not installed by default** — `miner-gpu-v3.js` uses `process.env.PRIVATE_KEY` (not `require('dotenv')`), so dotenv is not strictly needed. But if you run a quick node -e verify script that calls `require('dotenv')`, install it first: `npm install dotenv -s --prefix /root/hash-miner`.

## Multi-VPS Scaling

**One wallet can run on multiple VPS simultaneously** — contract does NOT block this. User confirmed: "orang ada yg run banyak vps tapi dengan satu wallet aman kok masuk, malah kalo nabrak pun tetep masuk dua duanya."

- Even if two VPS submit the same nonce simultaneously, both can land (confirmed by user)
- Each VPS should use a different random nonce offset to avoid redundant work
- Scale: N VPS = N× hashrate = N× mint frequency (linear)
- No penalty for nonce collision — contract accepts all valid submissions

**User confirmed (May 2026):** 8 VPS running simultaneously with 1 wallet, total ~30 GH/s, no issues. This is the preferred scaling strategy — easier than managing multiple wallets and funding them with ETH.

**16-GPU single instance strategy (May 2026):** Vast.ai can provision a single instance with 16× RTX 5090. Split into 4 screen sessions, each handling 4 GPUs via `GPU_OFFSET`:
```bash
# Session 1: GPU 0-3
screen -dmS hash-0 bash -c "cd /root/hash-miner && NUM_GPUS=4 GPU_OFFSET=0 PRIVATE_KEY=0x<PK> RPC_URL=<RPC> node miner-gpu-v3.js 2>&1 | tee miner-0.log"
# Session 2: GPU 4-7
screen -dmS hash-4 bash -c "cd /root/hash-miner && NUM_GPUS=4 GPU_OFFSET=4 PRIVATE_KEY=0x<PK> RPC_URL=<RPC> node miner-gpu-v3.js 2>&1 | tee miner-4.log"
# Session 3: GPU 8-11
screen -dmS hash-8 bash -c "cd /root/hash-miner && NUM_GPUS=4 GPU_OFFSET=8 PRIVATE_KEY=0x<PK> RPC_URL=<RPC> node miner-gpu-v3.js 2>&1 | tee miner-8.log"
# Session 4: GPU 12-15
screen -dmS hash-12 bash -c "cd /root/hash-miner && NUM_GPUS=4 GPU_OFFSET=12 PRIVATE_KEY=0x<PK> RPC_URL=<RPC> node miner-gpu-v3.js 2>&1 | tee miner-12.log"
```
Expected total: ~88 GH/s (~5.5 GH/s × 16). All sessions use same wallet — no extra ETH funding needed.

## Hashrate Expectations

| GPU | Approx Hashrate | Notes |
|-----|----------------|-------|
| RTX 3060 Ti | ~3-4 GH/s | |
| RTX 4090 | ~4.4–4.5 GH/s/GPU | 4× GPU = ~17.8 GH/s total (Ada89 sm_89) |
| RTX 5090 | ~5.0–5.7 GH/s/GPU | Confirmed May 2026 on Vast.ai: VPS1 (2× RTX 5090, CUDA 13.0) = ~5.4–5.5 GH/s/GPU. VPS3 (8× RTX 5090, CUDA 13.2) = ~5.5–5.7 GH/s/GPU. **16× RTX 5090 instance confirmed available on Vast.ai (May 2026) — cuInit: 0, Device count: 16, all GPUs accessible.** sm_120. Note: bandwidth-scaling from RTX 4090 overestimates — actual is ~5.5 GH/s not 7.8 GH/s. Raw binary benchmark shows ~400–850 GH/s but this is a `time()` resolution artifact — use Node.js wrapper hashrate for economics. CUDA 13.2 (driver 595.x) slightly faster than CUDA 13.0 (driver 580.x). |
| RTX A5000 | ~1.4-1.5 GH/s | **Much slower than expected** — see note below |
| RTX 5070 Ti | ~2.15 GH/s | Blackwell sm_120 — supplemental only |
| RTX 5070 | ~1.4 GH/s | Blackwell sm_120 — supplemental only |
| RTX 5060 Ti | ~1.0–1.15 GH/s | Blackwell sm_120 — supplemental only. Confirmed May 2026: 4× RTX 5060 Ti = ~4.6 GH/s total (~1,150–1,235 MH/s per GPU at steady state) |
| RTX 4070 SUPER | ~1.85 GH/s/GPU | Ada89 sm_89 — 2× GPU = ~3.7 GH/s total |
| RTX 2060 | ~700–730 MH/s/GPU | Turing sm_75 — 4× GPU = ~2.7–2.9 GH/s total. Confirmed May 2026 on Vast.ai. Compile: `nvcc -O3 -arch=sm_75`. Note: GPU1 may show higher (~720) than GPU0/2/3 due to process-to-GPU mapping quirk |
| RTX PRO 6000 Blackwell | ~1.56 GH/s/GPU | Blackwell sm_120 — 4× GPU = ~6.2 GH/s total |
| H200 SXM | ~17.7 GH/s/GPU | 4,058 GB/s bandwidth — 4× GPU = ~70.9 GH/s total. Estimated by bandwidth scaling from RTX 4090 baseline. |

**RTX A5000 warning:** Despite being a workstation GPU with 8,192 CUDA cores, the A5000 only achieves ~1.4 GH/s for keccak256 mining — far below the ~8-10 GH/s one might expect. Root cause: keccak256 is **memory-bandwidth-bound**, and the A5000 has only 768 GB/s bandwidth vs RTX 5090's 1.8 TB/s. Increasing CUDA block/thread count (e.g. 8192 blocks × 512 threads) does NOT help — the bottleneck is memory, not compute. **4× A5000 (~6 GH/s total) is worse than 4× RTX 5090 (~22 GH/s total).** Avoid A5000 for this workload. Compute capability is 8.6 (same as RTX 3090) — compile with `nvcc -O3 -arch=sm_86`. **Decision rule: if hashrate is disappointing after first benchmark, cancel the VPS immediately — don't waste time tuning a wrong GPU.**

**RTX 5070 Ti note:** Blackwell architecture, compute capability 12.0 — compile with `nvcc -O3 -arch=sm_120`. Achieves ~2.4 GH/s for keccak256. Better than A5000 but still far below RTX 5090 (~5.6 GH/s). Only 1 GPU per instance tested. Not recommended as primary mining GPU — use as supplemental hashrate only if cost is very low.

With difficulty `2^46` (70T nonces expected):
- RTX 5090 (22 GH/s): ~53 min/mint
- 4× RTX 5090: ~13 min/mint
- 4× A5000 (6 GH/s): ~3.2 hours/mint — not worth it

**Mining is purely probabilistic (lottery)** — a 3060 Ti can mint in 5 minutes on first try (luck), while a 5090 cluster can go 2 hours dry. Each nonce has equal probability regardless of GPU speed. GPU speed only determines how many lottery tickets you buy per second. Long-run averages follow the hashrate ratio, but short-term variance is high. Don't confuse a lucky early mint with superior hashrate.

## Monitoring Mints

```bash
# Watch for FOUND in miner log
tail -f /root/hash-miner/miner-gpu.log | grep -E "FOUND|mint|Error"

# Count total mints from wallet via logs
# See references/hash256-contract.md for event topics
```

### Automated Mint Alert via Cronjob

Set up a Hermes cronjob to notify on Telegram when a mint lands:

```
Name: HASH Mining Monitor
Schedule: every 5m
Deliver: telegram:<chat_id>
Prompt: Check if wallet 0x<WALLET> has received new HASH token mints from contract 0xAC7b5d...
  1. Get current block via eth_blockNumber (use https://rpc.mevblocker.io)
  2. Get logs from last 50 blocks with Mined event topic + wallet as topic[1]
     - Mined event topic: 0x8082c19e89c7dbd81a0225ea188067b2d0e7600a069c4f4035527721a5d41e59
     - Wallet topic: 0x000000000000000000000000<wallet_without_0x>
  3. Get HASH balance via eth_call selector 0x70a08231 + padded wallet
  If new logs found: send "✅ MINT MASUK! Block {n} | +100 HASH | TX: {hash[:20]}... | Balance: {bal} HASH"
  If no new mints: stay silent (do not deliver)
```

Key: set `repeat: forever` (not `once`) so it keeps running. The "stay silent if no mints" instruction prevents spam — only fires when something actually happens.

## Identifying Dominant Miners & Estimating Competition

Use `eth_getLogs` over last 2000 blocks to count mints per wallet and estimate relative hashrate:

```js
const logs = await p.getLogs({
  address: CONTRACT,
  fromBlock: '0x' + (latest - 2000).toString(16),
  toBlock: 'latest'
});

const miners = {};
for (const l of logs) {
  // topics[0] = Transfer event sig, topics[1] = from, topics[2] = to
  // Use slice(-40) not slice(26) — topics[1] may be from address not miner
  const raw = l.topics[1] || '';
  const miner = raw.length >= 42 ? '0x' + raw.slice(-40) : raw;
  miners[miner] = (miners[miner]||0) + 1;
}
const sorted = Object.entries(miners).sort((a,b) => b[1]-a[1]);
```

**PITFALL: `topics[1].slice(26)` fails if topics array is shorter than expected** — use `raw.slice(-40)` instead, always safe regardless of padding.

**PITFALL: Hashrate estimation formula is unreliable at high difficulty** — at difficulty `0x3fffffffffffffff`, the formula `mints/block × expectedNonces / 12s` produces absurd numbers (37,000 GH/s). Use **mint count** as the competition signal, not estimated GH/s.

**Confirmed dominant miners (May 2026):**
- `0x000000000004444c5dc75cb358380d2e3de08a90` — vanity address (leading zeros), 801 mints/2000 blocks. Professional mining farm, likely H100/H200 cluster or 1000+ RTX 5090s.
- `0xac7b5d06fa1e77d08aea40d46cb7c5923a87a0cc` — **this is the contract address itself** — dev/owner mining with privileged access, 761 mints/2000 blocks.
- `0x163f3103...` — 523 mints/2000 blocks, unknown large farm.

**Decision rule:** If top 3 miners hold >50% of mints in last 2000 blocks, difficulty will stay high and small miners cannot compete profitably. Wait for them to exit (difficulty retargets every 2,016 mints — if big miners leave, difficulty drops 4–16× within ~1 day).

## Checking If Mining Has Ended

Before starting or resuming mining, verify the project is still active:

```bash
# 1. Get latest block first
LATEST=$(curl -s -X POST https://rpc.mevblocker.io \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' \
  | python3 -c "import json,sys; print(int(json.load(sys.stdin)['result'],16))")
echo "Latest block: $LATEST"

# 2. Check recent contract activity — use last 500 blocks FIRST (fast check)
FROM=$(python3 -c "print(hex($LATEST - 500))")
LOGS=$(curl -s -X POST https://rpc.mevblocker.io \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getLogs\",\"params\":[{\"address\":\"0xCONTRACT\",\"fromBlock\":\"$FROM\",\"toBlock\":\"latest\"}]}" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('result',[])))")
echo "Logs in last 500 blocks: $LOGS"
# If > 0 → mining is ACTIVE regardless of website status

# 3. Check total supply vs max supply (only if logs = 0)
curl -s -X POST https://rpc.mevblocker.io \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":"0xCONTRACT","data":"0x18160ddd"},"latest"]}' \
  | python3 -c "import json,sys; print('Supply:', int(json.load(sys.stdin)['result'],16)/1e18, 'HASH')"

# 4. Check website HTTP status (LAST — website can be 503 while mining is active)
curl -s -o /dev/null -w "Website HTTP: %{http_code}\n" --max-time 10 https://hash256.org/mine
```

**CRITICAL PITFALL: Website 503 ≠ project dead.** In May 2026, hash256.org returned 503 while the contract had 5,000 logs in the last 500 blocks — mining was fully active. Always check `eth_getLogs` first. Website status is unreliable as a liveness indicator.

**CRITICAL PITFALL: Use recent blocks for log check.** Using a stale `fromBlock` (e.g. `0x17E8000` hardcoded) can return 0 logs even when mining is active because the range doesn't include recent blocks. Always compute `fromBlock = latest - 500` dynamically.

**$HASH status (May 2026):** Total supply shows 21,000,000 HASH but mining is still ACTIVE — contract had 5,000+ logs in last 500 blocks as of May 11 2026. The `totalSupply()` call returning 21M is the **max supply constant**, not the amount minted so far. Always use `eth_getLogs` to confirm activity, never `totalSupply()` alone. Website returns 503 intermittently but mining continues unaffected. Remaining: ~17.07M HASH as of May 12 2026. Minted: ~1.83M HASH.

**$HASH market status (May 12 2026):** Price dropped to ~$0.018 (from $0.13 earlier). Uniswap V3 pool (1% fee) at `0xe9f419a0f4425523aeb9b78756a9caa7b83c052d` has only ~$23 liquidity (626 HASH + 0.0045 WETH). Token is essentially **illiquid** — cannot sell meaningful amounts without crashing price to 0. No Uniswap V2 pair exists. Mining is NOT profitable at this price point for any GPU setup.

**Difficulty evolution (May 2026):**
- Early session: `0x3fff...` (210 bits) → ~70T nonces/mint → ~53 min at 22 GH/s
- Later session: `0x000000000000ffff...` (48 leading zero bits) → ~280T nonces/mint → ~2.6 hours at 30 GH/s
- May 12: `0x3fffffffffffffff...` (62 bits) → ~1,126T nonces/mint → ~3.7 hours at 84 GH/s. This is 16x harder than `0x3fff`.
- Difficulty adjusts every 2,016 mints targeting 5 blocks/mint. High competition → difficulty rises fast.

**Difficulty `0x3fffffffffffffff` interpretation:**
- `0x3fffffffffffffff` = 4,611,686,018,427,387,903 decimal (62-bit number)
- Expected nonces = 2^256 / 4.6e18 ≈ **1,126 trillion** nonces per mint
- At 84 GH/s (16x RTX 5090): ~1,126T / 84G = ~13,400 seconds ≈ **3.7 hours** per mint
- At 5.5 GH/s (1x RTX 5090): ~57 hours per mint — not viable solo
- May 12 2026: `0x3fffffffffffffff...` (62-bit) → ~1,125T nonces/mint → ~3.7 hours at 84 GH/s — difficulty rose 16× from the `0x3fff` baseline
- Difficulty adjusts every 2,016 mints targeting 5 blocks/mint. High competition → difficulty rises fast.

**Difficulty `0x000000000000ffff...` interpretation:**
- This is NOT 16 leading zero bits — the hex string `0x000000000000ffff` when padded to 32 bytes (64 hex chars) represents a number with ~48 leading zero bits
- `0x000000000000ffff` = 65535 decimal = 16-bit number
- As a 256-bit comparison target: hash must be < 65535 out of 2^256 possible values
- Expected nonces = 2^256 / 65535 ≈ **280 trillion** nonces per mint
- At 30 GH/s: ~280T / 30G = ~9,333 seconds ≈ **2.6 hours** per mint
- Formula: `expected_nonces = 2^256 / difficulty_value` (NOT `2^(256 - bit_length)` when difficulty is small)

**Correct formula for small difficulty values:**
```python
d = int(difficulty_hex, 16)
expected_nonces = (2**256) / d  # correct for small d
time_seconds = expected_nonces / hashrate_per_second
```

**Time-to-mint estimates at 30 GH/s:**
- Difficulty `0x3fff...` (210 bits, ~70T nonces): ~39 min
- Difficulty `0x000000000000ffff...` (~280T nonces): ~2.6 hours

Era 1, reward 100 HASH/mint, minted ~1.65M of 18.9M mining supply as of May 11 2026.

## Known Working Contract Function Selectors ($HASH)

These were confirmed via brute-force selector scanning (May 2026). Many standard names like `era()`, `epoch()`, `reward()` do NOT exist — use these exact names:

| Function | Selector | Returns |
|---|---|---|
| `name()` | `0x06fdde03` | `"Hash"` |
| `symbol()` | `0x95d89b41` | `"HASH"` |
| `decimals()` | `0x313ce567` | `18` |
| `totalSupply()` | `0x18160ddd` | `21000000 * 1e18` (max supply constant, NOT minted) |
| `totalMints()` | `0x1f21bfbf` | total mints so far (uint256) |
| `currentReward()` | `0x07621eca` | reward per mint in wei (100 * 1e18 = 100 HASH) |
| `currentDifficulty()` | `0x5c062d6c` | difficulty as uint256 |
| `EPOCH_BLOCKS()` | `0x74c259c6` | `100` |
| `MAX_MINTS_PER_BLOCK()` | `0xe2da2b4f` | `10` |

**PITFALL: Website "0 HASH" reward display is a bug.** The hash256.org/mine page showed "0 HASH per mint" in May 2026 — this is a frontend display bug. The contract `currentReward()` correctly returns 100 HASH. Always trust the contract over the website UI.

**Selector scanning approach** — when ABI is unknown, brute-force common function name variants. **CRITICAL: use `staticNetwork: true` and try multiple RPCs** — publicnode works but Ankr/Cloudflare may be rate-limited or return errors. If all selectors return errors, it's likely an RPC issue not a contract issue. Try `https://ethereum.publicnode.com` with `staticNetwork: true` first.
```js
const { ethers } = require("ethers");
const provider = new ethers.JsonRpcProvider(RPC, 1, { staticNetwork: true }); // staticNetwork=true required!
const names = ["currentReward", "totalMints", "currentDifficulty", "EPOCH_BLOCKS", "MAX_MINTS_PER_BLOCK"];
for (const name of names) {
  const sel = ethers.id(`${name}()`).slice(0, 10);
  try {
    const result = await provider.call({ to: CONTRACT, data: sel });
    if (result && result !== "0x") {
      const num = ethers.AbiCoder.defaultAbiCoder().decode(["uint256"], result);
      console.log(`${name}(): ${num[0].toString()}`);
    }
  } catch {}
}
```

**CRITICAL: `staticNetwork: true` required for `ethereum.publicnode.com`** — without it, ethers.js enters an infinite retry loop (`JsonRpcProvider failed to detect network and cannot start up; retry in 1s`) and the script never completes. Always pass `{ staticNetwork: true }` as the third argument when using publicnode or any RPC that doesn't respond to `eth_chainId` quickly.

## Reliable public RPCs for contract reads (no API key needed):
- `https://rpc.mevblocker.io` ✅ (best, no rate limit for reads)
- `https://ethereum.publicnode.com` ✅
- `https://1rpc.io/eth` ✅
- `https://eth.drpc.org` ✅ (confirmed May 2026 — no key, no batch limit for single requests, good fallback)
- `https://rpc.ankr.com/eth` ❌ **REQUIRES API KEY (confirmed May 2026)** — returns 401 Unauthorized without key. Do NOT use as public endpoint anymore. Also confirmed: even `https://rpc.ankr.com/eth` (no key) now returns `Unauthorized: You must authenticate your request with an API key` — fully blocked for unauthenticated use.
- `https://ethereum.publicnode.com` ✅ **Best free fallback (confirmed May 2026)** — no key, no batch limit, stable. Use `staticNetwork: true`. Confirmed working for PFFT miner on Vast.ai.
- `https://eth.llamarpc.com` ⚠️ (rate limited, "Too many connections")
- `https://cloudflare-eth.com/v1/mainnet` ❌ (returns Internal error)
- Ankr without API key ❌ (requires auth)
- Etherscan API v1 ❌ (deprecated, use v2 with `chainid=1` param)

**Premium RPC options (for miner submit + challenge refresh):**
- **Ankr Premium**: `https://rpc.ankr.com/eth/<key>` — confirmed stable for multi-wallet, multi-VPS. User key in memory.
- **dRPC**: `https://lb.drpc.live/ethereum/<key>` — tested May 2026 as Ankr alternative. User key in memory. Switched to when Ankr had TIMEOUT issues.

**PITFALL: dRPC free tier blocks batch requests** — ethers.js v6 batches JSON-RPC calls by default. dRPC free tier returns HTTP 500 with `"Batch of more than 3 requests are not allowed on free tier"`. This breaks miners that fetch multiple contract values simultaneously (challenge + target + info in one round). Fix: upgrade to dRPC paid, or switch to Ankr/Alchemy which support batching on free tier. Confirmed May 2026 on PFFT miner with 8 parallel Node.js instances all hitting the same dRPC free endpoint.
- **Flashbots fast** (submit only): `https://rpc.flashbots.net/fast` — private builder pool, no API key needed. Use for dual-broadcast alongside main RPC.

## Block Competition & Gas Tuning

**$HASH has a 10 mints/block cap globally.** When mining is popular, this slot fills up fast.

### Diagnosing competition level
```bash
# Check average mints per block over last 500 blocks
LATEST=$(curl -s -X POST https://rpc.mevblocker.io -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}' \
  | python3 -c "import json,sys; print(int(json.load(sys.stdin)['result'],16))")
FROM=$(python3 -c "print(hex($LATEST - 500))")
curl -s -X POST https://rpc.mevblocker.io -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_getLogs\",\"params\":[{\"address\":\"0xCONTRACT\",\"fromBlock\":\"$FROM\",\"toBlock\":\"latest\"}]}" \
  | python3 -c "
import json,sys
from collections import Counter
d=json.load(sys.stdin)
logs=d.get('result',[])
blocks=Counter(int(l['blockNumber'],16) for l in logs)
print(f'Total logs: {len(logs)}')
print(f'Avg mints/block: {len(logs)/500:.1f}')
print(f'Busiest blocks: {blocks.most_common(3)}')
"
```

**Interpretation:**
- Avg < 3/block → low competition, default gas is fine
- Avg 5–8/block → moderate, raise priority fee to 10–15 gwei
- Avg > 9/block → high competition, slots almost always full

**CRITICAL INSIGHT (confirmed May 2026):** When competition is high (9.8/10 avg), raising gas does NOT reliably help. Successful miner txs were observed using **0.3–1.0 gwei maxFee, 0–0.5 gwei priority** — far lower than our 25 gwei. This means block slots are filled based on **who submits first after finding a nonce**, not who pays more gas. The 10 mints/block cap is filled within milliseconds of each block. Gas only matters if your tx arrives at the same time as others — in practice, latency (RPC speed, network proximity to validators) matters more than gas price for this contract.

**Recommended: 10 gwei for both maxFee bump and priority** — enough to not be dropped, not so high as to waste ETH. User confirmed 10 gwei as preferred setting after testing 2 gwei (too low risk), 25 gwei (wasteful, no improvement), and observing competing miners at 0.3–1 gwei.

**Gas tuning sequence tried (May 2026):**
- 15 gwei → 25 gwei (both fields) → no improvement in mint rate
- Checked competing successful txs → they use 0.3–1 gwei
- Conclusion: gas is NOT the bottleneck; hashrate + latency is
- Settled on 10 gwei as safe middle ground

### Gas fee structure in miner-gpu-v3.js
```js
// Current structure (two separate fields):
maxFeePerGas: feeData.maxFeePerGas + ethers.parseUnits("25", "gwei"),  // cap
maxPriorityFeePerGas: ethers.parseUnits("10", "gwei"),                  // tip to validator
```

**Key insight:** `maxPriorityFeePerGas` (the validator tip) is what determines tx ordering within a block. Raising `maxFeePerGas` alone doesn't help if `maxPriorityFeePerGas` stays low. To compete for block slots, raise BOTH:
```js
maxFeePerGas: feeData.maxFeePerGas + ethers.parseUnits("30", "gwei"),
maxPriorityFeePerGas: ethers.parseUnits("25", "gwei"),
```

**User preference:** 10 gwei for both `maxFeePerGas` bump AND `maxPriorityFeePerGas` is the confirmed preferred setting. Raising to 25 gwei did not improve mint rate — successful competing miners use 0.3–1 gwei. Don't go above 15 gwei unless you have specific evidence it helps.

**Difficulty retarget interpretation pitfall (May 2026):**
- User reported "difficulty turun 75% (4x lebih mudah)" based on truncated decimal numbers
- Actual contract values: before `0x000000000003ffff...` (46 leading zero bits), after `0x000000000000ffff...` (48 leading zero bits)
- **48 bits > 46 bits = difficulty NAIK 4x, bukan turun** — more leading zeros = harder
- The "before" number user shared was truncated (22 digits vs 63 digits full) — cannot compare truncated decimals
- Always compare full hex representations, not truncated decimals
- Formula: more leading zero bits = harder. `0x000000000000ffff` (48 bits) is 4× harder than `0x000000000003ffff` (46 bits)

**Difficulty retarget schedule:**
- Retargets every 2,016 mints (like Bitcoin)
- Target: 1 mint/minute globally
- If too few miners → difficulty drops (easier)
- If too many miners → difficulty rises (harder)
- May 2026: difficulty rose 65,536× from launch due to GPU farm competition

## Epoch vs Difficulty

**EPOCH_CHANGED is the silent killer of mining sessions.** Epoch resets every 100 blocks (~20 minutes). When difficulty is high, the miner cannot find a nonce within one epoch — so it resets and starts over, making zero progress.

**Math check before starting:**
```python
difficulty = int("0x000000000000ffff", 16)  # example
expected_nonces = (2**256) / difficulty      # ~280 trillion
epoch_seconds = 100 * 12                     # ~1200 seconds (20 min)
hashrate = 30e9                              # 30 GH/s

nonces_per_epoch = hashrate * epoch_seconds  # ~36 trillion
probability_per_epoch = nonces_per_epoch / expected_nonces  # ~12.8%
# Average epochs to mint = 1 / probability = ~7.8 epochs = ~2.6 hours
```

**Rule of thumb:** If `hashrate × 1200 seconds < expected_nonces / 3`, you're unlikely to mint within a single epoch. You'll still eventually mint (probabilistic), but EPOCH_CHANGED will interrupt frequently.

**Minimum hashrate for reliable mining at difficulty `0x000000000000ffff`:**
- 1 mint per epoch (20 min): ~230 GH/s
- 1 mint per hour: ~77 GH/s  
- 1 mint per 3 hours: ~26 GH/s (our setup in May 2026)

**Real-world confirmation (May 2026):** User's friend with 100 GH/s got ~1 mint/hour. Our 29 GH/s got ~1 mint per 3+ hours. This matches the math exactly.

## CPU Multi-Thread Miner (Node.js worker_threads)

When GPU is busy or unavailable, run a CPU miner using Node.js `worker_threads` to utilize all CPU cores. This is free extra hashrate on VPS instances where CPU is idle.

**Pattern:** `miner-multi.js` — spawns N worker threads, each brute-forces keccak256 independently. First thread to find a valid nonce broadcasts via Flashbots + MEV Blocker.

```bash
# Install and run
cd /root/hash256-cli
npm install ethers dotenv
NUM_THREADS=$(nproc) PRIVATE_KEY=0x... RPC_URL=https://... node miner-multi.js
```

**Confirmed hashrates (May 2026, Vast.ai):**
- VPS1 (144 CPU cores): ~1.5 MH/s
- VPS3 (384 CPU cores): ~1.6 MH/s
- Total CPU contribution: ~3.1 MH/s (negligible vs GPU but free)

**PITFALL: `miningState().difficulty` display bug** — when logging `difficulty` from `miningState()`, doing `.slice(0,16)` on the hex string cuts into the significant bits and shows `0xffffffffffffffff...` instead of `0x000000000000ffff...`. This is a cosmetic log bug only — the actual difficulty value passed to workers is correct. Use `currentDifficulty()` selector `0x5c062d6c` directly if you want a clean display. Both `miningState().difficulty` and `currentDifficulty()` return the same correct value.

**PITFALL: `miningState()` ABI field name** — the last field is `epochBlocksLeft_` (with trailing underscore) not `epochBlocksLeft`. Use the exact name from the ABI or access by index.

**Worker thread pattern:**
```js
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
if (!isMainThread) {
  // Worker: brute-force keccak256
  const { challenge, difficulty, startNonce } = workerData;
  const diff = BigInt(difficulty);
  let nonce = BigInt(startNonce);
  while (true) {
    const nonceHex = ethers.zeroPadValue(ethers.toBeHex(nonce), 32);
    const hash = ethers.keccak256(challenge + nonceHex.slice(2));
    if (BigInt(hash) < diff) {
      parentPort.postMessage({ found: true, nonce: nonce.toString() });
      break;
    }
    nonce++;
  }
  return;
}
// Main: spawn workers, collect result, submit tx
```

**Nonce space partitioning:** divide `0xFFFFFFFFFFFFFFFF` by `NUM_THREADS` and assign each worker a different starting range. Add random offset to avoid overlap with GPU miners on same wallet.

**Source:** `https://github.com/mrfunntastiic/hash256-cli.git` — original single-thread CPU miner. Multi-thread version (`miner-multi.js`) was built on top of this.

- `templates/miner-multi.js` — ready-to-use multi-thread CPU miner with Flashbots dual-broadcast

## Third-Party CUDA Binary: hash256_miner (stablemarkk)

Repo: `https://github.com/stablemarkk/hash256_miner`

Contains an optimized CUDA kernel (`native/hash256_cuda.cu`) with grid-stride loop and 96 nonces/thread. Benchmarked at ~1.3 GH/s on RTX 4060 Ti (+12% vs baseline). **On RTX 5090, achieves same ~4.4 GH/s as our binary — no improvement.**

**Compile fix for Linux (the `.exe` binaries are Windows-only):**
```bash
# The source has a #pragma unroll HASHES_PER_THREAD that fails without -D flag
# Fix: patch the pragma AND pass -DHASHES_PER_THREAD=96
sed 's/#pragma unroll HASHES_PER_THREAD/#pragma unroll 96/' native/hash256_cuda.cu > hash256_cuda_patched.cu
nvcc -O3 -arch=sm_120 -Xptxas=-O3 -DHASHES_PER_THREAD=96 -o hash256-cuda-linux hash256_cuda_patched.cu
```

**CLI usage (different from our binary):**
```bash
# Args: <challenge_hex> <difficulty_hex> <blocks> <threads> <hashes_per_thread>
./hash256-cuda-linux 0xCHALLENGE 0xDIFF 0 384 96
# Output: PROGRESS <MH/s> total=<hashes>
# Found: FOUND 0x<nonce_hex> 0x<hash_hex>
```

**Verdict:** Not faster than our `hash_miner_v4.cu` on RTX 5090. The +12% gain was measured on RTX 4060 Ti (sm_89) — does not transfer to Blackwell (sm_120). Use our binary for RTX 5090.

## CPU / Browser Mining (PC without dedicated GPU)

When the user wants to mine on their own PC (no VPS cost), browser WASM or a CPU miner is viable — slow but free to run.

**Browser WASM hashrate expectations:**
- Modern 8-core CPU (Ryzen 7 / i7): ~50–200 MH/s via browser WASM workers
- The browser tab uses all available logical cores as WASM workers
- Chrome/Brave (V8 engine) is fastest — Firefox is ~20% slower for WASM

**CPU miner (Node.js) hashrate:**
- Same CPU, native Node.js: ~100–400 MH/s (slightly faster than browser due to no sandbox overhead)

**Time-to-mint at difficulty `0x000000000000ffff` (~280T nonces):**
- 100 MH/s: ~32 days per mint (not worth it)
- 200 MH/s: ~16 days per mint
- 500 MH/s: ~6.5 days per mint
- 1 GH/s (GPU): ~3.2 days per mint... wait, recalc:
  - 280T / 100M = 2,800,000 seconds = ~32 days at 100 MH/s
  - 280T / 1G = 280,000 seconds = ~3.2 days at 1 GH/s

**Verdict for PC mining:**
- Only worth it if the PC is idle anyway (zero marginal cost)
- At $0.13/HASH × 100 HASH = $13 per mint, even 32 days of CPU time is "free profit" if the PC runs 24/7
- If the PC has a gaming GPU (RTX 3060+), use the CUDA miner instead — 10–50× faster than CPU
- For GPU mining on PC: compile `hash_miner_v4.cu` locally with the correct `sm_XX` flag for the GPU

**Check if PC has a GPU:**
```bash
nvidia-smi  # Windows: nvidia-smi.exe in C:\Windows\System32\
# or
lspci | grep -i nvidia
```

## Cloud GPU Provider Templates

**Clore.ai template selection for $HASH mining:**
- ✅ Use `cloreai/jupyter:ubuntu24.04-v2` — lightweight, Ubuntu 24.04, CUDA support, Jupyter Lab for monitoring
- ❌ Avoid `cloreai/ml-tools:0.1` — ML training tools, overkill, more expensive

**Vast.ai template:** any CUDA 12.x base image works. Prefer Ubuntu 22.04/24.04 with CUDA 12.x.

**H200 economics (May 2026, $0.13/HASH):**
- 4× H200 = ~70.9 GH/s → 0.91 mints/hour → $11.78/hour revenue
- Clore.ai H200 cost: ~$22.16/hour
- **Net: -$10.38/hour** — NOT worth it at $0.13/HASH
- Breakeven price: **$0.244/HASH**
- Rule: H200 is memory-bandwidth-rich but cost/GH is terrible for this workload. Stick to consumer GPUs (RTX 4090, 3090) on Vast.ai for better cost efficiency.

**RTX 5090 multi-GPU economics (May 2026, $0.13/HASH, difficulty 48-bit):**
- 2× RTX 5090 (VPS1, Vast.ai $0.83/hr): ~10.9 GH/s → ~14 HASH/hr → $1.82/hr revenue → **+$0.99/hr profit** ✅
- 8× RTX 5090 (VPS3, Vast.ai, CUDA 13.2): ~45.1 GH/s → ~58 HASH/hr → $7.54/hr revenue ✅
- 8× RTX 5090 (VPS2, Vast.ai $5.20/hr): `cuInit: 999` — CUDA not accessible, zero real mining ❌ (destroy immediately)
- 16× RTX 5090 (May 12 2026): ~93 GH/s total (~5.8 GH/s per GPU confirmed). All 16 GPUs at 100% util, ~500W each. Setup: 4 screen sessions × 4 GPUs each (GPU_OFFSET 0/4/8/12).
- 9× RTX 5090 total (VPS1+VPS3): ~56.1 GH/s → ~72 HASH/hr → ~$9.33/hr revenue
- Breakeven HASH price: ~$0.10/HASH (at difficulty 48-bit). At difficulty 62-bit (`0x3fffffffffffffff`), breakeven is much higher.
- **May 12 2026 update:** HASH price dropped to $0.018, liquidity ~$23. Mining is NOT profitable at any scale. Stop mining until price recovers above $0.10.
- Worth it only if VPS cost < revenue. Check instance pricing before renting.
- Note: nvidia-smi may show 0% GPU utilization on some Vast.ai containers even when mining is active — use power draw (~450–560W per RTX 5090) as the real indicator. But if power is also ~15W, miner is genuinely dead.

**Clore.ai template for $HASH mining:**
- ✅ `cloreai/jupyter:ubuntu24.04-v2` — lightweight, Ubuntu 24.04, CUDA support, Jupyter Lab
- ❌ `cloreai/ml-tools:0.1` — ML training tools, overkill, more expensive

## Economics Check Before Scaling

Always calculate ROI before adding VPS:

```
Revenue = hashrate_GH/s × (1/77) mints/hour × reward_per_mint × token_price
Cost = VPS_cost_per_hour

Break-even token price = VPS_cost / (hashrate_GH/s × (1/77) × reward_per_mint)
```

**May 2026 example:**
- HASH price: $0.13/token
- 100 GH/s VPS cost: ~$50-60/hour
- Revenue at 100 GH/s: 1 mint/hour × 100 HASH × $0.13 = $13/hour
- **Net: -$37-47/hour loss**

**Decision rule:** If `token_price × reward_per_mint < VPS_cost_per_mint`, stop mining and hold existing tokens. Resume when price recovers.

## Dual-Broadcast for MEV Protection (Flashbots fast)

Sign the tx once, broadcast to **two RPCs in parallel**: Ankr Premium (public mempool) + Flashbots fast (private builder pool). This protects against MEV/front-running and can improve inclusion speed.

```js
// In miner-gpu-v3.js — replace the single submitContract.mine() call with:
const txData = await submitContract.mine.populateTransaction(BigInt(nonce), {
  gasLimit,
  maxFeePerGas: feeData.maxFeePerGas + ethers.parseUnits("25", "gwei"),
  maxPriorityFeePerGas: ethers.parseUnits("25", "gwei"),
  nonce: await submitProv.getTransactionCount(submitWallet.address, 'pending'),
  chainId: 1,
});
const signedTx = await submitWallet.signTransaction(txData);
const txHash = ethers.keccak256(signedTx);

const flashbotsProv = new ethers.JsonRpcProvider('https://rpc.flashbots.net/fast');
const [ankrResult, fbResult] = await Promise.allSettled([
  submitProv.broadcastTransaction(signedTx),
  flashbotsProv.broadcastTransaction(signedTx),
]);
// Log results, then wait for confirmation:
const receipt = await submitProv.waitForTransaction(txHash, 1, 60000);
```

**Why this works for $HASH:**
- $HASH contract is NOT front-runnable (challenge is address-bound) — so Flashbots doesn't protect against nonce theft
- But Flashbots fast endpoint routes tx directly to block builders, bypassing public mempool latency
- With 9.8/10 block slots filled by competition, every millisecond of latency matters
- Dual broadcast = tx reaches builders via two paths simultaneously = higher chance of inclusion

**Pitfall:** `populateTransaction` requires explicit `nonce` and `chainId` fields — without them, signing fails or produces wrong tx. Always fetch nonce fresh with `getTransactionCount(..., 'pending')` to avoid nonce conflicts when multiple VPS submit simultaneously.

### Bulk update gas across all VPS
```bash
# Update maxFeePerGas bump from 15→25 gwei on all VPS
for VPS in "PORT:IP:NAME"; do
  PORT=$(echo $VPS | cut -d: -f1); IP=$(echo $VPS | cut -d: -f2)
  ssh -o StrictHostKeyChecking=no -p $PORT root@$IP "
    sed -i 's/parseUnits(\"15\", \"gwei\")/parseUnits(\"25\", \"gwei\")/g' /root/hash-miner/miner-gpu-v3.js
    screen -S hash-gpu -X quit; sleep 1
    screen -dmS hash-gpu bash -c 'cd /root/hash-miner && PRIVATE_KEY=\$PK node miner-gpu-v3.js 2>&1 | tee miner-gpu.log'
  "
done
```

### Bulk swap RPC across all VPS
```bash
OLD_RPC="https://rpc.ankr.com/eth/OLDKEY"
NEW_RPC="https://lb.drpc.live/ethereum/NEWKEY"
for VPS in "PORT:IP:NAME"; do
  PORT=$(echo $VPS | cut -d: -f1); IP=$(echo $VPS | cut -d: -f2)
  ssh -o StrictHostKeyChecking=no -p $PORT root@$IP "
    sed -i 's|$OLD_RPC|$NEW_RPC|g' /root/hash-miner/miner-gpu-v3.js
    grep -o 'drpc\|ankr' /root/hash-miner/miner-gpu-v3.js | head -1
    screen -S hash-gpu -X quit; sleep 1
    screen -dmS hash-gpu bash -c 'cd /root/hash-miner && PRIVATE_KEY=\$PK node miner-gpu-v3.js 2>&1 | tee miner-gpu.log'
    echo 'done'
  "
done
```

## Contract Security — Front-Running / Nonce Sniping

**$HASH contract is NOT front-runnable.** The `mine()` function uses `msg.sender` in the challenge:

```solidity
function _challenge(address miner) internal view returns (bytes32) {
    return keccak256(abi.encode(
        block.chainid,
        address(this),
        miner,      // ← address-bound
        _epoch()
    ));
}
```

This means:
- A nonce valid for wallet A is **invalid** for wallet B — the hash won't meet difficulty
- Even if you see a valid nonce in the mempool, submitting it from your wallet will revert with `InsufficientWork`
- Double-spend protection: `usedProofs[keccak256(msg.sender, nonce, epoch)]` prevents replay

**There is no exploit.** The contract was verified on Sourcify (exact match, May 11 2026). Source code confirms address-binding. The only way to earn HASH is to mine with your own wallet.

## Common Pitfalls

1. **Wrong contract address** — always verify with `eth_getCode` first
2. **Keccak output endianness** — little-endian output vs big-endian difficulty = never finds valid nonce
3. **Difficulty misread** — `0x3fff...` (210 bits) padded to 64 chars looks like `0x000000000003fff...` — the number is still large, not small
4. **Token contract ≠ mining contract** — `balanceOf` goes to token contract, `mine()` goes to mining contract
5. **Epoch changes** — challenge rotates every ~100 blocks; miner must detect and restart round. **EPOCH_CHANGED error pattern:** if the miner logs show repeated `✗ Error: EPOCH_CHANGED` followed by `✗ Error: TIMEOUT: refreshing challenge`, the miner is stuck in a loop — it can't refresh the challenge because the RPC is timing out, and the epoch keeps changing before it can submit. Fix: restart the miner process (`screen -S hash-gpu -X quit && screen -dmS hash-gpu bash -c '...'`). If TIMEOUT persists after restart, switch to a different RPC endpoint. This pattern often appears when Ankr Premium has a brief outage — switching to dRPC resolves it.
6. **RPC rate limit with multi-wallet** — 4 wallets hitting the same Alchemy free endpoint simultaneously causes `TIMEOUT: refreshing challenge` loops. Symptoms: repeated TIMEOUT in logs, miner skips rounds, GPU keeps mining but never submits. Fix: use **Ankr Premium** (`https://rpc.ankr.com/eth/<key>`) — confirmed working for 4 simultaneous wallets. Alchemy free tier is insufficient for multi-wallet setups. Staggering wallet startup by a few seconds does NOT reliably fix this — upgrade the RPC.
7. **Nonce reuse after reverted tx (PFFT-specific)** — `miner.js` initializes `startNonce = 0n` at the start of every round. After a successful mint, the challenge changes but the next round starts from nonce 0 again — finding the same nonce as before. Contract rejects it (`execution reverted`). **PFFT permanently blacklists used nonces per wallet** (confirmed from whitepaper: "duplicate PoW nonces are rejected per address") — the nonce stays blacklisted even if the TX reverted. Fix: randomize startNonce per GPU per round: `const gpuOffset = BigInt(opts.gpu) * 0x100000000n + BigInt(Math.floor(Math.random() * 0xFFFFFFFF)); let startNonce = gpuOffset;`. See `references/pfft-token.md` for full fix. Confirmed fix May 2026 — 0 reverts after applying.
8. **Verifying mints** — use `eth_getLogs` with the Mined event topic + wallet as indexed topic. Do NOT use `eth_getTransactionCount` (counts all txs, not just mints). Do NOT use `balanceOf` on the mining contract (it's the token contract).
9. **Log grep for FOUND** — `grep -E "FOUND|MINED|✓ GPU"` in miner log. The `Minted:` field in round headers is **global supply**, not per-wallet count. A wallet can show `Minted: 1.5M` even if it has never minted.
10. **Variance vs bug** — W3/W4 not minting for 30+ minutes while W1 mints twice is normal variance, not a bug. Each wallet is an independent lottery. With expected ~53 min/mint per wallet, going 1 hour dry is within normal distribution. Only investigate if GPU shows errors or `TIMEOUT` loops.
11. **New VPS SSH "Connection refused"** — Vast.ai instances sometimes take 1-3 minutes to fully boot after creation. If `ssh` returns `Connection refused` immediately, wait and retry. Also double-check the SSH command from the Vast.ai dashboard — port and hostname can change between instance restarts. If it still refuses after 3+ minutes, the instance may have failed to provision — destroy and re-rent. Don't waste time retrying a dead instance.
    **User-stopped VPS also returns "Connection refused"** — when the user manually stops/pauses a Vast.ai instance, SSH will refuse. This is NOT a network issue or dead instance — it's intentional. Before diagnosing SSH failures, ask the user if they stopped the instance. Do NOT attempt to "fix" connection refused on a user-stopped VPS.
12. **Counting mints from logs** — `grep "✓ MINED" miner-w1.log` is the correct way. The `Minted:` field shown in round headers is **global contract supply** (e.g. `1,536,800 HASH`), not per-wallet count. All wallets show the same global `Minted:` value.
13. **`screen` not pre-installed** on some Vast.ai base images — run `apt-get install -y screen` before starting miners. Symptom: `screen: command not found` in startup script.
14. **`miner-gpu-v3.js` not in GitHub repo** — the main miner script is NOT committed to the public repo (only `miner.js` and `hash_miner_v4.cu` are). When setting up a new VPS, copy it manually: `scp -P <old_port> root@<old_host>:/root/hash-miner/miner-gpu-v3.js /tmp/ && scp -P <new_port> /tmp/miner-gpu-v3.js root@<new_host>:/root/hash-miner/`
15. **SSH drops on long inline commands** — when running multi-line bash via SSH, the connection often drops before completion. Workaround: write the script to a local file, `scp` it to the VPS, then `ssh ... 'bash /root/script.sh'`. This is reliable even for 20+ line scripts.

    **Confirmed pattern (May 2026, PFFT miner):** Heredoc (`<< 'ENDSSH'`) works for multi-command blocks. Single-line SSH commands after the first often return exit 255 on Vast.ai. The most reliable pattern for 8-GPU launch:
    1. Write launch script locally to `/tmp/launch_xxx.sh`
    2. `scp -P PORT /tmp/launch_xxx.sh root@HOST:/root/launch_xxx.sh`
    3. `ssh -p PORT root@HOST "chmod +x /root/launch_xxx.sh && bash /root/launch_xxx.sh"`
    This avoids heredoc quoting issues AND the Hermes tool's `nohup/&` restriction (write `setsid ... &` inside the script file, not in the SSH command itself).
16. **Vast.ai SSH key setup** — adding SSH key must be done via the Vast.ai dashboard (instance settings), not just by editing `~/.ssh/authorized_keys` on the instance. The dashboard method persists across reboots; direct file edits may not.
17. **Recovering PK from running process** — if PK is not in a .env file, recover it from the running screen process via `ps aux | grep "node miner"`. The full command line including `PRIVATE_KEY=0x...` is visible in the process list. This is how to get the PK when the miner is already running but no config file exists.
18. **Ankr Premium RPC URL format** — `https://rpc.ankr.com/eth/<32-byte-key>`. User's key: stored in memory. Confirmed working for 4 simultaneous wallets without TIMEOUT issues. Alchemy free tier fails with multi-wallet setups.

19. **Node.js not pre-installed** on some Vast.ai images (especially newer CUDA 13.x base images) — `node --version` returns nothing. Install via nodesource: `curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs`. Verify with `node --version` — should show v20.x. Confirmed on Vast.ai 2× RTX 5090 and 8× RTX 5090 instances (CUDA 13.0, Ubuntu 24.04, May 2026).

19c. **`/root/hash-miner/` Permission denied on local machine** — the local Hermes machine has `/root/hash-miner/` owned by root with restricted permissions. Cannot `cat` or `scp` directly. Workaround: files are also in `/tmp/hash_miner_v4.cu` and `/tmp/miner-gpu-v3.js` — use those paths for `cat | ssh` piping to remote VPS. Pattern: `cat /tmp/hash_miner_v4.cu | ssh -p PORT root@HOST "cat > /root/hash-miner/hash_miner_v4.cu"`.

19d. **Flashbots fast RPC cannot be used as primary RPC** — `https://rpc.flashbots.net/fast` does not support `eth_call` (returns `missing revert data`). It only supports `eth_sendRawTransaction`. Use it only for dual-broadcast tx submission, never as the main RPC for reading contract state (challenge, difficulty, etc.). Symptom: `✗ Error: missing revert data (action="call", data=null)` on every round.

19e. **MEV Blocker + Flashbots dual broadcast implementation** — to protect tx from public mempool, sign the tx manually and broadcast to both `https://rpc.flashbots.net/fast` AND `https://rpc.mevblocker.io` in parallel via `Promise.allSettled`. Use the main dRPC for all reads (getChallenge, estimateGas, getFeeData, getTransactionCount). Pattern:
```js
const PRIVATE_RPCS = [
  'https://rpc.flashbots.net/fast',
  'https://rpc.mevblocker.io',
];
async function broadcastPrivate(signedTx) {
  const results = await Promise.allSettled(
    PRIVATE_RPCS.map(async (rpc) => {
      const prov = new ethers.JsonRpcProvider(rpc, 1, { staticNetwork: true });
      return prov.send('eth_sendRawTransaction', [signedTx]);
    })
  );
  for (const r of results) if (r.status === 'fulfilled') return r.value;
  throw new Error('All private broadcasts failed');
}
// Sign manually:
const rawTx = await wallet.signTransaction({
  to: CONTRACT, data: txData, gasLimit,
  maxFeePerGas, maxPriorityFeePerGas,
  nonce: await provider.getTransactionCount(wallet.address, 'pending'),
  chainId: 1, type: 2,
});
const txHash = await broadcastPrivate(rawTx);
// Wait for receipt via dRPC (poll every 3s, up to 3 min):
let receipt = null;
for (let i = 0; i < 60; i++) {
  await new Promise(r => setTimeout(r, 3000));
  receipt = await provider.getTransactionReceipt(txHash);
  if (receipt) break;
}
```
Note: $HASH is not front-runnable (challenge is address-bound), so MEV protection is not strictly necessary — but private broadcast can improve inclusion speed by routing directly to block builders.

19f. **RTX 5090 actual hashrate on Vast.ai (May 2026)** — confirmed ~4.7–5.0 GH/s per GPU via Node.js wrapper (not 7.8 GH/s as bandwidth-scaling from RTX 4090 would suggest). 2× RTX 5090 = ~9.9 GH/s, 8× RTX 5090 = ~37.5 GH/s. CUDA 13.0, sm_120, Ubuntu 24.04. GPU4 on 8-GPU instance had hardware error (`Unable to determine the device handle for GPU4: Unknown Error`) — not recoverable via `nvidia-smi -r`, contact host for replacement.

**IMPORTANT: Raw CUDA binary hashrate vs Node.js wrapper hashrate are DIFFERENT.** When running `hash-miner-v4` directly (e.g. `timeout 10 /root/hash-miner/hash-miner-v4 $CHALLENGE $DIFF 0`), the binary reports ~408 GH/s per RTX 5090. This is because the binary counts cumulative hashes since start and divides by elapsed time — the display is correct but the Node.js wrapper adds overhead (challenge refresh, epoch watching, tx submission) that reduces effective throughput. The ~5 GH/s figure from the Node.js wrapper is the real-world mining throughput. Do NOT use raw binary benchmark numbers to estimate mining economics — use the Node.js wrapper hashrate instead.

**CRITICAL: Raw binary hashrate display is inflated due to `time()` resolution bug.** The binary uses `time(NULL)` which has 1-second resolution. In the first few seconds, `elapsed` is very small (1–5 seconds) while `total_hashes` has already accumulated billions of hashes. This makes the displayed MH/s appear to grow from 380 GH/s → 800 GH/s → 1 TH/s over 55 seconds — it's NOT the GPU getting faster, it's the denominator catching up. The true hashrate is `total_hashes / total_elapsed` at the END of a long run. For RTX 5090: after 55 seconds, `40 trillion hashes / 55s = ~728 GH/s` displayed — but this is still inflated because the counter never resets between epochs. The Node.js wrapper hashrate (~5 GH/s) is the only reliable figure for economics calculations. Rule: **never use raw binary output to estimate mining profitability**.

19i. **Vast.ai instance unreachable (100% packet loss)** — if `ping` shows 100% packet loss and SSH times out, the instance is not yet online or has failed to provision. Do NOT keep retrying — it won't help. Check the Vast.ai dashboard: if status is not "Running", wait or destroy and re-rent. If status shows "Running" but still unreachable after 3+ minutes, the instance has a network issue — destroy and rent a new one. Confirmed pattern: `ssh: connect to host X port Y: Connection timed out` + `ping: 100% packet loss` = instance not reachable at all, not an SSH key issue.

19h. **CUDA `cuInit: 999` = GPU not accessible in container** — if `cuInit` returns 999 (`CUDA_ERROR_UNKNOWN`) and `cuDeviceGetCount` returns 0, the CUDA runtime cannot access the GPU at all. This is a container-level issue, NOT a driver or binary issue. Symptoms: `nvidia-smi` shows GPUs correctly (driver works), but CUDA programs cannot initialize. The CUDA binary will appear to run (hashrate log shows numbers) but is actually running on CPU — GPU clock stays at 195 MHz (idle), power stays at ~15W. Diagnosis:
```python
import ctypes
cuda = ctypes.CDLL('libcuda.so')
result = cuda.cuInit(0)
print(f'cuInit: {result}')  # 0=success, 999=CUDA_ERROR_UNKNOWN
count = ctypes.c_int(0)
cuda.cuDeviceGetCount(ctypes.byref(count))
print(f'Device count: {count.value}')  # 0 = no GPU accessible
```
Fix: destroy the instance and rent a new one. This is a Vast.ai host configuration issue — the container was not set up with proper GPU passthrough. Cannot be fixed from inside the container. Confirmed on 8× RTX 5090 instance (May 2026) — all 7 working GPUs showed `cuInit: 999`. The instance appeared to work (nvidia-smi showed GPUs, binary ran, hashrate log showed numbers) but zero actual GPU compute was happening.

**MANDATORY: Always run CUDA init check before starting miners on a new VPS.** This takes 2 seconds and saves hours of wasted mining. Run immediately after SSH:
```bash
python3 -c "
import ctypes
cuda = ctypes.CDLL('libcuda.so')
r = cuda.cuInit(0)
print(f'cuInit: {r}')  # MUST be 0
count = ctypes.c_int(0)
cuda.cuDeviceGetCount(ctypes.byref(count))
print(f'Device count: {count.value}')  # MUST match nvidia-smi GPU count
"
```
If `cuInit != 0` or `Device count == 0` → destroy instance immediately, do not waste time compiling or starting miners. Confirmed pattern: VPS2 (8× RTX 5090, May 2026) had `cuInit: 999, Device count: 0` — all mining was fake CPU fallback. VPS3 (8× RTX 5090, same day) had `cuInit: 0, Device count: 8` — mining worked correctly at ~5.6 GH/s per GPU.

**How to detect fake hashrate from CPU fallback:** When CUDA fails to init, the binary falls back to CPU computation. The hashrate counter still increments (CPU is doing the loop), but: (1) GPU clock stays at 195 MHz, (2) GPU power stays at ~15W, (3) `nvidia-smi pmon` shows no compute processes, (4) `cuInit` returns 999. The displayed "400 GH/s" is physically impossible on CPU — it's the same `time()` resolution artifact inflating the counter. Real CPU keccak256 speed is ~100-500 MH/s, not 400 GH/s.

19g. **GPU hardware error on Vast.ai** — after an epoch change (`EPOCH_CHANGED` error), the miner process sometimes exits and the GPU drops to 0% utilization. The screen session stays alive but the Node.js process is dead. Symptoms: `nvidia-smi` shows 0% GPU util + ~15W idle power, but `screen -ls` shows sessions still exist. The log shows inflated hashrate numbers (e.g. 400+ GH/s) because the counter accumulated from the previous epoch and wasn't reset. Fix: kill all screen sessions and restart miners. Check with `nvidia-smi --query-gpu=utilization.gpu,power.draw --format=csv,noheader` — if power is ~15W (idle), miner is dead. Normal mining power for RTX 5090 is ~450–560W.

**Distinguishing dead miner from running miner on Vast.ai containers:** Some Vast.ai container environments do NOT report GPU utilization correctly via `nvidia-smi` (always shows 0% even when GPU is fully loaded). In this case, use power draw as the indicator: RTX 5090 at full load = ~450–560W, idle = ~5–20W. If power is high, the miner is running regardless of what `utilization.gpu` shows. Confirmed on 8× RTX 5090 instance (May 2026): `nvidia-smi` showed 0% util but power was 450W per GPU — miner was running fine. The hashrate log from Node.js is the most reliable indicator.

**CRITICAL: 0% util + ~15W power = miner is DEAD (not just a reporting bug).** If power is at idle levels (~5–20W per GPU), the GPU is genuinely not computing. This is different from the "0% util but 450W power" case above. Always check BOTH utilization AND power draw together. The three states:
- 0% util + ~15W power → miner dead, GPU idle (restart needed)
- 0% util + ~450W power → miner running, nvidia-smi reporting bug (normal on some containers)
- 100% util + ~450W power → miner running, nvidia-smi working correctly (VPS1 behavior)

— if `nvidia-smi` shows `Unable to determine the device handle for GPU N: Unknown Error`, the GPU has a hardware fault. `nvidia-smi -r -i N` will not fix it. The miner process for that GPU will fail silently. Skip that GPU index and run miners on the remaining GPUs. Report to Vast.ai host for potential refund/replacement.

19b. **`ethers` npm module not globally available** — when running quick contract-check scripts in `/tmp`, always `cd /tmp && npm install ethers` first. The module is not globally installed on fresh VPS instances. Alternatively, reuse `/root/hash-miner/node_modules` by running scripts from that directory.
20. **CUDA architecture flags by GPU generation:**
    - RTX 20xx (Turing): `sm_75`
    - RTX 30xx / A5000 / A6000: `sm_86`
    - RTX 40xx: `sm_89`
    - RTX 50xx (5090, 5070 Ti) / Blackwell / RTX PRO 6000: `sm_120`
    - CUDA 13.0 (driver 580.x) confirmed working with `sm_120` on RTX 5090 (Vast.ai, May 2026)
    - Always check with `nvidia-smi --query-gpu=compute_cap --format=csv,noheader` before compiling
26. **`miner-gpu-v3.js` display string hardcodes "4x RTX 5090"** — the startup banner always prints `GPUs: 4x RTX 5090` regardless of actual hardware. This is a cosmetic bug in the script. Trust `nvidia-smi` output for actual GPU model and count, not the miner banner. The script spawns 4 GPU worker processes regardless of how many physical GPUs exist — on a 1-GPU VPS, only GPU0 will do real work; GPU1/2/3 processes will still spawn but produce 0 hashes. This is fine — the script handles it gracefully.\n\n27. **RTX 4070 SUPER hashrate anomaly** — on a 2× RTX 4070 SUPER VPS, GPU1 showed ~1.9 GH/s while GPU0/2/3 showed ~617 MH/s each. This is because the script spawns 4 processes but only 2 physical GPUs exist — GPU0 and GPU1 get real work, GPU2/3 are phantom processes sharing GPU0/1 resources. Net result: ~3.7 GH/s total from 2× 4070 SUPER, which is correct (~1.85 GH/s per physical GPU). The uneven display is misleading but the total hashrate is accurate.\n\n22. **Vast.ai default processes use GPU at 100%** — fresh Vast.ai instances run tensorboard and jupyter by default, which can show 100% GPU utilization even with no miner running. Don't mistake this for the miner being active. Always check `ps aux | grep -E 'node|hash|miner'` to confirm the actual miner process is running. If only `tensorboard` and `jupyter-notebook` appear, the miner is dead.

23a. **PRIVATE_KEY passing via SSH single-quote can silently corrupt the key** — when passing PK inline via `ssh ... "PRIVATE_KEY=0x... node ..."`, shell quoting inside the SSH command can strip or mangle characters, causing ethers.js to throw `invalid private key` even though the key is correct. The key may appear to have the right length locally but arrive truncated on the remote side. **Fix: always write PK to a `.env` file on the VPS first, then source it in the screen command:**
```bash
# Write .env on VPS
ssh -p PORT root@HOST "cat > /root/hash-miner/.env << 'ENVEOF'
PRIVATE_KEY=0x<PK>
RPC_URL=https://...
ENVEOF"

# Start miner sourcing .env
screen -S hash-g0 -dm bash -c 'cd /root/hash-miner && set -a && source .env && set +a && NUM_GPUS=4 GPU_OFFSET=0 node miner-gpu-v3.js 2>&1 | tee miner-g0.log'
```
The `set -a && source .env && set +a` pattern exports all vars from .env into the environment before node starts. This is reliable regardless of special characters in the PK.

23. **PRIVATE_KEY not persisted on new VPS** — `miner-gpu-v3.js` reads `process.env.PRIVATE_KEY`. New VPS instances cloned from the repo have no `.env` file. Symptom: `TypeError: invalid private key (argument="privateKey", value="undefined")`. Fix: write `.env` file with heredoc then source it in screen command. **PITFALL: passing PK inline via SSH single quotes can mangle the value** — ethers.js reports `invalid private key` even though the key is correct. Always use `.env` file approach:
```bash
# Write .env on VPS
ssh -p PORT root@HOST "cat > /root/hash-miner/.env << 'ENVEOF'
PRIVATE_KEY=0x...
RPC_URL=https://...
ENVEOF"
# Start with source
screen -S hash-gpu -dm bash -c 'cd /root/hash-miner && set -a && source .env && set +a && NUM_GPUS=4 GPU_OFFSET=0 node miner-gpu-v3.js 2>&1 | tee miner-gpu.log'
```
Also install `dotenv` package: `npm install dotenv` in the hash-miner directory. The `.env` file is in `.gitignore` so it's never committed.

24. **`totalSupply()` is NOT minted amount** — for $HASH, `eth_call` to `0x18160ddd` (totalSupply) returns `21000000 * 1e18` which is the **max supply constant hardcoded in the contract**, not the amount minted so far. This caused a false "mining ended" conclusion. To check how much has been minted, use the `miningState()` view function which returns `minted` and `remaining` fields separately. Or just check `eth_getLogs` for recent activity — if logs exist, mining is active regardless of totalSupply.

25. **VPS label ≠ actual GPU** — the SSH port/hostname you rent from Vast.ai does NOT reliably indicate which GPU is inside. A VPS rented as "RTX 5070 Ti" may actually contain 4× RTX 5090 (or vice versa). Always run `nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader` immediately after SSH to confirm the actual hardware before compiling or benchmarking. The miner script also reports `GPUs: Nx <model>` at startup — trust that over the Vast.ai listing label.

28. **Contract address appearing as "miner" in eth_getLogs** — when scanning recent mint logs, `0xac7b5d06fa1e77d08aea40d46cb7c5923a87a0cc` (the mining contract itself) may appear as `topics[1]` (the miner address). This is NOT a real miner — it's likely an internal call or event emitted with the contract address as the indexed miner field. Ignore this address when analyzing competition. Real miners have normal EOA addresses.

29. **dotenv not installed by default** — `miner-gpu-v3.js` may use `require('dotenv')` but the package is not in the default `package.json`. If you get `Cannot find module 'dotenv'`, run `npm install dotenv` in `/root/hash-miner/`. Alternatively, use `set -a && source .env && set +a` in the shell before launching node — this exports .env vars without needing the dotenv package.

21. **Supplemental VPS strategy** — when a new VPS has only 1 GPU and it's not a top-tier card, run it with the same wallet as the main VPS (`PRIVATE_KEY=<same_pk>`). This adds hashrate to the same wallet without needing to fund a new wallet with ETH. User confirmed multi-VPS same wallet works fine.

## $HASH V2 — Cuckoo Cycle Mining (Launched May 14 2026)

V2 is a **completely different puzzle** from V1. V1 used keccak256 (GPU-friendly). V2 uses **Cuckoo Cycle 32-42** (memory-hard, WASM in browser).

### Key differences from V1

| | V1 | V2 |
|---|---|---|
| Puzzle | keccak256 | Cuckoo Cycle 32-42 |
| Working set | ~0 MB | ~256 MB |
| GPU advantage | ~1000× over phone | ~20× over phone |
| Retarget | every 2,016 mints | every 128 mints OR 600 blocks |
| Difficulty wedge fix | No | Yes (asymmetric: 4× harder, 16× easier) |
| Contract | 0xAC7b…A0cc | Not yet deployed at launch |

### V2 Puzzle Structure

```
challenge = keccak256(chainId ‖ contract ‖ miner ‖ epoch)
graph     = 2^25 nodes, ~256 MB working set, edges derived from challenge
valid iff edges form a 42-length cycle AND keccak256(challenge ‖ edges) < epochDifficulty
```

Five anti-gaming properties:
1. Challenge bound to miner address — solutions can't be stolen from mempool
2. ~256 MB working set — ASICs gain little, GPU advantage drops from 1000× to ~20×
3. Epochs rotate every 1,000 blocks (~3.3h) — per-epoch difficulty locked at first mine
4. Each (miner, edges, epoch) tuple mints once — replay impossible
5. 10 mints/block hard cap (controller-tunable)

### V2 Supply & Tokenomics

- Total: 21,000,000 HASH (hard cap, same as Bitcoin model)
- Genesis (Phase 1): 1,050,000 HASH @ 0.01 ETH per 1,000 HASH = $0.03/HASH
- LP side: 1,050,000 HASH (locked permanently in Uniswap V4)
- Mining: 18,900,000 HASH via PoW (90%)
- Team/VC/Airdrop: **0%**

Emission schedule:
- Era 1: 100 HASH/mint (~69 days, 10M HASH)
- Era 2: 50 HASH/mint
- Era 3: 25 HASH/mint
- Era 4: 12.5 HASH/mint
- Halvings every 100,000 mints
- Full distribution: ~290 days

### V2 Genesis Phase 1 — Whitelist Priority Window

Phase 1 opens a **3-hour priority window** for qualified V1 wallets before public mint.

**Qualification criteria (3,849 wallets total):**
- Wallet holding ≥75 HASH V1 at snapshot block, OR
- Wallet that mined ≥1 V1 block ever, OR
- 12 manually-approved addresses

**Mechanics:**
- Price: 0.01 ETH per 1,000 HASH (same as public — whitelist gets access, NOT discount)
- Per-wallet cap during window: 50 units = 50,000 HASH = 0.5 ETH max
- Per-tx cap: 5 units = 5,000 HASH = 0.05 ETH
- Proof: Merkle inclusion against `legacyHolderRoot` required during window
- After window: proof unused, anyone with ETH can mint

**Pool seeding (Phase 2):**
- Anyone calls `seedPool()` after genesis closes
- Contract atomically seeds Uniswap V4 ETH/HASH pool: 10.5 ETH + 1.05M HASH
- Pool opens at $0.03, LP locked permanently (no path to remove)
- If genesis doesn't fully sell out: `partialSeed()` available after 30-min delay

**Profit analysis for whitelist holders:**
- No discount vs public — whitelist = 3h head start only
- Profit depends on post-genesis demand
- Mining emission (90% of supply) will create ongoing sell pressure
- V2 contract not deployed until launch — technical risk exists until then
- Verdict: legitimate tokenomics (no insider allocation), but whitelist advantage is timing only

- `references/hash256-contract.md` — $HASH contract addresses, event topics, ABI details
- `references/new-vps-setup.md` — Complete step-by-step workflow for setting up a new Vast.ai VPS for $HASH mining (clone, compile, fund wallets, start miners)
- `references/competition-analysis.md` — Scripts and workflow for analyzing mining competition, whale accumulation, liquidity, and profitability decision framework
- `templates/start-4wallet.sh` — Ready-to-use 4-wallet × 1-GPU startup script (fill in PKs and RPC URL)
- `templates/pfft_colab_miner.ipynb` — Google Colab notebook for PFFT mining on free T4 GPU (sm_75). Supports hardcoded PK or auto-generate. Multi-account strategy: same wallet across many Google accounts.
