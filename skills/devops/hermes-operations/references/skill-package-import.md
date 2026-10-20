# Skill Package Import Workflow (from hermes-skill-package-importer)

Condensed from the `hermes-skill-package-importer` skill, merged 2026-06-18. Covers importing external skill packages (ZIP/folder) into Hermes as native skills.

## When to Use

- User sends a ZIP/folder containing skills (e.g., SUPERAGENT, custom agent packs)
- User says "daftarkan sebagai Hermes native" or "register as native skills"
- Importing/upgrading a skill collection

## Steps

### 1. Extract & Inventory

```bash
cd /tmp && unzip -o <path> -d <package_name>
find /tmp/<package> -type f | wc -l
find /tmp/<package> -name "*.md" | wc -l
```

Read CHANGELOG.md or README.md first for version/structure context.

### 2. Identify Skill Files

Look for:
- Named patterns: `m0.md`-`m48.md`, `x1.md`-`x7.md`, or `skill-name.md`
- Registry/index file (often `m0.md` or `INDEX.md`)
- Supporting `.py` files in `tools/` directory
- Reference docs in `references/` subdirectories

### 3. Create Directory Structure

```bash
mkdir -p ~/.hermes/skills/<package-name>/{tools,hermes}
```

Copy in order:
1. Skill `.md` files → `~/.hermes/skills/<package-name>/`
2. Python tools → `~/.hermes/skills/<package-name>/tools/`
3. Core docs (AGENTS.md, IDENTITY.md, etc.) → `~/.hermes/skills/<package-name>/`
4. Subdirectories (references, templates, tests) → `~/.hermes/skills/<package-name>/`



```yaml
---
name: <skill-name>
description: <extracted from first heading/paragraph, max 200 chars>
category: <package>/<subcategory>
---
```

**Category routing logic** — map skill names to subcategories (e.g., m33-m42 → trading, m43-m48 → hacking).

**Description extraction rules:**
- Extract title from first `# ` heading
- Extract description from first paragraph after title, clean markdown
- If extraction fails, write manually based on content

### 5. Fix Bad Descriptions

After bulk creation, check for `description: ---` (YAML parsing failures from `---` markers conflicting with markdown horizontal rules):

```bash
# Find broken descriptions
```

Fix each manually with a proper description string.

### 6. Verify Registration

```python
skills_list(category='<package-name>')
```

Check all expected skills appear, descriptions are meaningful, categories correct.

## Pitfalls

- **Duplicate skills**: Check if package overwrites existing skills. Report conflicts.
- **Description extraction**: YAML `---` markers conflict with markdown horizontal rules. Always validate after bulk creation.
- **Tool dependencies**: Python tools may need packages not installed. Note but don't block registration.
- **Memory overflow**: If user's memory is near capacity, skip saving installation details.
- **Symbolic links**: Use `cp -rL` to follow symlinks when copying.
