# Batch Install Workflow

When a user needs multiple skills installed (e.g., for a multi-faceted project like a thesis/skripsi), use this optimized workflow.

## Step 1: Multi-query search (parallel)

Run multiple `npx skills find` calls in parallel to cover different facets:
```bash
npx skills find "website development marketing" 2>&1 | head -80
npx skills find "research paper writing academic" 2>&1 | head -80
npx skills find "brand awareness SEO" 2>&1 | head -80
```

## Step 2: Present consolidated recommendations

Group results by purpose/role in the user's project. Use a table format:
- Skill name + install count + one-line purpose
- Organized by project phase (e.g., "Writing", "Development", "Marketing")


For each skill, construct the raw URL. If 404, use the tree API:
```bash
curl -fsSL "https://api.github.com/repos/<owner>/<repo>/git/trees/main?recursive=1" | grep -i "<skill-name>"
```

## Step 4: Install sequentially with category piping

```bash
# Pattern: pipe category name to avoid interactive prompt
```

Always use `--force` for batch installs to avoid blocking on CAUTION verdicts (after you've reviewed the skill content).

## Step 5: Verify all at once

```bash
hermes skills list 2>&1 | grep -E "skill1|skill2|skill3"
```

## Real example (from thesis/skripsi session)

User needed: academic writing + website dev + marketing/SEO for a Teaching Factory product website.

Searches run:
- `npx skills find "website development marketing"`
- `npx skills find "research paper writing academic"`
- `npx skills find "brand awareness SEO"`
- `npx skills find "web design UI UX"`
- `npx skills find "fullstack nextjs react"`

Installed 4 skills:
1. `paper-writing` → research category
2. `website-structure` → productivity category
3. `nextjs-react-typescript` → software-development category
4. `seo` → productivity category
