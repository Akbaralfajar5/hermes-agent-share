# Direct Push from ~/.hermes — Secrets Checklist

## When to Use This

When `~/.hermes` is already a git repo with an origin set (e.g., `github.com/username/hermes-agent-config`), and you need to push the latest config/skills/memory changes without creating a separate backup directory.

## Pre-Push Checklist

Run these checks BEFORE `git add` — once a secret is in the index, it's in git history and requires a force-push to remove.

### 1. Check `.gitignore` Is Complete

```bash
cat ~/.hermes/.gitignore
```

Must include:
```
*.bak.*
*.bak_*
cron/output/
shared/nous_auth.json
auth.json
.env
*.db
sessions/
cache/
```

### 2. Scan for Hardcoded API Keys in Config

```bash
grep -n "api_key:" ~/.hermes/config.yaml | grep -v "''" | grep -v '${' | grep -v '«redacted'
```

Any match must be replaced with an env var reference:
```
api_key: ${SOME_ENV_VAR}
```

### 3. Scan for Plaintext Passwords in Memories

```bash
grep -in "pwd=\|password=\|pass=" ~/.hermes/memories/MEMORY.md ~/.hermes/memories/USER.md
```

Redact with `<redacted>`.

### 4. Scan for Token-Plan Keys

```bash
grep -rn "tp-[a-z0-9]\{40,\}" ~/.hermes/config.yaml ~/.hermes/memories/ --include="*.md" --include="*.yaml" --include="*.yml"
```

These are LLM provider keys — replace with `${ENV_VAR}`.

### 5. Check `shared/nous_auth.json`

```bash
ls -la ~/.hermes/shared/nous_auth.json 2>/dev/null && echo "⚠️  EXISTS — add to .gitignore"
```

If it exists, ensure `.gitignore` has `shared/nous_auth.json` AND run `git rm --cached` if it was previously tracked.

### 6. Check Staged Files for Secrets (MOST IMPORTANT GATE)

This is the catch-all that saves you when `.gitignore` misses a leak. Run it on the
STAGED diff after `git add -A`, matching ONLY real secret shapes (not env-var refs or
already-redacted `...` values, which produce noise):

```bash
cd ~/.hermes && git add -A
git diff --cached | grep -E "^\+" | grep -Eo \
  "ghp_[A-Za-z0-9]{30,}|sk-[a-z0-9]{40,}|AIza[0-9A-Za-z_-]{30,}|AKIA[0-9A-Z]{16}|tp-[a-z0-9]{40,}" | sort -u
# ALSO scan for YOUR known live credentials verbatim (proxy user/pass, etc.):
git diff --cached | grep -E "^\+" | grep -Eo "<your-proxy-user>|<your-proxy-pass>" | sort -u
```

Empty output = safe to commit. Any hit = redact first (see below), re-`git add -A`, re-scan.

**PITFALL — secrets hide in tracked skill files, not just logs/sessions.**
`.gitignore` covers `logs/`, `sessions/`, `.env`, `*.db` — but credentials the user
pasted into chat often get quoted inside a **skill reference** you wrote during the
session (e.g. `skills/automation/.../references/*-case-study.md`). Those files ARE
tracked, so gitignore does nothing for them. The staged-diff grep is the only thing
that catches this class. Real case: DataImpulse proxy user+password leaked via a
`h51-case-study.md` reference; caught only by step 6, redacted to
`<DATAIMPULSE_USER>` / `<DATAIMPULSE_PASS>` before push.

To find WHICH staged file holds the secret:
```bash
git diff --cached --name-only | while read f; do \
  [ -f "$f" ] && grep -lE "<secret-pattern>" "$f" 2>/dev/null; done
```

Note: redacting live secrets in skill references is cheap and safe — the real value
of a case-study reference is the technique/flow, never the raw credential.

### 7. Verify Remote URL Has No Embedded PAT

```bash
git remote -v
```

If it shows `https://USER:PAT@github.com/...`, remove the PAT:
```bash
git remote set-url origin https://github.com/username/repo.git
```

## Redaction Methods

| Location | Method | Example |
|----------|--------|---------|
| `config.yaml` | `sed -i` | `sed -i 's|api_key: tp-.*|api_key: ${MIMO_VISION_API_KEY}|' config.yaml` |
| `memories/*.md` | `patch` tool | `patch(path="...", old_string="pwd=actual", new_string="pwd=<redacted>")` |
| `.gitignore` | `patch` tool | Add `shared/nous_auth.json` entry |
| `shared/nous_auth.json` | `git rm --cached` | `git rm --cached shared/nous_auth.json` |

## Commit & Push

```bash
cd ~/.hermes
git add -A
git commit -m "sync: <what changed> — <date>"
git push
```

## Recovery: If Secret Slips Through

If a push fails due to GitHub secret scanning:

1. Redact the secret in the file
2. `git rm --cached` the file (if it shouldn't be tracked at all)
3. Update `.gitignore`
4. Force push: `git push --force`

**Do NOT use `git filter-branch`** — it's overkill and error-prone. The fresh-commit approach (nuke `.git`, re-init) is cleaner for private repos.