# Charon audit notes — Telegram learning flow and runtime-safe verification

## What broke

### 1) `/lesson` routed into `/learn`
Cause: command handling relied on prefix checks such as `text.startsWith('/learn')`.

Effect:
- `/lesson` was interpreted as `/learn`
- a read-only UX command could trigger a learning run instead of showing lessons

Fix pattern:
- tokenize once, e.g. `const parts = text.trim().split(/\s+/)`
- normalize the command from `parts[0]`
- branch on exact equality (`command === '/learn'`, `command === '/lesson'`, `command === '/lessons'`)

### 2) Learning runs left stale active lessons behind
Cause: `learning_lessons` from older runs stayed `active`.

Effect:
- prompts could accumulate old lessons
- `/lessons` became harder to interpret because active state no longer meant "latest run"

Fix pattern:
- before inserting lessons for a new run, archive all currently `active` lessons
- save the new run's `activated_window` in run metadata (`raw_json`) for later reporting/audit

### 3) `/learn` on empty data had poor UX
Observed DB state during audit:
- `learning_runs = 0`
- `learning_lessons = 0`
- `active_lessons = 0`

Fix pattern:
- if there are no closed dry-run positions in the requested window, return a clear Telegram message and do not create a meaningless learning run

## Runtime verification pitfall

### `ETELEGRAM: 409 Conflict` during ad-hoc module imports
Observed when importing runtime modules from a one-off Node snippet while PM2 `charon` was already online.

Likely cause:
- imported module graph initialized Telegram polling again
- Telegram terminated one `getUpdates` consumer because another instance was already polling

Safer verification order:
1. Use static verification first: `node --check`, diff review, file inspection.
2. If you need runtime inspection, prefer logs/DB queries over importing startup paths.
3. If a module import can initialize polling, stop or isolate the live PM2 bot first.

## Practical checklist for future Charon audits

- Verify Telegram commands with exact-token parsing, not prefix matching.
- Check singular/plural aliases for user-facing commands (`/lesson` vs `/lessons`).
- Confirm learning runs archive prior active lessons.
- Confirm lesson/report output shows window and recency metadata.
- Avoid runtime imports that can spawn a second Telegram polling client while production PM2 is live.
