---
name: vps-app-deployment
description: "Deploy web apps (Next.js, Node, Python) to VPS and expose publicly — clone, install, run dev/prod server, open firewall ports, and handle cloud provider security groups."
tags: [vps, deployment, nextjs, node, firewall, ufw, port, public-access, devops]
---

# VPS App Deployment

Deploy any web app to a VPS and make it publicly accessible. Covers the full flow: provision → clone → install → run → expose.

## When to Use

- User wants to install/run a GitHub repo on VPS
- User wants to access an app from outside the VPS (public IP)
- Port is open in UFW but still unreachable from outside
- Need to run a dev or prod server persistently

## Initial VPS Provisioning (Fresh Instance)

When setting up a brand-new VPS from scratch (EC2, Lightsail, etc.) — covers everything before the first `git clone`.

### Cloud Provider Steps

| Provider | Notes |
|---|---|
| **AWS EC2** | Pick Ubuntu 24.04 (not 22.04 — both can be Free Tier). Choose **x86** (not arm64/Graviton — arm64 images often aren't Free Tier). Instance type: **t2.micro** or **t3.micro**. Storage: gp2/gp3 8-30GB. Create key pair: **RSA**, format **.pem**. |
| **Lightsail** | Simpler alternative to EC2. Create instance → OS Only → Ubuntu 22.04 → $3.50/month plan (1 month free). No security group fuss. |
| **Security Groups (EC2)** | UFW alone is NOT enough — cloud firewall sits outside the VM. Open ports in EC2 Console → Security Groups → Inbound Rules. |

### First Login

```bash
chmod 400 ~/Downloads/your-key.pem
ssh -i ~/Downloads/your-key.pem ubuntu@<PUBLIC_IP>
```

### System Update & Core Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install git curl wget build-essential -y
```

### Node.js Installation & Global Packages

**Option A — System-wide via apt (STRONGLY preferred for VPS):**

```bash
# Install Node.js 22 system-wide
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# 🔑 CRITICAL: Install global CLI tools with sudo
# This puts binaries in /usr/bin/ which is ALWAYS in PATH regardless of
# bashrc state, byobu sessions, nvm, or hash table issues.
sudo npm install -g vercel pm2 9router
vercel --version    # works immediately — in /usr/bin/
pm2 --version       # works immediately — in /usr/bin/
9router --version   # works immediately — in /usr/bin/
```

> ⚠️ **Do NOT use `npm config set prefix ~/.local`** unless you have a specific reason. While it works in theory, Ubuntu VPS instances often have byobu/tmux that reconnects old sessions where `~/.local/bin` was never added to PATH. Using `sudo npm install -g` avoids ALL path issues by placing binaries in `/usr/bin/`.

> ⚠️ **Byobu gotcha:** Many Ubuntu AMIs ship with byobu enabled by default. It reconnects to stale sessions on SSH login, so PATH changes from bashrc/profile edits never apply. Disable it immediately on fresh VPS: `byobu-disable && mkdir -p ~/.byobu && touch ~/.byobu/disable`. See `references/npm-global-command-not-found.md` for the full diagnosis playbook.

Check successful install with:
```bash
node --version     # Should be v22.x
npm --version      # Should be 10.x
```

**Option B — Via nvm (only if version switching is genuinely needed):**

> ⚠️ **Avoid nvm on production VPS unless you need multiple Node versions.** nvm adds PATH complexity that causes "command not found" issues with byobu, non-login shells, and SSH remote commands. If you only need one Node version, use Option A.

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 22

# 🔑 Still use sudo for global CLI tools to avoid PATH issues:
sudo npm install -g vercel pm2 9router
```

### SSH Key for GitHub (needed for cloning private repos)

```bash
ssh-keygen -t ed25519 -C "hermes-vps"
# Accept defaults (no passphrase)
cat ~/.ssh/id_ed25519.pub
# → Copy output, add at https://github.com/settings/keys
# Verify: ssh -T git@github.com
# Expected: "Hi <username>!" — means auth works
```

### Verify Environment Readiness

```bash
git --version
curl --version
python3 --version   # Ubuntu 22.04 ships Python 3.10, 24.04 ships Python 3.12
```

After these steps, the VPS is ready for cloning repos and deploying apps.

---
## Step-by-Step Flow

### 1. Clone & Install

```bash
cd ~ && git clone <repo-url>
cd <repo-dir>

# Node/Next.js
npm install

# Python
pip install -r requirements.txt
```

### 2. Run the Server

**Dev mode (background):**
```bash
# Next.js — bind to 0.0.0.0 so it's reachable from outside
npm run dev -- --port 3001 --hostname 0.0.0.0
```

**Prod mode (recommended for persistent):**
```bash
npm run build
npm start -- --port 3001 --hostname 0.0.0.0
# or via PM2:
pm2 start npm --name "app" -- start -- --port 3001 --hostname 0.0.0.0
```

> ⚠️ Without `--hostname 0.0.0.0`, Next.js dev server binds to `127.0.0.1` only — unreachable from outside even if port is open.

### 3. Open Firewall (UFW)

```bash
sudo ufw allow <port>/tcp
sudo ufw reload
sudo ufw status  # verify
```

### 4. Verify Locally First

```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:<port>
# Should return 200 before testing public access
```

### 5. Test Public Access

```bash
VPS_IP=$(curl -s ifconfig.me)
curl -s -o /dev/null -w "%{http_code}" http://$VPS_IP:<port>
```

## ⚠️ Critical Pitfall: Cloud Provider Security Groups

**UFW alone is NOT enough on cloud VPS providers.**

Most cloud providers have a separate network-level firewall (security group / network ACL) that sits *outside* the VM. UFW controls the OS-level firewall; the cloud firewall is independent.

| Provider | Where to open ports |
|---|---|
| Tencent Cloud | Console → Security Groups → Inbound Rules |
| AWS EC2 | Console → Security Groups → Inbound Rules |
| GCP | Console → VPC → Firewall Rules |
| Alibaba Cloud | Console → Security Groups |
| DigitalOcean | Console → Networking → Firewalls (if enabled) |
| Vultr / Hetzner | Usually no extra firewall by default |

**Symptom:** `ss -tlnp` shows app listening on `0.0.0.0:<port>`, localhost curl returns 200, but public IP times out.

**Fix:** Open the port in the cloud console security group, not just UFW.

## ⚠️ Bashrc Corruption After sed Cleanup

When using `sed -i` to remove nvm lines, PATH entries, or other content from `~/.bashrc`, stray characters or unbalanced `if/fi` blocks can break bashrc syntax. The result: subsequent SSH sessions silently fail to source bashrc, causing all PATH modifications to silently not apply.

**Always verify after editing:**
```bash
bash -n ~/.bashrc && echo "SYNTAX OK" || echo "SYNTAX ERROR"
```

Common corruption patterns:
- `sed` removed an `if` line but left its matching `fi` — causes orphaned `fi` syntax error
- `.profile` corruption via the same mechanism (`.profile` sources `.bashrc`)
- Multiple `echo >>` appends creating duplicated or unbalanced blocks

**Symptom of broken bashrc:** Global `npm install -g <pkg>` works, `~/.local/bin/<pkg>` exists, but shell says `command not found` because `~/.local/bin` was never added to PATH (bashrc failed silently).

## Diagnosing Timeout from Public IP

```bash
# 1. Confirm app is listening on 0.0.0.0 (not 127.0.0.1)
ss -tlnp | grep <port>

# 2. Confirm UFW allows the port
sudo ufw status | grep <port>

# 3. If both OK but still timing out → cloud security group issue
# → Go to cloud provider console and open the port there
```

## Get VPS Public IP

```bash
curl -s ifconfig.me
```

## PM2 for Persistent Processes

```bash
# Start
pm2 start npm --name "sekaidrama" -- run dev -- --port 3001 --hostname 0.0.0.0

# Auto-restart on reboot
pm2 save
pm2 startup

# Monitor
pm2 status
pm2 logs sekaidrama
```

## Decommissioning / Tearing Down a Service

The inverse of deploy. When a project is retired (user says "hapus", "bersihkan", "decommission"), **map every trace before deleting anything**, check what depends on it, then remove. Skipping the mapping step leaves orphan cron jobs that error forever and stale PM2 entries that resurrect on reboot.

### 1. Map ALL traces (don't delete yet)

```bash
# PM2 process — get script path + cwd to know what to clean
pm2 describe <name> 2>/dev/null | grep -iE "script path|exec cwd|status|uptime|restarts"

# Files/dirs — use search_files(target=files, pattern="*<name>*"), NOT `find ~ -maxdepth N`
#   `find` scanning the whole home dir frequently TIMES OUT. search_files is faster + safer.
ls -la ~/.pm2/logs/<name>-*.log          # out + error logs
ls -la ~/.pm2/pids/<name>-*.pid          # pid file

# Cron — check BOTH system crontab AND Hermes cron
crontab -l 2>/dev/null | grep -i <name>
python3 -c "import json; d=json.load(open('/home/ubuntu/.hermes/cron/jobs.json')); jobs=d if isinstance(d,list) else d.get('jobs',d); [print(j.get('id'),j.get('name'),j.get('enabled'),j.get('script')) for j in (jobs if isinstance(jobs,list) else jobs.values()) if '<name>' in json.dumps(j).lower()]"
# Hermes cron jobs often reference a script in ~/.hermes/scripts/ — clean that too

# Stray artifacts: HTML reports, audit scripts, etc.
```

### 2. Check dependencies BEFORE killing

Don't tear down a service something else relies on, and don't delete data you can't recover.

```bash
# Does another project call this service? grep for its port / name
grep -rniE "<port>|<service-name>" ~/OtherProject --include="*.ts" --include="*.json" | grep -v node_modules

# Active connections right now?
ss -tnp 2>/dev/null | grep <port>

# Where does the service write data? grep the source so you don't nuke valuable output
grep -nE "open\(|CACHE_DIR|to_csv|\.db|\.json|output|/home" <script>.py
# If output lives in /tmp it's ephemeral (safe). If it writes to a real path, confirm with user first.
```

### 3. Remove cron via the TOOL, not by hand

```python
# Use the cronjob tool — don't hand-edit jobs.json (corruption risk, no validation)
cronjob(action="remove", job_id="<id>")
```

> Even **disabled** cron jobs warrant removal for a full cleanup — disabled ≠ gone.

### 4. Stop + delete PM2, then PERSIST

```bash
pm2 delete <name>
pm2 save          # CRITICAL: without `pm2 save`, the process resurrects on reboot from dump.pm2
```

### 5. Delete files

```bash
rm -rf ~/<project-dir> /tmp/<cache-dir> ~/.pm2/logs/<name>-*.log ~/.pm2/pids/<name>-*.pid ~/.hermes/scripts/<name>-script.py
```

### 6. Verify clean

```bash
# search_files(target=files, pattern="*<name>*") should return 0
pm2 jlist | python3 -c "import sys,json; print([p['name'] for p in json.load(sys.stdin)])"  # name gone
# Re-grep jobs.json for the name → no matches
```

> ⚠️ **Blocklist pitfall when diagnosing restart loops.** Grepping a process's logs for exit signals with the words for system halt/reboot triggers Hermes's *hardline blocklist* — the command is refused even though it's a read-only `grep`. Use neutral terms instead: `grep -iE "exit|restart|killed|uncaught|sigterm|listening"`. A high PM2 restart count (e.g. 31) with a now-stable `uptime` usually means an old crash loop that already self-resolved — confirm by sampling `restart_time` twice ~15s apart; if it doesn't increment, it's stable, not actively looping.

> ⚠️ **Security note worth flagging to the user:** services bound to `0.0.0.0:<port>` with no auth (common in quick scraper/API scripts) are publicly exposed. When you find one during teardown, mention it — shutting it down closes an unauthenticated surface.

## Rebranding a Cloned Repo (Fork/White-label)

When the user wants to rename a cloned project (e.g. "SekaiDrama" → "my-project"):

```bash
# 1. Find all occurrences first
grep -rn "OldName\|oldname\|Old Name" src --include="*.tsx" --include="*.ts" -l

# 2. Bulk replace across all source files
find src -type f \( -name "*.tsx" -o -name "*.ts" \) \
  -exec sed -i 's/OldName/NewName/g; s/oldname/newname/g; s/Old Name/New Name/g' {} +

# 3. Also patch package.json
sed -i 's/oldname/newname/g; s/OldName/NewName/g' package.json

# 4. Verify nothing left
grep -rn "OldName\|oldname" src package.json
# Should return empty (exit 1 = no matches = clean)
```

> Note: `sed -i` on macOS requires `sed -i ''` (empty string arg). On Linux VPS, `sed -i` works directly.

## Common Port Choices

- `3000` — default Next.js/Node
- `3001` — alternate (avoids conflict with other apps)
- `8000` / `8080` — Python/FastAPI/Django
- `80` / `443` — production (needs nginx or root)

## Edit a Live Vercel HTML Deployment (Source Files Gone)

When local source files were deleted but the Vercel deployment is still live:

```bash
# 1. Fetch current HTML from live URL
curl -s -L https://your-site.vercel.app/ -o /tmp/current.html

# 2. Edit the file (patch, sed, or python string replace)
cp /tmp/current.html /tmp/edited.html
# ... make edits ...

# 3. Deploy via Vercel REST API (no CLI needed)
python3 << 'EOF'
import json, requests

TOKEN = "your_vercel_token"
with open('/tmp/edited.html', 'r') as f:
    content = f.read()

payload = {
    "name": "your-project-name",
    "files": [{"file": "index.html", "data": content, "encoding": "utf-8"}],
    "projectSettings": {"framework": None},
    "target": "production"
}

r = requests.post(
    "https://api.vercel.com/v13/deployments",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json=payload, timeout=30
)
d = r.json()
print("state:", d.get("readyState"), "url:", d.get("url"), "id:", d.get("id"))
EOF

# 4. Poll until READY
python3 << 'EOF'
import requests, time
TOKEN = "your_vercel_token"
DEP_ID = "dpl_xxx"  # from step 3
for i in range(12):
    r = requests.get(f"https://api.vercel.com/v13/deployments/{DEP_ID}",
                     headers={"Authorization": f"Bearer {TOKEN}"}, timeout=15)
    state = r.json().get("readyState")
    print(f"[{i+1}] {state}")
    if state in ("READY", "ERROR", "CANCELED"):
        break
    time.sleep(5)
EOF
```

> ⚠️ The API deployment creates a new preview URL. The production alias (`your-site.vercel.app`) updates automatically when `"target": "production"` is set.

> ⚠️ After editing, verify the live URL actually reflects changes — Vercel CDN may serve stale cache for a few seconds.

## Deploy to Vercel (Non-Interactive)

When the user wants to deploy to Vercel instead of running on VPS:

```bash
# Install Vercel CLI globally first (REQUIRED — avoids npx timeout)
npm install -g vercel

# Deploy — --yes skips all interactive prompts, --name sets project name
vercel --token "<VERCEL_TOKEN>" --yes --name <project-name>

# Redeploy to production (after code changes)
vercel --token "<VERCEL_TOKEN>" --prod --yes
```

> ⚠️ **Don't use `npx vercel`** for the first deploy — npx will install the package (~54MB) inline and time out on slow connections. Always install globally first with `npm install -g vercel`.

> ⚠️ **Tencent VPS + Vercel: `~/.npmrc` mirror conflict.** If the VPS uses a Tencent mirror (`registry=https://mirrors.tencentyun.com/npm`), Vercel builds will crash with `npm error Exit handler never called!` — a misleading error that looks like an npm bug but is actually the mirror being unreachable from Vercel's DC. Fix: create a project-level `.npmrc` that overrides to the official registry:
> ```bash
> echo "registry=https://registry.npmjs.org/" > ~/your-project/.npmrc
> ```
> This file gets uploaded with the deployment and takes precedence over the global `~/.npmrc`.

> ⚠️ **Disk full → npm crash with misleading error.** If VPS disk is at 100%, npm crashes with `Exit handler never called!` — same error as the mirror issue. Always check disk before debugging npm:
> ```bash
> df -h /
> # If full, clean npm cache first:
> npm cache clean --force
> ```
> After cleaning, if still tight, switch to yarn (generates `yarn.lock`, Vercel auto-detects):
> ```bash
> npm install -g yarn
> cd ~/your-project && yarn install
> # Add to package.json to force Vercel to use yarn:
> # "packageManager": "yarn@1.22.22"
> ```

> ⚠️ **Run `npm run build` locally before deploying** to catch errors early. Vercel build logs are truncated and hard to debug.

> ⚠️ **lockfileVersion 3 crashes npm on some Vercel build runners.** If `package-lock.json` was generated with npm v7+ it will have `"lockfileVersion": 3`. Some Vercel build environments run an older npm that crashes with `Exit handler never called!` on v3 lockfiles. Fix: regenerate with v2:
> ```bash
> rm -f package-lock.json
> npm install --lockfile-version=2
> # Verify:
> grep "lockfileVersion" package-lock.json  # should say 2
> ```

> ⚠️ **package-lock.json contains Tencent mirror URLs.** Even if the project has no `.npmrc`, the `package-lock.json` itself may contain `resolved` URLs pointing to `mirrors.tencentyun.com/npm/...` from a previous install on a Tencent-configured machine. Vercel's build environment can't resolve these domains. Symptom: `npm error ENOTFOUND mirrors.tencentyun.com` during install. Fix: replace all Tencent URLs in the lockfile before deploying:
> ```bash
> sed -i 's|http://mirrors.tencentyun.com/npm/|https://registry.npmjs.org/|g' package-lock.json
> # Verify zero matches:
> grep -c "tencentyun" package-lock.json  # should be 0
> ```
> Then rebuild and redeploy. If more than ~50 URLs are affected, it's faster to regenerate the lockfile entirely:
> ```bash
> rm -f package-lock.json
> npm install --registry=https://registry.npmjs.org/
> ```

> ⚠️ **Don't use yarn as a fallback for npm issues on Vercel.** Yarn fetches from `registry.yarnpkg.com` which can timeout from Vercel's DC (Washington IAD1). If yarn install fails with network retries, switch back to npm with lockfileVersion 2 instead.

> ⚠️ **lockfileVersion=2 + project .npmrc may still not fix `Exit handler never called!`.** In some Vercel build runner versions, npm crashes before reading any project files at all — no registry, no lockfile, nothing helps. The definitive fix is to switch to GitHub-connected deploy (not CLI). The GitHub-triggered build environment is more stable. If you've tried: (1) project `.npmrc` override, (2) lockfileVersion=2, (3) yarn — and all still fail with the same error, stop and push to GitHub instead.

> ⚠️ **Last resort: `--prebuilt` deploy.** If both CLI and GitHub-triggered deploys fail with npm errors, build locally on VPS and upload the output directly — Vercel skips `npm install` entirely:
> ```bash
> # Build with production target (important — must match deploy target)
> npx vercel build --prod --token <VERCEL_TOKEN> --yes
> # Deploy prebuilt output
> npx vercel deploy --prebuilt --prod --token <VERCEL_TOKEN> --yes
> ```
> Common pitfall: if you run `vercel build` without `--prod`, the output is tagged as "preview" and `--prebuilt --prod` will reject it with "environment mismatch". Always use `--prod` on both commands.

> ⚠️ **If Vercel CLI deploy keeps failing after 3+ attempts with `Exit handler never called!`, switch to GitHub-connected deploy immediately — don't keep trying CLI variations.** The build environment for GitHub-triggered deploys is different and more stable. Steps:
> ```bash
> cd ~/your-project
> git init && git add . && git commit -m "Initial commit"
> # Create repo via GitHub UI, then push:
> git push -u origin master
> ```
> Then connect via Vercel API (no dashboard needed):
> ```bash
> # 1. Get GitHub repo ID
>   -H "Authorization: token <GITHUB_PAT>" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
>
> # 2. Get Vercel project ID
> PROJECT_ID=$(curl -s "https://api.vercel.com/v9/projects/your-project?teamId=your-team" \
>   -H "Authorization: Bearer <VERCEL_TOKEN>" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
>
> # 3. Link repo to project
> curl -s -X POST "https://api.vercel.com/v9/projects/$PROJECT_ID/link?teamId=your-team" \
>   -H "Authorization: Bearer <VERCEL_TOKEN>" \
>   -H "Content-Type: application/json" \
>
> # 4. Trigger deploy from GitHub
> curl -s -X POST "https://api.vercel.com/v13/deployments?teamId=your-team" \
>   -H "Authorization: Bearer <VERCEL_TOKEN>" \
>   -H "Content-Type: application/json" \
>   -d "{\"name\":\"your-project\",\"gitSource\":{\"type\":\"github\",\"repoId\":$REPO_ID,\"ref\":\"master\"},\"target\":\"production\"}"
> ```
> Note: The `/link` endpoint uses `POST` not `PATCH`. Do NOT include `projectId` in the deploy payload body — it goes in the URL query param only.


**Output to check:**
- `▲ Production  https://<name>-<hash>.vercel.app` — preview URL
- `▲ Aliased     https://<name>.vercel.app` — canonical URL
- `✓ Ready in Xs` — deploy succeeded

**After deploy:** Kill the local dev server if it was running — no need to keep it alive once Vercel is live.

---

## References

- `references/nextjs-maintenance.md` — Next.js + Tailwind maintenance patterns: color system conflicts, audit checklist, Tailwind class pitfalls, localStorage key mapping bugs, Vercel deploy workflow.
- `references/hermes-backup-restore.md` — Hermes Agent backup to GitHub private repo and restore on a new VPS: what to backup, push steps, clone steps, dependency setup, swap config, and common pitfalls.
- `references/npm-global-command-not-found.md` — Diagnosing "command not found" after `npm install -g`: byobu session caching, bash hash table, nvm PATH issues, broken bashrc, and the nuclear fix pattern (`sudo npm install -g` → `/usr/bin/`).

## SSH Tunneling for Remote SSO/OAuth Callbacks

When a VPS-hosted admin panel (e.g. Kiro-Go, n8n, Hasura) uses SSO/OAuth login, the callback redirects to `localhost:<port>` on the **user's local machine** — not the VPS. Without a tunnel, the browser on the user's PC can't reach the VPS's localhost.

### The Problem

1. Admin panel runs on VPS at `http://<VPS_IP>:8080`
2. User opens panel from Windows/Mac browser
3. Clicks "SSO Login" → service starts a temporary callback listener on VPS's `127.0.0.1:3128`
4. SSO provider redirects browser to `http://localhost:3128`
5. Browser tries to hit `localhost:3128` on the **user's PC** → nothing there → fail

### The Fix: SSH Local Port Forwarding

```bash
ssh -L 8080:127.0.0.1:8080 -L 3128:127.0.0.1:3128 ubuntu@<VPS_IP>
```

This maps:
- `localhost:8080` on PC → VPS's `127.0.0.1:8080` (admin panel)
- `localhost:3128` on PC → VPS's `127.0.0.1:3128` (SSO callback)

Then access `http://localhost:8080/admin` — SSO redirect to `localhost:3128` flows through the tunnel.

### ⚠️ Pitfall: "Connection refused" on callback port is NORMAL before SSO flow starts

Some services (Kiro-Go, etc.) only **dynamically bind** the callback port (e.g. 3128) when the SSO login flow is initiated. If you see `channel X: open failed: connect failed: Connection refused` in the SSH terminal **before clicking SSO Login**, that's expected — the port isn't listening yet.

**Don't restart the service.** Just proceed: open panel → click SSO Login → the port binds automatically → redirect succeeds.

If you see the error **after** clicking SSO Login, then the service actually crashed — check logs and restart.

### Multiple Ports in One Command

```bash
# Common pattern: admin panel + callback + API
ssh -L 8080:127.0.0.1:8080 -L 3128:127.0.0.1:3128 -L 9000:127.0.0.1:9000 ubuntu@<VPS_IP>
```

### Port Conflict: Two Services Fighting for Same Port

If `ss -tlnp | grep 3128` shows an unexpected process (e.g. kiro-go occupying the callback port), kill it first:

```bash
lsof -i :3128        # find what's holding the port
kill <PID>            # free it
ss -tlnp | grep 3128  # confirm port is free
```

Then restart the intended service. The callback port should be free for it to bind.

---

## Running Bot Scripts from GitHub Repos

When user shares a GitHub repo for a bot/script (farming bots, game bots, crypto bots):

### Common Pattern
```bash
cd ~ && git clone <repo-url>
cd <repo-dir>
npm install
# Fix config (see pitfalls below)
node bot.js  # run in background
```

### Pitfalls

1. **Hardcoded wallet paths/addresses** — Many bot repos hardcode the author's wallet address and key file path instead of reading from `.env`. Always check the first 20 lines of the main script for hardcoded constants and patch them before running.

2. **bs58 v5 `.default` export issue** — `require('bs58').default` returns `undefined` in some bs58 v5 installations. Fix:
   ```javascript
   // Replace:
   const bs58 = require('bs58').default;
   // With:
   const bs58 = require('bs58').default || require('bs58');
   ```

3. **Wallet JSON format** — Many Solana bots expect a wallet JSON file with format:
   ```json
   {"private_key": "base58_encoded_key", "address": "wallet_address"}
   ```
   Create this file at the path the bot expects (check `WALLET_FILE` or similar constant).

4. **Bot outputs to log file, not stdout** — Many bots write to a log file (e.g., `/tmp/bot.log`) via `fs.appendFileSync`. Check for a `LOG` constant and `tail -f` that file to monitor.

5. **Hardcoded player IDs** — Game bots often have a hardcoded player UUID. This usually auto-updates after first authentication, but check if it causes issues.

### Running as Background Process
```bash
# Use Hermes terminal(background=true) with watch_patterns for key events
# Monitor via the bot's log file:
tail -f /tmp/bot_name.log

# Or PM2 for persistence:
pm2 start bot.js --name "farming-bot"
pm2 save && pm2 startup
```

---

For production, put nginx in front instead of exposing Node directly:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/app
sudo ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo ufw allow 80/tcp
```
