# Persistent Cronjob Cleanup

When cronjobs survive deletion or auto-recreate despite using `hermes cronjob delete`, use nuclear cleanup.

## Symptoms

- Cronjob notifications continue after deletion
- `hermes cronjob list` shows job is deleted, but notifications still arrive
- Screen sessions respawn automatically
- Processes restart after being killed

## Root Causes

1. **Multiple duplicate cronjobs** — user created similar jobs over time (e.g., "rpow2 Watchdog", "rpow2 Python Miner Watchdog", "VPS Hermes rpow2 Watchdog"), only paused/deleted one
2. **Job still enabled** — job shows `enabled: true` despite user thinking they stopped it
3. **Watchdog scripts** in project directories (e.g., `~/project/watchdog.sh`)
4. **Screen sessions** that respawn processes on detach
5. **Parent process trees** - killing child doesn't kill parent
6. **Source directories** containing auto-restart logic

## Diagnostic Workflow

### Step 1: Identify ALL duplicate jobs

```bash
# List all jobs (including paused)
hermes cronjob list --all

# Look for:
# - Multiple jobs with similar names (e.g., "rpow2 Watchdog", "rpow2 Python Miner Watchdog")
# - Jobs with `enabled: true` that user thought were stopped
# - Overlapping schedules (e.g., `every 5m` + `every 30m` + `daily`)
```

**Common pattern:** User creates a cronjob, it doesn't work, they create another with a slightly different name, repeat. Result: 3-5 similar jobs, only 1-2 actually paused.

### Step 2: Pause first, verify, then delete

```bash
# Pause the job
hermes cronjob pause <job_id>

# Verify state changed
hermes cronjob list  # Should show `enabled: false`, `state: paused`

# Delete
hermes cronjob remove <job_id>

# Verify gone
hermes cronjob list  # Should not appear
```

**Why pause first?** If a job is already scheduled for the next tick, deleting it immediately may not prevent that execution. Pausing sets `enabled: false` which prevents new executions.

### Step 3: Nuclear cleanup (if still appearing)

```bash
# 1. Delete Hermes cronjob
hermes cronjob delete <job_id>

# 2. Kill entire process tree (not just process)
pkill -9 -f <process_name>

# 3. Terminate all screen sessions
screen -wipe
screen -ls | grep <session_name> | cut -d. -f1 | xargs -I {} screen -S {} -X quit

# 4. Remove source directory (contains watchdog/auto-restart scripts)
rm -rf ~/project-directory

# 5. Clean screen socket directory
rm -rf /run/screen/S-$USER/*

# 6. Verify complete cleanup
hermes cronjob list  # Should not show deleted job
ps aux | grep <process_name>  # Should return nothing
screen -ls  # Should show "No Sockets found"
```

## Example: rpow2 Mining Cleanup

User said "STOP REMINDER!!" multiple times but cronjob kept sending notifications.

**Problem:** Cronjob deleted via Hermes, but:
- Screen session `rpow2` kept respawning
- Process tree had parent spawning children
- `~/rpow2-python-miner/watchdog.sh` was auto-restarting miner

**Solution:**
```bash
# Delete cronjob
hermes cronjob delete dfd990e2dd57

# Kill all rpow2 processes (including parent tree)
pkill -9 -f rpow2

# Remove source directories (contains watchdog.sh)
rm -rf ~/rpow2-python-miner
rm -rf ~/rpow2-rust-miner

# Clean screen sessions
screen -wipe
rm -rf /run/screen/S-root/*

# Verify
hermes cronjob list  # Only GIWA cronjob remains
ps aux | grep rpow2  # Nothing
screen -ls  # No sockets found
```

## Prevention

When creating cronjobs that run mining/monitoring scripts:

1. **Don't use watchdog scripts** that auto-restart - let Hermes cronjob handle restarts
2. **Use `nohup` or `systemd`** instead of screen for background processes
3. **Document cleanup procedure** when creating complex automation
4. **Test deletion** before considering setup complete

## User Frustration Signal

When user says:
- "STOP REMINDER!!"
- "Masih mengirim terus" (still sending continuously)
- "Kenapa anda mengirim terus ini bro?" (why do you keep sending this?)

This is a **critical signal** - nuclear cleanup required immediately, not incremental fixes.
