# Installing External Community Skills

This document provides a complete walkthrough for installing agent skills from external GitHub repositories (Vercel Labs, npx skills ecosystem, and other third-party sources).

## Quick Reference

| Goal | Command |
|------|---------|
| Add a GitHub repo as a tap | `hermes skills tap add <repo_url>` |
| Search available skills | `hermes skills search <query>` |
| Install from hub ID | `hermes skills install <hub-id>` |
| Force install (skip security block) | `hermes skills install <url> --name <skill-name> --force` |
| List installed skills | `hermes skills list` |
| Move misplaced skill | `mv ~/.hermes/skills/<wrong>/<name> ~/.hermes/skills/<correct>/` |

## Complete Installation Workflow

### Step 1: Explore Available Sources

**Option A — Browse the Skills Hub:**
```bash
hermes skills browse        # Interactive browser
hermes skills search <q>    # Keyword search
```

**Option B — Add an External Tap (Vercel Labs example):**
```bash
hermes skills tap add https://github.com/vercel-labs/skills
```
This enables `hermes skills search` to query that repository's skill index.

**Option C — Direct URL (always works):**
```
```

### Step 2: Search for the Desired Skill

```bash
# Search across all configured sources
hermes skills search evm wallet

# Example output:
# ┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
# ┃ Name        ┃ Description        ┃ Source    ┃ Trust     ┃ Identifier        ┃
# ┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
# │ evm-wallet  │ EVM Wallet &…      │ skills.sh │ community │ dodoex/chainpilot │
# └─────────────┴────────────────────┴───────────┴───────────┴───────────────────┘
```



Navigate to the skill's page on skills.sh or inspect the GitHub repo:

- skills.sh page: `https://skills.sh/<owner>/<repo>/<skill-name>`

Example:
```bash
```

### Step 4: Install the Skill

**Basic install with auto-confirm:**
```bash
printf "y\n" | hermes skills install "$RAW_URL" --name evm-wallet
```

**Expected interactive prompts:**
1. **Category selection:** `Pick a category (reuse an existing bucket, type a new one, or press Enter to install flat)`
   - Default suggestion may be a single letter like `y`
   - **Best practice:** Type an existing category name (e.g., `autonomous-ai-agents`) to avoid clutter
2. **Security scan:** `Running security scan... Verdict: SAFE / CAUTION`
   - If `CAUTION` or `BLOCKED`, see Step 4b
3. **Confirmation:** `Install 'evm-wallet'? Confirm [y/N]:`
   - Auto-confirm with `printf "y\n"` or `yes` command

**Step 4b — Override security scan (if needed):**
Some skills trigger false-positive security warnings (e.g., path traversal patterns from build configs). If blocked:
```bash
printf "y\n" | hermes skills install "$RAW_URL" --name evm-wallet --force
```
- Legitimate skills from reputable sources (vercel-labs, austintgriffith) may have known false positives
- After install, verify no malicious scripts are present in the skill directory

### Step 5: Verify & Organize

**Check installation:**
```bash
hermes skills list | grep evm-wallet
```
Expected output:
```
│ evm-wallet           │ y                    │ url     │ community │ enabled │
```

**If category is wrong (e.g., `y`):**
```bash
# Create target category if needed
mkdir -p ~/.hermes/skills/autonomous-ai-agents/

# Move the skill
mv ~/.hermes/skills/y/evm-wallet ~/.hermes/skills/autonomous-ai-agents/

# Verify
hermes skills list | grep evm-wallet
# Should now show: │ evm-wallet │ autonomous-ai-agents │ ...
```

**Reload the skill in current session:**
- In chat: `/skill evm-wallet`
- Or start new Hermes session
- Changes do NOT affect running session automatically

## Common Pitfalls & Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `hermes skills install` says "unrecognized arguments: --skill" | Using wrong flag format | Use `--name <skill-name>` or omit and accept interactive prompt |
| Skill lands in `~/.hermes/skills/y/` | Accepted default category letter | Move manually to correct category directory |
| Skill shows `disabled` after move | Enablement not updated | Run `hermes skills config` to verify category is enabled, or `/reset` to reload |
| Installation blocked with "BLOCKED" verdict | Security scan caution (medium findings) | Review skill content, then install with `--force` |
| `hermes skills list` doesn't show skill | Installed to wrong Hermes home (different profile) | Check `HERMES_HOME`; use `hermes config path` to see active config |

## Security Considerations

2. **Quarantine placement:** Hermes initially places externally-installed skills under `.hub/quarantine/` or single-letter categories. This is intentional isolation; move to a named category after review.
3. **Never auto-approve sensitive commands:** Even trusted skills may include steps requiring manual approval (private key handling, contract deployments). Let Hermes prompt the user.

## Best Practices

1. **Prefer `--name` flag:** Explicit naming avoids confusion and places skill under a predictable category during interactive prompts.
2. **Use named categories:** `autonomous-ai-agents`, `creative`, `mlops`, etc. — not single-letter defaults.
3. **Document each imported skill:** After installation, add a one-line note to your personal notes (or a session log) about why this skill was chosen and what it provides.
4. **Keep skills updated:** Periodically run `hermes skills check` and `hermes skills update` to receive upstream fixes.
5. **Verify via `find-skills`:** After installing `find-skills` from Vercel Labs, you can use it to discover more skills without manual GitHub browsing.

## Example: Full Walkthrough (ethereum-wingman)

```bash
# 1. Add Vercel Labs tap
hermes skills tap add https://github.com/vercel-labs/skills

# 2. Search
hermes skills search ethereum
# Shows: ethereum-wingman (299 installs)

# From skills.sh page or GitHub:

# 4. Install (security scan shows CAUTION, blocking install)
printf "y\n" | hermes skills install \
  --name ethereum-wingman
# Output: "Decision: BLOCKED — Blocked (community source + caution verdict)"

# 4b. Force install (reviewed content, known false positive from Scaffold-ETH build configs)
printf "y\n" | hermes skills install \
  --name ethereum-wingman --force

# 5. Move from quarantine to proper category
mv ~/.hermes/skills/y/ethereum-wingman ~/.hermes/skills/autonomous-ai-agents/

# 6. Verify
hermes skills list | grep ethereum-wingman
# Expected: │ ethereum-wingman │ autonomous-ai-agents │ url │ community │ enabled │

# 7. Load in session
/skill ethereum-wingman
```

## Troubleshooting External Skill Installation

**Q: `hermes skills tap add` fails with network error**
- Check internet connectivity and GitHub accessibility
- Use direct URL method instead (no tap required)

**Q: Skill installs but doesn't appear in `hermes skills list`**
- Confirm you're using the correct `HERMES_HOME` (run `hermes config path`)
- Some installs go to profile-specific directories; run `hermes profile show` to see active profile

**Q: Security scan flags a legitimate skill**
- Flag patterns are often generic (path traversal, command injection in build scripts)
- Verify the skill source (author reputation, GitHub stars, install count on skills.sh)
- If confident, use `--force` and document the rationale

**Q: Skill is `disabled` after install**
- Run `hermes skills config` to see category enablement matrix
- Enable the category for your current platform (Telegram, CLI, etc.)
- Or reset session: `/reset` (in-chat) or restart Hermes CLI
