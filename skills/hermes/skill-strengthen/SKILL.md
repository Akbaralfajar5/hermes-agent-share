---
name: skill-strengthen
description: "Strengthen existing skills by adding missing pieces: pitfalls from recent sessions, verification steps, linked reference files, cross-links to related skills, and trigger conditions. Makes good skills comprehensive."
tags: [skills, strengthen, improve, enhance, pitfalls, cross-link]
version: 1.0.0
author: Feb
category: hermes
metadata:
  hermes:
    tags: [skills, strengthen, improve, enhance, pitfalls, cross-link]
    platforms: [linux]
---

# Skill Strengthen

Improve existing skills by identifying and filling gaps: missing pitfalls, absent verification steps, no cross-links, thin trigger conditions, and missing reference files.

## When to use

- After a skill audit identifies skills with gaps
- After using a skill and hitting an issue not documented in it
- User says "kuatin skill ini" / "tambahin pitfall" / "lengkapin skill"
- After a session that revealed new patterns relevant to an existing skill
- Periodic skill quality improvement

## Strengthening procedure

### Step 1: Assess the skill

```bash
# Check skill structure
skill_view(name='<skill-name>')

# Check what's missing
ls ~/.hermes/skills/<category>/<skill-name>/
# Does it have references/? scripts/? templates/?
```

### Step 2: Search recent sessions for relevant findings

```bash
# Find sessions that used this skill or hit related issues
session_search(query="<skill-name> error pitfall", limit=5)
session_search(query="<keyword from skill> failed fix", limit=5)
```

Extract from those sessions:
- Pitfalls discovered but not in the skill
- Commands that worked differently than documented
- Edge cases that broke the procedure
- User corrections to the approach

### Step 3: Check for missing pieces

#### Missing pitfalls?
Compare the skill's "Pitfalls" section against:
- Recent session errors
- User corrections ("napa ga lu lgsg tes tolol" → "always test immediately" pitfall)
- Common failure modes in the domain

#### Missing verification steps?
Every procedure should end with "how to verify it worked":
```bash
# Verify
curl -s http://localhost:20128/v1/models | python3 -c "import sys,json; print('OK' if json.load(sys.stdin).get('data') else 'FAIL')"
```

If a skill has a procedure but no verification, add one.

#### Missing trigger conditions?
The "When to use" section should be specific:
- ❌ "When working with 9router" (too vague)
- ✅ "When user says 'inject akun' / 'cek kuota' / 'provider hilang dari dashboard'"

#### Missing cross-links?
Check if other skills reference this one:
```bash
```
If other skills link TO this one but this skill doesn't link back, add reciprocal links.

#### Missing reference files?
- Long code blocks (>30 lines) → extract to `scripts/`
- Detailed API endpoint tables → extract to `references/api-endpoints.md`
- Historical bug stories → extract to `references/historical-bugs.md`
- Configuration examples → extract to `templates/`

### Step 4: Apply strengthening patches

```python
# Add a new pitfall
skill_manage(action='patch', name='<skill-name>',
  old_string='## Pitfalls\n\n1. Existing pitfall...',
  new_string='## Pitfalls\n\n1. Existing pitfall...\n\n2. **NEW pitfall name** — description + fix')

# Add a verification step
skill_manage(action='patch', name='<skill-name>',
  old_string='## Procedure\n\n### Step 3: Do the thing',
  new_string='## Procedure\n\n### Step 3: Do the thing\n\n### Verification\n```bash\ncommand-to-verify\n```')

# Add a cross-link
skill_manage(action='patch', name='<skill-name>',
  old_string='## Related skills\n\n- `existing-skill` — relationship',
  new_string='## Related skills\n\n- `existing-skill` — relationship\n- `new-linked-skill` — relationship')
```

### Step 5: Create missing linked files

```python
# Extract detailed reference material
skill_manage(action='write_file', name='<skill-name>',
  file_path='references/detailed-procedure.md',
  file_content='# Detailed Procedure\n\n...')

# Create a verification script
skill_manage(action='write_file', name='<skill-name>',
  file_path='scripts/verify.py',
  file_content='#!/usr/bin/env python3\n...')
```

## Strengthening checklist

For each skill being strengthened, check:

- [ ] **Trigger conditions specific** — not just "when working with X" but actual trigger phrases
- [ ] **Top 5 pitfalls present** — the most common failures documented
- [ ] **Verification steps present** — every procedure has a "how to verify" step
- [ ] **Cross-links bidirectional** — if skill A links to skill B, skill B links back to A
- [ ] **Reference files for long sections** — code blocks >30 lines extracted
- [ ] **Scripts for repeated commands** — multi-line bash/python commands scripted
- [ ] **User corrections captured** — any user feedback ("tolol", "goblok") turned into pitfalls
- [ ] **Version bumped** — if content changed, bump version number
- [ ] **Tags comprehensive** — includes all keywords someone would search for

## Common strengthening patterns

### Pattern: User correction → pitfall

When a user says something like:
> "napa ga lu lgsg tes tolol" / "tiap inject lgsg tes"

This becomes:
```markdown
### Pitfall: Always test immediately after injecting accounts
**User correction:** "tiap inject lgsg tes" — when injecting accounts into 9router DB,
fire a real stream request immediately after. Don't ask, don't wait, don't batch-test later.
The test proves routing works; `/v1/models` listing alone does NOT prove routing.
```

### Pattern: Session error → pitfall

When a session reveals:
> `max_tokens: 0` passes through and pateway rejects with 400

This becomes:
```markdown
### Pitfall: max_tokens=0 breaks pateway (400)
**Root cause:** OpenAI→OpenAI routes skip the translator pipeline, so `adjustMaxTokens()`
never runs. A request with `max_tokens: 0` passes through to pateway, which rejects it.
**Fix:** Call `adjustMaxTokens()` in `DefaultExecutor.transformRequest`.
```

### Pattern: Discovered endpoint → reference file

When a session discovers API endpoints:
> openapi.qoder.sh/api/v1/jobToken/exchange, api2 vs api3

This becomes:
```bash
skill_manage(action='write_file', name='qoder-token-management',
  file_path='references/qoder-api-endpoints.md',
  file_content='# Qoder API Endpoints\n\n| Purpose | URL | Auth |\n|---|---|---|\n...')
```

## Pitfalls

1. **Don't strengthen skills you haven't used.** If you haven't used the skill in a real session, you don't know what's missing. Only strengthen based on actual experience.
2. **Don't add pitfalls that are already there.** Read the existing Pitfalls section first — many skills already have 20+ pitfalls. Adding a duplicate is worse than not adding it.
3. **Patch, don't rewrite.** Use `skill_manage(action='patch')` to add specific sections. Don't `edit` the whole file just to add one pitfall.
4. **Bump version when strengthening.** If you add content, bump the version in frontmatter: `version: 1.0.0` → `version: 1.1.0`.
5. **Cross-links must be reciprocal.** If you add "see `skill-x`" to skill A, also add "see `skill-a`" to skill B. One-way links create dead ends.

## Related skills

- `skill-audit` — audit identifies which skills need strengthening
- `skill-management` — lifecycle management (create, update, archive)
- `skill-anti-duplicate` — ensure strengthening doesn't create duplicates
- `skill-auto-organize` — structure and categorize
- `skill-auto-create` — auto-generate new skills from patterns
