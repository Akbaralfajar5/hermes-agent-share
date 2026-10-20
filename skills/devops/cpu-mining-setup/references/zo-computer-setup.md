# zo.computer Mining Setup

Cloud workspace platform with web-based terminal and dynamic resource allocation.

## Platform Characteristics

- **URL pattern:** `username.zo.computer`
- **Web interface:** Dashboard with system specs, terminal access, file browser
- **Dynamic specs:** Resources can change based on workload and plan
- **Snapshot support:** Built-in checkpoint/restore functionality
- **Network testing:** Integrated speed test tool

## Typical Specs (May 2026)

- **CPU:** 3 cores @ 1.8 GHz (x86_64)
- **RAM:** 4 GB
- **OS:** Linux 6.12 (modern kernel)
- **Uptime:** Resets on reboot/restore
- **Processes:** ~17 baseline (lightweight)

## Access Methods

### 1. Web Terminal (Primary)
- Click "Terminal" in left sidebar
- Browser-based shell (no SSH client needed)
- Copy-paste friendly

### 2. SSH (If Available)
Check Settings/Account page for:
- SSH hostname (may be `username.zo.computer` or IP)
- SSH port (usually 22)
- Username/password or key

Format: `ssh user@username.zo.computer`

## Setup Workflow

### Via Web Terminal

1. **Open Terminal** in zo.computer dashboard
2. **Run setup commands** directly in browser:

```bash
# Install dependencies
sudo apt-get update -qq
sudo apt-get install -y curl git build-essential screen jq bc pkg-config libssl-dev

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env

# Clone miner
git clone https://github.com/rizkypujir/miner.git ~/rpow2-rust-miner

# Build (takes 2-5 minutes)
cd ~/rpow2-rust-miner
cargo build --release

# Create mining directory
mkdir -p ~/rpow2-mining
cd ~/rpow2-mining

# Create mine.sh (adjust threads for 3-core system)
cat > mine.sh << 'EOF'
#!/bin/bash
MINER_PATH="$HOME/rpow2-rust-miner/target/release/rpow2-miner"
LOG_FILE="$HOME/rpow2-mining/mining.log"
THREADS=3  # Use all 3 cores

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting miner with $THREADS threads..." | tee -a "$LOG_FILE"
    timeout 86400 "$MINER_PATH" --threads "$THREADS" 2>&1 | tee -a "$LOG_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Miner stopped, restarting in 10s..." | tee -a "$LOG_FILE"
    sleep 10
done
EOF

chmod +x mine.sh

# Create start.sh
cat > start.sh << 'EOF'
#!/bin/bash
if screen -list | grep -q "rpow2"; then
    echo "Mining already running"
    exit 1
fi
echo "Starting rpow2 mining in screen session..."
screen -dmS rpow2 bash -c "cd ~/rpow2-mining && ./mine.sh"
sleep 2
if screen -list | grep -q "rpow2"; then
    echo "✓ Mining started"
else
    echo "✗ Failed to start"
    exit 1
fi
EOF

chmod +x start.sh

# Create stop.sh
cat > stop.sh << 'EOF'
#!/bin/bash
if ! screen -list | grep -q "rpow2"; then
    echo "Mining is not running"
    exit 1
fi
echo "Stopping rpow2 mining..."
screen -S rpow2 -X quit
sleep 2
if screen -list | grep -q "rpow2"; then
    echo "✗ Failed to stop mining"
    exit 1
else
    echo "✓ Mining stopped"
fi
EOF

chmod +x stop.sh

# Create status.sh
cat > status.sh << 'EOF'
#!/bin/bash
echo "=========================================="
echo "rpow2 Mining Status"
echo "=========================================="
echo ""
if screen -list | grep -q "rpow2"; then
    echo "✓ Mining is RUNNING"
    echo ""
    echo "Screen session:"
    screen -list | grep rpow2
    echo ""
    echo "Recent logs (last 20 lines):"
    echo "----------------------------------------"
    tail -20 mining.log
    echo ""
    echo "CPU Usage:"
    echo "----------------------------------------"
    top -bn1 | grep -E "Cpu|rpow2-miner" | head -5
else
    echo "✗ Mining is NOT running"
fi
echo ""
echo "Commands:"
echo "  screen -r rpow2     # Attach to mining session"
echo "  tail -f mining.log  # Follow logs"
echo "  ./stop.sh           # Stop mining"
EOF

chmod +x status.sh

# Add cookie
echo "rpow_session=YOUR_TOKEN_HERE" > accounts.txt

# Edit cookie (use nano or vi)
nano accounts.txt
# Paste your rpow_session cookie, save (Ctrl+O, Enter, Ctrl+X)

# Start mining
./start.sh

# Check status
./status.sh
```

### Via SSH (If Available)

Use standard remote setup workflow from main skill.

## Performance Expectations

3-core @ 1.8 GHz system:
- **Mining speed:** 0.5-2.5s per block (estimated)
- **Blocks/minute:** 8-12 blocks
- **Daily earnings:** ~0.17-0.26 rpow2 (post-nerf, May 2026)

Slower than Threadripper PRO but faster than 2-core systems due to extra core.

## Platform-Specific Considerations

### Snapshots
- Take snapshot AFTER successful mining setup
- Allows quick restore if system breaks
- Snapshot before major changes (kernel updates, etc.)

### Dynamic Resources
- Specs may change based on workload
- Monitor actual performance vs. dashboard specs
- If mining slows unexpectedly, check dashboard for resource changes

### Uptime Resets
- Uptime counter resets on reboot/restore
- Mining logs persist (unless restored to earlier snapshot)
- Screen sessions lost on reboot — use startup script or manual restart

### Web Terminal Limitations
- May disconnect on browser close/sleep
- Screen sessions persist through disconnects
- Reattach with `screen -r rpow2` after reconnect

## Troubleshooting

### Web Terminal Disconnects
- Screen session continues running
- Refresh page and reopen Terminal
- Reattach: `screen -r rpow2`

### Snapshot Restore
If mining breaks after restore:
1. Check if miner binary exists: `ls ~/rpow2-rust-miner/target/release/rpow2-miner`
2. Check if cookie file exists: `cat ~/rpow2-mining/accounts.txt`
3. Restart mining: `cd ~/rpow2-mining && ./start.sh`

### Resource Changes
If dashboard shows different specs than expected:
1. Check actual CPU count: `nproc`
2. Check actual RAM: `free -h`
3. Adjust threads in `mine.sh` if needed
4. Restart mining: `./stop.sh && ./start.sh`

## Migration Strategy

If moving from zo.computer to another VPS:
1. **Backup cookie:** Copy `~/rpow2-mining/accounts.txt` content
2. **Note performance:** Check `mining.log` for baseline speed
3. **Setup new VPS** using standard workflow
4. **Compare performance:** Ensure new VPS meets/exceeds zo.computer speed

## Cost Considerations

zo.computer pricing varies by plan. Compare:
- **Free tier:** May have resource limits or uptime restrictions
- **Paid plans:** Check $/month vs. mining earnings
- **Alternative VPS:** QuickPod Threadripper PRO 7985WX @ $101/month mines 3-4x faster

**Break-even analysis (May 2026 post-nerf):**
- zo.computer (3 cores): ~6 rpow2/month
- Need rpow2 price > (monthly cost / 6) to profit
- Example: $10/month plan needs rpow2 > $1.67 to break even

## See Also

- Main skill: `cpu-mining-setup`
- `references/rpow2-economics.md` — ROI calculations, break-even analysis
- `references/vps-comparison-may-2026.md` — zo.computer vs. QuickPod vs. others
