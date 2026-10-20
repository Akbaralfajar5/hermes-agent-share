# CPU Performance for Single-Threaded Mining Workloads

Benchmarks and comparisons for CPU single-core performance in mining contexts (rpow2, proof-of-work, hash computation).

## Key Metrics for Mining

**Single-core performance = Clock Speed × IPC**

- **Clock Speed (GHz)**: Higher = faster per-core computation
  - Base clock: Sustained 24/7 workload speed
  - Boost clock: Short-burst peak speed (mining often hits this)
- **IPC (Instructions Per Cycle)**: Architecture efficiency
  - Newer generations = higher IPC (Zen 4 > Zen 3 > Zen 2 > Broadwell)
- **Core count**: Less important for single-threaded mining (can run multiple workers, but each worker is single-threaded)

## Architecture Comparison (2016-2026)

### Intel Xeon E5-4669 v4 (Broadwell, 2016)
- **Base**: 2.20 GHz | **Boost**: ~2.9 GHz
- **IPC**: Broadwell (old, ~2016 baseline)
- **Mining speed**: 3-6 seconds/block ⚠️
- **Verdict**: Too slow for 5-minute challenge windows

### AMD Threadripper PRO 5995WX (Zen 3, 2021)
- **Base**: 2.7 GHz | **Boost**: 4.5 GHz
- **IPC**: Zen 3 (~19% faster than Broadwell per clock)
- **Mining speed**: 1-3 seconds/block ✅
- **Verdict**: 2x faster than Xeon E5-4669 v4, good value

### AMD Threadripper PRO 7985WX (Zen 4, 2022)
- **Base**: 3.2 GHz | **Boost**: 5.1 GHz
- **IPC**: Zen 4 (~13% faster than Zen 3, ~35% faster than Broadwell per clock)
- **Mining speed**: 0.5-2 seconds/block ✅✅
- **Verdict**: 3x faster than Xeon E5-4669 v4, fastest available

## Performance Multipliers

Relative to Intel Xeon E5-4669 v4 (baseline = 1.0x):

| CPU | Clock Advantage | IPC Advantage | **Total Speedup** |
|-----|----------------|---------------|-------------------|
| Xeon E5-4669 v4 | 1.0x (2.9 GHz) | 1.0x (Broadwell) | **1.0x** |
| Threadripper 5995WX | 1.55x (4.5 GHz) | 1.19x (Zen 3) | **~2.0x** |
| Threadripper 7985WX | 1.76x (5.1 GHz) | 1.35x (Zen 4) | **~2.5-3.0x** |

## QuickPod Pricing (May 2026)

| Instance | CPU | Threads | RAM | Price/hr | Price/mo | Mining Speed |
|----------|-----|---------|-----|----------|----------|--------------|
| 6X 5995WX | Threadripper PRO 5995WX | 6 | 15 GB | $0.138 | $99 | 1-3s/block |
| 6X 7985WX | Threadripper PRO 7985WX | 6 | 16 GB | $0.141 | $101 | 0.5-2s/block |
| 20X 5995WX | Threadripper PRO 5995WX | 20 | 40 GB | $0.453 | $325 | 1-3s/block |
| 32X 7985WX | Threadripper PRO 7985WX | 32 | 96 GB | $0.739 | $531 | 0.5-2s/block |

**Best value**: 6X 7985WX — only $2/mo more than 5995WX, but 15-20% faster.

## Verification Commands

After renting a VPS, verify actual performance:

```bash
# Check CPU model and clock speeds
lscpu | grep -E "Model name|MHz"

# Monitor real-time clock speeds under load
watch -n1 "grep MHz /proc/cpuinfo"

# Single-core benchmark (sysbench)
sysbench cpu --threads=1 --time=30 run

# Check for throttling
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq
```

Expected sysbench scores (events/sec, higher = better):
- Xeon E5-4669 v4: ~1000-1500
- Threadripper 5995WX: ~2000-3000
- Threadripper 7985WX: ~3000-4000

## Pitfalls

- **Boost clocks are not guaranteed**: Depends on thermal headroom, power limits, and workload duration. VPS hosts may limit boost duration.
- **Shared hosts = noisy neighbors**: Marketplace VPS (Vast, QuickPod) may have performance variance if other tenants saturate CPU/memory.
- **Network latency matters**: For API-heavy mining (rpow2), test latency to target API. Bulgaria → US API may add 100-200ms vs US-based VPS.
- **vCPU ≠ physical cores**: 6-thread instance may be 3 physical cores + hyperthreading. Check `lscpu` output for "Thread(s) per core".

## Source

Session: 2026-05-09, rpow2 mining VPS comparison (Vast.ai vs QuickPod)
