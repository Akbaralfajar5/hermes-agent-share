# hash256.org — Browser-Mined PoW Token on Ethereum Mainnet

## Overview
- URL: https://hash256.org/mine
- ERC-20 + Uniswap V4 hook + PoW miner in one immutable contract
- **Ethereum mainnet** (chain ID 1) — real ETH for gas
- Browser-based keccak256 PoW, but can be run headless via CPU/GPU

## Contract Address Discovery (CRITICAL)

**The contract address shown in the footer link (`0xAC7b5d06...`) is the MINING contract.**
**The token contract (`0x000000000004444c...`) is a separate ERC-20 — do NOT use for mining.**

**How to verify the correct contract address:**
1. Open hash256.org/mine in browser
2. Right-click footer link → inspect → copy href → extract address from Etherscan URL
3. OR: `curl -s https://hash256.org/_next/static/chunks/5948-*.js | grep -oP '"0x[0-9a-fA-F]{38,42}"'`
4. Verify bytecode exists: `eth_getCode` should return >100 bytes (not `0x`)

**Wrong address symptoms:**
- `getChallenge()` returns `0x` (empty) → ethers.js throws `could not decode result data`
- `miningState()` returns `era: 0` and `difficulty: 0x3fff...fff` (max uint256 = impossible)
- `missing revert data` on all contract calls
- `eth_getCode` returns `0x` or `0x` (2 chars = no bytecode)

**The `era: 0` + `difficulty: 0x3fff...fff` pattern** means you're calling a contract that doesn't implement the mining interface. This is NOT a "genesis not complete" issue — it's a wrong contract address.

**Source code extraction to find contract:**
```bash
# Download the main app chunk
curl -s "https://hash256.org/_next/static/chunks/5948-*.js" > /tmp/hash-main.js
# Find all 40-byte addresses
python3 -c "
import re
with open('/tmp/hash-main.js') as f: content = f.read()
addrs = re.findall(r'[\"\\x27](0x[0-9a-fA-F]{38,42})[\"\\x27]', content)
print(set(addrs))
"
# Look for the one with 'mine' function in ABI context
```

## Contract Address Discovery (CRITICAL)



## ABI (minimal, verified — May 2026)
```javascript
const ABI = [
  { type: 'function', stateMutability: 'view', name: 'getChallenge',
    inputs: [{ name: 'miner', type: 'address' }], outputs: [{ type: 'bytes32' }] },
  { type: 'function', stateMutability: 'view', name: 'currentDifficulty',
    inputs: [], outputs: [{ type: 'uint256' }] },
  { type: 'function', stateMutability: 'view', name: 'miningState',
    inputs: [], outputs: [
      { name: 'era', type: 'uint256' }, { name: 'reward', type: 'uint256' },
      { name: 'difficulty', type: 'uint256' }, { name: 'minted', type: 'uint256' },
      { name: 'remaining', type: 'uint256' }, { name: 'epoch', type: 'uint256' },
      { name: 'epochBlocksLeft', type: 'uint256' }
    ]},
  { type: 'function', stateMutability: 'nonpayable', name: 'mine',
    inputs: [{ name: 'nonce', type: 'uint256' }], outputs: [] },
];
// NOTE: miningState() field names matter — 'minted'/'remaining'/'epochBlocksLeft'
// NOT 'totalMints'/'epochBlock'/'blocksLeft' (those are wrong and cause undefined)
```

## Mining Mechanics
1. Challenge = `contract.getChallenge(miner_address)` — per-wallet, changes each epoch
2. Valid nonce: `keccak256(challenge ‖ nonce) < currentDifficulty`
3. Submit: `contract.mine(nonce)` — auto-pays gas from wallet
4. Epoch rotates every ~100 blocks (~20 min) — challenge changes automatically
5. Difficulty retargets every 2,016 mints to hold 1 mint/minute globally
6. Max 10 mints per block — no burst exploitation
7. Address-bound challenges — solutions cannot be stolen from mempool

## Reward Schedule (Era-based)
- Era 1: 100 HASH per mint (100,000 mints per era)
- Era 2: 50 HASH
- Era 3: 25 HASH
- Era 4: 12.5 HASH
- Total supply: 18,900,000 HASH

## Status (May 11, 2026)
- Era 1, reward 100 HASH/mint
- Difficulty started at `0x000000003fff...` (early), retargeted to `0x0000000000ff...` (5 leading zero bytes) by ~1M mints
- ~1M+ total mints by end of session (difficulty rising fast — many GPU miners active)
- Genesis complete — mining open
- **Difficulty retargets every 2,016 mints** — with many GPU miners, difficulty can 4x per period

## Difficulty Math
- Difficulty `0x000000003fff...` = probability ~5.82e-11 per hash
- Avg hashes needed: ~17.18 billion
- At 1.7 MH/s (Node.js): ~2.8 hours avg per mint
- At 84 MH/s (64-core C multi-process): ~3.4 minutes avg per mint
- At 543 MH/s (GPU): ~31 seconds avg per mint
- At 2,000+ MH/s (4x RTX 5090): ~8 seconds avg per mint

## RPC
- Use `https://ethereum-rpc.publicnode.com` (reliable, no auth)
- `https://eth.llamarpc.com` has issues (`header not found` errors) — avoid
- RPC does NOT affect hashrate — only used for challenge fetch + tx submit

---

## CPU Mining (Node.js Multi-Process Architecture)

### Architecture: Multiple Independent C Processes (v3 — optimal)
The key insight: spawn N independent C processes, each with own nonce range.
No shared memory, no mutex — pure parallel. Achieves ~99% CPU utilization.

**Why NOT pthreads (v1/v2):** mutex locking + shared state = only ~50% CPU utilization even with 64 threads.
**Why NOT Node.js workers:** ethers.js keccak256 is slow JS — ~1.7 MH/s total regardless of workers.

### miner-solo.c (single-threaded C, no mutex)
```c
// Compile: gcc -O3 -march=native -o miner-solo miner-solo.c
// Usage: ./miner-solo <challenge_hex> <difficulty_hex> <nonce_start> <nonce_step>
// Output: FOUND nonce=0x... hashes=... elapsed=... hashrate=...
```
Key: each process gets `nonce_start=process_id, nonce_step=num_processes`.
No inter-process communication until one finds a nonce (stdout FOUND line).

### miner-v3.js (Node.js orchestrator)
- Fetches challenge + difficulty from contract
- Spawns N `miner-solo` processes
- First FOUND stdout → kills all others → submits tx
- Progress from process 0 stderr only

### Performance (Threadripper 3970X, 32 physical cores / 64 threads)
- 32 processes: ~42 MH/s, ~50% CPU (only physical cores)
- 64 processes: ~84 MH/s, ~99% CPU (hyperthreads contribute too)
- Rule: use `nproc` (logical CPUs), not physical cores, for max throughput

### Setup on VPS
```bash
mkdir -p ~/hash-miner && cd ~/hash-miner
npm install ethers@6
gcc -O3 -march=native -o miner-solo miner-solo.c
cat > start.sh << 'EOF'
#!/bin/bash
cd ~/hash-miner
export PRIVATE_KEY=0x...
export RPC_URL=https://ethereum-rpc.publicnode.com
export WORKERS=$(nproc)
node miner-v3.js 2>&1 | tee -a miner.log
EOF
chmod +x start.sh
screen -dmS hash-miner ./start.sh
```

### Verify CPU utilization
```bash
ps aux | grep miner-solo | grep -v grep | awk '{sum+=$3} END {print "Total CPU%:", sum}'
# Should be close to nproc * 100
```

---

## GPU Mining (CUDA — RTX 5090 verified)

### Architecture
- CUDA kernel: each thread searches independent nonce range
- 4 GPU processes run in parallel (one per GPU), each with `gpu_id` offset
- Node.js orchestrator (miner-gpu.js) spawns 4 CUDA processes, first FOUND wins

### Compile
```bash
# RTX 5090 = sm_120 (Blackwell)
# RTX 4090 = sm_89 (Ada Lovelace)
# RTX 3090 = sm_86 (Ampere)
nvcc -O3 -arch=sm_120 -o hash-miner-cuda hash-miner-cuda.cu
```

### Key CUDA Implementation Notes

**keccak256 input encoding (CRITICAL — must match ethers.js):**
- Input = challenge (32 bytes) + nonce (32 bytes big-endian uint256)
- Nonce fits in uint64 (8 bytes), upper 24 bytes = 0
- Store as little-endian uint64 for keccak state, but nonce bytes must be byte-swapped:
```c
input[7] = (
    ((nonce & 0xffULL) << 56) |
    (((nonce>>8) & 0xffULL) << 48) |
    // ... etc (full byte-swap)
);
```
- Keccak padding: `s[8] ^= 0x01` (byte 64), `s[16] ^= 0x8000000000000000` (byte 135)
- This is Keccak-256 (NOT SHA3-256 — different padding byte: 0x01 vs 0x06)

**Verification against ethers.js:**
```javascript
const hash = ethers.solidityPackedKeccak256(['bytes32','uint256'], [challenge, nonce]);
// Must match CUDA output for same inputs
```

**Launch config (RTX 5090, 170 SMs):**
```c
int threads = 256;
int blocks  = prop.multiProcessorCount * 32; // 5440 blocks
// Total: 1,392,640 threads per GPU
```

**Nonce distribution across 4 GPUs:**
```c
uint64_t nonce_offset = (uint64_t)gpu_id * total_threads;
uint64_t nonce_stride = 4ULL * total_threads; // 4 GPUs
```

### Performance (verified May 2026, v4 CUDA with correct keccak256)
- 1x RTX 5090: ~4,800-5,800 MH/s (4.8-5.8 GH/s)
- 4x RTX 5090: ~19,000-22,000 MH/s (~20 GH/s)
- 1x RTX 4090: ~4,500-5,000 MH/s (user-reported: 4.69 GH/s)
- At 20 GH/s with difficulty `0x0000000000ffffff` (~16M avg hashes): ~1 second per mint
- At 20 GH/s with difficulty `0x000000003fffffff` (~1B avg hashes): ~50 seconds per mint

**NOTE:** v1/v2 CUDA with wrong keccak256 showed ~228 MH/s (fake — hashes were wrong). After fixing keccak256, same hardware jumped to ~4,800 MH/s. The 20x improvement was from fixing the implementation, not hardware change.

### miner-gpu.js (Node.js orchestrator)
```javascript
// Spawns NUM_GPUS processes: ./hash-miner-cuda <challenge> <diffHex> <gpu_id>
// First FOUND stdout wins, kills others, submits tx
export NUM_GPUS=4
```

### Setup on Vast.ai
1. Choose template: **NVIDIA CUDA** (`vastai/base-image`)
2. Launch mode: **Interactive shell server, SSH**
3. Add SSH key to Vast.ai account → restart instance after adding
4. Compile: `nvcc -O3 -arch=sm_120 -o hash-miner-cuda hash-miner-cuda.cu`
5. Install Node.js: `apt-get install -y nodejs npm`
6. `npm install ethers@6`

---

## Custom Error Codes
- `0x4992976a` — hash does not meet difficulty (hash >= difficulty). Means nonce is invalid.
- `0x02a387d3` — also hash-related revert (seen during epoch transitions).
- Gas used ~33,000 on revert = contract executed but rejected nonce. NOT a gas issue.
- Gas used ~83,000-89,000 on success = valid mint.

## CRITICAL: Nonce is Full 256-bit (uint256)

**Successful on-chain nonces are full 32 bytes**, e.g.:
```
0xb9b98f70f0ba7d919db3a9a0ed8027ef5c8115166b04790d61cccd36d4077b84
0x7b354bf392dee2e3872c45d6e0707c087ccb34ddebfa897400000158aab3f797
```

**WRONG approach (v1-v3 CUDA):** Only search 64-bit nonce space (last 8 bytes of uint256, upper 24 bytes = 0). This technically works but severely limits the search space and may cause issues.

**CORRECT approach (v4 CUDA):** Use full 256-bit random base nonce. Each GPU gets a random 32-byte starting point, increments by batch_size each iteration. Output is full 32-byte nonce hex.

```c
// v4: 256-bit nonce base, add uint64 offset per thread
__device__ void add256_64(const uint8_t* base, uint64_t delta, uint8_t* result) {
    for (int i=0;i<32;i++) result[i]=base[i];
    uint64_t carry = delta;
    for (int i=31; i>=0 && carry>0; i--) {
        uint64_t sum = (uint64_t)result[i] + (carry & 0xFF);
        result[i] = (uint8_t)(sum & 0xFF);
        carry = (carry >> 8) + (sum >> 8);
    }
}
```

Node.js orchestrator generates random 32-byte offsets:
```javascript
const rand = crypto.randomBytes(32);
rand[0] &= 0x7F; // keep positive
const offset = '0x' + rand.toString('hex'); // pass as 64-char hex to CUDA binary
```

CUDA binary outputs full 32-byte nonce:
```
FOUND nonce=0x50a03aa59b310a939ee6bfac0e88597fc5e67bddda5284678ca26ab730f8ddf5 gpu=2
```

## CRITICAL: keccak256 CUDA Implementation Must Match ethers.js

**Bug found in v1/v2 CUDA:** Custom keccak256 implementation produced wrong hashes — did not match `ethers.keccak256()`. Symptom: miner runs at full speed, finds "nonces", but ALL TXs revert with `0x4992976a`.

**Verification test** (always run before deploying new CUDA miner):
```bash
# Compile and run test
nvcc -O2 -arch=sm_90 -o test_keccak test_keccak.cu && ./test_keccak
# Must output: MATCH: YES - keccak256 correct!
```

**Correct keccak256 CUDA implementation** — the key is the Rho-Pi step must use the exact rotation schedule and the padding must be `0x01` (Keccak, not SHA3 which uses `0x06`):

```c
// Rho-Pi: must be done as a single chained rotation (not two separate loops)
t=st[1];
t=st[1]; st[1]=ROTL64(st[6],44); st[6]=ROTL64(st[9],20); ... st[10]=ROTL64(t,1);

// Padding for 64-byte input (rate=136):
block[64] = 0x01;   // Keccak padding (NOT 0x06 which is SHA3)
block[135] = 0x80;  // End of rate
```

The verified implementation is in `templates/hash256-cuda-miner-v4.cu`.

## Pitfalls

1. **Wrong ABI** — many community miners use `mint(bytes32, uint256)` — WRONG. Correct is `mine(uint256)`. Also `getChallenge(address)` not `currentEpoch()`.

2. **Challenge generation** — do NOT compute challenge locally. Always fetch from `contract.getChallenge(wallet_address)`. Local computation gives wrong result.

3. **Epoch check in mining loop** — calling RPC every nonce iteration kills hashrate (drops to hundreds H/s). Fetch challenge once per round, only re-fetch after epoch change or successful mint.

4. **Node.js keccak256 speed** — ethers.js `solidityPackedKeccak256` in a tight loop = ~1.7 MH/s regardless of workers. Must use native C or CUDA for real hashrate.

5. **Hyperthreading** — for keccak256 (CPU-bound integer ops), hyperthreading DOES help. Use `nproc` (logical CPUs) not physical cores. 64 logical > 32 physical for this workload.

6. **pthreads mutex overhead** — multi-threaded C with shared `found_flag` and mutex = ~50% CPU. Use independent processes instead (no shared state).

7. **CUDA sm_ version** — RTX 5090 = sm_120, RTX 4090 = sm_89, RTX 3090 = sm_86. Wrong arch flag = slow or won't compile.

8. **Vast.ai SSH key** — must add public key to Vast.ai account settings AND restart instance. Key is injected at container start, not live.

9. **Vast.ai CDI error** — `failed to inject CDI devices: unresolvable CDI devices` = GPU hardware issue on that host. Terminate and pick different instance.

10. **Gas cost** — each successful mint costs ~0.0002-0.0005 ETH gas. Keep wallet funded. 0.01 ETH ≈ 20-50 mints.

20. **10 mints per block limit causes TX reverts** — contract enforces max 10 mints per block. With many GPU miners competing, blocks fill up fast. Symptom: TX reverts with gas ~33,000 (contract executed but rejected). Fix: use **high gas priority** (3x maxFeePerGas, 5x maxPriorityFeePerGas) so TX lands early in block. Check block mint count: `getLogs(topic=Mined, fromBlock=N, toBlock=N)` — if 9-10 events, block was full.

21. **Epoch watcher — kill GPU if challenge changes** — without an epoch watcher, GPU keeps mining old challenge. When epoch rotates, all found nonces are invalid. Add a `setInterval` that polls `getChallenge()` every 20s during mining. If challenge changes, kill all GPU processes immediately and start new round. Without this, you waste 20 minutes mining stale challenge.

22. **Gas estimate `0x4992976a` on valid nonce** — `estimateGas` for `mine(nonce)` can fail even when nonce IS valid if: (a) epoch changed between find and estimate, (b) block already has 10 mints. Use fallback gas 150,000 and submit anyway — TX may still succeed. If TX also reverts, it's one of these two conditions.

23. **Miner binary version mismatch** — miner-gpu-v3.js may still reference `hash-miner-v3` (64-bit nonce) after upgrading to `hash-miner-v4` (256-bit nonce). Always verify: `grep MINER_BIN miner-gpu-v3.js`. If it says `hash-miner-v3`, run `sed -i 's/hash-miner-v3/hash-miner-v4/g' miner-gpu-v3.js` and restart.

24. **Uniswap V4 hook swaps also emit Mined events** — the contract is ERC20 + Uniswap V4 hook + PoW miner. Buying HASH via DEX swap triggers `Mined` event with tiny reward (proportional to swap amount). These are NOT PoW mints. Distinguish by: PoW mints have reward=100 HASH, swap mints have tiny fractional rewards. TX selector for PoW: `0x4d474898` (direct `mine()`). Swap mints go through Uniswap router (`0x3593564c` = Uniswap UniversalRouter).

25. **HASH balance shows 0 after mints** — if `balanceOf(wallet)` returns 0 despite seeing MINED in logs, check: (a) TX actually succeeded (status=1, not just pending), (b) correct contract address in balanceOf call, (c) TX may have been reverted (status=0) despite log showing MINED. Always verify via `eth_getTransactionReceipt` status field.

11. **RPC llamarpc** — `https://eth.llamarpc.com` returns `header not found` errors. Use `https://ethereum-rpc.publicnode.com` instead.

12. **Multi-wallet strategy** — each wallet has independent challenge. Running N wallets = N independent mining streams. No competition between your own wallets.

13. **CUDA keccak256 wrong implementation** — if all TXs revert with `0x4992976a` despite miner running at full speed, the keccak256 CUDA implementation is wrong. Always verify against ethers.js before deploying. See verification test above.

14. **64-bit nonce is technically valid but suboptimal** — the contract accepts any uint256 nonce. Using only 64-bit (upper 24 bytes = 0) works but limits search space. Real miners on-chain use full 256-bit random nonces. Use v4 CUDA binary with full 256-bit nonce.

15. **Gas estimate fails on invalid nonce** — `estimateGas` for `mine(nonce)` will fail with `0x4992976a` if the nonce is invalid (hash >= difficulty OR epoch changed). This is normal — use fallback gas limit 150,000. If gas estimate SUCCEEDS, the nonce is valid and TX will likely succeed.

16. **Epoch change between find and submit** — if epoch changes between when GPU finds nonce and when TX is mined, TX reverts. Mitigation: verify challenge hasn't changed before submitting (`currentChallenge !== challenge → skip`). Use high gas priority (3x maxPriorityFeePerGas) to get mined in next block.

17. **"Each (miner, nonce, epoch) tuple mints once"** — replay protection. Same nonce cannot be used twice in same epoch. If two GPUs find nonces simultaneously, only first TX succeeds. Second TX reverts. This is expected behavior, not a bug.

18. **Vast.ai instance SSH key injection** — SSH key is injected at container START. Adding key to Vast.ai account settings requires instance RESTART to take effect. If SSH fails after adding key, restart the instance.

19. **miningState() field names** — correct names: `era`, `reward`, `difficulty`, `minted`, `remaining`, `epoch`, `epochBlocksLeft`. Wrong names cause `undefined` in JS. The old incorrect names were `totalMints`, `epochBlock`, `currentBlock`, `blocksLeft`.

---

## Cost Comparison (CPU Mining)

| Platform | Instance | Cores | Price | Est. Hashrate |
|---|---|---|---|---|
| QuickPod | 3970X | 64 logical | $0.20/hr | ~84 MH/s |
| QuickPod | 5995WX | 32 threads | $0.72/hr | ~42 MH/s |
| Vast.ai | EPYC 7B12 | 256 cores | $1.60/hr | ~340 MH/s |
| Vast.ai | EPYC 9754 Zen4 | 256 cores | $2.62/hr | ~400 MH/s |
| Hetzner | CCX63 | 48 vCPU | $0.37/hr | ~63 MH/s |

**Best CPU value:** QuickPod 3970X ($0.20/hr, 64 logical cores)

## Cost Comparison (GPU Mining, Vast.ai)

| Instance | GPUs | Price | Est. Hashrate |
|---|---|---|---|
| 4x RTX 5090 | 4 | $1.39/hr | ~2,000 MH/s |
| 5x RTX 5090 | 5 | $2.00/hr | ~2,500 MH/s |
| 2x RTX 4090 | 2 | $0.34/hr | ~1,000 MH/s |
| 5x RTX 4090 | 5 | $1.60/hr | ~2,500 MH/s |

**Best GPU value:** 2x RTX 4090 at $0.34/hr (163 TFLOPS, 99% reliable, ID: 30872860)

## RPC Provider Notes (Vast.ai GPU Mining)

### ethers.js JsonRpcProvider — staticNetwork fix
Some RPC providers (dRPC, certain Ankr endpoints) return HTTP 500 when ethers.js tries to auto-detect the network via `eth_chainId`. The fix is `staticNetwork: true`:

```javascript
// WRONG — causes "server response 500" on dRPC and some providers:
return new ethers.JsonRpcProvider(RPC_URL);

// CORRECT — skip network auto-detection:
return new ethers.JsonRpcProvider(RPC_URL, 1, { staticNetwork: true });
```

Diagnosis: if `curl -X POST RPC_URL -d '{"method":"eth_blockNumber",...}'` works but ethers.js throws 500, it's the network detection call failing. Add `staticNetwork: true`.

### dRPC endpoint format
- URL from dashboard: `https://lb.drpc.live/ethereum/API_KEY`
- Alternative: `https://lb.drpc.org/ogrpc?network=ethereum&dkey=API_KEY`
- Both work via curl from Vast.ai IPs
- Requires `staticNetwork: true` in ethers.js (see above)

### Ankr premium RPC
- Format: `https://rpc.ankr.com/eth/API_KEY`
- If credit runs out, falls back to 401 Unauthorized
- Free alternative: `https://ethereum-rpc.publicnode.com` (reliable, no auth)
- Alchemy free tier: `https://eth-mainnet.g.alchemy.com/v2/API_KEY` — works well

### CUDA comparison difficulty `0x0fffff` vs `0x3fffff`
- `0x3fffff` = ~17B avg hashes needed → ~0.8s at 22 GH/s
- `0x0fffff` = ~4B avg hashes needed → ~0.2s at 22 GH/s (4x easier)
- Difficulty retargets DOWN when global mint rate drops (fewer miners)
- Difficulty retargets UP when global mint rate rises (more miners)

## CUDA keccak256 Output Endianness Bug (CRITICAL — May 2026)

**Root cause of 1+ hour with zero mints:** The CUDA keccak256 output was little-endian per 64-bit word, but the comparison was done big-endian (byte 0 = MSB). This caused ALL nonces to fail silently — miner ran at full speed, found "nonces", but every TX reverted with `0x4992976a`.

**Diagnosis path:**
1. Miner runs at full speed (22 GH/s) but zero mints for 30+ minutes
2. Verify a known-good nonce from a successful on-chain TX: `ethers.keccak256(concat([challenge, nonce32]))` → should produce hash with 10+ leading zeros
3. Run same nonce through CUDA binary — if output differs from ethers.js, keccak256 is wrong
4. Test with empty string: `keccak256("")` should = `0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470`

**The fix:**
```c
// WRONG — little-endian output (bytes within each word are reversed):
for (int i=0;i<4;i++) for (int j=0;j<8;j++) out[i*8+j]=(st[i]>>(j*8))&0xFF;
// This outputs word 0 as: 25 d4 00 00 00 00 00 00 (little-endian)
// But ethers.js expects:   00 00 00 00 00 00 d4 25 (big-endian)

// CORRECT — little-endian output IS correct for keccak256 (matches ethers.js):
// The keccak256 empty string test PASSES with little-endian output!
// The real bug was in the COMPARISON, not the output.
```

**The actual fix was in the comparison initialization:**
```c
// WRONG — valid starts true, causes false positives:
bool valid = true;
for (int j = 0; j < 32; j++) { ... }

// CORRECT — valid starts false, only set true on strict less-than:
bool valid = false;
for (int j = 0; j < 32; j++) {
    if (hash[j] < difficulty[j]) { valid = true; break; }
    if (hash[j] > difficulty[j]) { valid = false; break; }
}
```

**Verification test (always run before deploying):**
```bash
# Compile test binary with known-good nonce
# challenge: 2e0330429428d3780c1567bb74bf1b64e05c35be4802a269650e597a1b9d22a9
# nonce:     9d90e3b1746e1a87f4fe7984574be6a358c9716646145ecda73d3084e24b9054
# expected:  000000000000d425c4d617157220732152ad8e20080182e430677214f8127ff3
./test_keccak  # Must output: Match: YES
```

**How to find a known-good nonce for testing:**
```javascript
// Get recent successful mint from on-chain
const logs = await provider.getLogs({ address: CONTRACT, fromBlock: latest-3, toBlock: latest });
const minted = logs.filter(l => l.topics[0].startsWith('0x94b5f8ac'));
const tx = await provider.getTransaction(minted[0].transactionHash);
const nonce = BigInt('0x' + tx.data.slice(10));
const challenge = await contract.getChallenge(tx.from);
// Verify: ethers.keccak256(concat([challenge, zeroPadValue(toBeHex(nonce), 32)])) should have 10+ leading zeros
```

## CUDA Comparison Logic Bug (CRITICAL)

**Bug found in v4 CUDA:** `valid` initialized to `true` instead of `false` in hash comparison loop.

```c
// WRONG — valid starts true, so ANY hash where first byte matches passes:
bool valid = true;
for (int j = 0; j < 32; j++) {
    if (hash[j] < difficulty[j]) { valid = true; break; }
    if (hash[j] > difficulty[j]) { valid = false; break; }
}

// CORRECT — valid starts false, only set true when hash is strictly less:
bool valid = false;
for (int j = 0; j < 32; j++) {
    if (hash[j] < difficulty[j]) { valid = true; break; }
    if (hash[j] > difficulty[j]) { valid = false; break; }
}
```

Symptom: miner finds nonces quickly but TX reverts with `0x4992976a`. The nonce passes gas estimation (which also uses the wrong logic) but fails on-chain. Fix: change `bool valid = true` → `bool valid = false`. Recompile and restart.

## Vast.ai GPU Instance Selection

### RTX 5090 vs RTX 4090 for keccak256
- RTX 5090: ~5.5-5.9 GH/s per GPU (21760 CUDA cores, sm_120)
- RTX 4090: ~4.5-5.0 GH/s per GPU (16384 CUDA cores, sm_89)
- RTX 5060: ~1.1 GH/s per GPU (entry level)
- A100 SXM4: ~2.5-3.5 GH/s per GPU (NOT optimized for keccak256 — skip)
- RTX Pro 6000: ~6-7 GH/s per GPU (Blackwell workstation, expensive)

### Instance availability strategy
- 4x/8x RTX 5090 instances get rented within minutes when available
- Set up Hermes cronjob to poll Vast.ai API every 5 min and notify via Telegram
- Vast.ai API: `GET https://console.vast.ai/api/v0/bundles/?q={"gpu_name":{"in":["RTX 5090","RTX 4090"]},"num_gpus":{"gte":4},"rentable":{"eq":true},"rented":{"eq":false}}`
- Sort by `dph_total` ascending for best value
- Reliability > 99% preferred; avoid < 95%

### Template selection on Vast.ai
- **NVIDIA CUDA** (`vastai/base-image`) — best, has nvcc ready
- **Hashcat CUDA** (`dizcza/docker-hashcat`) — also works, CUDA 12.8
- **PyTorch / TensorFlow** — works but heavier image
- **Ollama** — works, CUDA available, just ignore the Ollama service

### SSH key injection
- Add key to Vast.ai account settings BEFORE renting
- If added after: must restart instance (key injected at container start)
- SSH command format: `ssh -p PORT root@ssh1.vast.ai` (host varies per instance)

## Multi-Wallet Strategy: 1 Wallet Per VPS (NOT Multi-Wallet Per VPS)

### Tested and Rejected: 2 GPU per wallet, 2 wallets per VPS
Session May 11 2026 tested splitting 4 GPUs into 2x2 (2 wallets per VPS, 2 GPU each):
- **Result: 30+ minutes with 0 mints** — worse than single wallet
- Root cause: 2 GPU per wallet = hashrate halved per wallet = expected time doubled
- Multi-wallet parallelism does NOT compensate because 10 mints/block limit is already filled by competitors
- Conclusion: **maximize hashrate per wallet**, not number of wallets

### Correct Multi-VPS Strategy
- 1 wallet per VPS, all GPUs on that wallet
- Add more VPS instances with different wallets for parallelism
- Each wallet has independent challenge — no collision between VPS instances
- 2 VPS × 4x RTX 5090 = 2 independent ~22 GH/s streams

### Thermal Throttling on Vast.ai (VPS 3 specific)
- GPU 2 & 3 on VPS 3 (ssh7.vast.ai) consistently hit 89-90°C
- Throttles clock from 2800 MHz → 2500-2600 MHz = ~20-30% hashrate loss
- Causes Node.js assertion crash (`void node::ResetStdio()`) when GPU shuts down mid-process
- Vast.ai does NOT allow `nvidia-smi -pl` (power limit) — insufficient permissions
- Fix: terminate instance and rent a different one with better cooling
- Diagnosis: `nvidia-smi --query-gpu=index,temperature.gpu,clocks.current.graphics --format=csv,noheader`
- Warning threshold: >85°C = throttling, >90°C = crash risk

### Difficulty Retarget Observation (May 11 2026)
- Started session at `0x0fffff` (easy)
- Retargeted to `0x3ffff` (4x harder) within ~1 hour
- Global mint rate: ~1,129 mints/hour = ~18-19 mints/minute
- With difficulty `0x3ffff` and 22 GH/s: expected ~3-5 min per mint
- Competitor top miner `0x2cced186...` gets 32 mints per block = massive hashrate advantage

### Vast.ai RTX 5090 Availability
- 4x/8x RTX 5090 instances are frequently fully rented
- When available, they get taken within minutes
- No 6x+ RTX 5090 instances observed available during this session
- B200 ($14/hr) and H100 ($25/hr) are NOT worth it for keccak256 — worse hashrate/$ than 5090
- Best fallback: 4x RTX 4090 (~$0.68/hr, ~18-20 GH/s total)

## Verified Working Setup (May 11, 2026)
- **VPS:** Vast.ai 4x RTX 5090, template NVIDIA CUDA, ssh -p 24790 root@ssh7.vast.ai
- **Binary:** hash-miner-v4 (CUDA, sm_90, full 256-bit nonce, verified keccak256)
- **Orchestrator:** miner-gpu-v3.js (Node.js, epoch watcher, gas 3x/5x)
- **RPC:** Ankr premium `https://rpc.ankr.com/eth/cb700ec566f02ba870e1bc736145f254e75d6e379c56a1297c6b67f82629b257`
- **Hashrate:** ~22 GH/s (4x ~5.5 GH/s each)
- **Start command:**
```bash
screen -dmS hash-gpu bash -c 'PRIVATE_KEY=0x... RPC_URL=https://rpc.ankr.com/eth/... NUM_GPUS=4 node miner-gpu-v3.js 2>&1 | tee miner-gpu.log'
```
