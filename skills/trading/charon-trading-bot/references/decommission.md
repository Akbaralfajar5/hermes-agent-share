# Charon Decommission

**Date:** May 26, 2026
**Action:** User explicitly requested deletion. PM2 process `charon` deleted, `~/charon/` directory removed.

## What was removed
- PM2 process name: `charon`
- Source directory: `~/charon/`
- Database: `~/charon/charon.sqlite` (was 900MB before pruning)
- Bot endpoint: `https://api.thecharon.xyz/api`

## Why
User said: "untuk bot charon hapus saja, saya sudah tidak pake" (just delete charon bot, I no longer use it)

## Before decommission — cleanup performed
1. Pruned `signal_events`: deleted 239,240 rows older than 3 days
2. Deleted `dry_run_positions` (141 rows) and `dry_run_trades` (272 rows)
3. Deleted old `candidates` (kept last 1,000)
4. Ran `VACUUM` — DB shrank from 900MB to 374MB
5. Freed ~526MB from database + cleaned other stale projects

## Issues that prompted the cleanup
- `charon.sqlite` at 900MB caused "database or disk is full" errors
- Positions 140 & 141 stuck in "Insufficient funds" loop (wallet had 0 SOL)
- Disk was at 93% (35G/40G used)

## If user wants to re-deploy
- Repo: https://github.com/yunus-0x/charon
- See main skill content for full setup instructions
- Fresh clone + npm install required
