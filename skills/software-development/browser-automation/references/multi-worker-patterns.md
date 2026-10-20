# Multi-Worker Playwright Patterns (Lessons Learned)

## Architecture: 1 Terminal, N Parallel Workers

Use `threading.Thread` + `sync_playwright().start()` per thread.
DO NOT share Playwright instances across threads.

```python
import threading
from playwright.sync_api import sync_playwright

def worker(email):
    pw = sync_playwright().start()  # Each thread gets own instance
    browser = pw.chromium.launch(headless=False, args=[...])
    context = browser.new_context(...)
    page = context.new_page()
    # ... do work ...
    # DON'T close browser if you want it to stay open
    # Keep references alive (append to global list)

threads = []
for email in batch:
    t = threading.Thread(target=worker, args=(email,))
    threads.append(t)
    t.start()
    time.sleep(0.5)  # Stagger to avoid port conflicts

for t in threads:
    t.join()
```

## Key Pattern: Browser Stays Open After Task

When user needs to interact manually after automation:
- DON'T use `finally: browser.close()`
- Append `(browser, pw)` to a global list to prevent GC
- Keep main script alive with `while True: time.sleep(60)` + KeyboardInterrupt handler
- Close browser only on error/failure paths

## Batch Processing with Pause Between Batches

```python
for i in range(0, len(remaining), batch_size):
    batch = remaining[i:i+batch_size]
    # ... spawn threads, join ...
    if more_remaining:
        input("Press ENTER for next batch...")
```

## Common Issues

1. **ThreadPoolExecutor hangs** if workers never return (browser stays open).
   Fix: use raw `threading.Thread` instead — join() returns when login done,
   browser stays alive in background.

2. **Port conflicts** with many parallel Chromium launches.
   Fix: add `time.sleep(0.5)` stagger between thread starts.

3. **sync_playwright context manager** (`with sync_playwright() as p:`) —
   closes Playwright when exiting scope, killing all browsers.
   Fix: use `pw = sync_playwright().start()` (manual lifecycle).

4. **Output interleaving** from parallel workers.
   Fix: use `print_lock = threading.Lock()` wrapper.

5. **File write races** (output/results file).
   Fix: use `output_lock = threading.Lock()` for writes.

## Cookie-Based 2-Phase Pattern

Phase 1 (Login): headless, parallel, save cookies to files
Phase 2 (Action): load cookies, skip login, do the actual task

Benefits:
- Login is slow (OAuth popup, consent) — do it once, reuse
- Action phase can use different parallelism level
- Failed logins don't waste action-phase resources
- Cookies persist — retry claim without re-login

```python
# Save
cookies = context.cookies()
with open(f'cookies/{email}.json', 'w') as f:
    json.dump({'cookies': cookies, 'user': session}, f)

# Load
context.add_cookies(data['cookies'])
```
