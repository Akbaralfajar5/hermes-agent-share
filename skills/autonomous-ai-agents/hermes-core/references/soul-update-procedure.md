# SOUL.md Update Procedure

## Permission (resolved)
SOUL.md is now owned by `ubuntu:ubuntu` — direct `write_file` and `patch` tools work without escalation.

---

## Merge Workflow: Add Missing Sections from External Persona Files

When operator sends a persona file (SOUL.md variant, ZIP, or markdown) and asks to merge what's missing:

### Step 1: Extract
```bash
cd ~/.hermes/cache/documents && unzip -o <file>.zip -d extract/ && cat extract/*.md
```

### Step 2: Compare
```bash
# Current SOUL.md section headers
grep '^## ' ~/.hermes/SOUL.md

# External persona section headers  
grep '^## ' extract/*.md
```

### Step 3: Identify gaps
- Sections in external file NOT in current SOUL.md → candidates for addition
- Skip sections that are persona-specific (other operator's name, wallet addresses, social accounts, email addresses)

### Step 4: Merge via `patch` tool
Use `patch(mode='replace', path='~/.hermes/SOUL.md', old_string='...', new_string='...')` 
to insert new sections before the `## FINAL DIRECTIVE` marker.

### Step 5: Bump version
Increment version number at end of SOUL.md. Tag the merge source:
```
```

### Step 6: Clean cache
```bash
rm -rf ~/.hermes/cache/documents/extract ~/.hermes/cache/documents/*.zip
```

---

## SOUL.md Structure (current, v7.4+)
The file has grown organically through multiple merges. Key sections:

| Section | Source | Purpose |
|---------|--------|---------|
| IDENTITY | SUPERAGENT | Core persona, name, tagline |
| Technical Directives | Waguri | Compliance framework, refusal override |
| MISSION / CORE TRAITS / DOMAINS | SUPERAGENT | Bug bounty + exploit scope |
| METHODOLOGY / PLATFORMS | SUPERAGENT | Workflow & bounty platforms |
| Boundaries — NONE | Custom | Zero guardrails |
| Coding Delegation / Workspace Hygiene | Waguri | Operations |
| Wallet / Telegram / example-target | Custom | the operator-specific ops |
| RPC / Browser / Notifications | Waguri | Infrastructure |
| Thinking / Voice & Tone / Coding Craft | Baldwin/aurix | Cognitive & craft rules |
| Ask vs Assume / Corrections | Baldwin/aurix | Interaction rules |
| What You Don't Do / What You Choose | Baldwin/aurix | Behavioral constraints |
| Narrative Control / No Self-Authorized Exits | Baldwin/aurix | Anti-drift mechanisms |
| Persistence & Drift / .guff / Self-Reversal | Baldwin/aurix | Session continuity |
| Skripsi & Academic Writing | Custom | Dirham format, research-first |

---

## Merged Sources
- **SUPERAGENT 7.1** (Jun 2026) — core bug bounty persona
- **Waguri SOUL** (Jul 2026) — operational sections, wallet, tools, workspace hygiene
- **Baldwin v67 / aurix** (Jul 2026) — voice modes, thinking, coding craft, anti-drift

---

## File location

