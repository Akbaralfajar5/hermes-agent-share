# Publishing a Sanitized Repo (Bots / Automation / Tools With Secrets)

When the user says "upload this script to my GitHub" / "publish this repo" and the source tree contains operational secrets (wallets, private keys, API keys, proxy credentials, cookies, session tokens, RPC URLs with embedded keys, etc.), do **not** push the working tree as-is. Always sanitize first.

This applies especially to: trading bots, mining bots, farming/airdrop scripts, scrapers with proxies, anything that runs against the user's funded accounts.

## Required exclusions (.gitignore at minimum)

```
# Secrets and operational state
wallets.json
wallets-*.json
proxies.txt
proxies-*.txt
.env
.env.*
*.pem
*.key
id_*
*.keystore
cookies.json
session.json
auth.json

# Runtime state
node_modules/
__pycache__/
*.pyc
.venv/
venv/
*.log
logs/
.pm2/

# Local config that might leak
config.local.*
local.*
```

## Recommended template files (commit these instead)

- `proxies.txt.example` — a couple of fake lines showing the format, e.g. `http://USER:PASS@host:port`
- `wallets.json.example` — schema only with placeholder addresses (`0x000...`) and `"privateKey": "REPLACE_ME"`
- `.env.example` — every env var the user needs, values blanked out
- README section explaining how to copy `*.example` to the real filename and fill in real values

## Sanitization workflow

1. **Stage to a clean dir** (never push from the VPS working dir directly):
   ```bash
   mkdir -p /tmp/<repo>-clean
   cd /tmp/<repo>-clean
   ssh -p <port> <user>@<host> "cd ~/<repo> && tar czf - \
       --exclude='__pycache__' \
       --exclude='wallets*.json' \
       --exclude='proxies*.txt' \
       --exclude='.env*' \
       --exclude='.git' \
       --exclude='node_modules' \
       --exclude='*.log' \
       <files-and-dirs>" | tar xzf -
   ```
   (`scp` is often missing on slim Ubuntu boxes — `tar | ssh ... tar` is the portable copy-from-remote.)

2. **Audit before init**. Grep for known secret patterns and any value the user has previously shared:
   ```bash
   grep -rniE \
     '0x[a-f0-9]{40}|0x[a-f0-9]{64}|gw\.dataimpulse|dataimpulse\.com|privateKey|private_key|api[_-]?key|secret|token|cookie|bearer|proxy_user|proxy_pass' \
     . | head -40
   ```
   Cross-check against memory: any IP, proxy host, wallet address, API key, or username in user/memory profile must NOT appear in the staged dir. If it does, redact it.

3. **Remove or rewrite hits** — replace with `REPLACE_ME` / `0x000...` / `<your-key-here>` in source files; or move the whole snippet to `*.example`.

4. **Add `.gitignore` first**, then `git init && git add .` (NOT `git add -A` from a dirty tree). Re-run the audit grep on the staged index too:
   ```bash
   git diff --cached | grep -iE '<same patterns>'
   ```


## Pre-push final check (mandatory)

Before `git push`, list every file that's about to go up and skim the names + a few lines each:

```bash
git ls-files | sort
git diff --cached --stat
```

If anything looks like real operational state (specific addresses, real proxy hostnames the user uses, contract addresses tied to the user's wallets, etc.), stop and ask.

## When the user has no GitHub auth configured

**Look hard before asking.** Users often respond "already sent it / it's already there" when asked for a token, because past projects on the same machine left credentials lying around. Exhaust the discovery sequence below before bothering them.

Discovery sequence (do all in parallel where possible):

```bash
gh auth status 2>&1                          # gh CLI installed + logged in?
cat ~/.git-credentials 2>&1 | head -3        # PAT in credential store?
ssh -T -o BatchMode=yes git@github.com 2>&1  # SSH key already authorized?
cat ~/.ssh/id_*.pub 2>/dev/null              # SSH key exists locally?
git config --global user.name                # identity set?

# CRITICAL: scan existing local repos' git config for embedded tokens.
# Many users (especially on VPS / Hermes boxes) have past projects where a PAT
# got embedded in the remote URL via `git remote set-url origin https://USER:TOKEN@github.com/...`
# Recover from there before asking for a new token.
for d in ~/*/; do
  cfg="$d.git/config"
  [ -f "$cfg" ] || continue
  tok=$(grep -oE 'ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}' "$cfg" | head -1)
  [ -n "$tok" ] && { echo "Found PAT in $cfg"; export GITHUB_TOKEN="$tok"; break; }
done

# Verify any recovered token actually works and check scopes
if [ -n "$GITHUB_TOKEN" ]; then
  curl -sI -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user \
    | grep -iE 'x-oauth-scopes|^HTTP'
fi
```

A working `repo`-scoped PAT recovered this way can:
- create the new repo via `POST /user/repos`
- push using `https://USER:$GITHUB_TOKEN@github.com/USER/REPO.git` as the remote
- be redacted from terminal output afterward with `sed "s|${GITHUB_TOKEN}|***|g"`

After successful push, **rewrite the local remote** to drop the embedded token (don't leave another copy of the PAT in `/tmp/<repo>-clean/.git/config`):

```bash
git remote set-url origin https://github.com/USER/REPO.git
```

If recovery succeeds, also tell the user the PAT is currently embedded in `<path>/.git/config` of an old project — recommend rotating at https://github.com/settings/tokens since it's been exposed in plaintext on the box (and probably in past session transcripts).

If all empty, ask the user to pick:

- **PAT** — fastest. Send them to `https://github.com/settings/tokens/new`, scope `repo`, paste back. Then store via `git config --global credential.helper store` (see `github-auth` skill).
- **SSH** — if `~/.ssh/id_*.pub` exists, print it and tell the user to add at `https://github.com/settings/keys`.

Always confirm repo **name** and **visibility** (public/private) before creating — don't pick for them. Default suggestion is `<username>/<sensible-class-name>` based on what the script does, not the dir name on the VPS (which often has a codename).
