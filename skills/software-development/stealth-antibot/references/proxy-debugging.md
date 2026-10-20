# Proxy Debugging — Isolate Browser vs Proxy Failures

When a Playwright/Camoufox browser fails to load pages (immediate close, `TargetClosedError`, `NS_ERROR_PROXY_CONNECTION_REFUSED`), **the proxy is the most likely culprit, NOT the browser code.**

## Diagnostic Flow (3 steps)

### Step 1: Test browser WITHOUT proxy

```python
from camoufox.async_api import AsyncCamoufox

async with AsyncCamoufox(headless=True) as browser:
    page = await browser.new_page()
    await page.goto('https://target.com/', timeout=30000)
    print(f'Title: {await page.title()}')  # If this works → browser is fine
```

If this succeeds, the browser is NOT the problem. Go to Step 2.

### Step 2: Test proxy SEPARATELY with curl

```bash
curl -x "http://user:pass@host:port" -m 15 https://target.com/ -o /dev/null -w "HTTP %{http_code} - %{time_total}s\n"
```

| Result | Meaning | Action |
|--------|---------|--------|
| `HTTP 200` | Proxy works | Problem is in browser proxy config format |
| `HTTP 407` | Auth rejected | Credentials wrong/expired — check provider dashboard |
| `Connection refused` | Server down | Proxy endpoint dead — check host:port |
| `Timeout` | Proxy unreachable | Network issue or wrong host |
| `HTTP 403` | Target blocking proxy IP | Need different proxy or residential IP |

### Step 3: Test browser WITH proxy (only after Step 2 passes)

```python
from camoufox.async_api import AsyncCamoufox

opts = {
    'headless': True,
    'proxy': {
        'server': 'http://host:port',  # Must include http:// prefix
        'username': 'user',
        'password': 'pass'
    }
}
async with AsyncCamoufox(**opts) as browser:
    page = await browser.new_page()
    await page.goto('https://target.com/', timeout=30000)
```

## Camoufox Proxy Config Format

```python
# Correct — dict with server, username, password
'proxy': {
    'server': 'http://gw.dataimpulse.com:10000',
    'username': 'user_id',
    'password': 'pass'
}

# Wrong — string format (this is for Playwright native, not Camoufox)
'proxy': 'http://user:pass@host:port'
```

## DataImpulse-Specific

- Default ports: `823` (HTTP), `10000` (HTTPS)
- Username format: `<customer_id>__cr.id`
- Dashboard: https://app.dataimpulse.com
- **407 error** = check if package expired or password rotated in dashboard
- Both ports return 407 simultaneously = account-level issue, not port issue

## Anti-Pattern: Debugging Browser Code When Proxy Is Down

**DON'T:** Spend 30 minutes rewriting browser launch code, switching libraries (cloakbrowser → AsyncCamoufox), changing viewport configs.

**DO:** Run Step 1 (no proxy) and Step 2 (curl proxy) first. Takes 10 seconds. If proxy is dead, tell user to fix their proxy account — no code changes needed.
