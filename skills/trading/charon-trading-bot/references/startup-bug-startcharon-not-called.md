# Critical Startup Bug: startCharon() Not Called

**Discovered:** 2026-05-16  
**Symptom:** Bot process runs but produces no logs, no signal tracking, no LLM calls, no position monitoring.

## Root Cause

`src/app.js` exports `startCharon()` function but **never calls it**. The function is defined but not invoked at module load.

## Diagnosis

```bash
# Bot shows as "online" in PM2
pm2 status charon
# → status: online, uptime: 5m

# But logs are empty
tail -50 ~/.pm2/logs/charon-out.log
# → (empty or only old logs)

# Process exists but does nothing
ps aux | grep "[n]ode.*charon"
# → ubuntu  12345  0.0  1.2  node /home/ubuntu/charon/src/app.js
```

## Fix

Add function call at end of `src/app.js`:

```javascript
// At end of file, after startCharon() definition
startCharon();
```

**Full context:**
```javascript
export async function startCharon() {
  console.log(`[${APP_NAME}] Starting...`);
  initDb();
  initLiveExecution();
  setupTelegram();
  console.log(`[${APP_NAME}] Initialized. Mode: ${SIGNAL_SERVER_URL ? 'server' : 'standalone'}`);
  
  // ... rest of function
}

// ADD THIS LINE:
startCharon();
```

## Verification

After fix:
```bash
pm2 restart charon
sleep 5
tail -20 ~/.pm2/logs/charon-out.log
```

**Expected output:**
```
[Charon] Starting...
[live] wallet loaded 5j37jsGx...
[Charon] Initialized. Mode: server
[candidate] filtered ABC123... market cap max: 50000 > 30000
```

## Prevention

When bot shows "online" but produces no logs:
1. Check if entry point function is called (not just defined)
2. Add startup log at beginning of main function
3. Verify PM2 is pointing to correct entry file

## Related Files

- `src/app.js` — main entry point
- `package.json` — may specify different entry point (check `main` field)
