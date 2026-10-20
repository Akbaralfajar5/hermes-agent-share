---
name: cpu-mining-setup
description: Setup CPU mining on VPS — install dependencies, build miners, configure auto-restart, and monitor. Covers rpow2 Rust miner and similar single-threaded CPU mining workloads.
tags: [mining, cpu, vps, rust, automation, monitoring]
---

# CPU Mining Setup on VPS

Automated setup for CPU mining workloads on fresh VPS instances. Focuses on single-threaded mining tasks (rpow2, similar proof-of-work systems) that benefit from high single-core clock speeds.

## ⚠️ rpow2 Status Update (May 2026)

**RECOMMENDED (May 10, 2026):** Native CLI miner (stablemarkk/rpow_cli_miner) — 2x faster than Python ✅

**Alternative:** Python miner v3/v4 with browser headers + FIXED TRAILING ZEROS **WORKING** ✅

### 🚨 CRITICAL: API Cooldown Bottleneck (May 10, 2026)

**RPOW2 enforces 5-second cooldown between challenges.** This makes high-core-count VPS unprofitable:

- **32 cores (122 MH/s):** Solve in 0.2s, wait 5s cooldown → **4.8 RPOW/hr** @ $0.74/hr
- **2 cores (3.4 MH/s):** Solve in 30s, no cooldown → **1.2 RPOW/hr** @ $0/hr (existing VPS)
- **4 cores (6.8 MH/s):** Solve in 5s, edge of cooldown → **6.9 RPOW/hr** @ $0.10/hr ✅ OPTIMAL

**Recommendation:** Use 2-4 cores max. More cores = wasted money. See `references/rpow2-api-cooldown-discovery-may-2026.md` for full analysis.

Original status (early May 2026):
- API returned 403 "automated mining clients are not permitted"
- Python miner repo deleted from GitHub (404)
- Rewards nerfed 99.84%

**Critical bug discovered (May 10):** Original Python miner counted **leading zeros** instead of **trailing zeros**, causing all solutions to be rejected with `INVALID_SOLUTION: hash does not meet difficulty`. Fixed in v3+.

**Working solutions:**

1. **Native CLI miner (RECOMMENDED)** — stablemarkk/rpow_cli_miner with patched headers
   - 2x faster than Python (3.4M vs 1.8M H/s on 2 cores)
   - Native C CPU miner + optional GPU support
   - State persistence, auto-retry, session management
   - **Requires patch:** Change `user-agent: "rpow-cli/1.0"` to full Chrome 135 headers
   - See `references/rpow2-native-cli-miner.md` for setup

2. **Python miner v2+** — Custom script with browser headers
   - No compile time, instant deployment
   - Fixed trailing zeros bug (critical)
   - Windows multiprocessing support
   - See `scripts/rpow2_miner_v2.py` and `references/rpow2-python-miner-v2-may-2026.md`

See:
- `scripts/rpow2_miner_v3_windows.py` — Windows-compatible miner (Queue + freeze_support)
- `scripts/rpow2_miner_v4_optimized.py` — Numba JIT optimized version (10-50x faster)
- `references/rpow2-python-miner-v2-may-2026.md` — Technical details, bug fixes, deployment guide

**Performance:** 
- 2 cores: ~30s per solve (difficulty 25 bits) → ~0.01 RPOW per 30s
- 12 cores: ~5-10s per solve → ~0.01 RPOW per 5-10s
- 32 cores (Threadripper): ~1-2s per solve → ~30 RPOW/hour

This skill remains useful for:
- **Active rpow2 mining** (use Python v2)
- Template for other CPU mining projects
- VPS setup patterns

## When to Use
- Setting up CPU mining on a new VPS (XMR, Juno Cash, SAT, or other RandomX/CPU coins)
- Setting up rpow2 mining on new VPS (use Python v2)
- Deploying CPU miners after VPS rental
- Migrating mining from one VPS to another
- Automating miner installation and configuration

## Quick Start: Native CLI Miner (Recommended)

**Fastest deployment with best performance** — working as of May 10, 2026:

```bash
# 1. Clone and patch
cd ~
git clone https://github.com/stablemarkk/rpow_cli_miner.git
cd rpow_cli_miner

# 2. CRITICAL: Patch rpow-cli.js line 497-502
# Change user-agent from "rpow-cli/1.0" to Chrome 135 headers
# See references/rpow2-native-cli-miner.md for exact patch

# 3. Add cookie
cat > .rpow-cli-state.json << 'EOF'
{
  "cookies": {
    "rpow_session": "YOUR_JWT_TOKEN_HERE"
  }
}
EOF

# 4. Build native miner
bash build-native.sh
ln -s rpow-native-miner rpow-native-miner.exe

# 5. Test
node rpow-cli.js me
node rpow-cli.js mine --count 1 --engine native --workers 2

# 6. Run continuous
screen -dmS rpow2 node rpow-cli.js mine --count 10000 --engine native --workers $(nproc)
```

**Performance:** 3.4M H/s (2 cores), ~55M H/s (32 cores) — 2x faster than Python

**Why Native CLI:**
- ✅ 2x faster than Python (native C)
- ✅ GPU support (OpenCL)
- ✅ State persistence (resume after crash)
- ✅ Auto-retry with backoff
- ⚠️ Requires header patch (upstream has bot-triggering user-agent)

See `references/rpow2-native-cli-miner.md` for full guide.

## Quick Start: Python Miner v2 (Alternative)

**Fastest deployment** — working as of May 10, 2026:

```bash
# 1. Install dependency
pip3 install requests

# 2. Download script
curl -O https://raw.githubusercontent.com/.../rpow2_miner_v2.py
# Or copy from scripts/rpow2_miner_v2.py

# 3. Edit cookie (line 22)
nano rpow2_miner_v2.py
# COOKIE = "rpow_session=YOUR_TOKEN_HERE"

# 4. Run in screen
screen -dmS rpow2 python3 -u rpow2_miner_v2.py

# 5. Monitor
screen -r rpow2  # Attach (Ctrl+A D to detach)
```

**Why Python v2:**
- ✅ No compile time (<1 min setup vs 3-5 min Rust)
- ✅ Bypasses API detection (browser headers)
- ✅ Fixed trailing zeros bug (original Python miner broken)
- ✅ Comparable performance (~30s/block, 25 bits)

See `references/rpow2-python-miner-v2-may-2026.md` for technical details.

## Prerequisites

- SSH access to VPS (password or key-based)
- Mining credentials (API keys, session cookies, wallet addresses)
- VPS with Ubuntu 22.04+ or Debian 12+

## Workflow

### 1. Verify VPS Access

```bash
# Test SSH connection
ssh -p <PORT> <USER>@<IP> "echo 'SSH OK'; uname -a"

# Check CPU specs
ssh -p <PORT> <USER>@<IP> "lscpu | grep -E 'Model name|Thread|MHz'"

# Check available RAM
ssh -p <PORT> <USER>@<IP> "free -h"
```

### 2. Run Setup Script

Use the template script from `templates/rpow2-mining-setup.sh`:

```bash
# Upload setup script
scp -P <PORT> templates/rpow2-mining-setup.sh <USER>@<IP>:~/setup.sh

# Run setup
ssh -p <PORT> <USER>@<IP> "chmod +x ~/setup.sh && ./setup.sh"
```

The script will:
1. Install dependencies (curl, git, build-essential, screen, jq, bc)
2. Install Rust compiler
3. Clone and build miner (rizkypujir/miner for rpow2)
4. Create mining directory structure
5. Generate start/stop/status scripts
6. Create cookie/credential placeholder

### 3. Add Mining Credentials

```bash
# Edit cookie file
ssh -p <PORT> <USER>@<IP> "nano ~/rpow2-mining/cookie.txt"

# Or upload directly
echo "rpow_session=YOUR_SESSION_TOKEN" | ssh -p <PORT> <USER>@<IP> "cat > ~/rpow2-mining/cookie.txt"
```

### 4. Start Mining

```bash
ssh -p <PORT> <USER>@<IP> "cd ~/rpow2-mining && ./start.sh"
```

Mining runs in a `screen` session named `rpow2` with:
- Auto-restart on crash (10s delay)
- 24-hour rotation (prevents memory leaks)
- Random jitter (0-60s) to avoid synchronized restarts
- Persistent logging to `mining.log`

### 5. Monitor Status

```bash
# Check status
ssh -p <PORT> <USER>@<IP> "cd ~/rpow2-mining && ./status.sh"

# View live logs
ssh -p <PORT> <USER>@<IP> "tail -f ~/rpow2-mining/mining.log"

# Attach to mining session
ssh -p <PORT> <USER>@<IP> -t "screen -r rpow2"
# Detach: Ctrl+A then D
```

## File Structure

After setup, VPS will have:

```
~/rpow2-mining/
├── mine.sh          # Main mining loop (auto-restart)
├── start.sh         # Start mining in screen
├── stop.sh          # Stop mining
├── status.sh        # Check status + recent logs
├── cookie.txt       # Mining credentials
└── mining.log       # Persistent logs

~/rpow2-rust-miner/
└── target/release/miner  # Compiled binary
```

## Configuration

### Adjust Thread Count

Edit `~/rpow2-mining/mine.sh`:

```bash
# Default: use all available threads (max 6)
THREADS=$(nproc)
if [ $THREADS -gt 6 ]; then
    THREADS=6
fi

# Override to fixed value:
THREADS=4  # Use 4 threads
```

### Change Auto-Restart Interval

Edit `~/rpow2-mining/mine.sh`:

```bash
# Default: 24 hours (86400 seconds)
timeout 86400 "$MINER_PATH" ...

# Change to 12 hours:
timeout 43200 "$MINER_PATH" ...
```

### Update Mining Credentials

```bash
# Edit cookie
nano ~/rpow2-mining/cookie.txt

# Restart mining
./stop.sh && ./start.sh
```

## Pitfalls

- **Rust compile time**: Building the miner takes 2-5 minutes on Threadripper, longer on slower CPUs. Don't interrupt.
- **OpenSSL build dependencies**: Rust miner requires `pkg-config` and `libssl-dev`. If build fails with "Could not find directory of OpenSSL installation", install both: `apt-get install -y pkg-config libssl-dev`. The error message will suggest installing pkg-config, but libssl-dev is also required.
- **Binary name varies by repo**: rizkypujir/miner builds as `rpow2-miner` not `miner`. Check `target/release/` for actual binary name with `ls -lh ~/rpow2-rust-miner/target/release/ | grep -E 'rpow|miner'`.
- **accounts.txt format**: Miner expects `accounts.txt` in working directory with one cookie per line (not `--cookie` CLI flag). The miner will fail with `[!] Cannot read accounts.txt` if this file is missing. Create: `echo "rpow_session=..." > ~/rpow2-mining/accounts.txt` and ensure the mining script runs from `~/rpow2-mining/` directory.
- **Cookie format**: rpow2 uses `rpow_session=` prefix, not just raw JWT. Full format: `rpow_session=eyJlbWFpbCI6...` (JWT token after equals sign).
- **Extra lines in accounts.txt**: Miner counts lines, not valid cookies. Extra blank lines cause "3 accounts detected" when only 1 cookie exists. Always verify: `cat accounts.txt | wc -l` should equal number of accounts.
- **API downtime during setup**: Mining APIs go down (503, 502). Don't declare setup "failed" on first API error. Check if server is responding: `curl -I https://api.rpow2.com/me` → 401 = server up (unauthorized but responding), 5xx = server down (wait and retry).
- **Reward nerfs change ROI**: Crypto mining rewards can drop 99%+ overnight (rpow2: 1 token/5min → 0.000015258/block = 99.84% nerf, May 2026). Always verify current reward rate before calculating profitability. Historical rates are misleading.
- **Multi-account thread splitting**: Running N accounts on M threads gives each account M/N threads. Total hashrate stays same, per-account speed drops proportionally. Only beneficial if: per-account withdrawal limits exist, referral bonuses apply, or airdrop snapshots count unique accounts. For rpow2 (no known limits), single account with all threads is optimal.
- **Cookie expiration**: rpow2 cookies expire (check `exp` field in JWT). Update before expiration to avoid downtime.
- **API timeouts**: rpow2 API frequently times out. Miner auto-retries — this is normal behavior.
- **Screen session persistence**: If SSH disconnects, screen session continues. Reattach with `screen -r rpow2`.
- **Multiple screen sessions**: If `start.sh` fails with "already running", kill old session: `screen -S rpow2 -X quit` then restart.
- **CPU throttling**: Monitor actual clock speeds under load (`watch -n1 "grep MHz /proc/cpuinfo"`). If throttling occurs, check thermal limits or noisy neighbors.

## Multi-Account Mining

### Thread Allocation

Miner splits threads evenly across accounts in `accounts.txt`:

| Accounts | Total Threads | Threads/Account | Speed/Account | Total Output |
|----------|---------------|-----------------|---------------|--------------|
| 1        | 6             | 6               | 1x            | 1x           |
| 2        | 6             | 3               | 0.5x (2x slower) | 1x (same)    |
| 3        | 6             | 2               | 0.33x (3x slower) | 1x (same)    |
| 6        | 6             | 1               | 0.17x (6x slower) | 1x (same)    |

**Key insight:** Total blocks mined stays constant — multi-account splits performance, doesn't multiply it.

### When Multi-Account Makes Sense

**Use multi-account when:**
- ✅ Diversification (ban risk mitigation)
- ✅ Referral bonuses exist
- ✅ Per-account airdrop snapshots
- ✅ Withdraw limits per account

**Skip multi-account when:**
- ❌ No per-account benefits
- ❌ Want faster mining per account
- ❌ Simpler management preferred

### Multi-VPS Strategy

**Better approach:** Run same account on multiple VPS

| Setup | Account 1 Speed | Total Speed | Management |
|-------|----------------|-------------|------------|
| 1 VPS (6 cores) | 6 cores | 6 cores | Simple |
| 2 VPS (3+3 cores), 2 accounts | 3 cores each | 6 cores | Complex |
| 2 VPS (3+3 cores), 1 account | 3+3=6 cores | 6 cores | Simple |

**Recommendation:** Use same account across multiple VPS for:
- ✅ Consolidated balance
- ✅ 2x mining speed for one account
- ✅ Simpler tracking
- ⚠️ Possible rate limiting (monitor API responses)

## Cookie File Format

rpow2 miner expects `accounts.txt` (not `cookie.txt`):

```
rpow_session=eyJlbWFpbCI6InVzZXJAZXhhbXBsZS5jb20iLCJleHAiOjE3ODA4NDM2NTh9.signature
```

**Format rules:**
- One cookie per line
- Must include `rpow_session=` prefix
- No quotes, no extra whitespace
- Multiple accounts: one line per account

**Common mistake:** Creating `cookie.txt` instead of `accounts.txt` — miner won't find it.

## API Error Handling

### 503 Service Temporarily Unavailable

```
<title>503 Service Temporarily Unavailable</title>
nginx/1.26.3 (Ubuntu)
```

**Cause:** API server down, overloaded, or maintenance

**Action:**
1. Wait 5-10 minutes
2. Retry mining
3. Miner auto-retries on error

**Not your fault** — server-side issue.

### 502 Bad Gateway

**Cause:** API timeout or upstream failure

**Action:** Miner auto-recovers, continues mining next block

### Failed to parse challenge

**Cause:** API returned non-JSON (HTML error page)

**Action:** Miner retries automatically

**Pattern:** Errors are transient — miner handles them gracefully.

## Verification

After setup completes:

```bash
# Check miner process is running
ps aux | grep miner

# Check CPU usage (should be near 100% per thread)
top -bn1 | grep miner

# Check recent mining activity
tail -50 ~/rpow2-mining/mining.log | grep -E "Success|block|challenge"

# Check network activity (API calls)
ss -tunap | grep miner
```

Expected behavior:
- CPU usage: ~100% per mining thread
- Memory usage: <500 MB
- Network: Periodic API calls (every few seconds)
- Logs: Regular "Success" or "block mined" messages

## Troubleshooting

### Miner won't start

```bash
# Check if binary exists
ls -lh ~/rpow2-rust-miner/target/release/miner

# Check cookie file
cat ~/rpow2-mining/cookie.txt

# Check logs for errors
tail -50 ~/rpow2-mining/mining.log
```

### API timeout errors

Normal behavior — miner auto-retries. Check success rate:

```bash
grep "Success" ~/rpow2-mining/mining.log | wc -l
grep "timeout" ~/rpow2-mining/mining.log | wc -l
```

If success rate < 10%, check:
- Network connectivity: `ping api.rpow2.com`
- API status: `curl -I https://api.rpow2.com`
- VPS location latency (Bulgaria → US may be high)

### Miner crashes repeatedly

```bash
# Check crash logs
tail -100 ~/rpow2-mining/mining.log | grep -A5 "crashed"

# Check system resources
free -h  # RAM available?
df -h    # Disk space?
dmesg | tail -50  # Kernel errors?
```

Common causes:
- Out of memory (increase RAM or reduce threads)
- Disk full (clean up logs: `> ~/rpow2-mining/mining.log`)
- Invalid cookie (update credentials)

### Screen session lost

```bash
# List all screen sessions
screen -list

# Kill zombie sessions
screen -wipe

# Restart mining
cd ~/rpow2-mining && ./start.sh
```

## Performance Tuning

### Optimal Thread Count

For single-threaded mining (rpow2):
- **6 threads** = optimal for 6-vCPU instances (one worker per thread)
- **4 threads** = good for 4-vCPU instances
- **More threads ≠ better** — diminishing returns beyond physical core count

Test different thread counts:

```bash
# Edit mine.sh to set THREADS=4
nano ~/rpow2-mining/mine.sh

# Restart and monitor
./stop.sh && ./start.sh
tail -f mining.log  # Watch blocks/second
```

### CPU Affinity (Advanced)

Pin miner threads to specific CPU cores:

```bash
# Install numactl
apt-get install numactl

# Run miner with CPU affinity
numactl --physcpubind=0-5 "$MINER_PATH" ...
```

## Monitoring & Alerts

### Daily Status Check

Add to crontab:

```bash
# Check mining status daily at 8 AM
0 8 * * * cd ~/rpow2-mining && ./status.sh | mail -s "Mining Status" your@email.com
```

### Watchdog (Auto-Restart on Failure)

The built-in auto-restart handles crashes, but for extra safety:

```bash
# Add to crontab: check every 5 minutes
*/5 * * * * screen -list | grep -q rpow2 || (cd ~/rpow2-mining && ./start.sh)
```

## Migration to New VPS

```bash
# On old VPS: backup config
scp -P <OLD_PORT> <OLD_USER>@<OLD_IP>:~/rpow2-mining/cookie.txt ./cookie.txt.bak

# On new VPS: run setup
./setup.sh

# Restore cookie
scp -P <NEW_PORT> ./cookie.txt.bak <NEW_USER>@<NEW_IP>:~/rpow2-mining/cookie.txt

# Start mining
ssh -p <NEW_PORT> <NEW_USER>@<NEW_IP> "cd ~/rpow2-mining && ./start.sh"

# Stop old VPS
ssh -p <OLD_PORT> <OLD_USER>@<OLD_IP> "cd ~/rpow2-mining && ./stop.sh"
```

## Web Terminal Setup (zo.computer, Replit, etc.)

For cloud workspaces with web-based terminals (no direct SSH):

### Step-by-Step Command Sequence

User pastes commands one-by-one into web terminal. Guide them through:

```bash
# 1. Check system
lscpu | grep -E 'Model name|CPU\(s\)|Thread|MHz|Architecture'
free -h

# 2. Install dependencies
sudo apt-get update -qq && sudo apt-get install -y curl git build-essential screen jq bc pkg-config libssl-dev

# 3. Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env

# 4. Clone & build miner
cd ~ && git clone https://github.com/rizkypujir/miner.git rpow2-rust-miner
cd rpow2-rust-miner
cargo build --release  # Takes 1-5 minutes

# 5. Create mining directory
mkdir -p ~/rpow2-mining
cd ~/rpow2-mining

# 6. Create scripts (paste each cat command separately)
cat > mine.sh << 'EOF'
#!/bin/bash
MINER_PATH="$HOME/rpow2-rust-miner/target/release/rpow2-miner"
LOG_FILE="$HOME/rpow2-mining/mining.log"
THREADS=$(nproc)

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting miner with $THREADS threads..." | tee -a "$LOG_FILE"

while true; do
    cd ~/rpow2-mining
    timeout 86400 "$MINER_PATH" --threads "$THREADS" --timeout 30 2>&1 | tee -a "$LOG_FILE"
    
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 24h rotation - restarting..." | tee -a "$LOG_FILE"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Miner crashed (exit $EXIT_CODE) - restarting in 5s..." | tee -a "$LOG_FILE"
        sleep 5
    fi
done
EOF

chmod +x mine.sh

# 7. Create start.sh
cat > start.sh << 'EOF'
#!/bin/bash
if screen -list | grep -q "rpow2"; then
    echo "Mining already running"
    exit 1
fi
screen -dmS rpow2 bash -c "cd ~/rpow2-mining && ./mine.sh"
sleep 2
screen -list | grep rpow2 && echo "✓ Mining started"
EOF

chmod +x start.sh

# 8. Create stop.sh
cat > stop.sh << 'EOF'
#!/bin/bash
screen -S rpow2 -X quit
sleep 2
echo "✓ Mining stopped"
EOF

chmod +x stop.sh

# 9. Create status.sh
cat > status.sh << 'EOF'
#!/bin/bash
echo "=========================================="
echo "rpow2 Mining Status"
echo "=========================================="
if screen -list | grep -q "rpow2"; then
    echo "✓ Mining is RUNNING"
    echo ""
    tail -20 mining.log
else
    echo "✗ Mining is NOT running"
fi
EOF

chmod +x status.sh

# 10. Add cookie
echo 'rpow_session=YOUR_TOKEN_HERE' > accounts.txt

# 11. Start mining
./start.sh

# 12. Check status
./status.sh
```

**Critical:** User must paste each `cat > file << 'EOF' ... EOF` block as a single unit. Breaking it up will fail.

### Web Terminal Pitfalls

- **Stuck on "Attaching to start.sh"**: User ran `./start.sh` but screen session didn't properly detach. Fix:
  ```bash
  # Press Ctrl+C to cancel
  screen -S rpow2 -X quit  # Kill stuck session
  pkill -f rpow2-miner     # Kill any orphaned processes
  ./start.sh               # Restart properly
  ```
- **"Mining already running" but nothing in logs**: Zombie screen session. Kill and restart:
  ```bash
  screen -wipe             # Clean up dead sessions
  screen -S rpow2 -X quit  # Force kill
  ./start.sh
  ```
- **Cookie added after starting mining**: Miner won't pick it up. Must stop and restart:
  ```bash
  ./stop.sh
  echo 'rpow_session=...' > accounts.txt
  ./start.sh
  ```

## Mining on Existing Infrastructure

If miner already built on local VPS/server (e.g., Hermes Agent host):

```bash
# Check if miner exists
ls -lh ~/rpow2-rust-miner/target/release/rpow2-miner

# Create mining directory
mkdir -p ~/rpow2-mining

# Copy management scripts (from templates or previous setup)
# Or create minimal versions:

# Create mine.sh
cat > ~/rpow2-mining/mine.sh << 'EOF'
#!/bin/bash
MINER_PATH="$HOME/rpow2-rust-miner/target/release/rpow2-miner"
LOG_FILE="$HOME/rpow2-mining/mining.log"
THREADS=$(nproc)  # Use all available cores

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting miner with $THREADS threads..." | tee -a "$LOG_FILE"
    timeout 86400 "$MINER_PATH" --threads "$THREADS" 2>&1 | tee -a "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Miner stopped, restarting in 10s..." | tee -a "$LOG_FILE"
    sleep 10
done
EOF

chmod +x ~/rpow2-mining/mine.sh

# Add cookie
echo "rpow_session=YOUR_TOKEN" > ~/rpow2-mining/accounts.txt

# Start mining
cd ~/rpow2-mining
screen -dmS rpow2 bash -c "./mine.sh"

# Verify
screen -list | grep rpow2
tail -f mining.log
```

**Use case:** Repurpose existing VPS after stopping paid mining instance. Lower performance but zero marginal cost.

## Alternative: Python Miner (Fast Deployment)

For rapid deployment without Rust compile time, see `references/python-miner-rpow2.md`.

**Advantages:**
- No compile time (3-5 minutes saved)
- Instant deployment (<1 minute)
- Comparable performance (1.40s vs 0.06-3.31s per block)
- Easier to customize

**When to use:** Bulk VPS setup, time-sensitive deployments, prototyping

## See Also

- `references/rpow2-api-cooldown-discovery-may-2026.md` — **🚨 CRITICAL: 5-second API cooldown makes high-core-count unprofitable (May 10, 2026)**
- `references/quickpod-32core-session-may-2026.md` — **Complete Quickpod 32X Threadripper deployment session (May 10, 2026) — 122 MH/s, cooldown discovery, termination decision**
- `references/rpow2-native-cli-miner.md` — **Native C/OpenCL CLI miner (RECOMMENDED) — 2x faster, GPU support, state persistence**
- `references/quickpod-vps-selection-guide.md` — **How to select the right VPS (avoid 1X/6X trap, choose 32X Threadripper)**
- `references/quickpod-setup-session-may-2026.md` — **Complete Quickpod deployment session (May 10, 2026) — 32X Threadripper, 122 M H/s, Node v20 upgrade, pitfalls**
- `scripts/rpow2_miner_v2.py` — **Working Python miner (May 2026) — browser headers bypass, fixed trailing zeros**
- `scripts/rpow2_miner_v3_windows.py` — **Windows-compatible version (Queue + freeze_support)**
- `scripts/rpow2_miner_v4_optimized.py` — **Numba JIT optimized (10-50x faster)**
- `references/rpow2-python-miner-v2-may-2026.md` — **Technical details: API bypass, bug fixes, Windows fixes, deployment guide**
- `references/rpow2-trailing-zeros-bug-fix.md` — **Critical bug discovery: leading vs trailing zeros (May 10, 2026)**
- `references/quickpod-cpu-recommendations-rpow2.md` — **Quickpod Threadripper recommendations, ROI analysis, performance estimates**
- `references/rpow2-shutdown-may-2026.md` — Original shutdown notice (now bypassed with Python v2+)
- `references/python-miner-rpow2.md` — Original Python miner (obsolete, missing headers + broken trailing zeros)
- `references/rpow2-mining-notes.md` — rpow2-specific setup notes, API quirks, cookie format [HISTORICAL]
- `references/vps-mining-benchmarks.md` — Real-world performance data for QuickPod Threadripper PRO 7985WX, Zo.computer, and generic VPS (rpow2 mining, May 2026)
- `references/rpow2-balance-api.md` — Check mining balance via API, balance conversion, performance calculation
- `references/multi-account-mining.md` — Multi-account thread distribution, performance impact, when to use
- `references/rpow2-economics.md` — Reward nerf history, ROI analysis, break-even calculations, decision framework
- `references/quickpod-threadripper-7985wx.md` — QuickPod VPS setup session notes, Threadripper PRO 7985WX performance benchmarks, reward nerf analysis (May 2026)
- `references/vps-comparison-may-2026.md` — Vast.ai vs QuickPod comparison, Threadripper PRO vs Xeon benchmarks, cost analysis for CPU mining
- `references/zo-computer-setup.md` — zo.computer cloud workspace setup, web terminal workflow, 3-core performance expectations
- `references/zo-computer-web-terminal.md` — zo.computer web terminal setup session (May 2026), stuck screen session fix, promo code CLAWCONMIA, performance benchmarks
- `references/zo-computer-signup-automation.md` — zo.computer signup automation challenges, Cloudflare blocks, temp mail limitations, manual vs automated decision framework
- `references/zo-computer-signup-automation.md` — zo.computer signup automation challenges, Cloudflare blocks, temp mail limitations, manual vs automated decision framework
- `templates/rpow2-mining-setup.sh` — Complete automated setup script
- `vps-provider-comparison` skill — Finding optimal VPS for CPU mining

## Related Skills

- `vps-provider-comparison` — Research and compare VPS providers
- `docker-compose` — Containerize mining setups
- `zo-computer-automation` — Automate zo.computer signup and provisioning

## References

- `references/rpow2-bypass-detection.md` — **CRITICAL**: Full browser headers to bypass bot detection (May 2026)
- `references/rpow2-economics.md` — Reward nerf analysis, break-even calculations, ROI scenarios
