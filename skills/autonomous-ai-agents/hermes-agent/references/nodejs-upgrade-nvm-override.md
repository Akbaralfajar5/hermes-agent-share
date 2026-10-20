# Node.js Upgrade When nvm Overrides System Node

## Problem

Hermes Control Interface (and other Vite-based tools) require Node.js 20.19+ or 22.12+. When upgrading Node.js on a system with nvm installed, the system Node may upgrade successfully but `node --version` still shows the old version because nvm's PATH takes precedence.

## Symptoms

```bash
# After apt install nodejs
node --version
# v18.20.8  ← still old!

which node
# /home/user/.nvm/versions/node/v18.20.8/bin/node  ← nvm override

/usr/bin/node --version
# v20.20.2  ← system Node is actually upgraded
```

## Solution

### 1. Install Node.js 20+ via system package manager

```bash
# Add NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

# Install Node.js
sudo apt-get install -y nodejs
```

### 2. Update nvm default to Node 20

```bash
source ~/.nvm/nvm.sh
nvm install 20
nvm use 20
nvm alias default 20
```

### 3. Verify

```bash
node --version
# v20.20.2 ✓

npm --version
# 10.8.2 ✓
```

## Fixing npm Optional Dependency Bugs

If `npm run dev` fails with:

```
Error: Cannot find native binding. npm has a bug related to optional dependencies
(https://github.com/npm/cli/issues/4828). Please try `npm i` again after removing
both package-lock.json and node_modules directory.
```

**Fix:**

```bash
cd ~/hermes-control-interface
rm -rf node_modules package-lock.json
source ~/.nvm/nvm.sh && nvm use 20
npm install
```

This forces npm to re-resolve optional dependencies with the correct Node.js version.

## Running Hermes Control Interface with Correct Node

Background processes spawned via `terminal(background=true)` or `npm run dev` may still use the old Node if nvm isn't sourced. Always prefix with nvm activation:

```bash
# Wrong (uses old Node from parent shell)
cd ~/hermes-control-interface && npm run dev

# Right (sources nvm first)
cd ~/hermes-control-interface && source ~/.nvm/nvm.sh && nvm use 20 && npm run dev
```

## Binding to 0.0.0.0 for Remote Access

By default, Vite dev server binds to `127.0.0.1` (localhost only). To allow remote access:

**Edit `vite.config.js`:**

```javascript
export default defineConfig({
  server: {
    host: '0.0.0.0',  // ← Add this line
    port: 5173,
    proxy: { ... }
  },
});
```

**Verify:**

```bash
netstat -tlnp | grep 5173
# tcp  0  0  0.0.0.0:5173  0.0.0.0:*  LISTEN  <pid>/node  ✓
```

**Security:** Port 5173 must be opened in cloud provider security group (Tencent Cloud, AWS, etc.) or local firewall (ufw) for external access.

## Key Takeaways

- **nvm overrides system Node** — always check `which node` after system upgrades
- **npm optional dependencies** can break when Node version changes mid-install — nuke `node_modules` and reinstall
- **Background processes need explicit nvm sourcing** — they don't inherit the parent shell's nvm state
- **Vite binds to localhost by default** — add `host: '0.0.0.0'` for remote access
