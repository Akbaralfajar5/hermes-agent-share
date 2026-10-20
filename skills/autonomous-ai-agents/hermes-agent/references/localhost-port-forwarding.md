# Exposing Localhost-Only Applications to External Networks

## Problem

Application binds to `127.0.0.1` (localhost) and cannot be accessed from external networks (mobile, remote browsers). Common with:
- npm packages that hardcode localhost binding (e.g., `9router`)
- Development servers with default localhost-only configs
- Applications that ignore `--host 0.0.0.0` flags

## Symptoms

- `curl http://localhost:PORT` works on the server
- `curl http://SERVER_IP:PORT` times out or connection refused
- `lsof -i :PORT` shows `127.0.0.1:PORT` instead of `0.0.0.0:PORT`

## Diagnosis

```bash
# Check what address the app is listening on
sudo lsof -i :PORT -P -n

# Look for:
# 127.0.0.1:PORT  → localhost only (problem)
# 0.0.0.0:PORT    → all interfaces (good)
# *:PORT          → all interfaces (good)
```

## Solutions (in order of preference)

### 1. Application-Level Config

Try these in order:

**Environment variables:**
```bash
HOST=0.0.0.0 PORT=20128 npm start
HOSTNAME=0.0.0.0 PORT=20128 npm start
```

**Command-line flags:**
```bash
app --host 0.0.0.0 --port 20128
app -H 0.0.0.0 -p 20128
```

**Config file:**
```js
// next.config.js, vite.config.js, etc.
module.exports = {
  server: {
    host: '0.0.0.0',
    port: 20128
  }
}
```

**Pitfall:** Some npm packages (like `9router`) ignore these flags and hardcode `127.0.0.1`. If `lsof` still shows `127.0.0.1` after trying all flags, move to solution 2.

### 2. iptables NAT (Recommended for Hardcoded Apps)

Forward external traffic to localhost:

```bash
# Allow external connections to the port
sudo ufw allow 20128/tcp
sudo ufw reload  # or skip if firewall disabled

# NAT rule: external → localhost
sudo iptables -t nat -A PREROUTING -p tcp --dport 20128 -j DNAT --to-destination 127.0.0.1:20128

# NAT rule: local machine → localhost (for testing from server itself)
sudo iptables -t nat -A OUTPUT -p tcp --dport 20128 -j DNAT --to-destination 127.0.0.1:20128

# Verify rules
sudo iptables -t nat -L -n -v | grep 20128

# Test from server
curl -I http://SERVER_IP:20128

# Test from external device (mobile/laptop)
curl -I http://SERVER_IP:20128
```

**Pros:**
- Works with any hardcoded localhost app
- No application restart needed
- Transparent to the app

**Cons:**
- Rules don't persist across reboots (see persistence section below)
- Requires root/sudo

**Persistence (optional):**
```bash
# Save rules
sudo iptables-save > /etc/iptables/rules.v4

# Auto-restore on boot (Ubuntu/Debian)
sudo apt install iptables-persistent
sudo netfilter-persistent save
```

### 3. socat Port Forward

Simple TCP proxy:

```bash
# Forward 20129 → localhost:20128
socat TCP-LISTEN:20129,fork,reuseaddr TCP:127.0.0.1:20128 &

# Access via http://SERVER_IP:20129
```

**Pros:**
- No root needed
- Easy to kill (`pkill socat`)

**Cons:**
- Uses a different port (20129 instead of 20128)
- Process dies if terminal closes (use `nohup` or `screen`)

### 4. Nginx Reverse Proxy

For production setups or when you want to expose on port 80 (standard HTTP):

**Full setup workflow:**

```bash
# 1. Install nginx
sudo apt update && sudo apt install nginx -y

# 2. Create config file
sudo tee /etc/nginx/sites-available/app > /dev/null <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name _;
    
    # Increase timeouts for long-running requests
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    proxy_read_timeout 600;
    send_timeout 600;
    
    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # Proxy headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    location / {
        proxy_pass http://localhost:20128;
    }
}
EOF

# 3. Enable the site (remove default, link new config)
sudo rm /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/app /etc/nginx/sites-enabled/app

# 4. Test config
sudo nginx -t

# 5. Restart nginx
sudo systemctl restart nginx

# 6. Enable auto-start on boot
sudo systemctl enable nginx

# 7. Verify nginx is running
sudo systemctl status nginx --no-pager

# 8. Test access
curl -I http://SERVER_IP
```

**Access via:**
- `http://SERVER_IP` (no port needed, uses standard port 80)
- `http://SERVER_IP:80` (explicit port)

**Pros:**
- Production-ready
- Standard port 80 (no `:20128` in URL)
- SSL/TLS support (add certbot for HTTPS)
- Load balancing, caching, rate limiting
- WebSocket support included
- Auto-starts on server reboot

**Cons:**
- Requires nginx installation
- More complex setup than iptables
- Needs root/sudo access

**SSL/HTTPS (optional):**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get free SSL certificate (requires domain name)
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

**Troubleshooting:**

1. **"Address already in use" on port 80:**
   ```bash
   # Check what's using port 80
   sudo lsof -i :80
   
   # If Apache is running, stop it
   sudo systemctl stop apache2
   sudo systemctl disable apache2
   ```

2. **"502 Bad Gateway":**
   ```bash
   # Check if backend app is running
   sudo lsof -i :20128
   
   # Check nginx error logs
   sudo tail -50 /var/log/nginx/error.log
   ```

3. **Config test fails:**
   ```bash
   # Detailed syntax check
   sudo nginx -t
   
   # Check for typos in config file
   sudo cat /etc/nginx/sites-available/app
   ```

### 5. Cloudflare Tunnel (Recommended for Quick Public Access)

For public internet access without exposing server IP:

```bash
# Install cloudflared (if not already installed)
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared

# Quick tunnel (temporary URL) - run in background
cloudflared tunnel --url http://localhost:20128 --no-autoupdate 2>&1 | tee /tmp/cloudflared.log &

# Wait 5-10 seconds for tunnel to establish
sleep 8

# Extract the public URL
cat /tmp/cloudflared.log | grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com'

# Output example: https://compile-issue-watson-employed.trycloudflare.com
```

**Pros:**
- No firewall/port config needed
- Free
- HTTPS by default
- Works even when iptables NAT fails
- Bypasses ISP port blocking

**Cons:**
- Random URL (unless you set up a named tunnel)
- Requires internet connection
- Cloudflare can see traffic
- URL changes on restart

**When to use:** When iptables NAT works from server but external access still fails (cloud security groups, ISP blocking, complex network topology).

## Verification

After applying any solution:

```bash
# From server
curl -I http://SERVER_IP:20128

# From external device
curl -I http://SERVER_IP:20128

# Or open in browser
http://SERVER_IP:20128
```

Expected: HTTP 200 or 307 redirect (not connection refused/timeout).

## Troubleshooting

### "Connection refused" after iptables rules

1. **Check firewall:**
   ```bash
   sudo ufw status
   sudo ufw allow 20128/tcp
   ```

2. **Verify app is running:**
   ```bash
   sudo lsof -i :20128
   ps aux | grep app_name
   ```

3. **Check iptables rules applied:**
   ```bash
   sudo iptables -t nat -L -n -v | grep 20128
   ```

4. **Test from server first:**
   ```bash
   curl -I http://127.0.0.1:20128  # Should work
   curl -I http://SERVER_IP:20128  # Should also work after NAT
   ```

### "Connection timeout" from mobile/external

1. **Cloud provider security groups** — AWS, GCP, Azure, etc. have separate firewall rules:
   - AWS: EC2 → Security Groups → Inbound Rules → Add TCP 20128
   - GCP: VPC → Firewall Rules → Create rule for TCP 20128
   - Azure: Network Security Groups → Inbound Rules → Add TCP 20128

2. **ISP/Network blocking** — some ISPs block non-standard ports:
   - Try port 8080 or 443 instead
   - Use Cloudflare Tunnel as workaround

3. **VPN/Proxy interference** — disable VPN on client device and retry

### App still binds to 127.0.0.1 after restart

Some apps re-read config on restart and override environment variables. Solutions:
1. Edit the app's source code (if accessible)
2. Use iptables NAT (solution 2) — works regardless of app config
3. Wrap the app in a script that forces the binding

## Example: 9router (May 2026)

**Problem:** `9router` npm package ignores `-H 0.0.0.0` flag and `HOST`/`HOSTNAME` env vars. Always binds to `127.0.0.1:20128`.

**Attempted solutions that failed:**
```bash
9router -H 0.0.0.0 -p 20128  # Still binds to 127.0.0.1
HOST=0.0.0.0 9router -p 20128  # Still binds to 127.0.0.1
HOSTNAME=0.0.0.0 9router -p 20128  # Still binds to 127.0.0.1
```

**Working solutions:**

**Option A: iptables NAT** (works but requires port in URL)
```bash
sudo ufw allow 20128/tcp
sudo iptables -t nat -A PREROUTING -p tcp --dport 20128 -j DNAT --to-destination 127.0.0.1:20128
sudo iptables -t nat -A OUTPUT -p tcp --dport 20128 -j DNAT --to-destination 127.0.0.1:20128

# Access via http://43.159.56.39:20128
curl -I http://43.159.56.39:20128  # Works from external
```

**Option B: Nginx reverse proxy** (production-ready, standard port 80)
```bash
# Install and configure nginx
sudo apt update && sudo apt install nginx -y

# Create config
sudo tee /etc/nginx/sites-available/9router > /dev/null <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    
    location / {
        proxy_pass http://localhost:20128;
    }
}
EOF

# Enable and start
sudo rm /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/9router /etc/nginx/sites-enabled/9router
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Access via http://43.159.56.39 (no port needed!)
curl -I http://43.159.56.39  # Works from external
```

**Option C: Cloudflare Tunnel** (public HTTPS URL, no firewall config)
```bash
# Start tunnel
cloudflared tunnel --url http://localhost:20128 --no-autoupdate 2>&1 | tee /tmp/cloudflared.log &

# Wait and extract URL
sleep 8
cat /tmp/cloudflared.log | grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com'

# Access via https://random-name.trycloudflare.com
```

**Key insight:** When an app hardcodes `127.0.0.1` in its source code, no amount of flags/env vars will change it. You need a network-level solution (iptables NAT, nginx proxy, or tunnel).

## Related Issues

- **"Can't access from mobile"** → this guide
- **"Port is open but connection refused"** → check if app binds to 0.0.0.0 vs 127.0.0.1
- **"Works on server but not externally"** → this guide
- **"lsof shows 127.0.0.1 instead of 0.0.0.0"** → this guide

## Security Considerations

**Before exposing any app to the internet:**

1. **Authentication** — ensure the app has login/auth enabled
2. **Firewall rules** — only allow specific IPs if possible:
   ```bash
   sudo ufw allow from YOUR_IP to any port 20128
   ```
3. **HTTPS** — use Cloudflare Tunnel or nginx with SSL for sensitive data
4. **Rate limiting** — prevent abuse (nginx, Cloudflare, or app-level)
5. **Monitoring** — watch logs for suspicious activity

**Never expose:**
- Development servers with debug mode enabled
- Apps with default/weak passwords
- Internal admin panels
- Database ports (3306, 5432, 27017, etc.)
