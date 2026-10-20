# QuickPod.io — CPU Instance Provider

**URL:** https://console.quickpod.io/

**Focus:** GPU and CPU compute instances, primarily for ML/AI workloads but excellent for CPU mining.

## Key Features

- **CPU-only instances available** (filter with "CPU" button in search)
- **High-performance CPUs**: AMD Threadripper PRO series (Zen 3, Zen 4)
- **Flexible rental**: 1-180 days max duration
- **SSH access**: Standard SSH with username/password or key
- **Templates**: Ubuntu 22.04 Jammy, Ubuntu 24.04, Debian 12, etc.
- **Verified hosts**: Green checkmark badge for reliable providers
- **Launch success rate**: Displayed per instance (aim for 95%+)

## Pricing (as of May 2026)

### Budget Options (Best Value for CPU Mining)

| CPU | Threads | RAM | Storage | Network | Price/hr | Price/month | Reliability |
|-----|---------|-----|---------|---------|----------|-------------|-------------|
| **Threadripper PRO 5995WX** (Zen 3) | 6 | 12-15 GB | ~400 GB | 560 Mbps | **$0.138** | **$99** | 96.61% |
| **Threadripper PRO 7985WX** (Zen 4) | 6 | 16 GB | ~400 GB | 560 Mbps | **$0.141** | **$101** | 96.61% |

### Mid-Range Options

| CPU | Threads | RAM | Storage | Price/hr | Price/month |
|-----|---------|-----|---------|----------|-------------|
| Threadripper PRO 5995WX | 20 | 40 GB | ~1 TB | $0.453 | $326 |
| Threadripper PRO 7985WX | 32 | 96 GB | ~1 TB | $0.739 | $532 |

**Location:** Most instances in Sofia, Bulgaria (Sofia-Capital, BG)

## Performance for CPU Mining

### Threadripper PRO 7985WX (Zen 4) — RECOMMENDED

- **Architecture:** Zen 4 (2022, 5nm)
- **Base clock:** 3.2 GHz
- **Boost clock:** 5.1 GHz
- **Single-core performance:** Excellent (top-tier for mining)
- **rpow2 mining speed:** 0.06-0.47s per block (avg ~0.20s)
- **Estimated blocks/5min:** 600-5000 blocks

### Threadripper PRO 5995WX (Zen 3) — BUDGET OPTION

- **Architecture:** Zen 3 (2021, 7nm)
- **Base clock:** 2.7 GHz
- **Boost clock:** 4.5 GHz
- **Single-core performance:** Very good (~15% slower than 7985WX)
- **rpow2 mining speed:** 1-3s per block
- **Estimated blocks/5min:** 100-300 blocks

## Connection Details

### SSH Access

After instance creation, click **"Connect"** button in dashboard to get:

```
ssh -p <PORT> <USERNAME>@<IP_ADDRESS>
```

- **Username format:** UUID-style (e.g., `b67793f2-36e3-4bbe-8b58-fe899db0759c`)
- **Port:** Custom high port (e.g., 41001)
- **Authentication:** Password or SSH key (set during creation)

### Passwordless SSH

QuickPod supports SSH key authentication. If no password is set during creation, SSH keys work without password prompt.

## Template Selection

**Recommended for CPU mining:**

- **Ubuntu 22.04 Jammy** ✅ (most stable, LTS until 2027)
- **Ubuntu 24.04 LTS** ✅ (newest, LTS until 2029)
- **Debian 12** ✅ (lightweight, very stable)

**Avoid:**

- Windows Server (overkill, expensive)
- ML/AI templates with CUDA/GPU drivers (unnecessary overhead)
- Desktop/GUI templates (waste resources)

## Bandwidth & Storage

- **Bandwidth cost:** $0.10 per TB/hr (typical)
- **Included bandwidth:** Usually 5-6 TB
- **Storage:** 300-1000 GB depending on instance
- **Network speed:** 560-600 Mbps up/down (Bulgaria location)

## Reliability Notes

- **96.61% uptime** is typical for Threadripper PRO instances
- **100% launch success** means instance starts reliably
- **Max duration:** 30 days for budget instances, 180 days for some
- **Auto-renewal:** Not mentioned — assume manual renewal required

## Comparison with Other Providers

| Provider | CPU Options | Price (6-thread Threadripper) | Notes |
|----------|-------------|-------------------------------|-------|
| **QuickPod** | Excellent (Threadripper PRO) | $99-101/month | Best single-core perf |
| **Vast.ai** | GPU-focused, no CPU-only | N/A | Skip for CPU mining |
| Hetzner | Good (EPYC, Xeon) | ~$50-80/month | Lower clock speeds |
| DigitalOcean | Moderate (generic Xeon) | ~$40-60/month | Slower than Threadripper |

## Gotchas

- **No CPU-only filter by default** — must click "CPU" button to hide GPU instances
- **Username is UUID** — not `root` or `ubuntu`, copy exact username from dashboard
- **Custom SSH port** — not standard port 22, check dashboard
- **Max rental period** — 30 days for budget instances, must renew manually
- **Bulgaria location** — may have higher latency to US-based APIs (but bandwidth is good)
- **No balance/credit system visible** — billing appears to be pay-as-you-go

## Verification After Rental

```bash
# Check CPU model
ssh -p <PORT> <USER>@<IP> "lscpu | grep 'Model name'"

# Check actual thread count
ssh -p <PORT> <USER>@<IP> "nproc"

# Check RAM
ssh -p <PORT> <USER>@<IP> "free -h"

# Check disk
ssh -p <PORT> <USER>@<IP> "df -h"

# Check network speed (install speedtest-cli first)
ssh -p <PORT> <USER>@<IP> "curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3 -"
```

## Recommendation

For rpow2 mining or similar single-threaded CPU mining:

**Best choice:** Threadripper PRO 7985WX, 6 threads, $0.141/hr
- Fastest single-core performance (5.1 GHz boost)
- Only $2/month more than 5995WX
- 10-30x faster than generic VPS CPUs

**Budget choice:** Threadripper PRO 5995WX, 6 threads, $0.138/hr
- Still 2-3x faster than generic VPS
- $99/month
- Good reliability (96.61%)

**Skip:** 32-thread or 20-thread instances (overkill for single-threaded mining, much more expensive)
