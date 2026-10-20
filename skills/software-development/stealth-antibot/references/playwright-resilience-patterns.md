# Playwright Resilience Patterns

Patterns for keeping Playwright workers alive through SSL errors, WAF blocks, and slow-loading pages. From multi-account automation sessions (Jul 2026).

## 1. WAF "Request Rejected" Auto-Retry

When a WAF blocks the request with "request was rejected because it was considered high risk", don't close the worker — refresh and retry.

```python
async def handle_waf_rejected(page, url, max_retries=3):
    """If WAF rejects request, refresh and retry."""
    for attempt in range(max_retries):
        try:
            is_rejected = await safe_eval(page, """() => {
                return document.body.innerText.includes('request was rejected')
                    || document.body.innerText.includes('considered high risk');
            }""", retries=1)
            if not is_rejected:
                return True

            log(0, f"WAF rejected (attempt {attempt+1}/{max_retries}), refreshing...")
            await asyncio.sleep(3)
            await page.reload(wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
            await handle_ssl_warning(page)
        except:
            break
    return False
```

**Pitfall:** DataImpulse (`__cr.id` username suffix) routes through datacenter IPs and triggers WAF. Use SOCKS5 on a VPS in the target region instead.

## 2. SSL Retry Loop (Don't Give Up After First Attempt)

When the page is slow to load or SSL warning keeps reappearing, retry up to N times with reload instead of closing the worker immediately.

```python
# After page.goto(URL):
for attempt in range(5):  # max 5 attempts
    r18_ready = await poll_until(page, """() => {
        const e = document.querySelector('.r18-entry');
        return e && e.offsetParent !== null;
    }""", timeout_s=20)

    if r18_ready:
        break

    log(worker_id, f"Not loaded (attempt {attempt+1}/5), retrying...")
    await handle_ssl_warning(page)
    try:
        await page.reload(wait_until='domcontentloaded', timeout=30000)
    except:
        pass
    await asyncio.sleep(3)
    await handle_ssl_warning(page)

if not r18_ready:
    log(worker_id, "Gave up after 5 attempts")
    return {'status': 'not-loaded'}
```

**User preference:** Workers should NOT close immediately on SSL errors or slow loads. Always retry with reload before giving up. "jangan langsung di close worker" — keep workers alive through transient errors.

## 3. Country Code Detection + Auto-Switch

For mobile-optimized sites that show a country code selector (VN+84, ID+62, etc.), detect and switch to the correct country code before filling forms.

```python
async def fix_country_code(page, target_country='ID', target_code='+62'):
    """Detect country code selector, switch to target if wrong."""
    for attempt in range(8):
        country = await safe_eval(page, """() => {
            const allEls = document.querySelectorAll('span, div, button, a');
            for (const el of allEls) {
                if (el.offsetParent === null) continue;
                const txt = (el.innerText || '').trim();
                if (/^[A-Z]{2}\\+\\d{1,3}$/.test(txt)) return txt;
                if (/\\+\\d{1,3}$/.test(txt) && txt.length < 15) return txt;
            }
            return 'not-found';
        }""")
        country = (country or '').upper()

        if target_country in country or target_code in country:
            return True  # Already correct

        # VN+84: refresh + redo flow (selector often broken)
        if 'VN' in country or '+84' in country:
            await page.reload(wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
            await handle_ssl_warning(page)
            continue

        # Other country: click selector, pick target
        clicked = await safe_eval(page, """() => {
            const allEls = document.querySelectorAll('span, div, button, a');
            for (const el of allEls) {
                if (el.offsetParent === null) continue;
                const txt = (el.innerText || '').trim();
                if (/\\+\\d{1,3}$/.test(txt) && txt.length < 15) {
                    el.click();
                    if (el.parentElement) el.parentElement.click();
                    return true;
                }
            }
            return false;
        }""")
        await asyncio.sleep(2)

        if clicked:
            await safe_eval(page, """() => {
                const allEls = document.querySelectorAll(
                    'div, li, span, a, button, .van-picker-column__item, ' +
                    '.van-cell, .van-list, [class*="country"], [class*="picker"]'
                );
                for (const el of allEls) {
                    if (el.offsetParent === null) continue;
                    const txt = ((el.innerText || '') + ' ' + (el.textContent || '')).toUpperCase();
                    if (txt.includes('INDONESIA') || txt.includes('+62')) {
                        el.click(); return true;
                    }
                }
                return false;
            }""")
            await asyncio.sleep(1)
            await safe_eval(page, """() => {
                const btns = document.querySelectorAll('button, .van-button');
                for (const b of btns) {
                    if (b.offsetParent === null) continue;
                    const txt = (b.innerText || '').trim().toLowerCase();
                    if (txt === 'ok' || txt === 'confirm' || txt === 'konfirmasi') {
                        b.click(); return true;
                    }
                }
                return false;
            }""")
            await asyncio.sleep(1)
    return False
```

**Pitfall:** VN+84 (Vietnam) country code often can't be clicked directly — must refresh page and redo the flow from scratch.

## 4. Domain Speed Testing

Find the fastest mirror of a multi-domain site:

```bash
#!/bin/bash
for domain in example-targetff.com example-targetgg.com example-targethh.com; do
    result=$(curl -sL --max-time 5 --connect-timeout 3 \
        -o /dev/null -w "%{time_total} %{http_code}" \
        "https://${domain}" 2>/dev/null)
    time_s=$(echo "$result" | awk '{print $1}')
    code=$(echo "$result" | awk '{print $2}')
    if [[ "$code" == "200" || "$code" == "301" || "$code" == "302" ]]; then
        echo "${domain} ${time_s} ${code}"
    fi
done | sort -t' ' -k2 -n
```

Speed categories: <0.15s excellent, <0.3s good, <1s acceptable, >1s slow.

## 5. Complete Resilient Worker Template

Full worker flow combining all resilience patterns:

```python
async def resilient_worker(worker_id, url, phone):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--ignore-certificate-errors',
                '--ignore-certificate-errors-spki-list',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
            ],
        )
        context = await browser.new_context(proxy=PROXY, **DEVICE)
        await context.add_init_script(STEALTH_JS)
        page = await context.new_page()

        # Step 1: Open + handle SSL/WAF
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(2)
        await handle_ssl_warning(page)
        await handle_waf_rejected(page, url)

        # Step 2: Wait for page with retry loop (up to 5 attempts)
        for attempt in range(5):
            ready = await poll_until(page, "() => document.querySelector('.target-element')")
            if ready:
                break
            await handle_ssl_warning(page)
            await page.reload(wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(3)
            await handle_ssl_warning(page)

        if not ready:
            return {'status': 'failed'}

        # Step 3: Fix country code if needed
        await fix_country_code(page)

        # ... rest of flow ...
```
