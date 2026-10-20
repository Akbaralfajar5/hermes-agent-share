# Skill Overlap Evaluation

When a user shares a skill library repo and asks "should I install these?", evaluate each skill against the existing library before recommending installation.

## Evaluation Workflow

### Step 1: Inventory the Repo Skills
```bash
curl -s https://raw.githubusercontent.com/<owner>/<repo>/main/README.md
```
Extract the full skill list with descriptions from the README.

### Step 2: Run `skills_list` to Get Existing Skills
Compare each repo skill against installed skills by matching:
- **Direct name match** (e.g., `test-driven-development` exists in both)
- **Functional overlap** (e.g., `security-and-hardening` ≈ `security-audit-review` + `web-application-testing`)
- **Domain overlap** (e.g., `frontend-ui-engineering` ≈ `frontend-interface-builder` + `ui-ux-pro-max`)

### Step 3: Check Format Compatibility
Different agent ecosystems use different skill formats:

| Ecosystem | Format | Compatible with Hermes? |
|-----------|--------|------------------------|
| Claude Code | `.claude/commands/`, plugin format | ⚠️ Needs adaptation |
| Cursor | `.cursor/rules/` | ⚠️ Needs adaptation |
| Gemini CLI | `GEMINI.md`, native skills | ⚠️ Needs adaptation |
| Generic | Plain markdown | ✅ Works as-is |

**Key check:** Does the skill assume a specific agent's slash commands, hooks, or runtime? If yes, it won't work natively in Hermes.

### Step 4: Assess Domain Relevance
Rate each skill on relevance to the user's actual work:

- **High relevance:** Directly matches user's stack and active projects
- **Medium relevance:** Useful but not currently needed
- **Low relevance:** Theoretical interest, user doesn't work in this domain

### Step 5: Check Skill Quality
```bash
```
Quality signals:
- Has structured process steps (not just prose)
- Includes verification gates / evidence requirements
- Has anti-rationalization tables or pitfalls section
- Code examples match user's stack (not just TypeScript/React)

## Decision Matrix

For each skill in the repo:

| Condition | Action |
|-----------|--------|
| Already exists (direct or functional match) | Skip |
| Format incompatible + no adaptation path | Skip |
| High relevance + no overlap + good quality | Recommend install |
| Medium relevance + no overlap | Mention, let user decide |
| Low relevance | Skip (mention only if user asks) |

## Output Format

Present as a structured comparison:

```
**Repo: <name>** (X stars, Y forks)
Z skills total. Summary of what it covers.

**Already covered:**
- skill-A → exists as our-skill-X ✅
- skill-B → covered by our-skill-Y + our-skill-Z ✅

**Potentially useful (no overlap):**
- skill-C — what it does, why it might help
- skill-D — what it does, why it might help

**Not relevant:**
- skill-E — reason (wrong stack, too generic, etc.)

**Recommendation:** [Install X / Skip / Cherry-pick specific skills]
```

## Common Patterns

### Pattern: "General SWE lifecycle" repos
Repos like `addyosmani/agent-skills` (23 skills covering spec→plan→build→test→review→ship) are designed as complete workflows for coding agents. They typically overlap heavily with Hermes's existing software-development category. Usually NOT worth installing wholesale — cherry-pick only genuinely novel concepts.

### Pattern: "Domain-specific" repos
Repos focused on a single domain (trading, security, design) may have deeper coverage than general skills. These are more likely worth installing if the domain is active for the user.

### Pattern: "Framework-specific" repos
Repos built for a specific agent (Claude Code plugins, Cursor rules) need format adaptation. Evaluate whether the knowledge is worth extracting and reformating vs just reading the source when needed.
