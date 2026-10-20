---
name: vps-provider-comparison
description: Research and compare VPS/cloud providers for specific compute requirements — CPU-only instances, GPU instances, pricing, performance benchmarks, and reliability metrics.
tags: [vps, cloud, hosting, comparison, performance, pricing]
---

# VPS Provider Comparison

Research and compare VPS/cloud providers to find optimal instances for specific compute workloads (CPU mining, batch processing, development environments, etc.).

## When to Use

- User needs to rent VPS/cloud instances with specific requirements
- Comparing providers for price/performance ratio
- Finding CPU-only or GPU-specific instances
- Evaluating reliability, network speed, or regional availability

## Workflow

### 1. Clarify Requirements

Before searching, confirm:
- **Compute type**: CPU-only, GPU, or hybrid
- **Performance priority**: Single-core speed, multi-core throughput, memory bandwidth
- **Budget**: Max $/hour or $/month
- **Duration**: Hourly, daily, monthly rental
- **Other constraints**: Region, network speed, storage, reliability

### 2. Navigate Provider Platforms

Common providers:
- **Vast.ai** — GPU-focused marketplace (https://cloud.vast.ai/)
- **QuickPod.io** — GPU + CPU marketplace (https://console.quickpod.io/)
- **Hetzner** — Dedicated CPU instances (https://www.hetzner.com/)
- **DigitalOcean** — General-purpose droplets
- **Vultr** — High-frequency compute
- **OVH** — Dedicated servers

Use browser automation to:
1. Navigate to provider console
2. Apply filters (CPU-only, GPU count, price range, region)
3. Sort by relevant metric (cost, performance, reliability)

### 3. Extract and Compare Specs

For each instance, capture:
- **CPU model** (architecture, generation, base/boost clock)
- **vCPU/threads** (actual core count matters for parallel workloads)
- **RAM** (capacity and type: DDR4 vs DDR5)
- **Storage** (size and type: NVMe, SSD, HDD)
- **Network** (bandwidth, latency, cost per TB)
- **Price** ($/hour, $/month)
- **Reliability** (uptime %, launch success rate)
- **Max duration** (hourly, daily, monthly limits)

### 4. Evaluate Performance

**For single-core workloads** (mining, single-threaded tasks):
- Prioritize: **Clock speed (GHz)** > IPC (architecture generation) > core count
- Modern architectures: Intel 12th+ gen, AMD Zen 3/4
- Look for "boost clock" specs (often 1-2 GHz higher than base)

**For multi-core workloads** (batch processing, compilation):
- Prioritize: **Total threads** × clock speed × IPC
- Check if vCPU = physical cores or hyperthreads

**For memory-intensive workloads**:
- Prioritize: **RAM capacity** > DDR generation (DDR5 > DDR4)

### 5. Calculate Price/Performance

Compare instances using:
- **$/GHz** (for single-core tasks)
- **$/thread** (for parallel tasks)
- **$/GB RAM** (for memory-bound tasks)

Factor in:
- Bandwidth costs (some providers charge per TB)
- Minimum rental duration (hourly vs daily vs monthly)
- Reliability (downtime = wasted money)

### 6. Present Recommendations

Structure output as:
1. **Top recommendation** with justification
2. **Runner-up options** (if budget/performance tradeoffs exist)
3. **Comparison table** (current setup vs new options)
4. **ROI estimate** (if applicable)

## Platform-Specific Notes

### Vast.ai
- **Focus**: GPU marketplace (NO CPU-only options as of May 2026)
- **Filters**: GPU count slider exists, but setting to 0 returns no results — all instances shown have GPUs
- **Pricing**: Competitive for GPU, not suitable for CPU-only workloads
- **Verdict**: Skip for CPU-only requirements (confirmed May 9, 2026 — no CPU-only instances available)

### QuickPod.io
- **Focus**: GPU + CPU marketplace (BEST for CPU-only as of 2026)
- **Filters**: "CPU" button for CPU-only instances (works reliably)
- **Sorting**: Cost, reliability, performance
- **CPU options**: AMD Threadripper PRO (5995WX Zen 3, 7985WX Zen 4), EPYC, Ryzen
- **Pricing**: $0.138-0.74/hr for Threadripper PRO (as of May 2026)
  - 6-thread instances: $0.138-0.141/hr (best value)
  - 20-thread: $0.45/hr
  - 32-thread: $0.72-0.74/hr
- **Reliability metric**: Shows uptime % (96%+ typical) and launch success rate
- **Location**: Primarily Bulgaria (Sofia) for Threadripper instances
- **Max duration**: 30 days typical for high-end CPUs
- **Bandwidth**: ~560 Mbps up/down, $0.10/TB overage

### Hetzner
- **Focus**: Dedicated CPU instances (no GPU)
- **Pricing**: Fixed monthly plans (CPX, CCX lines)
- **Performance**: High-frequency AMD EPYC
- **Best for**: Predictable workloads, monthly rentals

## Pitfalls

- **vCPU ≠ physical cores**: Some providers count hyperthreads as vCPUs (2 vCPU = 1 physical core). Check "threads" vs "cores" in specs.
- **Base clock vs boost clock**: Mining/compute tasks often hit boost clocks, but sustained workloads may throttle. Prioritize boost clock for short bursts, base clock for 24/7 tasks.
- **Bandwidth costs**: Some providers charge $2-4/TB for network transfer. Factor this in for data-heavy workloads.
- **Reliability varies**: Marketplace providers (Vast, QuickPod) aggregate third-party hosts — check uptime % and reviews.
- **Regional latency**: For API-heavy workloads (e.g., rpow2 mining), test latency to target API before committing.
- **GPU filters don't always work**: On GPU-focused platforms, setting "GPU count = 0" may return no results even if CPU instances exist. Try searching without GPU filters first.

## Example: Finding CPU for Mining

**User need**: Fast CPU for single-threaded mining (rpow2), budget $100-150/month.

**Steps**:
1. Navigate QuickPod.io → click "CPU" filter
2. Sort by "Cost" ascending
3. Extract top 5 cheapest instances
4. Compare CPU models:
   - AMD Threadripper PRO 7985WX (Zen 4, 5.1 GHz boost) ✅ Best single-core
   - AMD Threadripper PRO 5995WX (Zen 3, 4.5 GHz boost) ✅ Good value
   - AMD EPYC 7xx3 (Zen 3, 3.x GHz) ❌ Lower clock, server-focused
5. Recommend: Threadripper PRO 7985WX @ $0.141/hr ($101/month)
   - Justification: Highest single-core speed (5.1 GHz), modern Zen 4, only $3/month more than Zen 3 alternative

## Verification

After selecting an instance:
1. **Test latency** to target API/service (if applicable)
2. **Benchmark single-core speed** (e.g., `sysbench cpu --threads=1`)
3. **Monitor actual clock speeds** under load (`watch -n1 "grep MHz /proc/cpuinfo"`)
4. **Verify network speed** (`speedtest-cli` or `iperf3`)

If performance doesn't match expectations, check for:
- CPU throttling (thermal limits, power limits)
- Noisy neighbors (shared hosts)
- Network congestion (peak hours)

See `references/cpu-mining-performance.md` for detailed CPU benchmarks and mining-specific performance comparisons.

See `references/quickpod-threadripper-may-2026.md` for QuickPod Threadripper PRO availability, pricing, and selection criteria (May 2026 snapshot).
