# ZIP Skill Update Workflow

When user sends a `.zip` file with skill updates (e.g. `SUPERAGENT-v3.1-OPENCLAW.zip`):

## Pattern

> ⚠️ **GOLDEN RULE: ADD-ONLY, NEVER REPLACE.** User may have custom modifications in existing files. Replacing wipes their work. Always diff first, then ADD new files only. For updated files, show the user what changed and let them decide.

1. **Unzip** to `/tmp/<name>/`
2. **Inventory** all files: `find /tmp/<name> -type f | sort`
3. **Backup** existing skill dir: `cp -r <skill>/ <skill>.old`
4. **Diff** key files against existing skills to identify what's new/changed
5. **ADD only new files**, NEVER overwrite existing ones:
   - New `references/*.md` → copy to skill's `references/`
   - New `scripts/*.py` → copy to skill's `scripts/`
   - For UPDATED files → show diff to user, let them decide
6. **Install tools natively** (not just as skill references):
   - Copy executable scripts to `~/.hermes/scripts/<name>/`
   - Install Python deps in Hermes venv: `~/.hermes/hermes-agent/venv/bin/python -m pip install <pkg>`
   - User prefers tools directly accessible, not buried in skill folders

## File placement rules

| File type | Destination |
|---|---|
| `skills/<skill-name>/references/*.md` | Copy to matching skill's `references/` |
| `skills/<skill-name>/scripts/*.py` | Copy to matching skill's `scripts/` |
| `skills/m7.md`, `skills/m9.md` | `hermes-core/scripts/` |
| `SOUL.md`, `panduan.md` | `hermes-core/scripts/` with version suffix |
| `DISPATCH.md` | Relevant skill's `references/` |

## Verification

After copying, verify with:
```bash
ls /home/ubuntu/.hermes/skills/<skill>/references/
ls /home/ubuntu/.hermes/skills/<skill>/scripts/
```

## Notes

- Always diff before overwriting — check if new version has meaningful additions
- **ADD-ONLY is the default.** User explicitly corrected: "install yg belum ada aja jangan di replace, soalnya ada beberapa yg udh gw install jadi hilang"
- **Install native tools too.** User wants tools at `~/.hermes/scripts/` (executable), not just skill folders. "bisa langsung di update ke hermes nya aja, jangan dijadiin skills"
- Version suffix for persona/operator files (e.g. `SOUL_v3.md`) to preserve history
- `m7.md` and `m9.md` live in `hermes-core/scripts/` alongside other module files

## Pitfalls

- **DON'T blindly `cp` over existing files** — user loses custom changes. Always diff + add-only.
- **DON'T keep tools only in skill directories** — also install to `~/.hermes/scripts/` for native access
- **DON'T skip venv deps** — install Python packages in Hermes venv: `~/.hermes/hermes-agent/venv/bin/python -m pip install <pkg>`
- **DON'T forget the backup** — `cp -r` the whole skill dir before any changes
