# wgpu NVIDIA Segfault — GitHub Issue #4 + CUDA Workaround

## The Bug

**GitHub issue #4** (open as of May 12 2026): `equium-gpu-miner verify` segfaults on all NVIDIA/Vulkan instances.

- Crash point: `create_compute_pipeline` (after `create_pipeline_layout`)
- Affects: RTX 5090 (driver 580.x), RTX 4090 (driver 570.x), RTX 5060 Ti (driver 580.x AND 590.x)
- Ubuntu 22.04/24.04 headless, wgpu = "24"
- `verify-cpu` passes fine — only GPU path crashes
- `catch_unwind` does NOT help — crash is SIGSEGV from driver, not Rust panic
- wgpu correctly detects all GPUs via Vulkan before crashing

## v0.4.1 Escape Hatches (Try First)

**v0.4.1 (May 12 2026)** added two escape hatches:

### 1. EQUIUM_BACKEND=gl (OpenGL path)
```bash
EQUIUM_BACKEND=gl ./target/release/equium-gpu-miner verify
```
**Result on Vast.ai headless:** FAILS — `No config found!` / `Features(BUFFER_STORAGE | COMPUTE_SHADER | DYNAMIC_ARRAY_SIZE)` not supported via EGL without display. GL compute shaders require a proper EGL context that headless containers don't provide.

### 2. cloud-mine.sh bootstrap
```bash
curl -fsSL https://raw.githubusercontent.com/HannaPrints/equium/master/scripts/cloud-mine.sh -o cloud-mine.sh
chmod +x cloud-mine.sh
EQUIUM_RPC_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_KEY ./cloud-mine.sh
```
Auto-probes vulkan then gl. Warns on 575.x driver. Still fails on 580.x/590.x headless.

**Conclusion:** Both escape hatches fail on Vast.ai headless containers. Use CUDA bypass below.

## CUDA Workaround (Confirmed Working May 2026)

Replace wgpu with a standalone CUDA binary called via subprocess.

### Files

- `templates/eqm_leaves.cu` — CUDA kernel (single-nonce, hex output to stdout)
- `templates/gpu_cuda.rs` — replacement `gpu.rs` (subprocess-based, reads EQM_GPU_ID env)
- `templates/start-4gpu.sh` — 4-GPU startup script

### Deploy Steps

```bash
cd /root/equium

# 1. Compile CUDA binary
nvcc -O3 -arch=sm_120 -o eqm-leaves eqm_leaves.cu  # sm_120 for RTX 5060 Ti / 5090
# sm_89 for RTX 4090, sm_86 for RTX 3090, sm_75 for RTX 2060

# 2. Verify BLAKE2b correctness (MUST pass before mining)
python3 -c "
import subprocess, hashlib, struct
input_bytes = bytearray(81)
input_bytes[:9] = b'Equium-v1'
for i in range(9, 81): input_bytes[i] = (i * 7 + 13) % 256
nonce_bytes = bytearray(32)
for i in range(32): nonce_bytes[i] = (i * 31 + 2) % 256
result = subprocess.run(['./eqm-leaves', input_bytes.hex(), nonce_bytes.hex(), '10'],
                        capture_output=True, text=True)
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

# 3. Replace gpu.rs
cp templates/gpu_cuda.rs clients/gpu-miner/src/gpu.rs

# 4. Patch main.rs (see below)

# 5. Rebuild
source $HOME/.cargo/env
cargo build --release -p equium-gpu-miner
```

### main.rs Patch Summary

Five changes needed:

**P1 — mine() header:** Replace hard GPU init with soft fallback:
```rust
// OLD:
let gpu = Arc::new(gpu::GpuLeafGen::new()?);
println!("GPU backend: {}", gpu.adapter_name);

// NEW:
let gpu_opt: Option<Arc<gpu::GpuLeafGen>> = match gpu::GpuLeafGen::new() {
    Ok(g) => { println!("GPU backend: {}", g.adapter_name); Some(Arc::new(g)) }
    Err(e) => { println!("WARNING: GPU init failed: {e}"); None }
};
```

**P2 — call site:** `race_for_solution_gpu(gpu.clone(),` → `race_for_solution_gpu(gpu_opt.clone(),`

**P3 — race signature:** `gpu: Arc<gpu::GpuLeafGen>` → `gpu: Option<Arc<gpu::GpuLeafGen>>`

**P4 — worker leaf gen:** Replace `gpu.generate(...)` with:
```rust
match &gpu {
    Some(g) => { if g.generate(&input, &nonce, n_leaves, &mut leaves_buf).is_err() { continue; } }
    None => { cpu_leaves_into(&input, &nonce, n_leaves, &mut leaves_buf); }
}
```

**P5 — add cpu_leaves_into():** Insert before `// CPU reference (for verify, verify-cpu, bench)`:
```rust
fn cpu_leaves_into(input: &[u8; I_LEN], nonce: &[u8; 32], n_leaves: u32, out: &mut [u8]) {
    use blake2b_simd::Params;
    let mut personal = [0u8; 16];
    personal[..8].copy_from_slice(b"ZcashPoW");
    personal[8..12].copy_from_slice(&96u32.to_le_bytes());
    personal[12..16].copy_from_slice(&5u32.to_le_bytes());
    let base_state = Params::new().hash_length(60).personal(&personal).to_state();
    let mut state_with_input = base_state.clone();
    state_with_input.update(input);
    state_with_input.update(nonce);
    let n_calls = (n_leaves + gpu::LEAVES_PER_CALL - 1) / gpu::LEAVES_PER_CALL;
    let mut offset = 0usize;
    for call_idx in 0..n_calls {
        let mut s = state_with_input.clone();
        s.update(&call_idx.to_le_bytes());
        let h = s.finalize();
        let bytes = h.as_bytes();
        for k in 0..(gpu::LEAVES_PER_CALL as usize) {
            let leaf_idx = (call_idx * gpu::LEAVES_PER_CALL) as usize + k;
            if leaf_idx >= n_leaves as usize { break; }
            out[offset..offset + gpu::LEAF_BYTES]
                .copy_from_slice(&bytes[k * gpu::LEAF_BYTES..(k + 1) * gpu::LEAF_BYTES]);
            offset += gpu::LEAF_BYTES;
        }
    }
}
```

## BLAKE2b Param Block Bug

**Critical:** `digest_len = 60 = 0x3c`, NOT `0x60 = 96`.

```c
// WRONG — 0x60 = 96, not 60
h[0] ^= (uint64_t)0x0000000001010060ULL;

// CORRECT — 0x3c = 60
h[0] ^= (uint64_t)0x000000000101003cULL;
```

This caused CUDA output to not match CPU reference. The confusion: `n=96` appears in the personalization (`h[7] ^= 0x0000000500000060ULL` where `0x60=96`), but `digest_len=60=0x3c` is a separate field in param block word 0.

## 4-GPU Setup

Each instance gets its own GPU via `EQM_GPU_ID` env var:

```bash
# Run 4 instances, each on a different GPU
for GPU_ID in 0 1 2 3; do
  screen -dmS eqm-gpu${GPU_ID} bash -c "
    cd /root/equium
    source \$HOME/.cargo/env
    EQM_GPU_ID=${GPU_ID} ./target/release/equium-gpu-miner mine \
      --rpc-url 'YOUR_RPC' \
      --keypair ~/.config/solana/eqm-keypair.json \
      --threads 4 2>&1 | tee /root/eqm-gpu${GPU_ID}.log
  "
done
```

**PITFALL: Multiple CUDA processes on same GPU hang.** If two `eqm-leaves` subprocesses target the same GPU simultaneously, they deadlock. Always use different `EQM_GPU_ID` values.

**PITFALL: subprocess overhead.** Each nonce = 1 subprocess call. Keep `--threads` low (4-8). Higher thread counts don't help because subprocess spawn time dominates.

**PITFALL: eqm-leaves binary hangs with 4 concurrent miners running.** Kill all miner processes before testing the binary standalone. Multiple CUDA contexts on same GPU cause deadlock.

## Performance Reality

At v0.1, Wagner CPU is the bottleneck (~14s/nonce). GPU only handles BLAKE2b (~1s/nonce). GPU power stays ~20W (idle 93% of time). Expected time per mint at 17 H/s total: ~42 days. Not worth running on paid VPS until wgpu/NVIDIA bug is fixed and Wagner GPU (v0.2+) is accessible.

## Repo Update Timeline (May 2026)

| Date | Commit | What changed |
|------|--------|-------------|
| May 11 | v0.1 | Hybrid GPU/CPU miner (wgpu BLAKE2b + CPU Wagner) |
| May 11 | v0.2 | Full GPU Wagner pipeline (`rounds.wgsl`) added |
| May 11 | v0.3 | All 5 Wagner rounds on GPU |
| May 11 | v0.4 | WebGPU browser miner |
| May 12 | v0.4.1 | cloud-mine.sh, per-GPU workgroup tuning, NVIDIA 575 escape hatch |

**Note:** v0.2–v0.4 Wagner GPU code exists in repo but is unreachable on Vast.ai due to wgpu/NVIDIA crash. The CUDA bypass bypasses wgpu entirely and only handles BLAKE2b leaves — it does NOT use the new Wagner GPU shaders.
