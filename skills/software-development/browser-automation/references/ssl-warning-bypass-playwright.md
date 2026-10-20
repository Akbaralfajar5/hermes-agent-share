# SSL Certificate Warning Bypass (Playwright)

## Problem
Chromium shows "Your connection is not private" (`NET::ERR_CERT_COMMON_NAME_INVALID`) when:
- Site uses self-signed cert
- Domain changed but old cert cached
- Proxy intercepts HTTPS (mitmproxy, corporate proxy)
- Domain rotation (e.g., example-targetii.com → example-targethh.com)

## Fix 1: Chromium launch args (prevents the page entirely)
```python
browser = await p.chromium.launch(
    headless=False,
    args=[
        '--ignore-certificate-errors',
        '--ignore-certificate-errors-spki-list',
        # ... other args
    ],
)
```
This suppresses the warning page before it renders. Preferred approach.

## Fix 2: Auto-click Advanced → Proceed (if warning still appears)
Some Chromium versions or Playwright configs still show the warning even with the flag. Add this handler after `page.goto()`:

```python
async def handle_ssl_warning(page):
    """Click #details-button (Advanced) -> #proceed-link (Proceed)."""
    try:
        is_ssl = await safe_eval(page, """() => {
            return document.body.innerText.includes('Your connection is not private')
                || document.body.innerText.includes('NET::ERR_CERT');
        }""", retries=1)
        if not is_ssl:
            return False

        # Click "Advanced" button
        advanced = page.locator('#details-button')
        if await advanced.count() > 0:
            await advanced.click()
            await asyncio.sleep(0.5)

        # Click "Proceed to ..."
        proceed = page.locator('#proceed-link')
        if await proceed.count() > 0:
            await proceed.click()
            await asyncio.sleep(2)
            return True
    except:
        pass
    return False
```

### Integration
```python
await page.goto(URL, wait_until='domcontentloaded', timeout=60000)
await asyncio.sleep(2)
await handle_ssl_warning(page)  # bypass SSL if needed
# ... continue with normal flow
```

## Fix 3: WAF "Request Rejected" handler
Datacenter IPs (DataImpulse, etc.) sometimes trigger WAF:
"The request was rejected because it was considered high risk"

```python
async def handle_rejected(page, url, max_retries=3):
    for attempt in range(max_retries):
        is_rejected = await safe_eval(page, """() => {
            return document.body.innerText.includes('request was rejected')
                || document.body.innerText.includes('considered high risk');
        }""", retries=1)
        if not is_rejected:
            return True
        await asyncio.sleep(3)
        await page.reload(wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(3)
        await handle_ssl_warning(page)  # SSL may appear after reload
    return False
```

## Integration order in worker
```python
await page.goto(URL, wait_until='domcontentloaded', timeout=60000)
await asyncio.sleep(2)
await handle_ssl_warning(page)     # SSL bypass
await handle_rejected(page, URL)   # WAF bypass
# ... continue with normal flow
```

## Pitfalls
- `--ignore-certificate-errors` only works in headed mode for some Playwright versions
- SSL warning page uses Chrome's internal IDs (`#details-button`, `#proceed-link`), not page DOM — these are part of Chrome's interstitial page, not the website
- After clicking Proceed, the page may redirect or reload — add `await asyncio.sleep(2)` before continuing
- WAF retry loop should have a max to avoid infinite refresh storms
