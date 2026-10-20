# Iframe + Popup OAuth Login Pattern

Common pattern for third-party OAuth login (Google, GitHub, etc.) embedded in iframes with popup windows.

## Flow

1. Main page loads with an iframe containing login UI
2. Click OAuth button inside iframe triggers a popup window
3. Popup may show Terms of Service confirmation
4. Popup shows OAuth provider's login form
5. After successful auth, popup closes and main page redirects

## Implementation

```javascript
async function loginWithOAuthInIframe(page, email, password) {
  // 1. Wait for iframe to load
  await page.waitForSelector('iframe[id="login-iframe"]', { timeout: 15000 });
  
  // 2. Get iframe content
  const frameHandle = await page.$('iframe[id="login-iframe"]');
  const frame = await frameHandle.contentFrame();
  
  // 3. Find and click OAuth button (can't use :has-text() in Puppeteer)
  await frame.waitForFunction(() => {
    const links = Array.from(document.querySelectorAll('a'));
    return links.some(link => link.textContent.includes('Sign up with Google'));
  }, { timeout: 10000 });
  
  // 4. Click button and capture popup
  const [popup] = await Promise.all([
    new Promise(resolve => page.once('popup', resolve)),
    frame.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a'));
      const googleLink = links.find(link => link.textContent.includes('Sign up with Google'));
      if (googleLink) googleLink.click();
    })
  ]);
  
  await delay(3000);
  
  // 5. Handle Terms of Service if present
  try {
    await popup.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const confirmBtn = buttons.find(btn => 
        btn.textContent.includes('Confirm') || 
        btn.textContent.includes('I agree') || 
        btn.textContent.includes('Accept')
      );
      if (confirmBtn) confirmBtn.click();
    });
    await delay(2000);
  } catch (e) {
    // No ToS popup, continue
  }
  
  // 6. Fill OAuth form in popup
  await popup.waitForSelector('input[type="email"]', { timeout: 15000 });
  await popup.type('input[type="email"]', email, { delay: 100 });
  await popup.keyboard.press('Enter');
  await delay(4000);
  
  await popup.waitForSelector('input[type="password"]', { timeout: 15000 });
  await popup.type('input[type="password"]', password, { delay: 100 });
  await popup.keyboard.press('Enter');
  await delay(6000);
  
  // 7. Wait for main page to redirect after successful auth
  await page.waitForNavigation({ timeout: 15000, waitUntil: 'networkidle2' }).catch(() => {});
  
  return true;
}
```

## Key Pitfalls

1. **Puppeteer doesn't support `:has-text()` selector** — use `waitForFunction` + `evaluate` with `textContent.includes()` instead
2. **Popup timing** — use `page.once('popup')` in `Promise.all` to capture popup immediately when it opens
3. **Terms of Service modals** — wrap in try/catch since they may not appear for returning users
4. **Delays matter** — OAuth flows need generous delays (3-6s) for redirects and form submissions
5. **Navigation after login** — use `.catch(() => {})` on `waitForNavigation` since some sites don't trigger navigation events

## Headless Server Requirements

For servers without X display:

```javascript
const browser = await puppeteer.launch({
  headless: 'new',
  args: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-blink-features=AutomationControlled',
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--disable-software-rasterizer',
    '--no-first-run',
    '--no-zygote'
  ]
});
```

## Testing Pattern

Always test with screenshots before batch runs:

```javascript
await page.screenshot({ path: `01_login_page_${Date.now()}.png`, fullPage: true });
// ... after each major step
await page.screenshot({ path: `02_after_login_${Date.now()}.png`, fullPage: true });
```
