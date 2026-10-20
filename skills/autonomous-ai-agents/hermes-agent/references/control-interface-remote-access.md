# Hermes Control Interface — Remote Access Setup

Complete workflow for exposing Hermes Control Interface to external networks (mobile, remote browsers).

## Architecture

Hermes Control Interface is a two-component web application:

| Component | Port | Purpose | Config File |
|-----------|------|---------|-------------|
| **Frontend** (Vite dev server) | 5173 | React UI, serves static assets | `vite.config.js` |
| **Backend** (Express API) | 10272 | Authentication, WebSocket, file operations, terminal PTY | `server.js` + `.env` |

Frontend proxies `/api` and `/ws` requests to backend. Both must be accessible for the app to work.

## Prerequisites

- Node.js 20+ (Vite 8.x requirement)
- Hermes Control Interface installed at `~/hermes-control-interface`
- `.env` file configured with `HERMES_CONTROL_PASSWORD` and `HERMES_CONTROL_SECRET`

## Step 1: Upgrade Node.js (if needed)

Vite 8.x requires Node.js 20.19+ or 22.12+. If you have nvm installed and it overrides system Node:

```bash
# Check current version
node --version

# If < 20.19, upgrade via nvm
source ~/.nvm/nvm.sh
nvm install 20
nvm use 20
nvm alias default 20

# Verify
node --version  # Should show v20.20.2 or newer
```

**Pitfall:** System-installed Node (via apt) may be overridden by nvm. Always check `which node` — if it points to `~/.nvm/versions/node/`, you must use nvm commands to upgrade.

## Step 2: Fix npm Optional Dependencies Bug

Vite 8.x + rolldown has a known npm bug with optional dependencies. If you see `Cannot find native binding` errors:

```bash
cd ~/hermes-control-interface
rm -rf node_modules package-lock.json
source ~/.nvm/nvm.sh && nvm use 20
npm install
```

This forces a clean reinstall with the correct Node version, resolving missing native bindings.

## Step 3: Configure Frontend for 0.0.0.0

Edit `~/hermes-control-interface/vite.config.js`:

```javascript
export default defineConfig({
  // ... existing config
  server: {
    host: '0.0.0.0',  // ADD THIS LINE
    port: 5173,
    proxy: {
      '/api': backendUrl,
      '/ws': {
        target: backendWsUrl,
        ws: true,
      },
    },
  },
  // ...
});
```

**Default:** Vite listens on `127.0.0.1` (localhost only). Adding `host: '0.0.0.0'` makes it accessible from external IPs.

## Step 4: Configure Backend for 0.0.0.0

Edit `~/hermes-control-interface/.env`:

```bash
# Add these lines (or uncomment if present)
PORT=10272
HOST=0.0.0.0
```

**How it works:** `server.js` reads `process.env.HOST` at startup (line 4707, 4719). Default is `127.0.0.1`. Setting `HOST=0.0.0.0` makes the Express server listen on all interfaces.

## Step 5: Start Both Servers

**Terminal 1 — Frontend:**
```bash
cd ~/hermes-control-interface
source ~/.nvm/nvm.sh && nvm use 20
npm run dev
```

**Terminal 2 — Backend:**
```bash
cd ~/hermes-control-interface
source ~/.nvm/nvm.sh && nvm use 20
node server.js
```

**Verify both are listening on 0.0.0.0:**
```bash
netstat -tlnp | grep -E "5173|10272"
# Expected output:
# tcp  0  0  0.0.0.0:5173   0.0.0.0:*  LISTEN  <pid>/node
# tcp  0  0  0.0.0.0:10272  0.0.0.0:*  LISTEN  <pid>/node
```

## Step 6: Open Firewall Ports

**Both ports must be open** for the app to work. Frontend alone will load but show "Connection error" at login.

### Cloud Provider (Tencent Cloud, AWS, GCP, Azure)

Add inbound rules to the instance's security group:

| Rule | Protocol | Port | Source | Action |
|------|----------|------|--------|--------|
| Frontend | TCP | 5173 | 0.0.0.0/0 | Allow |
| Backend API | TCP | 10272 | 0.0.0.0/0 | Allow |

**For production:** Restrict `Source` to specific IPs (e.g., `YOUR_IP/32`) instead of `0.0.0.0/0`.

### Local Firewall (UFW)

If using UFW instead of cloud security groups:

```bash
# IMPORTANT: Allow SSH first to avoid lockout
sudo ufw allow 22/tcp

# Allow Hermes Control Interface
sudo ufw allow 5173/tcp
sudo ufw allow 10272/tcp

# Enable firewall
sudo ufw enable

# Verify
sudo ufw status
```

## Step 7: Access from Browser

**URL:** `http://<SERVER_IP>:5173`

**Login:**
- **Username:** None (password-only authentication)

**Test from mobile:** Open browser, navigate to `http://<SERVER_IP>:5173`, enter password, click UNLOCK.

## Troubleshooting

### "Connection error" at login

**Symptom:** Frontend loads, but login fails with red "Connection error" message.

**Cause:** Backend (port 10272) is not accessible. Either:
1. Backend not running
2. Backend listening on 127.0.0.1 instead of 0.0.0.0
3. Port 10272 blocked by firewall

**Fix:**
```bash
# Check if backend is running
netstat -tlnp | grep 10272

# If listening on 127.0.0.1, add HOST=0.0.0.0 to .env and restart
# If not running, start it: node server.js
# If running on 0.0.0.0 but still failing, check firewall
```

### Frontend loads but shows blank page

**Cause:** Node.js version too old (< 20.19).

**Fix:** Upgrade Node.js (see Step 1).

### "Cannot find native binding" error

**Cause:** npm optional dependencies bug with rolldown.

**Fix:** Clean reinstall (see Step 2).

### Changes to vite.config.js not taking effect

**Cause:** Vite dev server caches config.

**Fix:** Stop (`Ctrl+C`) and restart `npm run dev`.

### Changes to .env not taking effect

**Cause:** Backend reads `.env` once at startup.

**Fix:** Stop (`Ctrl+C`) and restart `node server.js`.

## Production Deployment

For production use, consider:

1. **HTTPS with Nginx reverse proxy:**
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://localhost:5173;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
       
       location /api {
           proxy_pass http://localhost:10272;
       }
       
       location /ws {
           proxy_pass http://localhost:10272;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "Upgrade";
       }
   }
   ```

2. **Build static frontend:**
   ```bash
   npm run build
   # Serve dist/ with nginx or any static host
   ```

3. **Systemd service for backend:**
   ```ini
   [Unit]
   Description=Hermes Control Interface Backend
   After=network.target
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/hermes-control-interface
   ExecStart=/home/ubuntu/.nvm/versions/node/v20.20.2/bin/node server.js
   Restart=on-failure
   Environment="NODE_ENV=production"
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Strong password:** Change `HERMES_CONTROL_PASSWORD` in `.env` to a long random string:
   ```bash
   openssl rand -hex 32
   ```

5. **IP allowlist:** Restrict security group source to known IPs instead of `0.0.0.0/0`.

## Key Insights

- **Two separate servers:** Frontend (Vite) and backend (Express) must both be configured and accessible.
- **Port 10272 is critical:** Without it, login will always fail with "Connection error".
- **nvm overrides system Node:** Always use `source ~/.nvm/nvm.sh && nvm use 20` before running npm commands if nvm is installed.
- **npm optional dependencies bug:** Clean reinstall fixes "Cannot find native binding" errors with Vite 8.x + rolldown.
- **Cloud security groups vs UFW:** Most cloud VMs use security groups (external firewall). UFW (local firewall) is usually inactive by default on cloud instances.

## Related References

- `references/control-interface-customization.md` — Branding, password-only login, display name changes.
