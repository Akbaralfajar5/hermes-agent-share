# npm Global Package "Command Not Found" — Diagnosis & Fix

## Problem

After `npm install -g <package>`, running the command returns:
```
-bash: /home/ubuntu/.nvm/versions/node/v22.22.2/bin/<pkg>: No such file or directory
```
…or simply `command not found`, even though the install succeeded.

## Root Causes (in order of likelihood)

### 1. Byobu/tmux Session Caching (most common on Ubuntu VPS)

Ubuntu VPS instances often have **byobu** pre-installed (`/etc/profile.d/Z97-byobu.sh`). Byobu auto-attaches to old sessions on SSH login, meaning:
- PATH changes in `.bashrc`/`.profile` never apply
- `hash -r` doesn't help because you're in the SAME shell process
- Even `exec bash` doesn't fully reset if byobu intercepts

**Fix:**
```bash
# Disable byobu permanently
byobu-disable
mkdir -p ~/.byobu && touch ~/.byobu/disable

# Kill ALL existing sessions
byobu kill-server 2>/dev/null
pkill -u $USER tmux 2>/dev/null

# Close terminal completely, SSH fresh
```

### 2. Bash Hash Table

Bash caches command paths. If a binary was previously found at path A, bash remembers it even after the binary moves to path B.

**Symptom:** `which <cmd>` returns correct path, but running `<cmd>` gives "No such file or directory" pointing to an OLD path.

**Fix:**
```bash
hash -d <command>   # Remove specific entry
hash -r             # Clear entire hash table
```

**Permanent fix:** Add to top of `~/.bashrc`:
```bash
hash -r 2>/dev/null
```

### 3. nvm PATH Not Loaded

nvm requires `source ~/.nvm/nvm.sh` in bashrc. Non-interactive SSH commands (`ssh host 'command'`) don't source bashrc by default.

**Symptom:** Works with `bash -l -c "command"` but not with plain `command`.

**Fix:** Don't use nvm for production VPS. Use system-wide Node instead:
```bash
rm -rf ~/.nvm
sed -i "/NVM_DIR\|nvm.sh\|bash_completion/d" ~/.bashrc
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

### 4. npm Prefix Mismatch

npm installs globals to different locations depending on how Node was installed:
- System Node (apt): `/usr/lib/node_modules/` → binary in `/usr/bin/`
- nvm Node: `~/.nvm/versions/node/vX.Y.Z/lib/node_modules/` → binary in same `bin/`
- Custom prefix: wherever `npm config get prefix` points

**Fix:** For system Node with user-owned globals:
```bash
npm config set prefix ~/.local
npm install -g <package>
# Binary lands in ~/.local/bin/ (already in Ubuntu's default PATH via .profile)
```

For guaranteed system-wide availability:
```bash
sudo npm install -g <package>
# Binary lands in /usr/bin/ — always in PATH
```

### 5. Broken .bashrc Syntax

If `.bashrc` has a syntax error (orphaned `fi`, missing `then`, etc.), it silently fails to load. All PATH modifications after the error line are ignored.

**Diagnosis:**
```bash
bash -n ~/.bashrc && echo "OK" || echo "BROKEN"
```

**Common cause:** Using `sed -i` to remove lines from bashrc can leave unbalanced if/fi blocks. Always verify syntax after sed edits.

## Nuclear Fix (when debugging is taking too long)

When PATH issues become intractable (user frustrated, multiple fix attempts failed):

```bash
# 1. Remove nvm entirely
rm -rf ~/.nvm
sed -i "/NVM_DIR\|nvm.sh\|nvm\|versions\/node/d" ~/.bashrc

# 2. Install Node system-wide
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# 3. Install package with sudo (goes to /usr/bin/)
sudo npm install -g <package>

# 4. Verify
bash -n ~/.bashrc    # syntax check
/usr/bin/<package> --version  # direct path test

# 5. Disable byobu
byobu-disable 2>/dev/null
mkdir -p ~/.byobu && touch ~/.byobu/disable

# 6. Disable byobu + kill sessions
byobu-disable 2>/dev/null
mkdir -p ~/.byobu && touch ~/.byobu/disable
byobu kill-server 2>/dev/null
pkill -u $USER tmux 2>/dev/null

# 7. User must fully disconnect and SSH fresh
# If STILL broken after fresh SSH → reboot is the final guarantee:
sudo reboot
# Wait 30s, then SSH again. All shell sessions, hash tables,
# and byobu state are wiped clean on reboot.
```

**Why `sudo npm install -g` is the nuclear option:** It puts the binary in `/usr/bin/` which is ALWAYS in PATH regardless of bashrc, nvm, byobu, hash table, or any other shell-level issue. No symlinks, no path resolution needed.

## Prevention (for fresh VPS setup)

1. **Don't install nvm** unless version switching is actually needed
2. **Use system Node** (apt) + `sudo npm install -g` for CLI tools
3. **Disable byobu** on first login if not needed: `byobu-disable`
4. **Always verify bashrc syntax** after any sed/grep manipulation
5. **Set `hash -r`** at top of bashrc as insurance
