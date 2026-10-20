# GitHub Push Protection Bypass

## Problem

When pushing config/skills to GitHub, secret scanning blocks the push even after redacting secrets in the latest commit. **GitHub scans every commit in history**, not just the latest.

### Error Message

```
remote: - GITHUB PUSH PROTECTION        
remote:     - Push cannot contain secrets        
remote:             
remote:       —— GCP API Key Bound to a Service Account ————————————        
remote:        locations:        
remote:          - commit: 19309fecdf9242b7a3c69f246a908087c49fbd72        
remote:            path: config/config.yaml:125        
```

## Detection: How GitHub Finds Secrets

GitHub scans for patterns including:
- GCP API Keys (`AIza...`, `AQ.` prefix)
- AWS Access Keys (`AKIA...`)
- OpenAI API Keys (`sk-...`)
- GitHub Personal Access Tokens (`ghp_...`, `gho_...`, `ghu_...`)
- Google OAuth credentials
- Stripe live/test keys
- Telegram Bot Tokens (`123456:ABC...` format)
- Token-plan provider keys (`tp-...` prefix)
- `shared/nous_auth.json` (Nous auth access tokens)
- Plaintext passwords in `memories/*.md` (`pwd=`, `password=`)
- GCP API Keys (`AIza...`, `AQ.` prefix)

If ANY commit in the push contains one of these, the entire push is rejected.

## Fix Options

### Option A: Fresh Commit History (Recommended)

The simplest fix — wipe git history so the flagged commit no longer exists:

```bash
# 2. Then wipe history and start fresh
cd ~/hermes-backup
rm -rf .git                     # Deletes ALL commits
git init                        # Fresh empty repo
git branch -M main
git add -A
git commit -m "🎯 Hermes Agent backup"  # Only this commit exists now
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git

# Overwrite the remote branch
git push -u origin main --force
```

**Why this works:** GitHub's push protection is *per-commit*. If commit `abc123` has a secret and commit `def456` redacts it, `abc123` still exists in git history and gets flagged. By deleting `.git/`, the flagged commits no longer exist, so the push passes.

### Option B: Allow-List via Unblock URL

GitHub provides an unblock URL in the error message:

```
https://github.com/YOUR_USER/YOUR_REPO/security/secret-scanning/unblock-secret/SOME_ID
```

Use this when:
- The secret was already rotated/revoked
- You're pushing to a private repo and accept the risk
- The detected pattern is a false positive (e.g., sample key in docs)

**Steps:**
1. Click the URL from the error
2. Review the detected secret
3. Confirm unblock
4. Push again

### Option C: Use `git filter-branch` (Nuclear Option)

Only if you want to keep existing commit history:

```bash
# Rewrite history to remove the secret from ALL commits
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/config.yaml" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
```

**Caveats:**
- Rewrites shared history (requires collaborators to re-clone)
- May still be blocked if other secrets exist in history
- Complex for large repos

## Prevention

**Always redact secrets BEFORE the first commit:**

```bash
# Before git init:
sed -i 's/api_key: sk-[a-zA-Z0-9]*/api_key: YOUR_API_KEY_HERE/g' config.yaml
sed -i 's/api_key: ogw_[a-zA-Z0-9]*/api_key: YOUR_API_KEY_HERE/g' config.yaml

# Double-check:
grep -n "api_key:" config.yaml | grep -v "YOUR_\|\"\""
# Should return nothing
```

## Credential Hygiene

After pushing, always clean the remote URL:

```bash
# Remove PAT from remote URL
git remote set-url origin https://github.com/YOUR_USER/YOUR_REPO.git
```

The PAT remains in `.git/config` if you don't clean it — this is a local security risk.
