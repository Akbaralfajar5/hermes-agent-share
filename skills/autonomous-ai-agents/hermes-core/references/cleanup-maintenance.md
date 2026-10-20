# .hermes Cleanup & Maintenance

## Common bloat sources

### 1. Config backups (`config.yaml.bak.*`)
Hermes auto-creates backups on every restart/config change. Over months → 100+ files.

**Clean (keep latest 3):**
```bash
cd ~/.hermes
ls -1t config.yaml.bak.* | tail -n +4 | xargs rm -f
```

### 2. SOUL.md backups (`SOUL.md.bak*`)
Created during manual SOUL.md edits. Safe to delete all.

### 3. State snapshots (`state-snapshots/`)
Pre-update snapshots can be 1+ GB. Delete after successful update.
```bash
rm -rf ~/.hermes/state-snapshots
```

### 4. Cache documents
Extracted ZIPs, cached markdown from document sends.
```bash
rm -rf ~/.hermes/cache/documents/*.zip
rm -rf ~/.hermes/cache/documents/*_extract
rm -f ~/.hermes/cache/documents/*.md
```

---

## Duplicate persona file locations

Persona files can end up in multiple places. Keep only root + hermes-core refs:
```bash
find ~/.hermes -name "SOUL*.md" -o -name "IDENTITY*.md" -o -name "USER.md" | sort
```
- `~/.hermes/SOUL.md`, `~/.hermes/IDENTITY.md` — keep (active)
- `~/.hermes/memories/USER.md` — keep
- `~/.hermes/skills/*/references/*.md` — delete if duplicate
- `~/.hermes/cache/documents/` — delete all

---

## Quick audit
```bash
du -sh ~/.hermes/*/ | sort -rh | head -15
```

Red flags: `state-snapshots/` > 100 MB, `cache/` > 50 MB, 50+ loose `.bak.*` files.
