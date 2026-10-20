#!/bin/bash
# Auto-deploy script with built-in watchdog
# Usage: curl -sSL https://raw.githubusercontent.com/USER/REPO/main/auto-deploy.sh | bash

echo "🚀 Auto-deploying miner..."

# Deploy miner (customize this section)
mkdir -p ~/miner && cd ~/miner

# Download miner script
curl -sSL https://raw.githubusercontent.com/USER/REPO/main/miner.py > miner.py
chmod +x miner.py

# Add config (customize cookie/credentials)
echo 'session_cookie=YOUR_COOKIE_HERE' > config.txt

# Create start/stop/status scripts
cat > start.sh << 'START_EOF'
#!/bin/bash
if screen -list | grep -q "miner"; then
    echo "Already running"
    exit 1
fi
THREADS=$(nproc)
echo "Starting with $THREADS threads..."
screen -dmS miner python3 miner.py $THREADS
sleep 2
echo "✓ Mining started"
START_EOF

cat > stop.sh << 'STOP_EOF'
#!/bin/bash
screen -S miner -X quit && echo "✓ Stopped"
STOP_EOF

cat > status.sh << 'STATUS_EOF'
#!/bin/bash
echo "=========================================="
echo "Miner Status"
echo "=========================================="
if screen -list | grep -q "miner"; then
    echo "✓ RUNNING"
    screen -S miner -X hardcopy /tmp/miner.txt
    tail -15 /tmp/miner.txt 2>/dev/null
else
    echo "✗ NOT running"
fi
STATUS_EOF

chmod +x *.sh

# Create watchdog script
cat > watchdog.sh << 'WATCHDOG_EOF'
#!/bin/bash
# Auto-start watchdog - monitors API and restarts miner

while true; do
    # Check if mining is running
    if ! screen -list | grep -q "miner"; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Mining not running, checking API..."
        
        # Check API status (customize URL)
        API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.example.com/challenge)
        
        if [ "$API_STATUS" = "200" ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] API UP! Starting miner..."
            ./start.sh
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] API down ($API_STATUS), waiting..."
        fi
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Mining is running"
    fi
    
    # Wait 5 minutes before next check
    sleep 300
done
WATCHDOG_EOF

chmod +x watchdog.sh

# Start watchdog in background
echo "🤖 Starting auto-start watchdog..."
screen -dmS miner-watchdog bash -c "cd ~/miner && ./watchdog.sh"

echo ""
echo "✅ Auto-deploy complete!"
echo ""
echo "Watchdog is running in background:"
echo "  - Checks API every 5 minutes"
echo "  - Auto-starts mining when API is UP"
echo "  - Auto-restarts if crashed"
echo ""
echo "Commands:"
echo "  screen -r miner-watchdog  # View watchdog logs"
echo "  screen -r miner           # View mining logs (when running)"
echo "  cd ~/miner && ./status.sh # Check status"
echo ""
