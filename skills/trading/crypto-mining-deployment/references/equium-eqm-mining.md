---
name: equium-eqm-mining
description: Mine $EQM (Equium) on Solana — Equihash (96,5) PoW token. UPDATED May 2026 with wgpu segfault fix + CUDA bypass. Covers protocol research, wallet generation, GPU miner setup (wgpu hybrid), VPS deployment, and token economics.
triggers:
  - equium
  - EQM mining
  - equihash solana
  - mine EQM
  - equium-gpu-miner
---

# Equium ($EQM) Mining

## Protocol Overview

**Chain:** Solana mainnet (SPL Token + Token-2022)
**Algorithm:** Equihash (96, 5) — same as Zcash, memory-hard, CPU-friendly by design
**Program ID:** `ZKGMUfxiRCXFPnqz9zgqAnuqJy15jk7fKbR4o6FuEQM`
**Token mint:** `1MhvZzEe8gQ8Rb9CrT3Dn26Gkn9QRErzLMGkkTwveqm`
**Repo:** https://github.com/HannaPrints/equium

## How Mining Works

Input block `I`:
```
I = "Equium-v1" || current_challenge[32] || miner_pubkey[32] || block_height_le[8]
```

Per nonce attempt:
1. Generate **131,072 BLAKE2b leaves** (60-byte output, ZcashPoW personalization, n=96, k=5)
2. Run **5 Wagner rounds** (sort + XOR-and-pair birthday collision)
3. Check: `sha256(solution_indices || I) < target`
4. Submit to Solana if valid

**Anti-front-running:** miner pubkey is baked into `I` — a valid nonce for wallet A is invalid for wallet B.

**Challenge rotation:** `sha256(prev_challenge || winner_pubkey || open_slot_hash)`

## Token Economics

| Parameter | Value |
|-----------|-------|
| Total supply | 21,000,000 EQM (hard cap) |
| Mineable | 18,900,000 EQM (90%) |
| Premine | 2,100,000 EQM (10% — DEX liquidity + treasury) |
| Block reward | **25 EQM** (initial) |
| Block target | ~1 minute |
| Halving | every 378,000 blocks (~8.6 months) |
| Retarget | every 60 blocks (~1 hour), ±2x clamp |
| Fee per mint | < 0.001 SOL |

Empty rounds permanently burn the reward — real fixed supply.

## ✅ CUDA Workaround for wgpu Segfault (WORKING — May 2026)

The official wgpu GPU miner segfaults on all NVIDIA/Vulkan instances (GitHub issue #4, unfixed). **We built a CUDA bypass that works.**

### How the fix works

1. Write a standalone CUDA binary (`eqm_leaves.cu`) that does BLAKE2b leaf generation on GPU
2. Replace `gpu.rs` to call this binary via subprocess instead of wgpu
3. Patch `main.rs` to accept `Option<Arc<GpuLeafGen>>` with CPU fallback

**Result:** `GPU backend: NVIDIA CUDA (eqm-leaves binary)` — no segfault, confirmed working on 4× RTX 5060 Ti (sm_120, driver 590.x).

### Deploy the CUDA fix

```bash
cd /root/equium

# 1. Compile CUDA leaf generator (sm_120 for RTX 5060 Ti / RTX 5090 Blackwell)
#    Use sm_89 for RTX 4090, sm_86 for RTX 3090
nvcc -O3 -arch=sm_120 -o eqm-leaves eqm_leaves.cu

# 2. Verify CUDA output matches CPU reference (MUST match before mining)
python3 -c "
import subprocess, hashlib, struct
input_bytes = bytearray(81)
input_bytes[:9] = b'Equium-v1'
for i in range(9, 81): input_bytes[i] = (i * 7 + 13) % 256
nonce_bytes = bytearray(32)
for i in range(32): nonce_bytes[i] = (i * 31 + 2) % 256
result = subprocess.run(['./eqm-leaves', input_bytes.hex(), nonce_bytes.hex(), '10'], capture_output=True, text=True)
cuda_out = result.stdout.strip()
personal = b'ZcashPoW' + struct.pack('<II', 96, 5)
cpu_leaves = bytearray()
for call_idx in range(2):
    msg = bytes(input_bytes) + bytes(nonce_bytes) + struct.pack('<I', call_idx)
    h = hashlib.blake2b(msg, digest_size=60, person=personal)
    digest = h.digest()
    for k in range(5): cpu_leaves += digest[k*12:(k+1)*12]
print('MATCH:', cuda_out == cpu_leaves.hex())
"
# Must print: MATCH: True

# 3. Replace gpu.rs with CUDA subprocess version (from templates/gpu_cuda.rs)
# 4. Patch main.rs (from templates/main_patched_diff.md)
# 5. Rebuild
source $HOME/.cargo/env
cargo build --release -p equium-gpu-miner

# 6. Run GPU miner
screen -dmS eqm-gpu bash -c 'cd /root/equium && ./target/release/equium-gpu-miner mine \
  --rpc-url "https://mainnet.helius-rpc.com/?api-key=YOUR_KEY" \
  --keypair ~/.config/solana/eqm-keypair.json \
  --threads 0 2>&1 | tee /root/eqm-gpu.log'
```

### BLAKE2b CUDA bug found during development

**Critical bug:** BLAKE2b param block word 0 must use `digest_len = 60 = 0x3c`, NOT `0x60 = 96`.

```c
// WRONG — 0x60 = 96, not 60
h[0] ^= (uint64_t)0x0000000001010060ULL;

// CORRECT — 0x3c = 60
h[0] ^= (uint64_t)0x000000000101003cULL;  // digest_len=60(0x3c), fanout=1, depth=1
```

This caused CUDA output to not match CPU reference. Always verify with the Python check above before mining.

### main.rs patches required

Three changes to `main.rs` to support optional GPU:

1. `mine()` header: `let gpu = Arc::new(gpu::GpuLeafGen::new()?)` → `let gpu_opt: Option<Arc<...>> = match gpu::GpuLeafGen::new() { Ok(g) => Some(Arc::new(g)), Err(e) => { println!("WARNING: {e}"); None } };`
2. Call site: `race_for_solution_gpu(gpu.clone(),` → `race_for_solution_gpu(gpu_opt.clone(),`
3. `race_for_solution_gpu` signature: `gpu: Arc<GpuLeafGen>` → `gpu: Option<Arc<GpuLeafGen>>`
4. Worker leaf gen: replace `gpu.generate(...)` with `match &gpu { Some(g) => g.generate(...), None => cpu_leaves_into(...) }`
5. Add `cpu_leaves_into()` function before the CPU reference section

See `templates/gpu_cuda.rs` for the single-nonce replacement `gpu.rs`.
See `templates/gpu_cuda_batch.rs` for the batch version (better GPU utilization).
See `templates/eqm_leaves_batch.cu` for the batch CUDA kernel.
See `templates/start-4gpu.sh` for the 4-GPU multi-instance startup script.
See `references/wgpu-nvidia-segfault.md` for full patch details and 4-GPU setup.

## ⚠️ GPU Miner Status (May 2026): wgpu STILL BROKEN on NVIDIA/Vulkan

**Official wgpu GPU miner segfaults on ALL NVIDIA instances tested** — GitHub issue #4.

- Crash point: `create_compute_pipeline` after wgpu initializes Vulkan adapter
- Affects: RTX 5060 Ti (driver **575.x, 580.x, AND 590.x**), RTX 4090 (driver 570.x), Ubuntu 22.04/24.04 headless
- `verify-cpu` passes fine — only GPU path crashes
- `catch_unwind` does NOT help — crash is a SIGSEGV from the driver, not a Rust panic
- **v0.4.1 (May 12 2026)** added `EQUIUM_BACKEND=gl` escape hatch and `cloud-mine.sh` bootstrap, but GL backend also fails on headless containers (no compute shader support via EGL)
- **v0.2 (May 11 2026)** added full GPU Wagner pipeline (`rounds.wgsl`) — but still blocked by the same wgpu/NVIDIA crash

### v0.4.1 escape hatches (try these first before CUDA bypass)

```bash
# Option 1: Force OpenGL backend (different SPIR-V path, dodges Vulkan bug)
EQUIUM_BACKEND=gl ./target/release/equium-gpu-miner verify
# Fails on headless containers: compute shader not supported via EGL
# Confirmed failing on: driver 575.x, 580.x, 590.x — ALL headless Vast.ai instances

# Option 2: Use cloud-mine.sh bootstrap (auto-probes backends)
curl -fsSL https://raw.githubusercontent.com/HannaPrints/equium/master/scripts/cloud-mine.sh -o cloud-mine.sh
chmod +x cloud-mine.sh
EQUIUM_RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_KEY ./cloud-mine.sh
# cloud-mine.sh auto-detects 575.x driver and warns; probes vulkan then gl
# Also fails on headless — same root cause
```

**→ If both escape hatches fail, use the CUDA bypass above, or CPU miner as fallback.**

## GPU Miner (Official — wgpu Hybrid)

**NOT CUDA** — uses `wgpu` (cross-platform: Vulkan on Linux, Metal on macOS, DX12 on Windows).

### Roadmap status (May 12, 2026)

- **v0.1** ✅ Hybrid: GPU BLAKE2b leaves + CPU Wagner
- **v0.2** ✅ Full GPU Wagner pipeline (`rounds.wgsl`) — committed May 11 2026
- **v0.3** ✅ All 5 Wagner rounds on GPU — committed May 11 2026
- **v0.4** ✅ WebGPU browser miner — committed May 11 2026
- **v0.4.1** ✅ cloud-mine.sh bootstrap, per-GPU workgroup tuning, NVIDIA 575 escape hatch — May 12 2026

**BUT:** All versions still crash on NVIDIA/Vulkan headless (wgpu SPIR-V bug). Wagner GPU code exists but is unreachable until the driver crash is fixed.

Current status (v0.4.1):
- GPU handles BLAKE2b leaf generation + Wagner rounds (in theory)
- In practice: crashes before any GPU work on NVIDIA Linux headless
- CPU miner or CUDA bypass are the only working options on Vast.ai

### Build & Run

```bash
git clone https://github.com/HannaPrints/equium.git
cd equium

# Build GPU miner
cargo build --release -p equium-gpu-miner

# Verify GPU output matches CPU reference
./target/release/equium-gpu-miner verify

# Benchmark leaf throughput
./target/release/equium-gpu-miner bench

# Mine
./target/release/equium-gpu-miner mine \
  --rpc-url https://mainnet.helius-rpc.com/?api-key=YOUR_KEY \
  --keypair ~/.config/solana/eqm-keypair.json \
  --threads 8
```

### CPU-only miner (PRIMARY until GPU bug fixed)

Package name is `equium-cli-miner` (NOT `equium-cpu-miner` — that doesn't exist).
Binary produced: `./target/release/equium-miner`

```bash
cargo build --release -p equium-cli-miner

./target/release/equium-miner \
  --rpc-url https://mainnet.helius-rpc.com/?api-key=YOUR_KEY \
  --keypair /tmp/eqm-keypair.json \
  --threads $(nproc)
```

**CPU-only VPS (no GPU at all):** cli-miner works fine — no Vulkan/CUDA needed. Just build and run. Confirmed working on 32-core CPU-only Vast.ai instance (Ubuntu 22.04, no nvidia-smi). SSH user format on Vast.ai CPU instances: `ssh -p PORT UUID@IP` (UUID as username, not `root`). Example: `ssh -p 41001 365bc2ec-b929-46fe-8e16-3d43f397d52e@84.242.173.26`

**PITFALL: dpkg lock on fresh Vast.ai containers** — fresh instances often run background apt processes on boot. If `apt-get install` fails with `Could not get lock /var/lib/dpkg/lock-frontend`, kill the holding process and remove the lock files:
```bash
kill -9 $(lsof /var/lib/dpkg/lock-frontend 2>/dev/null | awk 'NR>1{print $2}') 2>/dev/null
rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/cache/apt/archives/lock
sleep 2 && apt-get install -y ...
```

**Confirmed CPU-only build sequence (May 2026, 32-core Vast.ai):**
```bash
# apt-get update FIRST — fresh containers need this or packages not found
apt-get update -qq && apt-get install -y curl git build-essential pkg-config libssl-dev

# Install Rust — use . not source (POSIX sh)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
. "$HOME/.cargo/env"

# Clone and build (only cli-miner — gpu-miner not needed on CPU-only VPS)
git clone https://github.com/HannaPrints/equium.git
cd equium
cargo build --release -p equium-cli-miner   # ~1m 18s on 32-core

# Copy keypair and run
echo '[117,44,...]' > /tmp/eqm-keypair.json
nohup ./target/release/equium-miner \
  --keypair /tmp/eqm-keypair.json \
  --rpc-url 'https://mainnet.helius-rpc.com/?api-key=YOUR_KEY' \
  --threads 32 \
  --max-nonces-per-round 16 \
  > /tmp/eqm-mine.log 2>&1 &
echo "PID: $!"
```

**Confirmed hashrate (32-core CPU-only, May 2026):** ~81 H/s at steady state. Each batch of 16 nonces × 32 threads takes ~6 seconds. Log prints `· try #N exhausted Xms Y H/s` every ~6 seconds — this confirms the miner is alive.

**Vast.ai instance lifespan:** Instances can go offline mid-session (connection refused). Always run miner in background (`nohup ... &`) and check `ps aux | grep equium-miner` to confirm it's still alive before assuming it's running.

Key flags:
- `--threads N` — defaults to all physical cores (0 = auto). Always pass `$(nproc)` explicitly.
- `--max-nonces-per-round N` — cap per thread before refetching state (default 4096)
- `--max-blocks N` — stop after N successful mints (0 = forever)

**PITFALL: default `--max-nonces-per-round 4096` makes log appear frozen for hours.** With 32 threads × 4096 nonces × ~6s/nonce = ~22 hours before first log line. Use `--max-nonces-per-round 16` to get feedback every ~6 seconds and confirm the miner is alive. Increase once confirmed working. Confirmed: at `--max-nonces-per-round 16` with 32 threads, each batch takes ~6s and prints a `· try #N exhausted Xms Y H/s` line — this is the correct way to verify the miner is alive.

```bash
# Good starting command — gives feedback quickly
./target/release/equium-miner \
  --rpc-url 'https://mainnet.helius-rpc.com/?api-key=YOUR_KEY' \
  --keypair /tmp/eqm-keypair.json \
  --threads $(nproc) \
  --max-nonces-per-round 16
```

**Confirmed working (May 2026, Vast.ai):** 192-core VPS, ~12500% CPU usage, mining round #1170 at 25 EQM/mint. Log stays on current round header while grinding — this is normal, not a hang.

Sample output:
```
round #42   reward 25 EQM   target 0x10ffff…
  · try #1   above target        587ms   1.7 H/s
  · try #2   above target        612ms   1.6 H/s
  ✓ MINED!   +25 EQM     try #3   601ms   1.6 H/s
    sig 4xZ9Ks…2pH8Yt
```

**PITFALL: Log appears frozen** — the miner only updates the log when a try completes or a mint lands. During grinding (can take minutes), the round header stays static. Check CPU usage (`ps aux | grep equium-miner`) — if CPU% is high (e.g. 12000%+), it's working fine.

## Wallet Generation

**No `solana-keygen` needed** — generate via Python `solders`:

```bash
pip3 install solders

python3 -c "
from solders.keypair import Keypair
import json

k = Keypair()
pubkey = str(k.pubkey())
raw = bytes(k)  # 64 bytes: 32 secret + 32 pubkey
full_64 = list(raw)

print('Address:', pubkey)

with open('/tmp/eqm-keypair.json', 'w') as f:
    f.write(json.dumps(full_64))

print('Saved to /tmp/eqm-keypair.json')
"
```

The JSON format (64-byte array) is compatible with `solana-keygen` and the Equium miner `--keypair` flag.

**PITFALL: `pip install solders` vs `pip3 install solders`** — on some systems `pip` installs to a different Python env than `python3`. Always use `pip3 install solders` and verify with `python3 -c "import solders; print('ok')"`.

**PITFALL: `to_bytes_array()` doesn't exist** — use `bytes(k)` to get the raw 64-byte keypair. `bytes(k)` returns the full 64-byte representation (32 secret + 32 pubkey) compatible with Solana keypair JSON format.

## Prerequisites

- Rust + Cargo (for building miner)
- Helius free API key: https://helius.dev (public RPC endpoints rate-limit heavily)
- Small SOL balance: < 0.01 SOL covers hundreds of mints
- Vulkan drivers on Linux VPS for GPU backend

## ⚠️ Performance Reality Check (May 2026)

**EQM mining is NOT profitable at v0.1 GPU miner.** Wagner solver is the bottleneck, not BLAKE2b.

### Why "exhausted" appears constantly

"Exhausted" = miner tried all nonces in its budget for this round without finding a valid solution. This is **normal** — it's probabilistic. But the rate matters:

- At 4.2 H/s (nonces/sec) × 4 instances = **16.8 nonces/sec total**
- Target `0x00000023...` → expected ~61M nonces per solution
- Expected time: **60,000+ minutes = 42 days** per mint

This is not a bug — it's the Wagner CPU bottleneck. Each nonce attempt takes ~15 seconds because Wagner sort+XOR on 131K entries is memory-intensive.

### Hashrate comparison

| Setup | H/s | Expected time/mint |
|-------|-----|-------------------|
| 32-core CPU (cli-miner, Vast.ai) | ~81 H/s | Very long |
| 192-core CPU (cli-miner) | ~1.7 H/s | Very long |\*
| 4× RTX 5060 Ti GPU miner v0.1 | ~17 H/s | ~42 days |
| Future GPU miner v0.3 (all Wagner on GPU) | TBD | TBD |

\* 192-core result was anomalously low — likely memory contention at high thread count. 32-core at 81 H/s is more representative.

**Decision rule:** Don't run EQM GPU miner v0.1 on paid VPS — cost >> revenue. Wait for v0.2/v0.3 when Wagner moves to GPU. CPU miner on free/idle hardware is fine.

### Why GPU power stays low (~20W)

GPU only handles BLAKE2b leaf generation (~1 second per nonce). Then CPU does Wagner (~14 seconds). GPU is idle 93% of the time. This is expected at v0.1.

### Multiple CUDA processes conflict

Running 4 separate CUDA processes on the same GPU causes hang/timeout. Each process tries to init its own CUDA context. **Fix:** run 1 process per GPU (use `EQM_GPU_ID` env var), not multiple processes sharing one GPU.

**PITFALL: subprocess overhead kills throughput.** Each nonce = 1 subprocess call to `eqm-leaves`. With 46 threads × subprocess overhead, the bottleneck shifts entirely to process spawn time. Keep `--threads` low (4-8) when using subprocess-based GPU backend.

**PITFALL: 4 CUDA processes on same GPU hang.** When multiple `eqm-leaves` subprocesses target the same GPU simultaneously, they deadlock. Always use `EQM_GPU_ID=0/1/2/3` to pin each instance to a different physical GPU.

## Key Differences vs $HASH (Ethereum keccak256)

| | $HASH | $EQM |
|--|-------|------|
| Chain | Ethereum | Solana |
| Algorithm | keccak256 | Equihash (96,5) |
| GPU backend | CUDA | wgpu (Vulkan) |
| GPU speedup | ~1000x vs CPU | ~2-3x at v0.1 |
| Fee per mint | ~$5 gas | < $0.001 SOL |
| Memory-hard | No | Yes |
| Anti-ASIC | No | Yes (by design) |

## VPS Setup Notes

- Vulkan must be available: `vulkaninfo 2>/dev/null | head -5`
- Install Vulkan on Ubuntu: `apt-get install -y libvulkan1 vulkan-tools`
- NVIDIA GPUs on Linux: Vulkan works via proprietary driver (included in CUDA driver stack)
- `--threads N` controls CPU threads for Wagner rounds — set to `nproc` for max

### Recommended Vast.ai Template

Use `nvidia/cuda:12.4.1-devel-ubuntu22.04` or `pytorch/pytorch:2.3.0-cuda12.1-cudnn8-devel`.
- NVIDIA driver bundled → Vulkan support included automatically
- Avoid TensorFlow images (bloated, older CUDA)
- GPU choice: RTX 4090 or RTX 3090 — Equihash is memory-hard so RTX 5090 gives minimal extra speedup vs cost. Cheaper consumer GPUs are better value here than for keccak256 mining.

### Full VPS Deploy Sequence (Confirmed Working May 2026)

```bash
# 1. Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
# PITFALL: `source` is not available in /bin/sh — use . or bash -c
. "$HOME/.cargo/env"

# 2. Install build deps + Vulkan libs
# PITFALL: fresh containers need apt-get update first or packages won't be found
apt-get update -qq && apt-get install -y libvulkan-dev vulkan-tools pkg-config libssl-dev git screen

# 3. Clone and build BOTH miners (~2-4 min each)
git clone https://github.com/HannaPrints/equium.git
cd equium
cargo build --release -p equium-cli-miner    # CPU miner — use this first
cargo build --release -p equium-gpu-miner    # GPU miner — currently broken on NVIDIA

# 4. Copy keypair
mkdir -p ~/.config/solana
echo '[117,44,...]' > ~/.config/solana/eqm-keypair.json  # 64-byte array

# 5. Verify CUDA + Vulkan before starting
python3 -c "import ctypes; cuda=ctypes.CDLL('libcuda.so'); r=cuda.cuInit(0); print('cuInit:', r)"
vulkaninfo --summary 2>/dev/null | head -5

# 6. Run CPU miner in screen
screen -dmS eqm-miner bash -c "cd ~/equium && ./target/release/equium-miner \
  --rpc-url 'https://mainnet.helius-rpc.com/?api-key=YOUR_KEY' \
  --keypair ~/.config/solana/eqm-keypair.json \
  --threads $(nproc) 2>&1 | tee ~/eqm-miner.log"

# 7. Verify running
screen -list
ps aux | grep equium-miner | grep -v grep | awk '{print "CPU:", $3"%"}'
tail -20 ~/eqm-miner.log
```

**Build times (Vast.ai, May 2026):**
- `equium-cli-miner`: ~1m 33s
- `equium-gpu-miner`: ~2m 35s

**PITFALL: `screen` not pre-installed** on some Vast.ai images. Always `apt-get install -y screen` before starting.

**PITFALL: `source` not available in `/bin/sh`** — Rust installer outputs `. "$HOME/.cargo/env"` for sh. Use `. "$HOME/.cargo/env"` (POSIX dot) or run commands via `bash -c '...'`. Using `source` in a non-bash shell gives `source: not found`.

**PITFALL: apt-get install fails with "Unable to locate package"** on fresh containers — always run `apt-get update -qq` first before any `apt-get install`.

**PITFALL: Helius API key placeholder** — miner immediately exits with `401 Unauthorized` if you pass a fake/placeholder key. Always confirm the real API key before starting the miner process.

## GitHub Distribution


Suggested repo contents:
- `setup.sh` — one-command VPS bootstrap (install Rust, deps, clone equium, build cli-miner, copy keypair, start in screen)
- `README.md` — wallet address, RPC setup, usage
- `keypair-template.json` — placeholder (never commit real keypair)

## References

- `references/eqm-protocol.md` — Full protocol spec, contract addresses, links
- `references/wgpu-nvidia-segfault.md` — GitHub issue #4 details, full CUDA workaround, main.rs patch steps, BLAKE2b param block bug, batch binary, 4-GPU setup
- `templates/eqm_leaves.cu` — CUDA kernel for BLAKE2b leaf generation (single-nonce, hex output)
- `templates/eqm_leaves_batch.cu` — CUDA kernel for BLAKE2b leaf generation (batch, binary output — preferred)
- `templates/gpu_cuda.rs` — Replacement `gpu.rs` (single-nonce subprocess version)
- `templates/gpu_cuda_batch.rs` — Replacement `gpu.rs` (batch subprocess version — preferred)
- `templates/start-4gpu.sh` — 4-GPU multi-instance startup script (EQM_GPU_ID=0/1/2/3)
