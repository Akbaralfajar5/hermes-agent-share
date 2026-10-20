---
name: skill-auto-organize
tags: [skills, organize, categorize, trim, cleanup]
version: 1.0.0
author: Feb
category: hermes
metadata:
  hermes:
    tags: [skills, organize, categorize, trim, cleanup]
    platforms: [linux]
---

# Skill Auto-Organize

Automatically organize the skill library: categorize, trim, and structure.

## When to use

- After skill audit reveals uncategorized or oversized skills
- User says "rapikan skill" / "organize skill" / "bersihin skill"
- Monthly maintenance
- After bulk skill creation

## 1. Categorize uncategorized skills

Root-level skills (directly in `~/.hermes/skills/` without a category subdirectory) should be moved into appropriate categories.

### Category mapping rules

| Keyword in name/description/tags | Suggested category |
|----------------------------------|--------------------|
| farm, farming, harvest, mass-account | `automation/` |
| 9router, gateway, proxy, sqlite, systemd | `devops/` |
| qoder, tokenharbor, pateway, provider | `automation/` or `devops/` |
| audit, vulnerability, pentest, exploit | `security/` or `bug-bounty/` |
| pytorch, training, fine-tune, dataset | `mlops/` |
| writing, creative, blog, content | `creative/` |
| apple, macos, imessage, notes | `apple/` |
| research, paper, citation | `research/` |
| email, calendar, reminder, productivity | `productivity/` |
| skill, hermes, agent, memory | `hermes/` |
| github, git, ci/cd | `github/` |
| blockchain, solana, ethereum, smart-contract | `blockchain/` |
| oauth, credential, auth, token | `autonomous-ai-agents/` or `devops/` |

### Categorize procedure

```bash
cd ~/.hermes/skills
# Find uncategorized skills
  name=$(basename "$d")
  echo "UNCATEGORIZED: $name → $desc"
done
```

For each uncategorized skill:
1. Read name + description + tags
2. Map to category using the table above
3. Create category dir if needed: `mkdir -p <category>`
4. Move: `mv <skill-name> <category>/<skill-name>`
5. Verify: `skill_view(name='<skill-name>')`

### When NOT to categorize

Some skills are intentionally root-level:
- Skills that span multiple categories (meta-skills)
- Skills with very short names that are universally relevant
- Skills that are already well-known by their root-level path

Use judgment — don't force everything into categories.

## 2. Trim oversized skills

### Size thresholds

| Size | Status | Action |
|------|--------|--------|
| < 20KB | ✅ Good | No action |
| 20-50KB | 🟡 Watch | Consider extracting detailed sections to references/ |
| 50-80KB | 🟠 Large | Extract sections to references/, trim stale content |

### Trim procedure

2. Identify sections that are:
   - **Detailed reference material** → move to `references/<topic>.md`
   - **Historical bug fixes** (already resolved, not needed daily) → move to `references/archive-<topic>.md`
   - **Repeated patterns** (same pitfall in multiple sections) → consolidate
   - **Stale content** (references deleted services, old versions) → remove or archive
   ```markdown
   See `references/<topic>.md` for full details.
   ```

### Example trim

```markdown
## Pateway Farm
[3000 lines of detailed pateway farm methodology]
```

```markdown
## Pateway Farm
See `references/pateway-ai.md` for full farm methodology, captcha handling, and provider-specific pitfalls.
```


|-------------------|---------------------|
| Overview, when-to-use | Detailed step-by-step with code |
| Trigger conditions | Provider-specific API maps |
| Top 5 most common pitfalls | Historical bug fix logs |
| Verification commands | Long configuration examples |
| Related skills links | Session-specific war stories |

## 3. Frontmatter consistency


```yaml
---
name: <skill-name>           # REQUIRED, matches directory name
description: "<one-liner>"   # REQUIRED, for search/matching
tags: [tag1, tag2]           # REQUIRED, for keyword matching
version: 1.0.0               # RECOMMENDED
author: Feb                  # RECOMMENDED
category: <category>         # RECOMMENDED, matches directory
metadata:
  hermes:
    tags: [tag1, tag2]       # DUPLICATE of top-level tags (for hermes platform)
    platforms: [linux]       # RECOMMENDED
---
```

### Frontmatter audit command

```bash
cd ~/.hermes/skills
  if ! head -3 "$1" | grep -q "^name:"; then
    echo "MISSING name: $1"
  fi
  if ! head -5 "$1" | grep -q "^description:"; then
    echo "MISSING description: $1"
  fi
  if ! head -10 "$1" | grep -q "^tags:"; then
    echo "MISSING tags: $1"
  fi
' _ {} \;
```

## 4. Linked file structure

Standard structure for skills with linked files:

```
skill-name/
├── references/                 # Detailed reference docs
│   ├── api-endpoints.md
│   ├── troubleshooting.md
│   └── historical-bugs.md
├── scripts/                    # Executable helper scripts
│   ├── audit.py
│   └── check.sh
├── templates/                  # Copy-and-modify templates
│   ├── config.yaml
│   └── setup.sh
└── assets/                     # Non-code assets (images, configs)
    └── diagram.png
```

Not every skill needs all four directories. Only create what's used.

## Pitfalls

1. **Don't over-trim.** A 67KB skill like `9router-ops` is large because the system is complex. Trimming it to 20KB by moving everything to references means the agent has to load 5 reference files instead of 1 — slower and more error-prone. Only trim when content is genuinely stale or duplicated.
2. **Don't force categories on meta-skills.** Skills like `hermaguard` or `avoid-ai-writing` are root-level by design — they span multiple domains. Forcing them into a category makes them harder to find.
3. **Always verify after moving.** `skill_view(name='<skill-name>')` after any move to ensure the skill still loads correctly from its new location.
5. **Script files must be executable.** `chmod +x scripts/*.py scripts/*.sh` after creating script files.
6. **Category directories must exist before moving.** `mkdir -p <category>` before `mv <skill> <category>/<skill>`.

## Related skills

- `skill-audit` — full audit including size and category checks
- `skill-management` — lifecycle management
- `skill-anti-duplicate` — duplicate detection and merge
- `skill-strengthen` — improve existing skills
- `skill-auto-create` — auto-generate from session patterns
