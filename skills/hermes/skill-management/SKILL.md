---
name: skill-management
description: "Manage the full skill lifecycle: create, update, archive, restore, delete. Covers when to create vs update, how to patch vs full-rewrite, archive/restore from .archive/, and the auto-load pin pattern for always-on skills."
tags: [skills, lifecycle, management, create, update, archive, pin]
version: 1.0.0
author: Feb
category: hermes
metadata:
  hermes:
    tags: [skills, lifecycle, management, create, update, archive, pin]
    platforms: [linux]
---

# Skill Management

Full lifecycle management of Hermes skills in `~/.hermes/skills/`.

## When to use

- Creating a new skill from a successful task
- Updating an existing skill with new findings
- Archiving a stale or merged skill
- Restoring a previously archived skill
- Pinning a skill to auto-load in every session

## Lifecycle stages

```
CREATE → USE → UPDATE (loop) → ARCHIVE → (optional RESTORE) → final DELETE
```

## 1. CREATE — when to create a new skill

Create a skill when ALL of these are true:
- Complex task succeeded (5+ tool calls)
- Errors were overcome (pitfalls discovered)
- User-corrected approach worked
- Non-trivial workflow discovered
- User asks to "remember this" / "simpen skill"

**Do NOT create when:**
- Single tool call (just do it)
- Simple one-off task
- Mechanical multi-step with no reasoning
- An existing skill already covers it (check with `skills_list` first)

### Create procedure

1. `skills_list` — check if a similar skill exists
2. If yes → `skill_view` it, then `skill_manage(action='patch')` to add new findings


```markdown
---
name: <skill-name>
description: "<one-line description for search/matching>"
tags: [tag1, tag2, ...]
version: 1.0.0
author: Feb
category: <category>
metadata:
  hermes:
    tags: [tag1, tag2, ...]
    platforms: [linux]
---

# Skill Title

## Overview
Brief summary of what this skill does and when to use it.

## When to use
- Trigger conditions

## Procedure
### Step 1: ...
### Step 2: ...

## Pitfalls
1. **Pitfall name** — description + fix

## Related skills
- `other-skill` — relationship description
```

### Good skill markers
- ✅ Trigger conditions ("When to use" section)
- ✅ Numbered steps with exact commands
- ✅ Pitfalls section with real failures encountered
- ✅ Verification steps ("how to confirm it worked")
- ✅ Related skills cross-linked

## 2. UPDATE — when and how to update

Update a skill when:
- Instructions are stale/wrong (API changed, endpoint moved)
- OS-specific failures found during use
- Missing steps or pitfalls discovered
- User corrected an approach that the skill got wrong

### Patch vs Edit

| Action | When to use |
|--------|-------------|
| `patch` | Small fix — add a pitfall, update a command, fix a typo. Preserves rest of file. |

**Always prefer `patch` over `edit`.** Patches are surgical and safe. Edits risk losing content.

### Update immediately after use

If you used a skill and hit an issue NOT covered by it, patch it immediately:
```
skill_manage(action='patch', name='<skill>', old_string='<existing text>', new_string='<updated text>')
```

Don't wait — the context is fresh and the pitfall is clear.

## 3. ARCHIVE — moving skills to .archive/

Archive (don't delete!) when:
- Skill is a confirmed duplicate of another (merged)
- Target service is permanently shut down
- Skill hasn't been used in 6+ months
- User explicitly asks to remove

### Archive procedure

```bash
cd ~/.hermes/skills
mv <skill-name> .archive/<skill-name>
```

Or for categorized skills:
```bash
mv category/skill-name .archive/skill-name
```

**Before archiving:**
1. Check for unique linked files (references/scripts/templates)
2. Copy unique files to the canonical/umbrella skill
3. Add a "merged into `<canonical>`" note

Archived skills:
- Do NOT appear in `skills_list` (excluded from active set)
- Are preserved on disk in `~/.hermes/skills/.archive/`
- Can be restored at any time
- Serve as pattern references

## 4. RESTORE — bringing back archived skills

```bash
cd ~/.hermes/skills
mv .archive/<skill-name> <original-location>
```

Verify: `skill_view(name='<skill-name>')`

## 5. DELETE — permanent removal (rare)

Only delete when:
- Skill contains sensitive data (secrets leaked)
- User explicitly demands deletion
- Backup exists elsewhere

```bash
rm -rf ~/.hermes/skills/<skill-name>
```

For archived skills:
```bash
rm -rf ~/.hermes/skills/.archive/<skill-name>
```

**Always prefer archive over delete.**

## 6. PIN — auto-load in every session

To make a skill auto-load in ALL sessions regardless of model or conversation:

1. Create or ensure the skill exists
2. Add to the auto-load configuration:

```bash
# Check current pinned skills
cat ~/.hermes/config.yaml | grep -A 20 "auto_load_skills"
```

3. Pin the skill by adding its name to the `auto_load_skills` list in config.yaml:

```yaml
# In ~/.hermes/config.yaml
skills:
  auto_load_skills:
    - skill-audit
    - skill-management
    - skill-anti-duplicate
    - skill-auto-organize
    - skill-strengthen
    - skill-auto-create
```

4. Verify by starting a new session and checking:
```bash
# In a new session, the pinned skills should appear in context
skill_view(name='skill-audit')
```

### When to pin
- Meta-skills that should always be available (skill management, audit)
- Core operational skills used every session (9router-ops, gateway management)
- Skills the user explicitly wants always-on

### When NOT to pin
- Domain-specific skills (only relevant for specific tasks)
- Large skills that consume context budget unnecessarily
- Skills that are easily found via `skills_list` when needed

## Pitfalls

1. **Never edit workspace files directly.** Always use `skill_manage` actions — they handle file paths, frontmatter parsing, and directory structure correctly.
2. **Always check `skills_list` before creating.** Creating a duplicate wastes effort and requires later audit+merge.
3. **Patch immediately after discovering a pitfall.** If you wait, you'll forget the exact error and fix. The best time to patch is right after the issue occurred.
4. **Archive, don't delete.** Even seemingly useless skills may contain patterns or references needed months later. Disk space is cheap; re-discovery is expensive.
5. **Pinned skills consume context budget.** Don't pin 20 skills — each one adds to the system prompt. Pin only the 3-6 meta-skills that are genuinely needed every session.
6. **Category matters for organization.** Uncategorized skills (root-level) clutter the namespace. Always assign a category when creating.

## Related skills

- `skill-audit` — audit all skills for duplicates and issues
- `skill-anti-duplicate` — automated duplicate detection
- `skill-auto-organize` — auto-categorize and trim
- `skill-strengthen` — improve existing skills
- `skill-auto-create` — auto-generate from session patterns
