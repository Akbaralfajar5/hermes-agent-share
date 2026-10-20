# SSL Retry Loop Pattern (Jul 2026)

## Problem

Website may be slow to load or show SSL warnings. If worker gives up immediately on first failure, it wastes the browser session.

## Solution

Retry up to 5 times with reload + SSL handler before closing the worker.

## Pattern

```python
r18_ready = False
for r18_attempt in range(5):  # max 5 attempts
    r18_ready = await poll_until(page, """() => {
        const e = document.querySelector('.r18-entry');
        return e && e.offsetParent !== null;
    }""", timeout_s=20)

    if r18_ready:
        break

    log(worker_id, f"⚠️ r18 not found (attempt {r18_attempt+1}/5), retrying...")
    await handle_ssl_warning(page)
    try:
        await page.reload(wait_until='domcontentloaded', timeout=30000)
    except:
        pass
    await asyncio.sleep(3)
    await handle_ssl_warning(page)

if not r18_ready:
    log(worker_id, "❌ r18 not rendered (gave up after 5 attempts)")
    return {'phone': phone, 'status': 'r18-not-rendered'}
```

## Why 5 Attempts

- Each attempt: 20s poll + 3s reload delay = ~23s
- 5 attempts × 23s = ~115s max wait
- SSL warning may appear intermittently
- Page may be slow due to proxy latency
- Worker stays alive during retries

## Integration Points

1. After `page.goto(URL)`: Call `handle_ssl_warning(page)` immediately
2. Before age gate check: Add retry loop for r18 element
3. After each retry: Call `handle_ssl_warning(page)` again

## Related

- `references/ssl-warning-bypass-playwright.md` — SSL warning handler functions
- `references/example-target-registration.md` — Full registration flow
