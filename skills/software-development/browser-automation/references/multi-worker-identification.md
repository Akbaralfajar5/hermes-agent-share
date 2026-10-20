# Multi-Worker Visual Identification

When running 5+ tabs in parallel, the user (and you) cannot tell which tab is
which when one fails. The user-facing complaint that triggers this every time:

> "ada 1 worker yang ga ke login, gimana cara cek itu worker berapa"
> ("one worker didn't log in, how do I check which one?")

This is the #1 follow-up after any multi-worker bot ships. Solve it up-front,
not after the user complains.

## The three layers (use ALL of them)

### 1. Tab title — visible in tab strip / OS window list
```python
await page.evaluate(f"document.title = '[W-{worker_id}] {label} — {step}'")
```

### 2. Floating in-page badge — visible while user is looking at the tab
```python
async def set_status(page, worker_id, label, status):
    await page.evaluate(f"""
        (() => {{
            let badge = document.getElementById('__worker_badge__');
            if (!badge) {{
                badge = document.createElement('div');
                badge.id = '__worker_badge__';
                badge.style.cssText = 'position:fixed;top:8px;left:8px;'
                  + 'z-index:2147483647;background:rgba(0,0,0,0.85);'
                  + 'color:#0f0;padding:6px 10px;border-radius:6px;'
                  + 'font:bold 13px monospace;border:2px solid #0f0;'
                  + 'pointer-events:none;max-width:90vw;';
                document.documentElement.appendChild(badge);
            }}
            badge.textContent = 'W-{worker_id} | {label} | {status}';
            document.title = '[W-{worker_id}] {label} — {status}';
        }})()
    """)
```

Call at the start of every meaningful step. On error, override colors to red.
On success, override to bright green.

### 3. Structured return + per-worker summary
```python
async def worker(page, worker_id, data) -> tuple[bool, str]:
    current_step = 'init'
    try:
        current_step = 'fill-phone'
        # ...
        current_step = 'submit-login'
        # ...
        return True, 'ready'
    except Exception:
        return False, current_step

# Runner:
for i, (data, res) in enumerate(zip(inputs, results), 1):
    if isinstance(res, tuple):
        success, step = res
        icon = '✅' if success else '❌'
        msg = 'READY' if success else f"FAILED @ '{step}'"
        print(f"  {icon} W-{i}: {data} — {msg}")
```

## Detect failure state, don't trust timing

After a login/submit/navigate, *verify* the expected outcome happened.
Don't just sleep N seconds and assume success.

```python
await asyncio.sleep(8)  # wait for navigation/animation
login_failed = await page.evaluate("""
    () => {
        const popup = document.querySelector('.login-popup');
        return popup && popup.offsetParent !== null;
    }
""")
if login_failed:
    return False, 'login-failed'
```

Without state verification, a wrong-credentials worker silently proceeds and
fails confusingly downstream — the real failure is upstream.

## Why all three layers, not just one

| Layer | Visible when | Failure if missing |
|-------|--------------|--------------------|
| Tab title | Tab strip / OS window list | Can't tell tabs apart in tab strip |
| Floating badge | Tab is focused | Can't tell tab apart while *looking at it* |
| Terminal summary | After run finishes | Can't see which step failed without scrolling logs |

## Anti-pattern

Logging `[W-3] failed` to terminal when 10 workers run in parallel is useless.
Terminal output is interleaved and the user is looking at the browser, not
the terminal. **Visual identification in the tab itself is non-negotiable
for >2 workers.**

## Production case study

- v1: only terminal logs → user complained "gimana cara cek itu worker berapa"
- v2: added title + badge + structured returns + login-failure detection
- Result: failed worker spotted visually in <2 seconds via red badge,
  post-run summary names the exact step.
