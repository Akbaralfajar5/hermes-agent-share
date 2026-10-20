# VPS Provider Comparison for CPU Mining (May 2026)

Session: May 9, 2026 — Research for rpow2 mining after reward nerf

## Requirements

**Target workload:** rpow2 CPU mining (single-threaded per worker)
**Key metric:** Single-core performance (high clock speed > core count)
**Budget:** ~$100-150/month
**Preferred specs:**
- Modern CPU (Zen 3/4 or Intel 12th gen+)
- 4-8 vCPU threads
- 8-16 GB RAM
- Good network (API-heavy workload)

## Providers Evaluated

### 1. Vast.ai ❌

**URL:** https://cloud.vast.ai/

**Findings:**
- **No CPU-only instances** — all listings include GPU
- Platform optimized for GPU compute (AI/ML training)
- Pricing includes GPU cost even if unused
- Not suitable for CPU-only mining

**Verdict:** Skip for CPU mining workloads

---

### 2. QuickPod.io ✅

**URL:** https://console.quickpod.io/

**Findings:**
- **CPU-only filter available** — dedicated CPU instances
- **267 CPU instances** available (as of May 2026)
- Modern CPUs: Threadripper PRO, EPYC, Xeon

**Best Options Found:**

#### Option 1: AMD Threadripper PRO 5995WX (Zen 3) ⭐
- **CPU:** 64-core, Zen 3 architecture
- **Config:** 6 vCPU threads
- **RAM:** 15-16 GB
- **Clock:** 2.7 GHz base, 4.5 GHz boost
- **Price:** $0.138/hr (~$99/month)
- **Location:** Sofia, Bulgaria
- **Reliability:** 96.61% uptime
- **Max rental:** 30 days
- **Mining speed:** ~1-3s per block (estimated)

#### Option 2: AMD Threadripper PRO 7985WX (Zen 4) 🚀 BEST
- **CPU:** 64-core, Zen 4 architecture
- **Config:** 6 vCPU threads (some 3-thread options)
- **RAM:** 16 GB
- **Clock:** 3.2 GHz base, 5.1 GHz boost
- **Price:** $0.141/hr (~$101/month)
- **Location:** Sofia, Bulgaria
- **Reliability:** 96.61% uptime
- **Max rental:** 30 days
- **Mining speed:** 0.06-0.47s per block (verified)
- **Performance:** 10-30x faster than older Xeon CPUs

**Verdict:** Excellent value for single-core performance. Zen 4 architecture provides best-in-class IPC and clock speeds.

---

### 3. Intel Xeon E5-4669 v4 (Comparison Baseline) ⚠️

**Specs:**
- **Architecture:** Broadwell-EP (2016, 14nm)
- **Clock:** 2.20 GHz base, 2.9 GHz boost
- **Cores:** 22 cores / 44 threads
- **IPC:** Old (Broadwell generation)

**Mining Performance:**
- **Speed:** 3-6s per block
- **Blocks/5min:** ~50-100 blocks

**Comparison to Threadripper PRO 7985WX:**
- **Clock speed:** 7985WX 76% faster (5.1 vs 2.9 GHz boost)
- **IPC:** 7985WX ~40% more efficient per clock
- **Total single-core:** 7985WX ~2.5x faster
- **Mining speed:** 7985WX 10-30x faster in practice

**Verdict:** Avoid older Xeon CPUs for single-threaded mining. Modern Threadripper/EPYC vastly superior.

---

## Performance Benchmarks

### rpow2 Mining Speed Comparison

| CPU | Architecture | Boost Clock | Mining Speed | Blocks/Min | Relative Performance |
|-----|--------------|-------------|--------------|------------|---------------------|
| Xeon E5-4669 v4 | Broadwell (2016) | 2.9 GHz | 3-6s/block | ~10-20 | 1× (baseline) |
| Threadripper 5995WX | Zen 3 (2021) | 4.5 GHz | 1-3s/block | ~20-60 | 2-3× |
| Threadripper 7985WX | Zen 4 (2022) | 5.1 GHz | 0.06-0.47s/block | ~127-1000 | 10-30× |
| AMD EPYC 7K62 (2 cores) | Zen 2 (2019) | ~3.3 GHz | 0.29-4.19s/block | ~14-207 | 1.5-5× |

**Key insight:** Modern Zen 4 architecture (Threadripper PRO 7985WX) provides massive single-core advantage for mining workloads.

---

## Cost Analysis

### QuickPod Threadripper PRO 7985WX
- **Hourly:** $0.141/hr
- **Daily:** $3.38/day
- **Monthly (30 days):** $101.45
- **Performance:** 0.06-0.47s per block
- **Earnings (post-nerf):** ~13.44 rpow2/month
- **Break-even:** $7.51 per rpow2

### Free Alternative: Existing VPS (Hermes host)
- **CPU:** AMD EPYC 7K62 (2 cores)
- **Cost:** $0 (already paid for other services)
- **Performance:** 0.29-4.19s per block (~10× slower)
- **Earnings (post-nerf):** ~3.9-6.6 rpow2/month
- **Break-even:** N/A (marginal cost = $0)

**Decision framework:**
- **Paid VPS:** Only if token price expected > $7.51
- **Free VPS:** Always profitable (zero marginal cost)

---

## Lessons Learned

1. **Vast.ai is GPU-focused** — no CPU-only instances available
2. **QuickPod has excellent CPU options** — Threadripper PRO at competitive prices
3. **Zen 4 architecture dominates** — 5.1 GHz boost + modern IPC = 10-30× faster than old Xeons
4. **Single-core speed matters most** — for single-threaded mining, clock speed > core count
5. **Bulgaria location acceptable** — 96.61% uptime, good network speeds (560+ Mbps)
6. **30-day rental limit** — QuickPod max rental period, plan accordingly
7. **Reward nerfs change economics** — 99.84% nerf made paid VPS marginal, free VPS still viable

---

## Recommendation

**For rpow2 mining (post-nerf):**
1. **Best paid option:** QuickPod Threadripper PRO 7985WX @ $0.141/hr
2. **Best free option:** Repurpose existing VPS (if available)
3. **Avoid:** Vast.ai (no CPU-only), old Xeon CPUs (too slow)

**Decision criteria:**
- If token price expected > $10: Rent Threadripper PRO 7985WX
- If token price uncertain: Use free VPS only
- If token price < $5: Stop mining entirely

---

## Related Research

- QuickPod CPU filter: Click "CPU" button in search interface
- Sort by "Cost" to find cheapest options first
- Check "Verified" badge for reliable hosts
- Bulgaria location (Sofia) common for budget instances
- Multiple identical instances = same host, different allocation slots
