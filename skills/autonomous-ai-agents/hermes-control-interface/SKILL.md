---
name: hermes-control-interface
description: "Setup and configure Hermes monitoring dashboards — web-based Control Interface for remote management and terminal-based HUD for quick status checks."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, web-dashboard, remote-access, monitoring, control-panel]
    homepage: https://github.com/xaspx/hermes-control-interface
    related_skills: [hermes-agent, hermes-hud]
---

# Hermes Control Interface

Web-based dashboard for managing and monitoring Hermes Agent. Provides chat interface, file explorer, agent session management, usage tracking, and real-time monitoring via browser.

**When to use:**
- Need web UI for Hermes Agent (vs terminal-only)
- Want remote access to agent from any device
- Managing multiple agent sessions
- Monitoring token usage and costs
- Need mobile-friendly interface

**Installation:** See `hermes-agent` skill → Hermes ecosystem tools section.

## Architecture

Hermes Control Interface runs **two separate servers**:

1. **Backend API** (Node.js Express)
   - Port: `10272` (default)
   - Handles auth, file operations, agent API calls
   - WebSocket for real-time updates

2. **Frontend** (Vite dev server)
   - Port: `5173` (default, dev mode)
   - Serves static UI, proxies API calls to backend
   - Hot-reload during development

**Both servers must run simultaneously** for the dashboard to work.

## Quick Start

### Prerequisites

- Node.js 20+ (Vite requires 20.19+ or 22.12+)
- npm 10+
- Hermes Agent installed

### Installation

```bash
# Clone repo
cd ~
git clone https://github.com/xaspx/hermes-control-interface.git
cd hermes-control-interface

# Install dependencies
npm install

# Configure environment
cp .env.example .env
nano .env  # Set password and secrets
```

### Configuration

Edit `~/hermes-control-interface/.env`:

```bash
# Required
HERMES_CONTROL_PASSWORD=your_secure_password_here
HERMES_CONTROL_SECRET=$(openssl rand -hex 32)

# Optional: Remote access
HOST=0.0.0.0  # Listen on all interfaces (default: 127.0.0.1)
PORT=10272    # Backend API port (default: 10272)
```

**Security:** Generate strong secrets with `openssl rand -hex 32`.

### Start Servers

**Terminal 1 - Backend:**
```bash
cd ~/hermes-control-interface
node server.js
```

**Terminal 2 - Frontend:**
```bash
cd ~/hermes-control-interface
npm run dev
```

**Access:** http://localhost:5173

## Remote Access Setup

To access from other devices (phone, laptop on same network, or internet):

### 1. Configure Servers for Remote Access

Edit `~/hermes-control-interface/.env`:

```bash
HOST=0.0.0.0
PORT=10272
```

Edit `~/hermes-control-interface/vite.config.js`:

```javascript
export default defineConfig({
  // ...
  server: {
    host: '0.0.0.0',  // Add this line
    port: 5173,
    // ...
  },
});
```

### 2. Open Firewall Ports

**Required ports:**
- `5173` - Frontend (Vite)
- `10272` - Backend API

**Cloud provider (AWS, GCP, Tencent Cloud, etc.):**
1. Go to Security Groups / Firewall Rules
2. Add inbound rules:
   - Type: Custom TCP
   - Port: 5173
   - Source: 0.0.0.0/0 (or specific IP for security)
3. Repeat for port 10272

**Local firewall (UFW):**
```bash
sudo ufw allow 5173/tcp
sudo ufw allow 10272/tcp
sudo ufw status
```

### 3. Find Server IP

```bash
curl -s ifconfig.me
# Or: curl -s icanhazip.com
```

### 4. Access from Remote Device

**URL:** `http://YOUR_SERVER_IP:5173`

**Login:** Enter password (no username required by default)

## Node.js Version Management

Hermes Control Interface requires Node.js 20+. If you have an older version:

### Using nvm (recommended)

```bash
# Install/update to Node 20
nvm install 20
nvm use 20
nvm alias default 20

# Verify
node --version  # Should show v20.x.x
```

### System-wide upgrade

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node --version
```

### Reinstall Dependencies After Node Upgrade

If you upgraded Node after initial `npm install`:

```bash
cd ~/hermes-control-interface
rm -rf node_modules package-lock.json
npm install
```

This fixes native module compatibility issues (e.g., `rolldown` binding errors).

## Customization

See `references/custom-branding.md` for complete guide on rebranding (name, logo, colors, fonts).

### Password-Only Login (No Username)

By default, HCI uses username + password. To simplify to password-only:

**1. Frontend HTML** (`src/index.html`):

Remove username fields from both login and setup forms:

```html
<!-- Login form -->
<form id="login-form" class="login-form">
  <!-- Remove: <input id="login-username" ... /> -->
  <input id="login-password" type="password" placeholder="Password" />
  <button type="submit">unlock</button>
</form>

<!-- Setup form -->
<form id="setup-form" class="login-form">
  <!-- Remove: <input id="setup-username" ... /> -->
  <input id="setup-password" type="password" placeholder="Password (min 8 chars)" />
  <input id="setup-password-confirm" type="password" placeholder="Confirm password" />
  <button type="submit">create admin</button>
</form>
```

**2. Frontend JavaScript** (`src/js/main.js`):

Update form handlers to send password only:

```javascript
// Login form
document.getElementById('login-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const password = document.getElementById('login-password').value;
  // Remove: const username = ...
  
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),  // Remove username
    credentials: 'include',
  });
  // ...
});

// Setup form - same pattern
```

**3. Backend API** (`server.js`):

Update auth endpoints to use fixed username:

```javascript
// Setup endpoint
app.post('/api/auth/setup', loginRateLimiter, (req, res) => {
  const { password } = req.body || {};
  const username = 'admin';  // Fixed username
  
  if (!password) {
    return res.status(400).json({ ok: false, error: 'Password required' });
  }
  // ... rest of setup logic
});

// Login endpoint
app.post('/api/auth/login', loginRateLimiter, (req, res) => {
  const { password } = req.body || {};
  const username = 'admin';  // Fixed username
  
  if (!password) {
    return res.status(400).json({ ok: false, error: 'Password required' });
  }
  // ... rest of login logic
});
```

**4. Restart servers** after changes.

## Production Deployment

For production use:

### Build Static Assets

```bash
cd ~/hermes-control-interface
npm run build
```

This creates `dist/` directory with optimized static files.

### Serve with Node (Production Mode)

```bash
# Backend serves both API and static files
node server.js
```

Access at: `http://YOUR_SERVER_IP:10272`

### Reverse Proxy with Nginx (Recommended)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:10272;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Add SSL with Let's Encrypt:

```bash
sudo certbot --nginx -d your-domain.com
```

## Pitfalls

### Connection Error on Login

**Symptom:** Frontend loads but login shows "Connection error"

**Cause:** Backend server (port 10272) not running or not accessible

**Fix:**
1. Check backend is running: `netstat -tlnp | grep 10272`
2. If not running, start it: `node server.js`
3. If running on 127.0.0.1, change to 0.0.0.0 in `.env`
4. Open port 10272 in firewall/security group

### Vite Version Error

**Symptom:** `You are using Node.js 18.x. Vite requires Node.js version 20.19+`

**Cause:** Node.js version too old

**Fix:** Upgrade Node.js (see "Node.js Version Management" section above)

### Native Module Binding Error

**Symptom:** `Cannot find native binding` or `Cannot find module '@rolldown/binding-linux-x64-gnu'`

**Cause:** npm optional dependencies bug (https://github.com/npm/cli/issues/4828), or Node version changed after install

**Fix:**
```bash
cd ~/hermes-control-interface
rm -rf node_modules package-lock.json
npm install
```

**Note:** This is a known npm bug with optional dependencies. Always do clean reinstall after Node.js version upgrades.

### Frontend Works but Backend Unreachable from Remote

**Symptom:** Can access port 5173 remotely, but API calls fail

**Cause:** Port 10272 not opened in cloud security group

**Fix:** Add security group rule for port 10272 (see "Remote Access Setup" section)

### nvm Not Persisting Across Sessions

**Symptom:** `node --version` shows old version after reopening terminal

**Cause:** nvm not loaded in shell profile

**Fix:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Set default version
nvm alias default 20
```

## Features

Once logged in, the dashboard provides:

- **Home** - Overview dashboard with system stats
- **Agents** - Manage agent sessions, view active conversations
- **Usage** - Token usage tracking, cost analysis, billing breakdown
- **Skills** - Browse installed skills, view documentation
- **Chat** - Web-based chat interface with agent
- **Logs** - View agent logs, filter by session/level
- **Monitor** - Real-time monitoring of agent activity
- **Maintenance** - System maintenance tasks, cache clearing
- **Files** - File explorer for Hermes directories

## Troubleshooting

### Check Server Status

```bash
# Check if processes are running
ps aux | grep -E "node.*server.js|vite"

# Check ports
netstat -tlnp | grep -E "5173|10272"
# Or: ss -tlnp | grep -E "5173|10272"
```

### View Logs

Backend logs print to stdout when running `node server.js`. For persistent logging:

```bash
# Run with output redirect
node server.js > ~/hci-backend.log 2>&1 &

# View logs
tail -f ~/hci-backend.log
```

### Reset Admin Password

```bash
cd ~/hermes-control-interface
npm run reset-password
```

## Hermes HUD (Terminal Dashboard)

Terminal-based heads-up display for Hermes Agent. Shows real-time agent state including memory entries, user profile, installed skills, cron jobs, and activity timeline. Think of it as `neofetch` for your AI agent.

### HUD Installation
```bash
cd ~
git clone https://github.com/joeynyc/hermes-hud.git
cd hermes-hud
python3 -m venv venv
source venv/bin/activate
pip install -e ".[neofetch]"
```

### HUD Usage
```bash
source ~/hermes-hud/venv/bin/activate
hermes-hud --text    # Compact text output
hermes-hud           # Interactive TUI mode
hermes-hud --ai      # Neofetch-style ASCII art
hermes-hud --br      # Blade Runner aesthetic
hermes-hud --fsociety # Mr. Robot theme
```

### HUD vs Control Interface
| Feature | HUD | Control Interface |
|---------|-----|-------------------|
| Interface | Terminal (TUI/text) | Web browser |
| Access | Local only | Remote capable |
| Speed | Instant | Requires server startup |
| Use case | Quick checks, scripting | Full management, mobile |
| Dependencies | Python venv | Node.js 20+, dual servers |
| Interactivity | Read-only monitoring | Full control (chat, files) |

**When to use HUD:** Quick status checks, terminal workflows, scripting, cron monitoring
**When to use Control Interface:** Remote access, mobile, full agent management, chat interface

### HUD Troubleshooting
- `hermes-hud: command not found` → activate venv first
- No data displayed → verify `~/.hermes/` exists and has config.yaml
- TUI crashes → use `--text` mode instead

## See Also

- `hermes-agent` skill → Main Hermes Agent configuration
- GitHub (Control Interface): https://github.com/xaspx/hermes-control-interface
- GitHub (HUD): https://github.com/joeynyc/hermes-hud
