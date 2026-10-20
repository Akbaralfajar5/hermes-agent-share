# Hermes Agent — VPS Backup & Restore

## Overview

Hermes is a heavy setup (skills/, memories/, config/, plugins/) — ~20MB+ of config and state. Cannot rely on `curl | bash` reinstall; must backup **everything** and restore as a complete copy.

## What to Backup

| Path | Contents | Critical? |
|---|---|---|
| `~/.hermes/SOUL.md` | Agent persona + boundaries | ✅ Critical |
| `~/.hermes/config.yaml` | All settings, tools, providers | ✅ Critical |
| `~/.hermes/config/*` | Full config directory | ✅ |
| `~/.hermes/skills/` | All user-created skills | ✅ (largest — ~1600 files) |
| `~/.hermes/memories/` | MEMORY.md + USER.md + session notes | ✅ |
| `~/.hermes/.env` | API keys, credentials | ⚠️ Do NOT push raw — `.env.example` instead |
| `~/.hermes/cron/jobs.json` | Cron job schedule | ✅ |
| `~/.hermes/scripts/` | User scripts | ✅ |
| `~/.hermes/plugins/` | Plugins | ✅ |
| `~/.hermes/gateway/` | Gateway config | ✅ |

## Backup Method: GitHub Private Repo

Recommended over tar.gz — easy to clone on new VPS.

### Step 1: Create Private Repo

Create a private repo on GitHub (e.g. `<username>/hermes-backup`).

### Step 2: Push Hermes Config

```bash
cd ~/.hermes/
git init
git remote add origin git@github.com:<username>/hermes-backup.git

# IMPORTANT: Don't push credentials
cat >> .gitignore << 'EOF'
.env
*.log
*.pid
gateway/store/
cron/logs/
hermes_cache/
image_cache/
audio_cache/
EOF

git add .
git commit -m "Hermes backup $(date +%Y-%m-%d)"
git push -u origin main
```

### Step 3: Add .env.example

```bash
cp .env .env.example
# Edit .env.example to remove secret values, keep keys only:
# PROVIDER_API_KEY=your_key_here → PROVIDER_API_KEY=
git add .env.example
git commit -m "Add env example"
git push
```

## Restore on New VPS

### Step 1: SSH Into New VPS

```bash
chmod 400 ~/Downloads/hermes-key.pem
ssh -i ~/Downloads/hermes-key.pem ubuntu@<NEW_VPS_IP>
```

### Step 2: Install Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install git curl wget build-essential -y

# Python 3.11+ (Hermes needs it)
sudo apt install python3.11 python3.11-venv -y
# Or for 3.12 on Ubuntu 24.04:
# sudo apt install python3.12 python3.12-venv -y

# Node.js 20+ (for some Hermes tools)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y
```

### Step 3: Setup SSH Key for GitHub

```bash
ssh-keygen -t ed25519 -C "hermes-vps"
cat ~/.ssh/id_ed25519.pub
# → Add to https://github.com/settings/keys
ssh -T git@github.com  # Verify
```

### Step 4: Clone Backup

VPS baru biasanya **t2.micro (1GB RAM)** — clone bisa lambat. Sabar ~30-60 detik.

```bash
cd ~
git clone git@github.com:<username>/hermes-backup.git .hermes
cd .hermes
```

### Step 5: Restore .env

```bash
cp .env.example .env
# Edit .env and fill in actual API keys:
nano .env
```

### Step 6: Setup Python Venv

```bash
cd ~/.hermes
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
# Install Hermes core (if node-based):
# pip install -r requirements.txt  (if exists)
```

### Step 7: Install Hermes Agent

Two methods:

**A) If `curl | bash` works (fastest):**
```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```
May timeout on slow VPS (1GB RAM, limited bandwidth). Retry or use method B.

**B) Git clone Hermes Agent repo (fallback):**
```bash
# Clone Hermes Agent into a subdirectory
cd ~/.hermes
git clone https://github.com/nousresearch/hermes-agent.git hermes-agent
cd hermes-agent
npm install   # or pip install -e .
```

**C) If both fail due to low RAM:** Add swap first:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
# Make permanent:
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```
Then retry method A or B.

## Common Pitfalls

1. **`curl | bash` timeout on low-RAM VPS** — t2.micro has 1GB RAM. Hermes install script may timeout fetching deps. Use `git clone` + manual install instead, or add swap first.

2. **Skills directory is large (~1600 files, 21MB)** — `git push` and `git clone` on the skills dir takes the longest. Normal. First push may take 30-60s on slow upload.

3. **GitHub 100MB file limit** — If any single file exceeds 100MB, `git push` fails. Use `git lfs` or exclude large files via `.gitignore`. Hermes skills are typically many small files (< 100KB each), so this rarely triggers.

4. **Node.js version mismatch** — Hermes dev builds sometimes need Node 20+. Ubuntu 22.04 ships Node 12 via apt. Must add NodeSource PPA:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt install nodejs -y
   ```

5. **Provider API keys missing** — Without `.env`, Hermes connects to no providers. Always restore `.env` manually after clone (it's gitignored for security).
