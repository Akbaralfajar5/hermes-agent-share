# Terminal Session Recovery

## Symptom

All `terminal()` tool calls fail with:
```
FileNotFoundError: [Errno 2] No such file or directory: '/path/to/nonexistent/dir'
```

Even simple commands like `pwd` or `cd ~` fail with the same error.

## Root Cause

The terminal backend's working directory is stuck in a directory that no longer exists. This happens when:
1. A previous command changed to a directory
2. That directory was deleted (by user or another process)
3. The terminal session persists with the stale working directory

The terminal backend maintains a persistent working directory across tool calls within a session. If that directory is deleted, all subsequent commands fail immediately without attempting execution.

## Diagnosis

```python
# Attempt any simple command
terminal(command="pwd", timeout=5)
# Returns: FileNotFoundError: [Errno 2] No such file or directory: '/home/ubuntu/deleted-dir'
```

The error message reveals the stuck directory path.

## Solutions (in order of preference)

### 1. Pass `workdir` explicitly on the next `terminal()` call

An explicit `workdir` overrides the stale cwd so the call executes — the stale path only breaks the session's implicit `cd`. Keep passing `workdir` for the session's follow-up calls; no `/new` and no gateway restart needed.

```python
terminal(command="your_command", workdir="/home/ubuntu", timeout=30)
```

If the failure reads `cd: <stale-path>: No such file or directory` (exit 126) instead of `FileNotFoundError`, it is the same root cause.

### 2. Use `execute_code` tool as workaround

The `execute_code` tool spawns fresh Python subprocesses and doesn't inherit the broken terminal session state:

```python
execute_code(code="""
import subprocess
result = subprocess.run(['bash', '-c', 'cd ~ && your_command_here'], 
                       capture_output=True, text=True, timeout=30)
print(result.stdout)
if result.returncode != 0:
    print(f"Error: {result.stderr}")
""", timeout=60)
```

**Pros:** Works immediately, no session restart needed  
**Cons:** More verbose, requires Python wrapper

### 3. Start a new Hermes session

The terminal backend resets when starting a fresh conversation:

```
/new
# or
/reset
```

**Pros:** Clean slate, fixes all session state issues  
**Cons:** Loses conversation context (unless you summarize first)

### 4. Restart Hermes gateway/CLI

If `/new` doesn't fix it (rare), restart the entire Hermes process:

**CLI:**
```bash
# Exit and relaunch
/exit
hermes
```

**Gateway:**
```bash
# From terminal
systemctl --user restart hermes-gateway
# or from Telegram
/restart
```

**Pros:** Guaranteed fix  
**Cons:** Interrupts all active sessions

## Prevention

1. **Avoid `cd` to temporary directories** — use absolute paths in commands instead:
   ```bash
   # Bad (if /tmp/build gets deleted)
   cd /tmp/build && make
   
   # Good
   make -C /tmp/build
   ```

2. **Check directory exists before cd:**
   ```bash
   [ -d /path/to/dir ] && cd /path/to/dir || echo "Directory not found"
   ```

3. **Use `workdir` parameter** — set it explicitly instead of relying on the session cwd; it is also the fastest recovery (see Solutions):
   ```python
   terminal(command="your_command", workdir="/safe/path", timeout=30)
   ```

## Related Issues

- **"Command execution failed: FileNotFoundError"** on every terminal call → this issue
- **"No such file or directory"** but the file/command exists → this issue
- **Terminal works in some sessions but not others** → session-specific stuck directory

## Example from Session (May 2026)

User reported localhost:20128 app needed to be exposed publicly. All attempts to diagnose with `terminal()` failed:

```python
terminal(command="pwd")  # Failed
terminal(command="cd ~ && pwd")  # Failed
terminal(command="ps aux | grep 20128")  # Failed
```

All returned: `FileNotFoundError: [Errno 2] No such file or directory: '/home/ubuntu/rot-minter'`

**Root cause:** Previous session had `cd ~/rot-minter` but directory was deleted. Terminal backend stuck in nonexistent path.

**Solution used:** User manually restarted Hermes gateway via SSH:
```bash
ssh ubuntu@43.159.56.39
pkill -f hermes
hermes gateway start
```

After restart, `terminal(command="pwd")` returned `/home/ubuntu` successfully.

## Key Insight

The terminal backend's working directory is **persistent state** that survives across tool calls but **not** across sessions. When that state becomes invalid (directory deleted), recovery options are:
1. Pass `workdir` on the next call — it runs immediately despite the stale cwd
2. Work around it with `execute_code`
3. Reset the session state (`/new`)
4. Restart the process

Recovery without restart works: pass an explicit `workdir` and the call executes despite the stale cwd. Reset/restart is only needed if `workdir` is unavailable.
