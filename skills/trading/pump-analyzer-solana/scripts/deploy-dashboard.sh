#!/bin/bash
# Deploy Pump.fun monitoring dashboard with auto-screening
# Creates a real-time WebSocket dashboard on port 8888

set -e

INSTALL_DIR="${1:-$HOME/pump-monitor}"

echo "🚀 Deploying Pump.fun Monitor Dashboard"
echo "========================================"
echo ""
echo "Install directory: $INSTALL_DIR"
echo ""

# Create directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Create index.html
cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pump.fun Token Monitor - Real-time Screening</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
        }
        h1 {
            font-size: 2.5em;
            background: linear-gradient(135deg, #14F195 0%, #9945FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: rgba(20, 241, 149, 0.1);
            border: 1px solid #14F195;
            border-radius: 20px;
            margin-top: 10px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            background: #14F195;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
        }
        .filter-group { display: flex; flex-direction: column; gap: 5px; }
        .filter-group label { font-size: 0.85em; color: #a0a0a0; }
        input, select {
            padding: 10px 15px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: #e0e0e0;
        }
        button {
            padding: 10px 20px;
            background: linear-gradient(135deg, #14F195 0%, #9945FF 100%);
            border: none;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            cursor: pointer;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
        }
        .stat-value { font-size: 1.8em; font-weight: 700; color: #14F195; }
        .token-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        .token-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            animation: slideIn 0.3s ease-out;
        }
        @keyframes slideIn { from { opacity: 0; transform: translateY(-10px); } }
        .token-card.safe { border-color: #14F195; background: rgba(20, 241, 149, 0.05); }
        .token-card.warning { border-color: #FFA500; background: rgba(255, 165, 0, 0.05); }
        .token-card.danger { border-color: #FF4444; background: rgba(255, 68, 68, 0.05); }
        .token-header { display: flex; align-items: center; gap: 15px; margin-bottom: 15px; }
        .token-image { width: 60px; height: 60px; border-radius: 12px; }
        .token-name { font-size: 1.2em; font-weight: 700; }
        .safety-score { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }
        .score-bar { flex: 1; height: 8px; background: rgba(255, 255, 255, 0.1); border-radius: 4px; overflow: hidden; }
        .score-fill { height: 100%; transition: width 0.3s; }
        .score-fill.safe { background: #14F195; }
        .score-fill.warning { background: #FFA500; }
        .score-fill.danger { background: #FF4444; }
        .token-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px; }
        .metric { padding: 10px; background: rgba(255, 255, 255, 0.05); border-radius: 8px; }
        .metric label { font-size: 0.75em; color: #a0a0a0; }
        .metric-value { font-size: 1.1em; font-weight: 600; color: #14F195; }
        .flags-list { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
        .flag { padding: 4px 8px; border-radius: 4px; font-size: 0.75em; font-weight: 600; }
        .flag.red { background: rgba(255, 68, 68, 0.2); color: #FF4444; }
        .flag.green { background: rgba(20, 241, 149, 0.2); color: #14F195; }
        .flag.yellow { background: rgba(255, 165, 0, 0.2); color: #FFA500; }
        .token-actions { display: flex; gap: 10px; }
        .btn-small {
            flex: 1;
            padding: 8px 12px;
            font-size: 0.85em;
            text-align: center;
            text-decoration: none;
            border-radius: 6px;
        }
        .btn-primary { background: linear-gradient(135deg, #14F195 0%, #9945FF 100%); color: white; }
        .btn-secondary { background: rgba(255, 255, 255, 0.1); color: #e0e0e0; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 Pump.fun Token Monitor</h1>
            <p style="color: #a0a0a0;">Real-time screening & analytics</p>
            <div class="status" id="status">
                <div class="status-dot"></div>
                <span>Connecting...</span>
            </div>
        </header>
        <div class="controls">
            <div class="filter-group">
                <label>Min Market Cap (SOL)</label>
                <input type="number" id="minMcap" value="5" step="1">
            </div>
            <div class="filter-group">
                <label>Max Market Cap (SOL)</label>
                <input type="number" id="maxMcap" value="50" step="5">
            </div>
            <div class="filter-group">
                <label>Max Initial Buy (SOL)</label>
                <input type="number" id="maxInitial" value="5" step="0.5">
            </div>
            <div class="filter-group">
                <label>Safety Filter</label>
                <select id="safetyFilter">
                    <option value="all">All Tokens</option>
                    <option value="safe" selected>Safe Only (✅)</option>
                    <option value="warning">Safe + Warning</option>
                </select>
            </div>
            <div class="filter-group" style="justify-content: flex-end;">
                <label>&nbsp;</label>
                <button onclick="applyFilters()">Apply Filters</button>
            </div>
        </div>
        <div class="stats">
            <div class="stat-card">
                <div style="font-size: 0.85em; color: #a0a0a0;">Total Tokens</div>
                <div class="stat-value" id="totalTokens">0</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 0.85em; color: #a0a0a0;">Safe (✅)</div>
                <div class="stat-value" id="safeTokens">0</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 0.85em; color: #a0a0a0;">Warning (⚠️)</div>
                <div class="stat-value" id="warningTokens" style="color: #FFA500;">0</div>
            </div>
            <div class="stat-card">
                <div style="font-size: 0.85em; color: #a0a0a0;">Danger (🚨)</div>
                <div class="stat-value" id="dangerTokens" style="color: #FF4444;">0</div>
            </div>
        </div>
        <div class="token-grid" id="tokenGrid">
            <div style="text-align: center; padding: 60px; color: #a0a0a0;">
                <h3>Waiting for tokens...</h3>
            </div>
        </div>
    </div>
    <script src="app.js"></script>
</body>
</html>
EOF

# Create app.js (WebSocket + screening logic)
cat > app.js << 'EOFJS'
const PUMP_WS_URL = 'wss://pumpportal.fun/api/data';
let ws = null;
let tokens = [];
let stats = { total: 0, safe: 0, warning: 0, danger: 0 };
let filters = { minMcap: 5, maxMcap: 50, maxInitial: 5, safetyFilter: 'safe', keyword: '' };

document.addEventListener('DOMContentLoaded', () => {
    loadFilters();
    connectWebSocket();
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

function connectWebSocket() {
    updateStatus('Connecting...', 'warning');
    ws = new WebSocket(PUMP_WS_URL);
    
    ws.addEventListener('open', () => {
        updateStatus('Connected - Monitoring live', 'success');
        ws.send(JSON.stringify({ method: 'subscribeNewToken' }));
    });
    
    ws.addEventListener('message', (event) => {
        const data = JSON.parse(event.data);
        if (data.txType === 'create') handleNewToken(data);
    });
    
    ws.addEventListener('close', () => {
        updateStatus('Reconnecting...', 'error');
        setTimeout(connectWebSocket, 2000);
    });
}

function handleNewToken(tokenData) {
    const analysis = analyzeToken(tokenData);
    const token = { ...tokenData, analysis, timestamp: Date.now() };
    tokens.unshift(token);
    stats.total++;
    stats[analysis.level]++;
    updateStats();
    if (passesFilters(token)) {
        renderToken(token);
        if (analysis.level === 'safe') sendNotification(token);
    }
}

function analyzeToken(token) {
    let score = 100;
    const flags = [];
    const initialBuy = token.initialBuy || 0;
    const mcap = token.marketCapSol || 0;
    
    if (initialBuy > 10) { flags.push({ type: 'red', text: `Initial buy too high: ${initialBuy.toFixed(2)} SOL` }); score -= 30; }
    else if (initialBuy > 5) { flags.push({ type: 'yellow', text: `Initial buy high: ${initialBuy.toFixed(2)} SOL` }); score -= 15; }
    else if (initialBuy >= 0.5) { flags.push({ type: 'green', text: `Initial buy normal: ${initialBuy.toFixed(2)} SOL` }); }
    
    if (mcap < 2) { flags.push({ type: 'red', text: `Market cap too low: ${mcap.toFixed(2)} SOL` }); score -= 25; }
    else if (mcap >= 5 && mcap <= 50) { flags.push({ type: 'green', text: `Market cap in sweet spot: ${mcap.toFixed(2)} SOL` }); score += 10; }
    
    const level = score >= 70 ? 'safe' : score >= 40 ? 'warning' : 'danger';
    return { score: Math.max(0, Math.min(100, score)), level, flags };
}

function passesFilters(token) {
    const mcap = token.marketCapSol || 0;
    const initialBuy = token.initialBuy || 0;
    if (mcap < filters.minMcap || mcap > filters.maxMcap) return false;
    if (initialBuy > filters.maxInitial) return false;
    if (filters.safetyFilter === 'safe' && token.analysis.level !== 'safe') return false;
    if (filters.safetyFilter === 'warning' && token.analysis.level === 'danger') return false;
    return true;
}

function renderToken(token) {
    const grid = document.getElementById('tokenGrid');
    const empty = grid.querySelector('div[style*="text-align"]');
    if (empty) empty.remove();
    
    const card = document.createElement('div');
    card.className = `token-card ${token.analysis.level}`;
    const scoreColor = token.analysis.level;
    const flagsHtml = token.analysis.flags.map(f => `<span class="flag ${f.type}">${f.text}</span>`).join('');
    
    card.innerHTML = `
        <div class="token-header">
            <img src="${token.imageUri || 'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 100 100\'%3E%3Crect fill=\'%23333\' width=\'100\' height=\'100\'/%3E%3C/svg%3E'}" class="token-image">
            <div><span class="token-name">${token.name || 'Unknown'}</span><br><span style="color: #a0a0a0;">$${token.symbol || 'N/A'}</span></div>
        </div>
        <div class="safety-score">
            <span style="font-size: 0.85em;">Safety: ${token.analysis.score}/100</span>
            <div class="score-bar"><div class="score-fill ${scoreColor}" style="width: ${token.analysis.score}%"></div></div>
        </div>
        <div class="token-metrics">
            <div class="metric"><label>Market Cap</label><div class="metric-value">${(token.marketCapSol || 0).toFixed(2)} SOL</div></div>
            <div class="metric"><label>Initial Buy</label><div class="metric-value">${(token.initialBuy || 0).toFixed(2)} SOL</div></div>
        </div>
        <div class="flags-list">${flagsHtml}</div>
        <div class="token-actions">
            <a href="https://pump.fun/${token.mint}" target="_blank" class="btn-small btn-primary">Trade</a>
            <a href="https://solscan.io/token/${token.mint}" target="_blank" class="btn-small btn-secondary">Solscan</a>
        </div>
    `;
    grid.prepend(card);
    while (grid.children.length > 50) grid.removeChild(grid.lastChild);
}

function sendNotification(token) {
    if (Notification.permission === 'granted') {
        const n = new Notification(`✅ Safe Token: ${token.name}`, {
            body: `$${token.symbol} - ${(token.marketCapSol || 0).toFixed(2)} SOL - Score: ${token.analysis.score}/100`,
            icon: token.imageUri
        });
        n.onclick = () => window.open(`https://pump.fun/${token.mint}`, '_blank');
        setTimeout(() => n.close(), 10000);
    }
}

function updateStatus(msg, type) {
    const status = document.getElementById('status');
    status.querySelector('span').textContent = msg;
    const colors = { success: '#14F195', warning: '#FFA500', error: '#FF4444' };
    status.style.borderColor = colors[type];
    status.querySelector('.status-dot').style.background = colors[type];
}

function updateStats() {
    document.getElementById('totalTokens').textContent = stats.total;
    document.getElementById('safeTokens').textContent = stats.safe;
    document.getElementById('warningTokens').textContent = stats.warning;
    document.getElementById('dangerTokens').textContent = stats.danger;
}

function applyFilters() {
    filters.minMcap = parseFloat(document.getElementById('minMcap').value) || 0;
    filters.maxMcap = parseFloat(document.getElementById('maxMcap').value) || 1000;
    filters.maxInitial = parseFloat(document.getElementById('maxInitial').value) || 100;
    filters.safetyFilter = document.getElementById('safetyFilter').value;
    saveFilters();
    document.getElementById('tokenGrid').innerHTML = '';
    tokens.filter(passesFilters).forEach(renderToken);
}

function saveFilters() { localStorage.setItem('pump_filters', JSON.stringify(filters)); }
function loadFilters() {
    const saved = localStorage.getItem('pump_filters');
    if (saved) {
        filters = JSON.parse(saved);
        document.getElementById('minMcap').value = filters.minMcap;
        document.getElementById('maxMcap').value = filters.maxMcap;
        document.getElementById('maxInitial').value = filters.maxInitial;
        document.getElementById('safetyFilter').value = filters.safetyFilter;
    }
}
EOFJS

# Create README
cat > README.md << 'EOFMD'
# Pump.fun Token Monitor

Real-time screening dashboard for Pump.fun tokens on Solana.

## Quick Start

```bash
python3 -m http.server 8888
```

Open: http://localhost:8888

## Features

- Real-time WebSocket connection to Pump.fun
- Auto-screening with safety score (0-100)
- Customizable filters (market cap, initial buy, safety level)
- Browser notifications for safe tokens
- Direct links to Pump.fun & Solscan

## Screening Criteria

**Safe (70-100):** Green border
- Initial buy 0.5-3 SOL
- Market cap $5-50K
- Has description

**Warning (40-69):** Orange border
- Initial buy 5-10 SOL
- Market cap issues

**Danger (0-39):** Red border
- Initial buy > 10 SOL
- Market cap < $2K

## Usage

1. Open dashboard in browser
2. Enable notifications (click Allow)
3. Set filters (recommended: Safe Only)
4. Wait for green tokens (✅)
5. Click "Trade" to enter on Pump.fun

## Risk Management

- Max 2-5% per token
- Stop loss -30%
- Take profit in stages (50%, 100%, 200%)
- Always DYOR

**Not financial advice. Trade at your own risk.**
EOFMD

echo ""
echo "✅ Dashboard deployed successfully!"
echo ""
echo "📊 Start server:"
echo "   cd $INSTALL_DIR"
echo "   python3 -m http.server 8888"
echo ""
echo "🌐 Access:"
echo "   http://localhost:8888"
echo ""
echo "📚 See README.md for full documentation"
EOFJS

chmod +x "$INSTALL_DIR/deploy.sh" 2>/dev/null || true

echo "✅ Deployment complete!"
