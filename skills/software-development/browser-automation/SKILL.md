---
name: browser-automation
description: "Browser automation powers web testing, scraping, and AI agent interactions. Covers Playwright patterns, multi-worker parallel execution, anti-detection, cookie management, and production-grade bot scripting."
risk: unknown
source: vibeship-spawner-skills (Apache 2.0)
date_added: 2026-02-27
embedding_hint: "playwright multi-worker parallel browser automation mass account login registration thread pool concurrent"
embedding_hint: "playwright puppeteer browser automation multi-worker parallel threadpool turnstile cloudflare anti-detect stealth"
embedding_hint: "playwright puppeteer multi-worker parallel browser automation turnstile cloudflare anti-detect stealth headless scraping"
embedding_hint: "browser automation playwright puppeteer parallel multi-worker threading mass account login claim captcha"
---

# Browser Automation

Browser automation powers web testing, scraping, and AI agent interactions.
The difference between a flaky script and a reliable system comes down to
understanding selectors, waiting strategies, and anti-detection patterns.

This skill covers Playwright (recommended) and Puppeteer, with patterns for
testing, scraping, and agentic browser control. Key insight: Playwright won
the framework war. Unless you need Puppeteer's stealth ecosystem or are
Chrome-only, Playwright is the better choice in 2025.

Critical distinction: Testing automation (predictable apps you control) vs
scraping/agent automation (unpredictable sites that fight back). Different
problems, different solutions.

## Principles

- Use user-facing locators (getByRole, getByText) over CSS/XPath
- Never add manual waits - Playwright's auto-wait handles it
- Each test/task should be fully isolated with fresh context
- Screenshots and traces are your debugging lifeline
- Headless for CI, headed for debugging
- Anti-detection is cat-and-mouse - stay current or get blocked

## Multi-Worker Pattern (Single Terminal)

User preference: ALWAYS use single-command multi-worker (ThreadPoolExecutor), NEVER ask user to open multiple terminals.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
import threading

print_lock = threading.Lock()

def worker(worker_id, emails):
    """Each worker gets its own Playwright instance."""
    with sync_playwright() as p:
        for email in emails:
            browser = p.chromium.launch(headless=False, args=[...])
            context = browser.new_context(...)
            page = context.new_page()
            # ... do work ...
            browser.close()  # or keep open if user claims manual

def main():
    chunks = split_list(remaining, num_workers)
    with ThreadPoolExecutor(max_workers=num_workers) as pool:
        futures = {pool.submit(worker, i+1, chunk): i for i, chunk in enumerate(chunks)}
        for f in as_completed(futures):
            results = f.result()
```

### Keep Browser Open Pattern
When user needs to interact manually after automation:
- Use `sync_playwright().start()` (not context manager) so it doesn't auto-close
- Track open browsers in a global list to prevent GC
- Keep script alive with `while True: time.sleep(60)` + KeyboardInterrupt handler
- Process in batches with `input("Press ENTER for next batch...")` between them

### Multi-Worker Parallel Browser Pattern

When running N browser instances in parallel from 1 terminal (e.g., mass account operations):

```python
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

def worker(email):
    """Each worker gets its own Playwright instance."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome",
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        context = browser.new_context(...)
        # Remove webdriver flag for anti-detection
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        page = context.new_page()
        # ... do work ...
        browser.close()

# Run N parallel
with ThreadPoolExecutor(max_workers=N) as pool:
    futures = {pool.submit(worker, email): email for email in accounts}
    for f in as_completed(futures):
        result = f.result()
```

Key points:
- Each thread needs its OWN `sync_playwright()` instance — cannot share across threads
- Use `channel="chrome"` for real Chrome (better anti-detection than Chromium)
- Fresh browser per account (reusing context drops success rate ~50%)
- Thread-safe logging with `threading.Lock()`
- Thread-safe file writes with separate lock

### Browser-stays-open pattern
When you need browsers to remain open (manual user interaction after automation):
- Don't use `with sync_playwright()` context manager — call `.start()` manually
- Store `(browser, pw_instance)` in a list to prevent GC
- Keep main script alive with `while True: time.sleep(60)` + KeyboardInterrupt handler
- Process accounts in batches with `input("Press ENTER for next batch...")`

## Cloudflare Turnstile Behavior

- **Datacenter IPs**: Turnstile silently refuses to render (no iframe, no error). Widget div stays empty.
- **Residential IPs**: Renders normally, auto-solves with single click.
- **Captcha solver tokens** (sctg.xyz, 2captcha): Server-side Turnstile verification binds token to solver's IP. If claim request comes from different IP → "Token verification failed or expired".
- **Conclusion**: For Turnstile-gated actions, the solve AND the action must originate from the same residential IP. Solver services don't work unless the target server skips IP validation (rare).

Workaround for mass operations:
1. Login headless (works from any IP) → save cookies
2. Claim from user's PC (residential) with saved cookies — browser renders Turnstile natively

## Worker Resilience Pattern (Don't Close on First Failure)

When a page fails to load (SSL error, slow network, WAF block), do NOT immediately close the worker.
Instead, retry with handler + reload loop before giving up. This prevents losing workers to transient issues.

```python
# BAD: Close immediately on failure
r18_ready = await poll_until(page, "...", timeout_s=25)
if not r18_ready:
    return {'status': 'r18-not-rendered'}  # Worker dead

# GOOD: Retry loop with handler + reload
r18_ready = False
for attempt in range(5):  # Max 5 retries
    r18_ready = await poll_until(page, "...", timeout_s=20)
    if r18_ready:
        break

    log(f"⚠️ Not found (attempt {attempt+1}/5), retrying...")
    await handle_ssl_warning(page)  # SSL bypass if needed
    try:
        await page.reload(wait_until='domcontentloaded', timeout=30000)
    except:
        pass
    await asyncio.sleep(3)
    await handle_ssl_warning(page)

if not r18_ready:
    return {'status': 'gave-up-after-5-attempts'}
```

**Key insight:** User explicitly said "website lemot ga masuk2 juga jangan auto ke close" (if the website is slow and won't load, don't auto-close). Workers cost time to launch — a 2-minute retry loop is cheaper than re-launching from scratch.

**When to use this pattern:**
- SSL certificate warnings (site uses domain rotation)
- WAF/bot detection blocking (retry may succeed on different IP)
- Slow network / proxy latency (page loads eventually)
- Cloudflare challenges (may pass on retry)

**Adjust retry count based on context:**
- SSL errors: 5 retries (~2 min)
- WAF blocks: 3 retries (~1 min)
- Slow loading: 3 retries (~1 min)

## Proxy Auth with Playwright

### SOCKS5 Proxy (no auth required)

Simplest setup — works without credentials. Ideal for private SSH/VPN SOCKS5 tunnels:

```python
proxy = {'server': 'socks5://43.159.56.39:5858'}

browser = await p.chromium.launch(
    proxy=proxy,
    headless=False,
    args=CHROMIUM_ARGS,
)
```

**When to use SOCKS5:**
- You have a VPS-based SSH tunnel or SOCKS5 forwarder
- Provider gives SOCKS5 endpoints (e.g., Webshare, IPRoyal SOCKS5)
- No authentication needed — Chromium handles SOCKS5 natively

**Pitfall:** SOCKS5 does NOT proxy DNS by default with all Chromium builds. For DNS-through-proxy enforcement, combine with `--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE <proxy_ip>` launch arg.

### HTTP Proxy with Auth (DataImpulse, BrightData, etc.)

When using Playwright with **authenticated HTTP proxies** (DataImpulse, BrightData, etc.), Chromium often throws `ERR_PROXY_AUTH_UNSUPPORTED`.

**First fix:** Use `http://` scheme, NEVER `https://` — residential proxies are HTTP, not HTTPS:
```python
# WRONG - causes ERR_PROXY_AUTH_UNSUPPORTED
proxy = {'server': 'https://gw.dataimpulse.com:823', 'username': '...', 'password': '...'}

# RIGHT - works in some Chromium versions
proxy = {'server': 'http://gw.dataimpulse.com:823', 'username': '...', 'password': '...'}
```

**Definitive fix when scheme change doesn't work:** Run a local auth relay proxy (`scripts/relay_proxy.py`) that handles upstream authentication so Chrome connects to a proxy without credentials. See `references/playwright-proxy-auth-relay.md`.

**Note:** CloakBrowser (anti-detection Chromium fork) handles proxy auth natively — no relay required. See `references/cloakbrowser-setup.md` and the CloakBrowser section below.

**IP rotation:** If websites start blacklisting after repeated use, switch DataImpulse upstream port from `823` (sticky IP) → `824` (rotating IP, changes per request). Change `UPSTREAM_PORT` in `relay_proxy.py`. The relay handles rotation transparently — no script changes needed.

**IP rotation:** If websites start blacklisting after repeated use, switch DataImpulse upstream port from `823` (sticky IP) → `824` (rotating IP, changes per request). Change `UPSTREAM_PORT` in `relay_proxy.py`. The relay handles rotation transparently — no script changes needed.

## CloakBrowser with Playwright (executable_path)

When CloakBrowser is installed via npm/npx (standalone binary, not the Python `cloakbrowser` package), the binary lives at:
```
~/.cloakbrowser/chromium-<version>/chrome        (Linux)
C:\Users\<user>\.cloakbrowser\chromium-<version>\chrome.exe  (Windows)
```

**Key advantage over bundled Chromium:** CloakBrowser handles proxy auth (Basic, Digest) natively — no `ERR_PROXY_AUTH_UNSUPPORTED`. No relay proxy needed.

### Domain Rotation Pattern

When a website has multiple mirror domains (e.g., `example-target.com`, `example-targetff.com`, `example-targetii.com`), rotate across them to distribute requests and avoid domain-level rate limiting:

```python
# Config
DOMAINS = [
    'https://example-target.com',
    'https://example-targetff.com',
    'https://example-targetii.com',
    'https://example-targetkk.com',
]

# Pick random domain per worker (inside worker function)
import random as _r
domain_url = _r.choice(DOMAINS)

# Before navigating:
await page.goto(domain_url, ...)
```

**When to rotate:** If all workers hit the same domain, the website can pattern-detect them as a batch. Randomizing per worker breaks that signal.

**Pitfalls:**
- Test each mirror first (not all may be functional)
- Some mirrors may have slightly different UI/selectors
- SSL warnings common on mirrors — handle with retry loop

### Usage
```python
CLOAK_PATH = r"C:\Users\User\.cloakbrowser\chromium-146.0.7680.177.5\chrome.exe"

browser = await p.chromium.launch(
    executable_path=CLOAK_PATH,
    headless=False,
    args=[f'--window-position={x},{y}', f'--window-size={w},{h}'],
    proxy={'server': 'http://gw.dataimpulse.com:824', 'username': 'user', 'password': 'pass'},
)
context = await browser.new_context(...)
```

### Finding the binary
Check `~/.cloakbrowser/chromium-*/` directory. The version folder is auto-named (e.g. `chromium-146.0.7680.177.5`). Run `cloakbrowser info` or `dir ~/.cloakbrowser` to find it.

### Pitfalls
- Don't set both `executable_path` and `channel='chrome'` — they conflict
- Binary is ~200-300MB; multiple versions accumulate
- On Windows, use raw strings `r"C:\..."` or double backslashes
- Version directory changes on update — scripts need periodic path checks

## Pitfalls
1. **ThreadPoolExecutor + browser open** — if browser stays open, worker thread never returns. Use `threading.Thread` directly instead of ThreadPoolExecutor for keep-open flows.
2. **sync_playwright per thread** — each thread needs its own Playwright instance. Don't share across threads.
3. **Port conflicts** — stagger browser launches with `time.sleep(0.5)` between threads.
4. **RAM** — each Chromium ~300-500MB. 15 workers = 5-8GB. Warn user about limits.
5. **Don't close workers on transient failures** — SSL warnings, slow loads, and WAF blocks are often temporary. Always retry with handler + reload before giving up. User correction: "jangan auto ke close" (don't auto-close).

## Capabilities

- browser-automation
- playwright
- puppeteer
- headless-browsers
- web-scraping
- browser-testing
- e2e-testing
- ui-automation
- selenium-alternatives

## Scope

- api-testing → backend
- load-testing → performance-thinker
- accessibility-testing → accessibility-specialist
- visual-regression-testing → ui-design

## Tooling

### Frameworks

- Playwright - When: Default choice - cross-browser, auto-waiting, best DX Note: 96% success rate, 4.5s avg execution, Microsoft-backed
- Puppeteer - When: Chrome-only, need stealth plugins, existing codebase Note: 75% success rate at scale, but best stealth ecosystem
- Selenium - When: Legacy systems, specific language bindings Note: Slower, more verbose, but widest browser support

### Stealth_tools

- puppeteer-extra-plugin-stealth - When: Need to bypass bot detection with Puppeteer Note: Gold standard for anti-detection
- playwright-extra - When: Stealth plugins for Playwright Note: Port of puppeteer-extra ecosystem
- undetected-chromedriver - When: Selenium anti-detection Note: Dynamic bypass of detection

### Cloud_browsers

- Browserbase - When: Managed headless infrastructure Note: Built-in stealth mode, session management
- BrowserStack - When: Cross-browser testing at scale Note: Real devices, CI integration

## Patterns

### Test Isolation Pattern

Each test runs in complete isolation with fresh state

**When to use**: Testing, any automation that needs reproducibility

# TEST ISOLATION:

"""
Each test gets its own:
- Browser context (cookies, storage)
- Fresh page
- Clean state
"""

## Playwright Test Example
"""
import { test, expect } from '@playwright/test';

// Each test runs in isolated browser context
test('user can add item to cart', async ({ page }) => {
  // Fresh context - no cookies, no storage from other tests
  await page.goto('/products');
  await page.getByRole('button', { name: 'Add to Cart' }).click();
  await expect(page.getByTestId('cart-count')).toHaveText('1');
});

test('user can remove item from cart', async ({ page }) => {
  // Completely isolated - cart is empty
  await page.goto('/cart');
  await expect(page.getByText('Your cart is empty')).toBeVisible();
});
"""

## Shared Authentication Pattern
"""
// Save auth state once, reuse across tests
// setup.ts
import { test as setup } from '@playwright/test';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Sign in' }).click();

  // Wait for auth to complete
  await page.waitForURL('/dashboard');

  // Save authentication state
  await page.context().storageState({
    path: './playwright/.auth/user.json'
  });
});

// playwright.config.ts
export default defineConfig({
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    {
      name: 'tests',
      dependencies: ['setup'],
      use: {
        storageState: './playwright/.auth/user.json',
      },
    },
  ],
});
"""

### User-Facing Locator Pattern

Select elements the way users see them

**When to use**: Always - the default approach for selectors

# USER-FACING LOCATORS:

"""
Priority order:
1. getByRole  - Best: matches accessibility tree
2. getByText  - Good: matches visible content
3. getByLabel - Good: matches form labels
4. getByTestId - Fallback: explicit test contracts
5. CSS/XPath - Last resort: fragile, avoid
"""

## Good Examples (User-Facing)
"""
// By role - THE BEST CHOICE
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByRole('link', { name: 'Sign up' }).click();
await page.getByRole('heading', { name: 'Dashboard' }).isVisible();
await page.getByRole('textbox', { name: 'Search' }).fill('query');

// By text content
await page.getByText('Welcome back').isVisible();
await page.getByText(/Order #\d+/).click();  // Regex supported

// By label (forms)
await page.getByLabel('Email address').fill('user@example.com');
await page.getByLabel('Password').fill('secret');

// By placeholder
await page.getByPlaceholder('Search...').fill('query');

// By test ID (when no user-facing option works)
await page.getByTestId('submit-button').click();
"""

## Bad Examples (Fragile)
"""
// DON'T - CSS selectors tied to structure
await page.locator('.btn-primary.submit-form').click();
await page.locator('#header > div > button:nth-child(2)').click();

// DON'T - XPath tied to structure
await page.locator('//div[@class="form"]/button[1]').click();

// DON'T - Auto-generated selectors
await page.locator('[data-v-12345]').click();
"""

## Filtering and Chaining
"""
// Filter by containing text
await page.getByRole('listitem')
  .filter({ hasText: 'Product A' })
  .getByRole('button', { name: 'Add to cart' })
  .click();

// Filter by NOT containing
await page.getByRole('listitem')
  .filter({ hasNotText: 'Sold out' })
  .first()
  .click();

// Chain locators
const row = page.getByRole('row', { name: 'John Doe' });
await row.getByRole('button', { name: 'Edit' }).click();
"""

### Auto-Wait Pattern

Let Playwright wait automatically, never add manual waits

**When to use**: Always with Playwright

# AUTO-WAIT PATTERN:

"""
Playwright waits automatically for:
- Element to be attached to DOM
- Element to be visible
- Element to be stable (not animating)
- Element to receive events
- Element to be enabled

NEVER add manual waits!
"""

## Wrong - Manual Waits
"""
// DON'T DO THIS
await page.goto('/dashboard');
await page.waitForTimeout(2000);  // NO! Arbitrary wait
await page.click('.submit-button');

// DON'T DO THIS
await page.waitForSelector('.loading-spinner', { state: 'hidden' });
await page.waitForTimeout(500);  // "Just to be safe" - NO!
"""

## Correct - Let Auto-Wait Work
"""
// Auto-waits for button to be clickable
await page.getByRole('button', { name: 'Submit' }).click();

// Auto-waits for text to appear
await expect(page.getByText('Success!')).toBeVisible();

// Auto-waits for navigation to complete
await page.goto('/dashboard');
// Page is ready - no manual wait needed
"""

## When You DO Need to Wait
"""
// Wait for specific network request
const responsePromise = page.waitForResponse(
  response => response.url().includes('/api/data')
);
await page.getByRole('button', { name: 'Load' }).click();
const response = await responsePromise;

// Wait for URL change
await Promise.all([
  page.waitForURL('**/dashboard'),
  page.getByRole('button', { name: 'Login' }).click(),
]);

// Wait for download
const downloadPromise = page.waitForEvent('download');
await page.getByText('Export CSV').click();
const download = await downloadPromise;
"""

### Stealth Browser Pattern

Avoid bot detection for scraping

**When to use**: Scraping sites with anti-bot protection

# STEALTH BROWSER PATTERN:

"""
Bot detection checks for:
- navigator.webdriver property
- Chrome DevTools protocol artifacts
- Browser fingerprint inconsistencies
- Behavioral patterns (perfect timing, no mouse movement)
- Headless indicators
"""

## Puppeteer Stealth (Best Anti-Detection)
"""
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());

const browser = await puppeteer.launch({
  headless: 'new',
  args: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-blink-features=AutomationControlled',
  ],
});

const page = await browser.newPage();

// Set realistic viewport
await page.setViewport({ width: 1920, height: 1080 });

// Realistic user agent
await page.setUserAgent(
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
);

// Navigate with human-like behavior
await page.goto('https://target-site.com', {
  waitUntil: 'networkidle0',
});
"""

## Playwright Stealth
```python
import { chromium } from 'playwright-extra';
import stealth from 'puppeteer-extra-plugin-stealth';

chromium.use(stealth());

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  userAgent: 'Mozilla/5.0 ...',
  locale: 'en-US',
  timezoneId: 'America/New_York',
});
```

### Key Stealth Patches (add_init_script)

When using `context.add_init_script()` or `page.add_init_script()`, ensure these critical patches are included (many sites check them):

```python
STEALTH_JS = """
// 1. navigator.webdriver — most common detection
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
delete navigator.__proto__.webdriver;
delete Navigator.prototype.webdriver;

// 2. pdfViewerEnabled — Playwright returns false, real Chrome returns true
Object.defineProperty(navigator, 'pdfViewerEnabled', {get: () => true});

// 3. Hardware fingerprint
Object.defineProperty(navigator, 'deviceMemory', {get: () => 4});
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});

// 4. Platform
Object.defineProperty(navigator, 'platform', {get: () => 'Linux armv81'});
Object.defineProperty(navigator, 'vendor', {get: () => 'Google Inc.'});

// 5. Languages
Object.defineProperty(navigator, 'languages', {get: () => ['id-ID', 'id', 'en-US', 'en']});

// 6. Chrome runtime
if (!window.chrome) window.chrome = {};
if (!window.chrome.runtime) window.chrome.runtime = {id:'', connect:()=>null, sendMessage:()=>null};

// 7. Screen
Object.defineProperty(screen, 'availWidth', {get: () => 412});
Object.defineProperty(screen, 'availHeight', {get: () => 915});
Object.defineProperty(screen, 'colorDepth', {get: () => 24});

// 8. Touch support
Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 10});

// 9. App version
Object.defineProperty(navigator, 'appVersion', {get: () => '5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'});

// 10. Connection API (spoof Indonesian 4G)
if (!navigator.connection) Object.defineProperty(navigator, 'connection', {get: () => ({effectiveType:'4g', rtt:50, downlink:10, saveData:false, type:'cellular', addEventListener:()=>{}, removeEventListener:()=>{}})});

// 11. Battery API
if (navigator.getBattery) navigator.getBattery = () => Promise.resolve({charging:true, chargingTime:0, dischargingTime:Infinity, level:0.87, addEventListener:()=>{}, removeEventListener:()=>{}, dispatchEvent:()=>true});
"""
await page.add_init_script(STEALTH_JS)
```

**Critical:** `pdfViewerEnabled` is one of the most common new detections — Playwright sets it to `false` while real Chrome sets it to `true`. Always patch this in init scripts.

## Human-Like Behavior
"""
// Random delays between actions
const randomDelay = (min: number, max: number) =>
  new Promise(r => setTimeout(r, Math.random() * (max - min) + min));

await page.goto(url);
await randomDelay(500, 1500);

// Mouse movement before click
const button = await page.$('button.submit');
const box = await button.boundingBox();
await page.mouse.move(
  box.x + box.width / 2,
  box.y + box.height / 2,
  { steps: 10 }  // Move in steps like a human
);
await randomDelay(100, 300);
await button.click();

// Scroll naturally
await page.evaluate(() => {
  window.scrollBy({
    top: 300 + Math.random() * 200,
    behavior: 'smooth'
  });
});
"""

### Error Recovery Pattern

Handle failures gracefully with screenshots and retries

**When to use**: Any production automation

# ERROR RECOVERY PATTERN:

## Automatic Screenshot on Failure
"""
// playwright.config.ts
export default defineConfig({
  use: {
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  retries: 2,  // Retry failed tests
});
"""

## Try-Catch with Debug Info
"""
async function scrapeProduct(page: Page, url: string) {
  try {
    await page.goto(url, { timeout: 30000 });

    const title = await page.getByRole('heading', { level: 1 }).textContent();
    const price = await page.getByTestId('price').textContent();

    return { title, price, success: true };

  } catch (error) {
    // Capture debug info
    const screenshot = await page.screenshot({
      path: `errors/${Date.now()}-error.png`,
      fullPage: true
    });

    const html = await page.content();
    await fs.writeFile(`errors/${Date.now()}-page.html`, html);

    console.error({
      url,
      error: error.message,
      currentUrl: page.url(),
    });

    return { success: false, error: error.message };
  }
}
"""

## Retry with Exponential Backoff
"""
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> {
  let lastError: Error;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (attempt < maxRetries - 1) {
        const delay = baseDelay * Math.pow(2, attempt);
        const jitter = delay * 0.1 * Math.random();
        await new Promise(r => setTimeout(r, delay + jitter));
      }
    }
  }

  throw lastError;
}

// Usage
const result = await withRetry(
  () => scrapeProduct(page, url),
  3,
  2000
);
"""

### Parallel Execution Pattern

Run tests/tasks in parallel for speed

**When to use**: Multiple independent pages or tests

# PARALLEL EXECUTION:

## Playwright Test Parallelization
"""
// playwright.config.ts
export default defineConfig({
  fullyParallel: true,
  workers: process.env.CI ? 4 : undefined,  // CI: 4 workers, local: CPU-based

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
});
"""

## Browser Contexts for Parallel Scraping
"""
const browser = await chromium.launch();

const urls = ['url1', 'url2', 'url3', 'url4', 'url5'];

// Create multiple contexts - each is isolated
const results = await Promise.all(
  urls.map(async (url) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    try {
      await page.goto(url);
      const data = await extractData(page);
      return { url, data, success: true };
    } catch (error) {
      return { url, error: error.message, success: false };
    } finally {
      await context.close();
    }
  })
);

await browser.close();
"""

## Rate-Limited Parallel Processing
"""
import pLimit from 'p-limit';

const limit = pLimit(5);  // Max 5 concurrent

const results = await Promise.all(
  urls.map(url => limit(async () => {
    const context = await browser.newContext();
    const page = await context.newPage();

    // Random delay between requests
    await new Promise(r => setTimeout(r, Math.random() * 2000));

    try {
      return await scrapePage(page, url);
    } finally {
      await context.close();
    }
  }))
);
"""

### Network Interception Pattern

Mock, block, or modify network requests

**When to use**: Testing, blocking ads/analytics, modifying responses

# NETWORK INTERCEPTION:

## Block Unnecessary Resources
"""
await page.route('**/*', (route) => {
  const url = route.request().url();
  const resourceType = route.request().resourceType();

  // Block images, fonts, analytics for faster scraping
  if (['image', 'font', 'media'].includes(resourceType)) {
    return route.abort();
  }

  // Block tracking/analytics
  if (url.includes('google-analytics') ||
      url.includes('facebook.com/tr')) {
    return route.abort();
  }

  return route.continue();
});
"""

## Mock API Responses (Testing)
"""
await page.route('**/api/products', async (route) => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([
      { id: 1, name: 'Mock Product', price: 99.99 },
    ]),
  });
});

// Now page will receive mocked data
await page.goto('/products');
"""

## Capture API Responses
"""
const apiResponses: any[] = [];

page.on('response', async (response) => {
  if (response.url().includes('/api/')) {
    const data = await response.json().catch(() => null);
    apiResponses.push({
      url: response.url(),
      status: response.status(),
      data,
    });
  }
});

await page.goto('/dashboard');
// apiResponses now contains all API calls
"""

## Sharp Edges

### Using waitForTimeout Instead of Proper Waits

Severity: CRITICAL

Situation: Waiting for elements or page state

Symptoms:
Tests pass locally, fail in CI. Pass 9 times, fail on the 10th.
"Element not found" errors that seem random. Tests take 30+ seconds
when they should take 3.

Why this breaks:
waitForTimeout is a fixed delay. If the page loads in 500ms, you wait
2000ms anyway. If the page takes 2100ms (CI is slower), you fail.
There's no correct value - it's always either too short or too long.

Recommended fix:

# REMOVE all waitForTimeout calls

# WRONG:
await page.goto('/dashboard');
await page.waitForTimeout(2000);  # Arbitrary!
await page.click('.submit');

# CORRECT - Auto-wait handles it:
await page.goto('/dashboard');
await page.getByRole('button', { name: 'Submit' }).click();

# If you need to wait for specific condition:
await expect(page.getByText('Dashboard')).toBeVisible();
await page.waitForURL('**/dashboard');
await page.waitForResponse(resp => resp.url().includes('/api/data'));

# For animations, wait for element to be stable:
await page.getByRole('button').click();  # Auto-waits for stable

# NEVER use setTimeout or waitForTimeout in production code

### CSS Selectors Tied to Styling Classes

Severity: HIGH

Situation: Selecting elements for interaction

Symptoms:
Tests break after CSS refactoring. Selectors like .btn-primary stop
working. Frontend redesign breaks all tests without changing behavior.

Why this breaks:
CSS class names are implementation details for styling, not semantic
meaning. When designers change from .btn-primary to .button--primary,
your tests break even though behavior is identical.

Recommended fix:

# Use user-facing locators instead:

# WRONG - Tied to CSS:
await page.locator('.btn-primary.submit-form').click();
await page.locator('#sidebar > div.menu > ul > li:nth-child(3)').click();

# CORRECT - User-facing:
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByRole('menuitem', { name: 'Settings' }).click();

# If you must use CSS, use data-testid:
<button data-testid="submit-order">Submit</button>

await page.getByTestId('submit-order').click();

# Locator priority:
# 1. getByRole - matches accessibility
# 2. getByText - matches visible content
# 3. getByLabel - matches form labels
# 4. getByTestId - explicit test contract
# 5. CSS/XPath - last resort only

### navigator.webdriver Exposes Automation

Severity: HIGH

Situation: Scraping sites with bot detection

Symptoms:
Immediate 403 errors. CAPTCHA challenges. Empty pages. "Access Denied"
messages. Works for 1 request, then gets blocked.

Why this breaks:
By default, headless browsers set navigator.webdriver = true. This is
the first thing bot detection checks. It's a bright red flag that
says "I'm automated."

Recommended fix:

# Use stealth plugins:

### Puppeteer Stealth (best option):
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());

const browser = await puppeteer.launch({
  headless: 'new',
  args: ['--disable-blink-features=AutomationControlled'],
});

### Playwright Stealth:
import { chromium } from 'playwright-extra';
import stealth from 'puppeteer-extra-plugin-stealth';

chromium.use(stealth());

### Manual (partial):
await page.evaluateOnNewDocument(() => {
  Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
  });
});

# Note: This is cat-and-mouse. Detection evolves.
# For serious scraping, consider managed solutions like Browserbase.

### Tests Share State and Affect Each Other

Severity: HIGH

Situation: Running multiple tests in sequence

Symptoms:
Tests pass individually but fail when run together. Order matters -
test B fails if test A runs first. Random failures that "fix themselves"
on rerun.

Why this breaks:
Shared browser context means shared cookies, localStorage, and session
state. Test A logs in, test B expects logged-out state. Test A adds
item to cart, test B's cart count is wrong.

Recommended fix:

# Each test must be fully isolated:

### Playwright Test (automatic isolation):
test('first test', async ({ page }) => {
  // Fresh context, fresh page
});

test('second test', async ({ page }) => {
  // Completely isolated from first test
});

### Manual isolation:
const context = await browser.newContext();  // Fresh context
const page = await context.newPage();
// ... test code ...
await context.close();  // Clean up

## Shared authentication (the right way):
// 1. Save auth state to file
await context.storageState({ path: './auth.json' });

// 2. Reuse in other tests
const context = await browser.newContext({
  storageState: './auth.json'
});

# Never modify global state in tests
# Never rely on previous test's actions

### No Trace Capture for CI Failures

Severity: MEDIUM

Situation: Debugging test failures in CI

Symptoms:
"Test failed in CI" with no useful information. Can't reproduce
locally. Screenshot shows page but not what went wrong. Guessing
at root cause.

Why this breaks:
CI runs headless on different hardware. Timing is different. Network
is different. Without traces, you can't see what actually happened -
the sequence of actions, network requests, console logs.

Recommended fix:

# Enable traces for failures:

### playwright.config.ts:
export default defineConfig({
  use: {
    trace: 'retain-on-failure',    # Keep trace on failure
    screenshot: 'only-on-failure', # Screenshot on failure
    video: 'retain-on-failure',    # Video on failure
  },
  outputDir: './test-results',
});

### View trace locally:
npx playwright show-trace test-results/path/to/trace.zip

### In CI, upload test-results as artifact:
# GitHub Actions:
- uses: actions/upload-artifact@v3
  if: failure()
  with:
    name: playwright-traces
    path: test-results/

# Trace shows:
# - Timeline of actions
# - Screenshots at each step
# - Network requests and responses
# - Console logs
# - DOM snapshots

### Tests Pass Headed but Fail Headless

Severity: MEDIUM

Situation: Running tests in headless mode for CI

Symptoms:
Works perfectly when you watch it. Fails mysteriously in CI.
"Element not visible" in headless but visible in headed mode.

Why this breaks:
Headless browsers have no display, which affects some CSS (visibility
calculations), viewport sizing, and font rendering. Some animations
behave differently. Popup windows may not work.

Recommended fix:

# Set consistent viewport:
const browser = await chromium.launch({
  headless: true,
});

const context = await browser.newContext({
  viewport: { width: 1280, height: 720 },
});

# Or in config:
export default defineConfig({
  use: {
    viewport: { width: 1280, height: 720 },
  },
});

# Debug headless failures:
# 1. Run with headed mode locally
npx playwright test --headed

# 2. Slow down to watch
npx playwright test --headed --slowmo 100

# 3. Use trace viewer for CI failures
npx playwright show-trace trace.zip

# 4. For stubborn issues, screenshot at failure point:
await page.screenshot({ path: 'debug.png', fullPage: true });

### Getting Blocked by Rate Limiting

Severity: HIGH

Situation: Scraping multiple pages quickly

Symptoms:
Works for first 50 pages, then 429 errors. Suddenly all requests fail.
IP gets blocked. CAPTCHA starts appearing after successful requests.

Why this breaks:
Sites monitor request patterns. 100 requests per second from one IP
is obviously automated. Rate limits protect servers and catch scrapers.

Recommended fix:

# Add delays between requests:

const randomDelay = () =>
  new Promise(r => setTimeout(r, 1000 + Math.random() * 2000));

for (const url of urls) {
  await randomDelay();  // 1-3 second delay
  await page.goto(url);
  // ... scrape ...
}

# Use rotating proxies:
const proxies = ['http://proxy1:8080', 'http://proxy2:8080'];
let proxyIndex = 0;

const getNextProxy = () => proxies[proxyIndex++ % proxies.length];

const context = await browser.newContext({
  proxy: { server: getNextProxy() },
});

# Limit concurrent requests:
import pLimit from 'p-limit';
const limit = pLimit(3);  // Max 3 concurrent

await Promise.all(
  urls.map(url => limit(() => scrapePage(url)))
);

# Rotate user agents:
const userAgents = [
  'Mozilla/5.0 (Windows...',
  'Mozilla/5.0 (Macintosh...',
];

await page.setExtraHTTPHeaders({
  'User-Agent': userAgents[Math.floor(Math.random() * userAgents.length)]
});

### New Windows/Popups Not Handled

Severity: MEDIUM

Situation: Clicking links that open new windows

Symptoms:
Click button, nothing happens. Test hangs. "Window not found" errors.
Actions succeed but verification fails because you're on wrong page.

Why this breaks:
target="_blank" links open new windows. Your page reference still
points to the original page. The new window exists but you're not
listening for it.

Recommended fix:

# Wait for popup BEFORE triggering it:

### New window/tab:
const pagePromise = context.waitForEvent('page');
await page.getByRole('link', { name: 'Open in new tab' }).click();
const newPage = await pagePromise;
await newPage.waitForLoadState();

// Now interact with new page
await expect(newPage.getByRole('heading')).toBeVisible();

// Close when done
await newPage.close();

### Popup windows:
const popupPromise = page.waitForEvent('popup');
await page.getByRole('button', { name: 'Open popup' }).click();
const popup = await popupPromise;
await popup.waitForLoadState();

### Multiple windows:
const pages = context.pages();  // Get all open pages

### Can't Interact with Elements in iframes

Severity: MEDIUM

Situation: Page contains embedded iframes

Symptoms:
Element clearly visible but "not found". Selector works in DevTools
but not in Playwright. Parent page selectors work, iframe content
doesn't.

Why this breaks:
iframes are separate documents. page.locator only searches the main
frame. You need to explicitly get the iframe's frame to interact
with its contents.

Recommended fix:

# Get frame by name or selector:

### By frame name:
const frame = page.frame('payment-iframe');
await frame.getByRole('textbox', { name: 'Card number' }).fill('4242...');

## By selector:
const frame = page.frameLocator('iframe#payment');
await frame.getByRole('textbox', { name: 'Card number' }).fill('4242...');

### Nested iframes:
const outer = page.frameLocator('iframe#outer');
const inner = outer.frameLocator('iframe#inner');
await inner.getByRole('button').click();

### Wait for iframe to load:
await page.waitForSelector('iframe#payment');
const frame = page.frameLocator('iframe#payment');
await frame.getByText('Secure Payment').waitFor();

## Validation Checks

### Using waitForTimeout

Severity: ERROR

waitForTimeout causes flaky tests and slow execution

Message: Using waitForTimeout - remove it. Playwright auto-waits for elements. Use waitForResponse, waitForURL, or assertions instead.

### Using setTimeout in Test Code

Severity: WARNING

setTimeout is unreliable for timing in tests

Message: Using setTimeout instead of Playwright waits. Replace with await expect(...).toBeVisible() or page.waitFor*.

### Custom Sleep Function

Severity: WARNING

Sleep functions indicate improper waiting strategy

Message: Custom sleep function detected. Use Playwright's built-in waiting mechanisms instead.

### CSS Class Selector Used

Severity: WARNING

CSS class selectors are fragile

Message: Using CSS class selector. Prefer getByRole, getByText, getByLabel, or getByTestId for more stable selectors.

### nth-child CSS Selector

Severity: WARNING

Position-based selectors are very fragile

Message: Using position-based selector. These break when DOM order changes. Use user-facing locators instead.

### XPath Selector Used

Severity: INFO

XPath should be last resort

Message: Using XPath selector. Consider getByRole, getByText first. XPath should be last resort for complex DOM traversal.

### Auto-Generated Selector

Severity: WARNING

Framework-generated selectors are extremely fragile

Message: Using auto-generated selector. These change on every build. Use data-testid instead.

### Puppeteer Without Stealth Plugin

Severity: INFO

Scraping without stealth is easily detected

Message: Using Puppeteer without stealth plugin. Consider puppeteer-extra-plugin-stealth for anti-detection.

### navigator.webdriver Not Hidden

Severity: INFO

navigator.webdriver exposes automation

Message: Launching browser without hiding automation flags. For scraping, add stealth measures.

### Scraping Loop Without Error Handling

Severity: WARNING

One failure shouldn't crash entire scrape

Message: Scraping loop without try/catch. One page failure will crash the entire scrape. Add error handling.

## Solana Wallet Injection (DApp Automation)

For automating Solana DApps that require Phantom/Solflare wallet connection in headless browsers, see `references/solana-wallet-injection.md`. Covers: injecting mock `window.solana` provider, base58 key decoding in-browser, `signTransaction`/`signMessage` handling, and Pitfalls (page reload clears injection, auth challenges need real ed25519, etc).

## Cookie Injection

For session hijacking via stolen/extracted browser cookies, see `references/cookie-injection-workflow.md`. Covers: Chrome console injection, EditThisCookie extension, iOS bookmarklets, Playwright programmatic injection, Kiwi Browser (Android), and cookie sourcing.

## Camoufox vs Chromium

For converting between Camoufox (Firefox-based) and Playwright Chromium, see `references/camoufox-vs-chromium.md`. Covers: launch config conversion, Firefox prefs → Chromium args, window positioning, stealth JS injection, grid layout, and audio mute.

## Collaboration

### Delegation Triggers

- user needs full desktop control beyond browser -> computer-use-agents (Desktop automation for non-browser apps)
- user needs API testing alongside browser tests -> backend (API integration and testing patterns)
- user needs testing strategy -> test-architect (Overall test architecture decisions)
- user needs visual regression testing -> ui-design (Visual comparison and design validation)
- user needs browser automation in workflows -> workflow-automation (Durable execution for browser tasks)
- user building browser tools for agents -> agent-tool-builder (Tool design patterns for LLM agents)

## Related Skills

Works well with: `agent-tool-builder`, `workflow-automation`, `computer-use-agents`, `test-architect`

## Key Reference Files

- **example-target.com login flow:** `references/example-target-login-flow-2026.md` — full login + deposit automation
- **example-target.com registration:** `references/example-target-registration.md` — OTP registration, country code fix, "Unduh Aplikasi" popup handling
- **example-target.com domain rotation:** `references/example-target-domain-mirrors.md` — known working mirror domains and response times
- **Proxy toggle in-browser:** `references/proxy-toggle-in-browser.md` — floating button UX for proxy on/off
- **Mobile viewports (50):** `references/mobile-viewports-50.md` — randomized device profiles
- **Camoufox vs Chromium:** `references/camoufox-vs-chromium.md` — framework conversion guide
- **Anti-detection patterns:** `references/anti-detection-patterns.md`
- **Proxy debugging:** `references/proxy-debugging.md`
- **Proxy auth relay (ERR_PROXY_AUTH_UNSUPPORTED fix):** `references/playwright-proxy-auth-relay.md`
- **Multi-worker patterns:** `references/multi-worker-patterns.md`
- **Domain speed testing:** `references/domain-speed-testing.md` — test mirror domain response times

## When to Use
- User mentions or implies: playwright
- User mentions or implies: puppeteer
- User mentions or implies: browser automation
- User mentions or implies: headless
- User mentions or implies: web scraping
- User mentions or implies: e2e test
- User mentions or implies: end-to-end
- User mentions or implies: selenium
- User mentions or implies: chromium
- User mentions or implies: browser test
- User mentions or implies: page.click
- User mentions or implies: locator

### Multi-Worker Parallel Pattern (1 Terminal, N Browsers)

When user wants parallel browser automation from a single terminal (not multiple terminals):

```python
import threading
from playwright.sync_api import sync_playwright
import random

open_browsers = []  # Prevent GC from closing browsers

def worker(email, idx):
    """Each worker gets its OWN playwright instance + browser."""
    # Worker stagger: delay per worker so they don't all start simultaneously
    stagger = random.uniform(0.5, 4.0) * idx
    time.sleep(stagger)

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=False, args=[...])
    context = browser.new_context(...)
    page = context.new_page()
    # ... do work ...
    
    # Keep browser open: append to list, DON'T close
    open_browsers.append((browser, pw))

# Spawn N threads
threads = []
for i, email in enumerate(batch):
    t = threading.Thread(target=worker, args=(email, i))
    threads.append(t)
    t.start()
    time.sleep(0.5)  # Additional stagger to avoid port conflicts

for t in threads:
    t.join()

# Keep script alive (browsers stay open)
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    for b, pw in open_browsers:
        b.close(); pw.stop()
```

Key rules:
- Each thread needs its OWN `sync_playwright().start()` — can't share across threads
- Don't use `ThreadPoolExecutor` if browsers must stay open (executor waits for return)
- Use `threading.Thread` + `.join()` for batch-then-wait pattern
- Stagger starts by 0.5s to avoid Chromium port conflicts
- Track open browsers in list to prevent garbage collection
- Process in batches (e.g. 15 at a time) with user prompt between batches

### Batch Processing Pattern
```python
for i in range(0, len(remaining), num_workers):
    batch = remaining[i:i+num_workers]
    # ... spawn threads for batch ...
    # ... join all ...
    if more_remaining:
        input("Press ENTER for next batch...")
```

## Turnstile / CAPTCHA Rendering in Parallel

Cloudflare Turnstile may fail to render when:
- Too many browser instances from same IP (rate limit)
- Browser detected as automated (webdriver flag)
- Site isolation blocks iframe

Fix args for Turnstile-heavy automation:
```python
browser = pw.chromium.launch(
    headless=False,  # MUST be non-headless for Turnstile
    args=[
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-site-isolation-trials",
        "--disable-web-security",  # Cross-origin Turnstile iframe
        "--disable-dev-shm-usage"
    ]
)
context = browser.new_context(
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    # ^ Override Playwright default UA which Turnstile flags
)
```

If Turnstile still won't render:
1. Reduce parallel count (15 → 5-8)
2. User refresh (F5) in affected browser
3. Close modal → reopen it
4. Restart router to get new IP (Cloudflare flags IPs)
5. Turnstile NEVER works from datacenter/VPS IPs — must be residential

## Limitations
- Use this skill only when the task clearly matches the scope described above.
- Do not treat the output as a substitute for environment-specific validation, testing, or expert review.
- Stop and ask for clarification if required inputs, permissions, safety boundaries, or success criteria are missing.
