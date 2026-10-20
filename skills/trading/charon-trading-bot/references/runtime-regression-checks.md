# Runtime Regression Checks

Use this after patching Charon entry/exit logic, especially when restarting a live PM2-managed bot.

## Pre-restart checks

- `git status --short`
- `git branch --show-current`
- `git log -1 --oneline`
- `pm2 status charon`
- `pm2 describe charon`

Why: capture branch/process state before restart and confirm the PM2 app name, cwd, logs, and runtime.

## Restart sequence

1. `pm2 restart charon`
2. `pm2 status charon`
3. Tail logs:
   - `tail -n 120 ~/.pm2/logs/charon-out.log`
   - `tail -n 120 ~/.pm2/logs/charon-error.log`

Healthy signs:
- PM2 status returns `online`
- startup log shows `node index.js`
- wallet loads successfully
- bot prints started/server-mode line
- error log remains empty or unchanged

## Post-patch pitfalls found in practice

### 1) Telegram notification failure after successful live buy

If swap execution and `createLivePosition()` already succeeded, `sendPositionOpen()` must not be allowed to throw an error that bubbles up as a failed execution.

Preferred handling:
- wrap `sendPositionOpen(positionId)` in `try/catch`
- log a warning
- keep trade intent / execution state aligned with the already-opened live position

### 2) Manual close must re-read row after refresh

`refreshPosition(row, { autoExit: false })` can update DB-backed fields such as:
- `partial_tp_done`
- `token_amount_raw`
- `token_amount_est`
- even close state in edge paths

Before `executeLiveSell()` or final accounting:
- re-query the latest row from `dry_run_positions`
- abort safely if the position is no longer open

## Verification checklist after restart

- `node --check` on modified JS files
- `git diff --check` on modified files
- PM2 status online
- no fresh stack traces in `charon-error.log`
- `charon-out.log` shows normal screening / bot startup lines
- if entry/exit logic changed, manually inspect one open position flow before trusting unattended runtime

## Commit hygiene

When finishing a focused entry/exit fix:
- commit only the files related to the logic change
- leave unrelated dirty files out of the commit unless intentionally bundled
- re-run `git status --short` after commit to confirm leftovers
