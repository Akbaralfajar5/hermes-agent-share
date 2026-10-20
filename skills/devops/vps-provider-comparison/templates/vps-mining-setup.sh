#!/bin/bash
# Universal VPS Mining Setup Script
# Supports: rpow2 Rust miner on any Debian/Ubuntu VPS
# Tested on: QuickPod Threadripper PRO instances

set -e

echo "=========================================="
echo "VPS Mining Setup (rpow2 Rust Miner)"
echo "=========================================="
echo ""

# Detect CPU info
echo "[1/8] Detecting CPU..."
CPU_MODEL=$(lscpu | grep "Model name" | cut -d: -f2 | xargs)
CPU_THREADS=$(nproc)
echo "✓ CPU: $CPU_MODEL"
echo "✓ Available threads: $CPU_THREADS"
echo ""

# Install dependencies
echo "[2/8] Installing dependencies..."
apt-get update -qq
apt-get install -y curl git build-essential screen jq bc > /dev/null 2>&1
echo "✓ Dependencies installed"
echo ""

# Install Rust (for miner)
echo "[3/8] Installing Rust..."
if ! command -v rustc &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
    echo "✓ Rust installed"
else
    echo "✓ Rust already installed"
fi
echo ""

# Clone and build Rust miner
echo "[4/8] Cloning rpow2 Rust miner..."
cd ~
if [ -d "rpow2-rust-miner" ]; then
    echo "✓ Miner directory exists, pulling latest..."
    cd rpow2-rust-miner
    git pull
else
    git clone https://github.com/rizkypujir/miner.git rpow2-rust-miner
    cd rpow2-rust-miner
fi
echo ""

echo "[5/8] Building Rust miner (this may take 2-5 minutes)..."
cargo build --release
echo "✓ Miner built successfully"
echo ""

# Setup mining directory
echo "[6/8] Setting up mining directory..."
mkdir -p ~/rpow2-mining
cd ~/rpow2-mining
echo "✓ Mining directory ready"
echo ""

# Create mining script
echo "[7/8] Creating mining script..."
cat > ~/rpow2-mining/mine.sh << 'MINESCRIPT'
#!/bin/bash
# rpow2 Mining Script with Auto-Restart

MINER_PATH="$HOME/rpow2-rust-miner/target/release/miner"
COOKIE_FILE="$HOME/rpow2-mining/cookie.txt"
LOG_FILE="$HOME/rpow2-mining/mining.log"

# Check if cookie exists
if [ ! -f "$COOKIE_FILE" ]; then
    echo "ERROR: Cookie file not found at $COOKIE_FILE"
    echo "Please create cookie.txt with your rpow2 cookie"
    exit 1
fi

COOKIE=$(cat "$COOKIE_FILE")

# Detect optimal thread count (use all available, max 6 for QuickPod)
THREADS=$(nproc)
if [ $THREADS -gt 6 ]; then
    THREADS=6
fi

echo "=========================================="
echo "rpow2 Mining Started"
echo "=========================================="
echo "Threads: $THREADS"
echo "Miner: $MINER_PATH"
echo "Log: $LOG_FILE"
echo "=========================================="
echo ""

# Mining loop with auto-restart
while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting miner with $THREADS threads..." | tee -a "$LOG_FILE"
    
    # Run miner with timeout (restart every 24 hours)
    timeout 86400 "$MINER_PATH" --cookie "$COOKIE" --threads "$THREADS" 2>&1 | tee -a "$LOG_FILE"
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 124 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 24-hour timeout reached, restarting..." | tee -a "$LOG_FILE"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Miner crashed (exit code: $EXIT_CODE), restarting in 10s..." | tee -a "$LOG_FILE"
        sleep 10
    fi
    
    # Random jitter to avoid synchronized restarts
    JITTER=$((RANDOM % 60))
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Adding ${JITTER}s jitter..." | tee -a "$LOG_FILE"
    sleep $JITTER
done
MINESCRIPT

chmod +x ~/rpow2-mining/mine.sh
echo "✓ Mining script created"
echo ""

# Create cookie placeholder
if [ ! -f ~/rpow2-mining/cookie.txt ]; then
    echo "[8/8] Creating cookie placeholder..."
    cat > ~/rpow2-mining/cookie.txt << 'COOKIEINFO'
# Paste your rpow2 cookie here
# Get it from browser DevTools > Application > Cookies > api.rpow2.com
# Format: session=your_session_token_here
COOKIEINFO
    echo "⚠️  Cookie file created, please edit it with your actual cookie"
else
    echo "[8/8] Cookie file already exists"
fi
echo ""

# Create start/stop scripts
cat > ~/rpow2-mining/start.sh << 'STARTSCRIPT'
#!/bin/bash
# Start mining in screen session

if screen -list | grep -q "rpow2"; then
    echo "Mining already running in screen session 'rpow2'"
    echo "Use: screen -r rpow2  (to attach)"
    exit 1
fi

echo "Starting rpow2 mining in screen session..."
screen -dmS rpow2 bash -c "cd ~/rpow2-mining && ./mine.sh"
sleep 2

if screen -list | grep -q "rpow2"; then
    echo "✓ Mining started successfully!"
    echo ""
    echo "Commands:"
    echo "  screen -r rpow2     # Attach to mining session"
    echo "  screen -d           # Detach (Ctrl+A then D)"
    echo "  ./stop.sh           # Stop mining"
    echo "  tail -f mining.log  # View logs"
else
    echo "✗ Failed to start mining"
    exit 1
fi
STARTSCRIPT

cat > ~/rpow2-mining/stop.sh << 'STOPSCRIPT'
#!/bin/bash
# Stop mining

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
STOPSCRIPT

cat > ~/rpow2-mining/status.sh << 'STATUSSCRIPT'
#!/bin/bash
# Check mining status

echo "=========================================="
echo "rpow2 Mining Status"
echo "=========================================="
echo ""

# Check screen session
if screen -list | grep -q "rpow2"; then
    echo "✓ Mining is RUNNING"
    echo ""
    echo "Screen session:"
    screen -list | grep rpow2
else
    echo "✗ Mining is NOT running"
    exit 1
fi

echo ""
echo "Recent logs (last 20 lines):"
echo "----------------------------------------"
if [ -f ~/rpow2-mining/mining.log ]; then
    tail -n 20 ~/rpow2-mining/mining.log
else
    echo "No logs found"
fi

echo ""
echo "CPU Usage:"
echo "----------------------------------------"
top -bn1 | grep "miner" | head -5

echo ""
echo "Commands:"
echo "  screen -r rpow2     # Attach to mining session"
echo "  tail -f mining.log  # Follow logs"
echo "  ./stop.sh           # Stop mining"
STATUSSCRIPT

chmod +x ~/rpow2-mining/start.sh
chmod +x ~/rpow2-mining/stop.sh
chmod +x ~/rpow2-mining/status.sh

echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit cookie file:"
echo "   nano ~/rpow2-mining/cookie.txt"
echo "   (Paste your rpow2 session cookie)"
echo ""
echo "2. Start mining:"
echo "   cd ~/rpow2-mining"
echo "   ./start.sh"
echo ""
echo "3. Check status:"
echo "   ./status.sh"
echo ""
echo "4. View logs:"
echo "   tail -f mining.log"
echo ""
echo "5. Attach to mining session:"
echo "   screen -r rpow2"
echo "   (Detach: Ctrl+A then D)"
echo ""
echo "=========================================="
echo "Mining directory: ~/rpow2-mining"
echo "Miner binary: ~/rpow2-rust-miner/target/release/miner"
echo "=========================================="
