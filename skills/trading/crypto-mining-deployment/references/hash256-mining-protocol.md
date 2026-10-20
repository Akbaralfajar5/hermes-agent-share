# $HASH Mining Protocol (hash256.org)

## Overview

$HASH is an ERC-20 token on Ethereum mainnet mined via browser-based keccak256 PoW.
Contract: `0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc` ← **CORRECT address** (verified from hash256.org footer → Etherscan)
(Note: `0x0000000000B8c862F2a57372E4F4Bb7e1E3F7E7E` was wrong — empty address, no bytecode — do not use)

### ⚠️ ALWAYS VERIFY CONTRACT HAS BYTECODE BEFORE STARTING

Wrong contract = silent failure. GPU runs at full speed, no errors in log, zero mints forever.
```bash
curl -s -X POST https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getCode","params":["0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc","latest"],"id":1}' \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print('Has code:', len(r['result']) > 4)"
# Must print: Has code: True
```


## Mining Algorithm

```
challenge = keccak256(abi.encode(chainId, contractAddress, minerAddress, epoch))
valid if: keccak256(challenge ‖ nonce) < currentDifficulty
```

- Challenge is **per-wallet** — each address gets a unique challenge
- Challenge rotates every epoch (~100 blocks, ~20 min)
- Nonce is **full uint256 (256-bit)** — search space is 2^256
- Replay protection: each (miner, nonce, epoch) tuple mints once

## 🚨 CRITICAL: Nonce Must Be Full 256-bit

**This was the root cause of all TX reverts in May 2026.**

Early miner versions used 64-bit nonce (stored in last 8 bytes of 32-byte buffer). The contract accepts any uint256 nonce, but successful miners in the wild use **full 256-bit random nonces**.

**Wrong (64-bit nonce in last 8 bytes):**
```c
// nonce_buf = [0x00 * 24] + [8 bytes of nonce]
for (int j = 0; j < 24; j++) input[32+j] = 0;
for (int j = 0; j < 8; j++)
    input[32 + 24 + j] = (nonce >> (56 - j*8)) & 0xFF;
```

**Correct (full 256-bit nonce):**
```c
// nonce_base = random 32 bytes, incremented per thread
// Each thread: nonce = nonce_base + thread_id
add256_64(nonce_base, thread_id, nonce);
for (int j = 0; j < 32; j++) input[32+j] = nonce[j];
```

**Why it matters:** The contract's custom error `0x4992976a` fires when the nonce is invalid. With 64-bit nonce, the hash was technically valid (< difficulty) but the contract rejected it — likely because the nonce space was too small or there's a minimum nonce size check.

**Observed in successful on-chain TXs:** Nonces like `0x88bc052f5e551281c5d3e5a6f01483104615e3438f96eee0d91deb4a09299399` — full 32 bytes of entropy.

## Contract ABI (relevant methods)

```json
[
  { "type": "function", "name": "mine", "stateMutability": "nonpayable",
    "inputs": [{ "name": "nonce", "type": "uint256" }] },
  { "type": "function", "name": "getChallenge", "stateMutability": "view",
    "inputs": [{ "name": "miner", "type": "address" }],
    "outputs": [{ "type": "bytes32" }] },
  { "type": "function", "name": "currentDifficulty", "stateMutability": "view",
    "inputs": [], "outputs": [{ "type": "uint256" }] },
  { "type": "function", "name": "miningState", "stateMutability": "view",
    "inputs": [], "outputs": [
      { "name": "era", "type": "uint256" },
      { "name": "reward", "type": "uint256" },
      { "name": "difficulty", "type": "uint256" },
      { "name": "minted", "type": "uint256" },
      { "name": "remaining", "type": "uint256" },
      { "name": "epoch", "type": "uint256" },
      { "name": "epochBlocksLeft", "type": "uint256" }
    ]}
]
```

**Mined event topic:** `0x7c79f7e2d6a937218f79ecfcfa53746a3a6b942a3ac07439b606d982eb2fa6f0`
(Not `Mined(address,uint256,uint256)` — use topic hash to query logs)

## Tokenomics

- Era 1 reward: **100 HASH per mint**
- Total supply cap: 21,000,000 HASH
- Max 10 mints per block
- Difficulty retarget: every 2,016 mints (targets 1 mint/min globally)
- Immutable contract — no admin keys, no upgrade path
- Genesis sale: 1,050,000 HASH @ 0.01 ETH per 1,000 HASH
- LP: 1,050,000 HASH locked in Uniswap V4 ETH/HASH pool

## Contract Architecture Note

The contract is **ERC20 + Uniswap V4 hook + PoW miner** in one. This means:
- `Mined` events fire both from direct `mine()` calls AND from Uniswap V4 swaps (hook)
- Most on-chain `Mined` events are from DEX swaps, not PoW mining
- Direct `mine()` calls (selector `0x4d474898`) are the actual PoW miners
- Don't confuse swap-triggered events with PoW mining when analyzing on-chain activity

## Multi-Wallet Strategy

- Each wallet has its own challenge → independent mining
- Multiple wallets = multiple parallel mining streams
- Each wallet needs ETH for gas on submit (~90K gas per mint)

## 🚨 CRITICAL: CUDA keccak256 Bug

**Symptom:** GPU miner runs for hours, 100B+ hashes, zero nonces found, zero TX submitted.

**Root cause:** Incorrect keccak256 implementation in CUDA — output does not match ethers.js/Solidity.

**Diagnosis:** Compare CUDA output vs ethers.js for same input:
```js
// ethers.js reference (correct)
const hash = ethers.keccak256('0x' + challenge_hex + nonce_hex_padded_64);
// Must match CUDA output byte-for-byte
```

**The bug:** The rho/pi step in keccakf() was using a generic loop with wrong index mapping. The correct implementation uses explicit unrolled rho-pi with exact rotation constants.

**Fix — correct keccakf() rho-pi step:**
```c
// WRONG (generic loop, wrong index mapping):
for (int i=0;i<24;i++) {
    int x=keccak_pi[i]%5, y=keccak_pi[i]/5;
    B[i+1] = ROTL64(state[keccak_pi[i]], keccak_rho[i]);
}

// CORRECT (explicit unrolled, verified against ethers.js):
t = st[1];
st[1]=ROTL64(st[6],44); st[6]=ROTL64(st[9],20); st[9]=ROTL64(st[22],61);
st[22]=ROTL64(st[14],39); st[14]=ROTL64(st[20],18); st[20]=ROTL64(st[2],62);
st[2]=ROTL64(st[12],43); st[12]=ROTL64(st[13],25); st[13]=ROTL64(st[19],8);
st[19]=ROTL64(st[23],56); st[23]=ROTL64(st[15],41); st[15]=ROTL64(st[4],27);
st[4]=ROTL64(st[24],14); st[24]=ROTL64(st[21],2); st[21]=ROTL64(st[8],55);
st[8]=ROTL64(st[16],45); st[16]=ROTL64(st[5],36); st[5]=ROTL64(st[3],28);
st[3]=ROTL64(st[18],21); st[18]=ROTL64(st[17],15); st[17]=ROTL64(st[11],10);
st[11]=ROTL64(st[7],6); st[7]=ROTL64(st[10],3); st[10]=ROTL64(t,1);
```

**Also critical — padding:** For 64-byte input (32-byte challenge + 32-byte nonce), use Keccak (not SHA3) padding:
```c
block[64] = 0x01;   // Keccak padding (NOT 0x06 which is SHA3)
block[135] = 0x80;  // rate = 136 bytes
```

**Bonus:** Fixing the keccak256 also unlocked full GPU throughput — hashrate jumped from ~228 MH/s to ~4,800 MH/s per RTX 5090 (21x improvement). The wrong implementation was preventing compiler optimization.

**Verification test before running full miner:**
```bash
# Input: challenge=147e6b95...b233, nonce=1
# Expected: 0xfce6649a12704d5502456ad9a108fdb547793cd2f49de019a441f9ff7f730907
nvcc -O2 -arch=sm_90 -o test_keccak test_keccak.cu && ./test_keccak
# Must print: MATCH: YES
```

## Custom Error Codes

| Selector | Meaning |
|----------|---------|
| `0x4992976a` | Invalid nonce (wrong nonce format, already used, or epoch mismatch) |
| `0x02a387d3` | Unknown — seen during TX reverts |

## Hashrate Reference (May 2026)

| Setup | Hashrate | Notes |
|-------|----------|-------|
| RTX 4090 (1x) | ~4,690 MH/s | 777B hashes in 165.74s |
| RTX 5090 (4x) — v4 fixed | ~5,500-5,900 MH/s per card = ~22-23 GH/s total | Observed: GPU0=5.9, GPU1=5.8, GPU2=5.5, GPU3=5.7 GH/s |
| RTX 5090 (8x) — estimated | ~44-46 GH/s | 2x VPS 3 — best available config on Vast.ai |
| RTX 5060 Ti (4x) — v4 fixed | ~1,100 MH/s per card = ~4.4 GH/s total | sm_120, CUDA 13.0, compute cap 12.0 |
| RTX 5090 (4x) — v3 fixed keccak only | ~4,800 MH/s per card | Correct keccak256, but 64-bit nonce (TX reverts) |
| RTX 5090 (4x) — v2 broken | ~228 MH/s per card | Wrong keccak256 |
| A100 SXM4 (4x) | ~10-14 GH/s estimated | NOT recommended — AI/ML GPU, keccak256 not optimal. $4-6.7/hr but hashrate lower than 4x RTX 5090 |
| CPU 64-core (C multi-process) | ~84 MH/s | |
| CPU 20-core Threadripper | ~27 MH/s | |

### GPU Selection for keccak256 Mining

**Best:** RTX 5090 > RTX 4090 > RTX 3090 (gaming GPUs — high CUDA core count + high clock)
**Avoid:** A100, H100, A6000 (AI/ML GPUs — optimized for matrix ops, not hash loops)

A100 SXM4 has 6,912 CUDA cores @ 1.41 GHz vs RTX 5090's 21,760 cores @ 2.4 GHz.
For keccak256, raw CUDA core count × clock speed matters more than memory bandwidth or TFLOPS.

## Gas Reference

- Successful `mine()` TX: ~83,000-90,000 gas
- Failed/reverted TX: ~33,306 gas (contract executes but reverts)
- Gas limit to use: `estimateGas * 1.3` (30% buffer)

### 🚨 CRITICAL: Priority Fee Must Be Hardcoded High

**Root cause of TX reverts even with valid nonce:** 10 mints per block limit + 29+ competing mine() TXs per block.

**Observed competitor priority fees:** 20 gwei hardcoded (not dynamic)
**Our dynamic fee (5x base):** ~0.00036 gwei — 55,000x lower than competitors → always loses race

**Fix — hardcode priority fee:**
```js
// WRONG — dynamic fee is near-zero on Ethereum mainnet
maxPriorityFeePerGas: feeData.maxPriorityFeePerGas * 5n  // ~0.00036 gwei

// CORRECT — hardcode competitive fee
maxFeePerGas: feeData.maxFeePerGas + ethers.parseUnits("30", "gwei"),
maxPriorityFeePerGas: ethers.parseUnits("25", "gwei"),  // beats 20 gwei competitors
```

**Cost breakdown (May 2026, ETH=$2,333):**
- 25 gwei priority + 0.12 gwei base = ~25.1 gwei total
- 89,468 gas × 25.1 gwei = 0.00225 ETH ≈ **$5.24 per mint**
- Break-even HASH price: **$0.052/HASH**
- Genesis price was $0.03/HASH → mining at 25 gwei is currently unprofitable unless HASH price rises

**Lower fee option (10-15 gwei):**
- 10 gwei → ~$2.10/mint, break-even $0.021/HASH
- Risk: may lose race to 20 gwei competitors → TX reverts (gas still consumed)

## VPS Setup (May 2026)

- VPS 1: 64-core, 125GB RAM — `ssh -p 33744 ...@73.101.83.132` (may be expired)
- VPS 2: AMD Threadripper PRO 5995WX, 20-core, 40GB RAM — `ssh -p 44001 ...@84.242.173.26`
- VPS 3: Vast.ai 4x RTX 5090, 256 CPU, 503GB RAM — `ssh -p 24790 root@ssh7.vast.ai` ✅ ACTIVE
- VPS 4: Vast.ai 4x RTX 5060 Ti, 128 CPU, 503GB RAM — `ssh -p 46351 root@38.247.78.5`
- Wallet VPS 3: `0xFA8d81089006aeAD923378e744B7769d7935952C`
- Wallet VPS 4: `0x6D49A15C023672F5ceD4F00523E569b731786408`

## Vast.ai Instance Hunting

### Search API (working endpoint May 2026)
```bash
# Find available RTX 4090/5090 instances, min 4 GPUs, not rented
curl -s "https://console.vast.ai/api/v0/bundles/?q=%7B%22gpu_name%22%3A%7B%22in%22%3A%5B%22RTX+5090%22%2C%22RTX+4090%22%5D%7D%2C%22num_gpus%22%3A%7B%22gte%22%3A4%7D%2C%22rentable%22%3A%7B%22eq%22%3Atrue%7D%2C%22rented%22%3A%7B%22eq%22%3Afalse%7D%7D" | python3 -c "
import json, sys
data = json.load(sys.stdin)
offers = data.get('offers', [])
results = []
for o in offers:
    results.append({
        'id': o.get('id'),
        'gpu': o.get('gpu_name'),
        'num_gpus': o.get('num_gpus'),
        'price': o.get('dph_total'),
        'reliability': o.get('reliability2'),
        'country': o.get('geolocation'),
        'cuda': o.get('cuda_max_good'),
    })
results.sort(key=lambda x: x['price'] or 999)
for r in results[:15]:
    print(f\"ID:{r['id']} | {r['num_gpus']}x {r['gpu']} | \${r['price']:.3f}/hr | Reliability:{r['reliability']:.2%} | {r['country']} | CUDA:{r['cuda']}\")
"
```

### Instance Availability Notes
- **8x RTX 5090 instances get rented within minutes** — act immediately when spotted
- Good 4x RTX 5090 instances also go fast during active mining periods
- **Best value found:** 8x RTX 4090 Hong Kong @ $2.136/hr, reliability 99.18% (ID:32083932)
- **Best 4x RTX 5090:** Canada @ $1.277/hr, reliability 99.67% (ID:32984234)
- A100 SXM4 instances are NOT worth it for keccak256 — lower hashrate than RTX 5090 at same/higher price
- Sort by `dph_total` (price) and filter reliability > 99% for stable long-term instances
- **Connection refused after SSH command appears:** Normal — wait 1-2 min for full boot

### What to Look For
Priority order:
1. 8x RTX 5090 — ~44 GH/s, best ROI if price reasonable
2. 4x RTX 5090 — ~22 GH/s, proven setup (VPS 3)
3. 8x RTX 4090 — ~36-40 GH/s, cheaper and more available
4. 4x RTX 4090 — ~18-20 GH/s, most available option

Skip: A100, H100, V100, A6000 — all AI/ML GPUs, poor keccak256 performance per dollar.

### RTX 5060 Ti Compile Note
RTX 5060 Ti uses compute capability 12.0 → compile with `sm_120`:
```bash
nvcc -O3 -arch=sm_120 -o hash-miner-v4 hash_miner_v4.cu
```
`nvidia-smi` may not be in PATH on some Vast.ai instances — use `/usr/bin/nvidia-smi` explicitly.

## Miner Files Location

`/root/hash-miner/` on all VPS:
- `hash_miner.c` / `hash_miner` — C binary for CPU keccak256
- `hash_miner_v3.cu` / `hash-miner-v3` — CUDA binary (fixed keccak256, but 64-bit nonce — TX reverts)
- `hash_miner_v4.cu` / `hash-miner-v4` — CUDA binary (fixed keccak256 + full 256-bit nonce ✅ USE THIS)
- `miner-v3.js` — Node.js wrapper for CPU miner
- `miner-gpu-v3.js` — Node.js wrapper for GPU miner (uses hash-miner-v4, Ankr RPC, challenge verify before submit)
- `start.sh` — contains PRIVATE_KEY env var
- `test_keccak_v3.cu` — verification test (CUDA vs ethers.js)

## Screen Sessions

- CPU miner: `screen -S hash-miner`
- GPU miner: `screen -S hash-gpu`
- Log: `tail -f /root/hash-miner/miner.log` or `miner-gpu.log`

## Node.js Wrapper Best Practices

1. **Always verify challenge before submitting** — fetch `getChallenge()` again after nonce found, skip if changed
2. **Use single premium RPC** — don't rotate to public RPCs (drpc, mevblocker have rate limits)
3. **Fresh provider per round** — create new `JsonRpcProvider` each loop iteration
4. **Hardcode priority fee 25 gwei** — dynamic fee is near-zero on mainnet, always loses to competitors
5. **`lastChallenge = ''` on any error** — always force challenge refresh after failure
6. **Epoch watcher** — poll `getChallenge()` every 20s while GPU is mining, kill processes if epoch changes:
   ```js
   const epochWatcher = setInterval(async () => {
     if (done) { clearInterval(epochWatcher); return; }
     const newChallenge = await contract.getChallenge(wallet.address);
     if (newChallenge !== challenge) {
       done = true; clearInterval(epochWatcher);
       procs.forEach(p => p.kill('SIGTERM'));
       reject(new Error('EPOCH_CHANGED'));
     }
   }, 20000);
   ```
7. **Timeout 10 min** — epoch is ~20 min but refresh early to avoid stale nonce

## Pitfall: add256_64 Nonce Corruption Pattern

**Symptom:** Found nonces contain repeating byte patterns like `0x00ccf0f1facb57d5d5d5d5d5d5d5d5d5d5d5d5d5d50c0c0e0ecb704d49fdbbc3` — lots of `d5` or `8a` repeating.

**Cause:** Bug in `add256_64()` CUDA device function — carry propagation overflows into a repeating pattern when the base nonce has certain byte values.

**Impact:** The hash may still be valid (< difficulty) and TX may still succeed. This is a cosmetic bug, not a correctness bug for mining purposes. However, it means the nonce space being searched is not truly random — some regions are skipped.

**Status (May 2026):** Not fixed — mining still works despite the pattern. Low priority fix.

**If fixing:** The carry loop in `add256_64` needs to handle multi-byte carry correctly:
```c
__device__ void add256_64(const uint8_t* base, uint64_t delta, uint8_t* result) {
    for (int i=0;i<32;i++) result[i]=base[i];
    uint64_t carry=delta;
    for (int i=31;i>=0&&carry>0;i--) {
        uint64_t sum=(uint64_t)result[i]+(carry&0xFF);
        result[i]=(uint8_t)(sum&0xFF);
        carry=(carry>>8)+(sum>>8);  // carry must propagate ALL bits, not just low byte
    }
}
```

## Difficulty Display Bug in Node.js Wrapper

**Symptom:** Log shows `Difficulty: 0x000000000003ffff...` which looks tiny/easy, but mining never succeeds.

**Root cause:** `difficulty.toString(16)` for value `0x3ffffffffffffffffffffffffffffffffffffffffffffffffffff` (53 hex chars) gets padded with `padStart(64, '0')` → becomes `0x000000000003ffff...` in the log. The **actual value passed to GPU binary is correct** — the display is just misleading.

**Verify actual difficulty:**
```bash
node -e "
const {ethers}=require('ethers');
const p=new ethers.JsonRpcProvider('https://ethereum.publicnode.com',1,{staticNetwork:true});
const c=new ethers.Contract('0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc',
  [{type:'function',name:'currentDifficulty',stateMutability:'view',inputs:[],outputs:[{type:'uint256'}]}],p);
c.currentDifficulty().then(d=>{
  console.log('Raw hex:', '0x'+d.toString(16));
  console.log('Bit length:', d.toString(2).length);
  console.log('Expected nonces:', (2n**(256n-BigInt(d.toString(2).length))).toString());
}).catch(console.error);
"
```

**Difficulty `0x3fff...fff` (210 bits) math:**
- Expected nonces per mint: `2^(256-210)` = `2^46` ≈ **70 trillion**
- At 22 GH/s: `70e12 / 22e9` ≈ **53 minutes per mint** (expected average)
- This is correct and normal — mining is probabilistic, could be 10 min or 2 hours
- Top miners getting 32 mints/block imply ~187 TH/s hashrate (8500x our setup)

## Verifying Mint Came From Our Wallet (Not Competitors)

**Critical:** When a mint appears on-chain near the time you're mining, do NOT assume it's yours. Always verify.

**Wrong approach:** Seeing a `Mined` event in the same block as your mining session and claiming success.

**Correct verification:**
```bash
# Check wallet TX count (nonce) — if it increased, we submitted a TX
curl -s -X POST https://ethereum.publicnode.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getTransactionCount","params":["YOUR_WALLET","latest"],"id":1}'
# Compare to nonce before mining session started

# Check miner log for "✓ GPU found!" or "MINED" — if absent, we didn't mint
grep -E "MINED|found!|✓" /root/hash-miner/miner-gpu.log | tail -10

# Check if any round ended with FOUND vs EPOCH_CHANGED
grep -E "EPOCH_CHANGED|✓ GPU" /root/hash-miner/miner-gpu.log | tail -20
# If all rounds end with EPOCH_CHANGED → zero mints from us
```

**Lesson (May 2026):** Gue salah klaim mint berhasil karena ada `Mined` event di block 25070726 saat binary baru di-deploy. Ternyata itu dari miner lain. Wallet kita punya 67 TX tapi semua dari sebelum sesi ini. Setiap round di log berakhir dengan `EPOCH_CHANGED`, bukan `FOUND`.

## Per-Wallet Difficulty (CONFIRMED May 2026)

$HASH contract has **per-miner difficulty adjustment** — the more mints from a single wallet, the harder the difficulty becomes for that wallet specifically.

**Observed:** After 7 mints from `0xFA8d81089006aeAD923378e744B7769d7935952C`, user noted "makin banyak mint makin sulit" and requested wallet rotation.

**Strategy:**
- Rotate wallet every **5-10 mints** to maintain optimal difficulty
- Keep old wallet's ETH — transfer to new wallet or use for gas on other wallets
- Each new wallet starts at base difficulty
- With 4x RTX 5090 (~22 GH/s), rotating every 7 mints is a good cadence

**Wallet rotation workflow:**
1. Generate new wallet: `node -e "const {ethers}=require('ethers'); const w=ethers.Wallet.createRandom(); console.log(w.address, w.privateKey)"`
2. Update `PRIVATE_KEY` in `.env` or `start.sh`
3. Transfer ETH from old wallet to new wallet (keep ~0.005 ETH in old for gas)
4. Restart miner: `screen -S hash-gpu -X stuff "^C"` then `bash start.sh`
5. Send new wallet address + PK to user

## Competition Analysis (May 2026)

- ~29 mine() TXs per block competing for 10 slots
- Top miners use 20 gwei priority fee hardcoded
- Block time ~12 seconds → ~2.5 mints/block on average
- At 22 GH/s (4x RTX 5090), expected ~1 nonce per 45-70 seconds
- With 25 gwei priority fee, TX consistently lands in top 10 of block

## Quick Deploy (new VPS)

```bash
cd hash-miner
bash setup.sh
# Edit .env → set PRIVATE_KEY
# Send ETH to wallet address
bash start.sh
```
