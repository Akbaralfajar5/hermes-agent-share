# VPS Mining Performance Benchmarks

Real-world mining performance data for CPU-intensive single-threaded workloads (rpow2 mining, May 2026).

## QuickPod - AMD Threadripper PRO 7985WX

**Specs:**
- CPU: AMD Ryzen Threadripper PRO 7985WX (Zen 4, 64-core)
- Allocated: 6 threads
- RAM: 18 GB
- Base: 3.2 GHz, Boost: 5.1 GHz
- Location: Sofia, Bulgaria
- Cost: $0.1409/hr (~$101/month, 30-day max rental)
- Reliability: 96.61% uptime

**rpow2 Mining Performance:**
- Mining speed: **0.06-0.47s per block**
- Average: ~0.20s/block
- Blocks/minute: ~20 blocks
- Fastest recorded: 0.02s (Session 2)
- Success rate: 100% (no API timeouts)

**Comparison to Generic VPS (2-core AMD EPYC 7K62):**
- Generic VPS: 2-7s/block
- Threadripper: 0.06-0.47s/block
- **Performance gain: 10-30x faster**

## Zo.computer - Unknown CPU (3 cores allocated)

**Specs:**
- CPU: Unknown model (shown as "unknown" in lscpu)
- Allocated: 3 cores @ 1.8 GHz
- RAM: 4 GB
- OS: Debian 12 (Bookworm)
- Architecture: x86_64

**Estimated Performance:**
- Mining speed: ~0.5-2.5s/block (estimated, not measured)
- Blocks/minute: ~8-12 (estimated)
- Note: Lower clock speed (1.8 GHz vs 5.1 GHz boost) suggests slower performance than Threadripper

## VPS Hermes (Current Session Host)

**Specs:**
- CPU: AMD EPYC 7K62
- Allocated: 2 cores @ ~2.x GHz
- RAM: 1.9 GB
- OS: Ubuntu

**rpow2 Mining Performance:**
- Mining speed: **0.06-4.19s per block**
- Average: ~1.9s/block
- Blocks/minute: ~6-10 blocks
- Fastest: 0.06s, Slowest: 4.19s
- Success rate: 95% (occasional 502 Bad Gateway)

## Key Takeaways

1. **Clock speed matters most** - Threadripper 7985WX (5.1 GHz boost) is 10-30x faster than generic 2 GHz VPS
2. **Core count secondary** - 6 threads @ 5.1 GHz beats 2 threads @ 2 GHz by massive margin
3. **Modern architecture helps** - Zen 4 (2022) has better IPC than older EPYC generations
4. **QuickPod best value** - $101/month for 10-30x performance gain over generic VPS
5. **Zo.computer unknown** - Low clock speed (1.8 GHz) suggests slower than Threadripper, but untested

## ROI After Reward Nerf (May 2026)

**Post-nerf reward:** 0.000015258 rpow2/block (99.84% reduction from pre-nerf)

| VPS | Blocks/day | Earnings/day | Cost/month | Break-even Price |
|-----|-----------|--------------|------------|------------------|
| Generic (2-core) | 8,640-14,400 | 0.13-0.22 rpow2 | Free (existing) | N/A |
| Threadripper 7985WX | 28,800 | 0.44 rpow2 | $101 | $7.51/rpow2 |
| VPS Hermes | 8,640-14,400 | 0.13-0.22 rpow2 | Free (existing) | N/A |

**Conclusion:** After 99.84% reward nerf, only free/existing VPS are profitable. Renting dedicated mining VPS requires rpow2 price >$7.51 to break even.
