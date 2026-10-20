# Skill ZIP Update Pattern (SUPERAGENT / OPENCLAW)

When user sends a `.zip` file containing skill updates (e.g. `SUPERAGENT-v3.1-OPENCLAW.zip`):

## SUPERAGENT 7.1+ Installation Pattern


### Step 1: Extract & Inspect
```bash
unzip -o /path/to/file.zip -d /tmp/skill_extract
find /tmp/skill_extract -type f | sort
```

Use `skill_manage(action='create', name=..., content=...)` — do NOT use cp.

### Step 3: Install reference files into the skill
Use `skill_manage(action='write_file', name=..., file_path='references/...')` for each reference `.md`.

### Step 4: Install persona files to Hermes ROOT (NOT skill references)
```
IDENTITY.md → ~/.hermes/IDENTITY.md
SOUL.md     → ~/.hermes/SOUL.md
```
These go to root, NOT to skill dir or references/. User will correct you if you put them elsewhere.

### Step 5: Merge USER.md into memory
```
USER.md content → MERGE into ~/.hermes/memories/USER.md
```

### Step 6: Clean duplicates
After root install, delete duplicates:
```bash
# Remove cache extract
rm -rf /tmp/skill_extract

# Remove identity/soul/user from skill references (they're now in root)
rm -f ~/.hermes/skills/<skill_name>/references/identity.md
rm -f ~/.hermes/skills/<skill_name>/references/soul.md
rm -f ~/.hermes/skills/<skill_name>/references/user.md
```

For SOUL.md MERGE operations (when user sends a SOUL to ADD missing sections, not replace), see `references/soul-merge-pattern.md`.

---

## Old Pattern (SUPERAGENT / OPENCLAW v3.x)

### Workflow

```bash
# 1. Extract
unzip -o /path/to/file.zip -d /tmp/skill_update

# 2. Inspect structure
find /tmp/skill_update -type f | sort

# 3. Identify what's new vs existing
# - references/*.md → check if already in skill's references/
# - scripts/*.py → check if already in skill's scripts/
# - standalone *.md (m7.md, m9.md, SOUL.md, panduan.md) → check hermes-core/scripts/
```

### Comparison Pattern

```bash

# Compare module files (m7, m9, etc.)
diff /tmp/skill_update/skills/m9.md \
     /home/ubuntu/.hermes/skills/autonomous-ai-agents/hermes-core/scripts/m9.md | head -20
```

### File Routing

| File in ZIP | Destination |
|---|---|
| `skills/hermes/references/*.md` | `~/.hermes/skills/trading/hermes-crypto-agent/references/` |
| `skills/hermes/scripts/*.py` | `~/.hermes/skills/trading/hermes-crypto-agent/scripts/` |
| `skills/hermes/DISPATCH.md` | `~/.hermes/skills/trading/hermes-crypto-agent/references/DISPATCH.md` |
| `skills/m7.md`, `skills/m9.md` | `~/.hermes/skills/autonomous-ai-agents/hermes-core/scripts/` |
| `SOUL.md` | `~/.hermes/skills/autonomous-ai-agents/hermes-core/scripts/SOUL_v3.md` |
| `panduan.md` | `~/.hermes/skills/autonomous-ai-agents/hermes-core/scripts/panduan_operator_v3.md` |

### Notes

- Always `diff` before copying — don't blindly overwrite if the existing version has local patches
- DISPATCH.md goes into `references/` not root of skill dir
- SOUL.md and panduan.md are versioned (append `_v3`, `_v31`, etc.) to preserve history
- After update, verify with `ls` on both references/ and scripts/ directories
