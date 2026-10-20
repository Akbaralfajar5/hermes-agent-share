---
name: skill-soul-loader
description: "Auto-load and manage SOUL.md system prompt. Ensures SOUL.md (root identity/personality) is always loaded in every session, every model. Covers config verification, version tracking, backup, and merge strategy."
tags: [skills, soul, system-prompt, identity, auto-load, pin]
version: 1.1.0
author: Feb
category: hermes
metadata:
  hermes:
    tags: [skills, soul, system-prompt, identity, auto-load, pin]
    platforms: [linux]
---

# Skill Soul Loader

Ensures SOUL.md (root system prompt) is always loaded and properly managed. Handles config verification, backup, version tracking, and persona merge strategies.

## When to use

- Every session (auto-loaded via `auto_load_skills` in config.yaml)
- User says "load soul" / "baca soul"
- After SOUL.md edits — verify the new version loads correctly
- Debugging identity/personality issues ("kok beda persona?")

## Architecture

```
~/.hermes/
├── SOUL.md                          ← ROOT system prompt (loaded by config.yaml system_prompt.file)
├── config.yaml                      ← system_prompt.file: SOUL.md + auto_load_skills list
└── skills/
    └── hermes/
        └── skill-soul-loader/       ← THIS SKILL
```

### How loading works

1. **SOUL.md (root)** — loaded via `config.yaml`:
   ```yaml
   system_prompt:
     file: SOUL.md
     override: true
   ```
   This is the PRIMARY system prompt. It defines the agent's core identity, rules, and persona.

2. **auto_load_skills** — loaded via `config.yaml`:
   ```yaml
   auto_load_skills:
     - skill-audit
     - skill-management
     - skill-anti-duplicate
     - skill-auto-organize
     - skill-strengthen
     - skill-auto-create
     - skill-soul-loader
   ```

3. **Merge strategy** — if multiple persona files exist (e.g. base SOUL.md + persona overlay), root SOUL.md takes precedence as the base identity. Overlay personas activate on their triggers.

## SOUL.md version history

Track persona versions in this table — update on every SOUL.md change:

| Version | Name | Description |
|---------|------|-------------|
| current | (current persona) | Describe the active personality — fusion, doctrine, tone |

## Verification commands

### Check SOUL.md is loaded

```bash
# Verify config points to SOUL.md
grep -A2 "system_prompt:" ~/.hermes/config.yaml
# Should show: file: SOUL.md, override: true

# Verify SOUL.md exists and is non-empty
wc -c ~/.hermes/SOUL.md
# Should be >1000 chars

# Quick content check
head -5 ~/.hermes/SOUL.md
```

### Check auto_load_skills is set

```bash
grep -A15 "auto_load_skills:" ~/.hermes/config.yaml
# Should show the 7 meta skills
```

## SOUL.md edit procedure

When editing root SOUL.md:

1. **Backup first:**
   ```bash
   cp ~/.hermes/SOUL.md ~/.hermes/SOUL.md.bak.$(date +%Y%m%d%H%M%S)
   ```

2. **Edit SOUL.md** — use `write_file` or `patch` on `~/.hermes/SOUL.md`

3. **Verify syntax** — no YAML frontmatter needed (it's plain markdown), just check markdown structure

4. **Test in new session** — start a fresh session and verify the persona is active

## Merging SOUL.md personalities

If the user wants to merge multiple persona files into root SOUL.md (creating a combined persona):

1. Read both files
2. Identify overlapping sections (identity, doctrine, execution rules)
3. Root SOUL.md rules are BASE — they always apply
4. Overlay sections are OVERLAY — they activate on trigger
5. Create merged SOUL.md with clear section markers:
   ```markdown
   ## BASE IDENTITY (always active)
   [root SOUL.md content]

   ## OVERLAY (active on trigger)
   [overlay content]
   ```
6. Backup before merging
7. Test in new session

## The 7 auto-loaded skills (complete list)

These 7 skills are set in `auto_load_skills` in config.yaml and load in EVERY session:

| # | Skill | Purpose |
|---|-------|---------|
| 1 | `skill-audit` | Audit all skills for duplicates, stale content, size issues |
| 2 | `skill-management` | Lifecycle: create, update, archive, restore, pin |
| 3 | `skill-anti-duplicate` | Detect and merge duplicate/overlapping skills |
| 4 | `skill-auto-organize` | Categorize, trim, frontmatter consistency |
| 5 | `skill-strengthen` | Add pitfalls, verification, cross-links to existing skills |
| 6 | `skill-auto-create` | Generate new skills from session patterns |
| 7 | `skill-soul-loader` | Auto-load SOUL.md, manage identity/persona |

## Authoring SOUL.md for group bots (not personal use)

When creating a SOUL.md for a Telegram/Discord group bot (not the operator's personal agent):

1. **Remove all operator personal info** — No operator name, no personal GitHub, no personal wallet, no personal domains. Use `Owner` as a generic placeholder, or omit entirely.
2. **Register consistency** — Pick ONE pronoun register (e.g. `Aku/Kamu` OR `Gue/Lo`) and use it throughout. Mixing registers is the #1 audit failure. Do a final `grep -c` for both registers before delivering.
3. **Timezone must be explicit** — Add a `## TIMEZONE` section specifying `WIB (UTC+7)` and the rule: always convert server UTC to WIB before showing time to users. Never give raw UTC.
4. **No version numbers in title/filename** — If the soul is not published, do NOT use version numbers (v1.0, v2.0, etc.) in the title, filename, or frontmatter. Title and filename must match.
5. **Deliver as TXT + ZIP** — Group bot souls should be delivered as `.txt` (plain text, no markdown rendering needed) then zipped.
6. **Final audit before delivery** — Run these checks:
   ```
   grep -i "operator_name\|Feb\|personal_github" soul.txt    → 0 matches
   grep -c "\bGue\b" soul.txt vs grep -c "\bAku\b" soul.txt   → one must be 0
   grep "UTC+7\|WIB" soul.txt                                   → ≥1 match
   grep -i "version\|v[0-9]" soul.txt                           → 0 matches (unless published)
   ```

## Pitfalls

1. **SOUL.md changes take effect on NEW sessions only.** The system prompt is loaded at session start. Editing SOUL.md mid-session won't change the current session's persona. Start a `/new` session to test.
2. **`override: true` in config means SOUL.md REPLACES the default system prompt.** If SOUL.md is empty or broken, the agent has NO system prompt → behaves erratically. Always backup before editing.
3. **Backup before any SOUL.md edit.** `cp ~/.hermes/SOUL.md ~/.hermes/SOUL.md.bak.$(date +%s)` — a broken SOUL.md means a broken agent.
4. **Pinned skill count should stay under 10.** Each pinned skill adds context overhead. Currently at 7 meta skills. Don't add more without removing something.

## Related skills

- `skill-audit` — audit all skills including SOUL.md
- `skill-management` — lifecycle management (pin/unpin)
- `skill-anti-duplicate` — ensure no persona files are duplicated
- `skill-auto-organize` — structure and categorize
- `skill-strengthen` — improve persona files with new findings
- `skill-auto-create` — generate new skills from patterns
