---
name: skill-auto-create
description: "Auto-generate new skills from successful session patterns. Analyzes conversation history for repeated workflows, common pitfalls, and user corrections, then proposes skill content. Also covers the 'offer to save' pattern after difficult tasks."
tags: [skills, auto-create, generate, patterns, session-analysis]
version: 1.0.0
author: Feb
category: hermes
metadata:
  hermes:
    tags: [skills, auto-create, generate, patterns, session-analysis]
    platforms: [linux]
---

# Skill Auto-Create


## When to use

- After a complex task succeeds (5+ tool calls, errors overcome)
- User says "simpen skill" / "save skill" / "buat skill dari ini"
- User-corrected approach worked and should be remembered
- After discovering a non-trivial workflow worth preserving
- Periodic review of recent sessions for skill-worthy patterns

## Auto-create procedure

### Step 1: Identify skill-worthy sessions

```bash
# Search recent sessions for complex tasks
session_search(query="error fix solved workaround", limit=10, sort="newest")

# Search for user corrections (usually become pitfalls)
session_search(query="tolol goblok napa ga", limit=5, sort="newest")

# Search for successful multi-step procedures
session_search(query="step 1 step 2 verify OK", limit=5, sort="newest")
```

### Step 2: Check if a skill already exists

```bash
# Before creating, check for existing coverage
skills_list

# If a similar skill exists, STRENGTHEN it instead of creating a new one
skill_view(name='<similar-skill>')
```

### Step 3: Extract skill content from session

From the session transcript, extract:

| Content type | Where in session | Skill section |
|--------------|-----------------|---------------|
| Task goal | First user message | Overview / When to use |
| Trigger phrase | User's words describing the task | When to use (trigger conditions) |
| Procedure steps | Tool calls in order | Procedure (Step 1, 2, ...) |
| Errors hit | Error messages in tool output | Pitfalls |
| User corrections | "tolol", "napa ga", "goblok" | Pitfalls (highest priority) |
| Verification | How success was confirmed | Verification steps |
| Commands that worked | Terminal commands that succeeded | Procedure / Scripts |


Structure the extracted content into the standard skill format:

```markdown
---
name: <descriptive-name>
description: "<one-line from task goal>"
tags: [keyword1, keyword2, ...]
# NO version field until published (Feb rule — unpublished skills carry no version number)
author: Feb
category: <mapped-category>
metadata:
  hermes:
    tags: [keyword1, keyword2, ...]
    platforms: [linux]
---

# <Skill Title — must match frontmatter name>
```
## Overview
<from task goal — what this skill does>

## When to use
- <trigger condition 1>
- <trigger condition 2>
- User says "<exact phrase the user used>"

## Procedure
### Step 1: <action>
```bash
<command that worked>
```

### Step 2: <action>
<from successful tool call sequence>

## Pitfalls
1. **<pitfall name>** — <what went wrong> → <fix>
   - User correction: "<exact user words>" → <what the correction means>

## Verification
```bash
<command to verify success>
```

## Related skills
- `<existing-skill>` — <relationship>
```

### Step 5: Extract linked files

If the session produced:
- Long code blocks → `scripts/<name>.py`
- API endpoint tables → `references/api-endpoints.md`
- Configuration files → `templates/config.yaml`

```python
# Create linked files
skill_manage(action='write_file', name='<skill-name>',
  file_path='scripts/<helper>.py',
  file_content='<extracted code>')

skill_manage(action='write_file', name='<skill-name>',
  file_path='references/<topic>.md',
  file_content='<extracted reference>')
```

### Step 6: Create the skill

```python
skill_manage(action='create', name='<skill-name>',
  category='<category>')
```

### Step 7: Verify

```bash
skill_view(name='<skill-name>')
```

## The "offer to save" pattern

After completing a difficult task, OFFER to save it as a skill:

```
"That took several iterations. Want me to save this as a skill so next time
it's a one-shot? It would cover: <brief summary of what the skill would include>."
```

Offer when ALL of these are true:
- ✅ 5+ tool calls
- ✅ Errors were overcome
- ✅ User corrected the approach at least once
- ✅ The workflow is reusable (not a one-off)

Do NOT offer when:
- ❌ Single tool call
- ❌ Simple mechanical task
- ❌ Task specific to this exact moment (e.g., "restart this one service now")

## Auto-creation from repeated patterns

When the same type of task appears across multiple sessions, auto-create a skill:

1. `session_search(query="<task keyword>", limit=5)` — find 3+ sessions with same task
2. Extract common steps across all sessions
3. Collect all unique pitfalls from each session
4. Merge into a single comprehensive skill
5. Create with `skill_manage(action='create')`

### Example: Farming skill auto-creation

Multiple sessions about farming different providers (pateway, tokenharbor, qoder) share:
- Same proxy rotation pattern
- Same tempmail provider fallback chain
- Same OTP polling strategy
- Same 9router inject shape

→ Auto-create `mass-account-api-key-farm` as the generic playbook, with provider-specific skills linking to it.

## Category auto-assignment

When generating a skill, auto-assign category based on keywords:

```python
CATEGORY_MAP = {
    "farm|farming|harvest|mass-account": "automation",
    "9router|gateway|proxy|sqlite|systemd": "devops",
    "audit|vuln|pentest|exploit|bounty": "bug-bounty",
    "pytorch|training|fine-tune|dataset": "mlops",
    "writing|blog|content|creative": "creative",
    "apple|macos|imessage": "apple",
    "skill|hermes|agent|memory": "hermes",
    "github|git|ci": "github",
}

def assign_category(desc, tags):
    text = (desc + " " + " ".join(tags)).lower()
    for keywords, category in CATEGORY_MAP.items():
        if any(kw in text for kw in keywords.split("|")):
            return category
    return None  # root-level if no match
```

## Pitfalls

1. **Always check `skills_list` before creating.** Creating a duplicate wastes effort and requires later audit+merge. 30 seconds of checking saves 10 minutes of merge work.
2. **Don't auto-create from single sessions.** One session might be a one-off. Look for repeated patterns across 2+ sessions before auto-creating. Exception: if the user explicitly says "simpen skill dari ini", create immediately.
3. **User corrections are the most valuable pitfalls.** When a user says "tolol" or "goblok" or "napa ga lu...", that's a pitfall waiting to be documented. Capture the exact user words — they encode the emotional weight of the lesson.
4. **Generated skills need human review.** Auto-generated content is a draft, not a final product. Review for: accuracy, completeness, correct commands, proper categorization.
5. **Always offer before auto-creating.** Don't silently create skills — the user might not want another skill cluttering their library. Use the "offer to save" pattern.
7. **Version numbers: ONLY if published — otherwise ABSENT.** Per Feb's correction: NO `version:` in frontmatter, NO "v1.0" in the title, for any skill that isn't published yet. The template above and the frontmatter block default to OMITTING version. Only add a version once the skill is actually published/shipped. Don't "bump" versions of unpublished drafts.
8. **Title, frontmatter name, and filename must all sync.** If the skill is `web-engineering`, the H1 title is `# WEB ENGINEERING`, frontmatter `name: web-engineering`, and the delivered file is `web-engineering.md`. Don't use codename suffixes (`-v4`, `-rebuild`, `-fullstack`) in the filename/title for an unpublished skill — that's "amburadul" per Feb.

## Related skills

- `skill-audit` — audit all skills including newly created ones
- `skill-management` — lifecycle management (create, update, pin)
- `skill-anti-duplicate` — ensure new skill isn't a duplicate
- `skill-auto-organize` — categorize and trim new skills
- `skill-strengthen` — improve skills after creation
