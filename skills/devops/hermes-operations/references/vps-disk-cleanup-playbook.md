# VPS Disk Cleanup Playbook (40G root, fills fast)

## Trigger
User says "tolong bersihkan file file yang tidak terpakai" / disk full. This VPS root is 40G and hits 90%+ regularly (miners, Rust builds, npm caches, session dumps).

## Order of Attack (biggest wins first)

```bash
df -h /                                   # how bad?
du -sh ~/* 2>/dev/null | sort -rh | head -15   # biggest home dirs
du -sh ~/.cache/* 2>/dev/null | sort -rh | head
du -sh ~/.hermes/* 2>/dev/null | sort -rh | head
```

### 1. Rust build artifacts — the 8-9G whale
`~/agave/target/` (or any project with `target/`) is pure build output:
```bash
ps aux | grep -i agave | grep -v grep   # confirm not running
cd ~/agave && cargo clean               # frees 8-9G; source (~47M) untouched
```

### 2. npm caches — ~570M+
```bash
rm -rf ~/.npm/_cacache ~/.npm/_prebuilds ~/.npm/_logs ~/.npm/_npx
```
`_npx` is 90% of it (262M + 170M + 73M single entries). Safe — re-downloads on demand.

### 3. uv cache — ~290M
```bash
rm -rf ~/.cache/uv
```

### 4. Hermes session debug dumps — ~156M
```bash
rm -f ~/.hermes/sessions/request_dump_*.json   # debug artifacts, 1000+ files
```
Keep `session_*.json` — that's real chat history for session_search.

### 5. Old zips & temp renders
- Home root: old versioned zips (`reg_*.zip`, `klaim_*.zip`, `deposit_*.zip`) — keep only the newest version.
- `/tmp`: rendered PNGs, old docx versions, `deposit_final*.zip` — safe to clear (regenerate).

### 6. Old docx versions — ARCHIVE, never delete (user preference)
User keeps every skripsi/jurnal revision. Move to `~/archive-skripsi-lama/` instead of deleting:
```bash
mkdir -p ~/archive-skripsi-lama
for f in $(ls skripsi*.docx | grep -v "terbaru"); do mv "$f" ~/archive-skripsi-lama/; done
```

## NEVER Delete (active infra)
| Path | Why |
|------|-----|
| `~/.hermes/hermes-agent/venv` | Running gateway process (check `ps aux \| grep hermes_cli.main gateway`) |
| `~/.hermes/state.db` (~1.3G) | Session history DB — FTS5 search |
| `~/.hermes/sessions/` (non-dump) | Chat history |
| `~/.rustup` (~3G) + `~/.cargo` (~800M) | Rust toolchain — needed for Alpenglow audit |
| `~/sniper-bot`, `~/myapp-full`, `~/my-site`, `~/ethena-audit`, `~/arc-agent` | Active projects |
| `~/agave` source (non-target) | Alpenglow consensus audit repo |

## Success Metric
Target: <75% used after cleanup. From 98% → 72% in the 2026-08 session (freed ~10G).

## Related
- Git push after cleanup? Use the direct-push-secrets-checklist in this skill (`.hermes` is a git repo → private GitHub).
