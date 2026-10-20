# CodeBuddy.ai Login Flow (OAuth via Google)

**URL:** `https://www.codebuddy.ai/login`  
**Challenge:** Heavily client-side rendered React app with iframe-based OAuth  
**Date discovered:** 2026-05-04

## Problem

Standard Puppeteer selectors (`querySelector`, `waitForSelector`) fail completely on CodeBuddy's login page:
- `document.querySelectorAll('button, a')` returns `[]` even after page load
- `waitForSelector('button')` times out after 15+ seconds
- Page appears fully loaded in screenshots but DOM is empty from Puppeteer's perspective

## Root Cause

CodeBuddy uses a **dynamically-loaded iframe** (`#login-iframe`) that contains the actual login UI. The main page DOM is nearly empty — all interactive elements live inside the iframe.

## Solution

### 1. Wait for iframe to load
```javascript
await page.waitForSelector('iframe#login-iframe', { timeout: 20000 });
```

### 2. Access iframe content
```javascript
const frameHandle = await page.$('iframe#login-iframe');
const frame = await frameHandle.contentFrame();
```

### 3. Use XPath inside iframe
Standard CSS selectors still fail inside the iframe. Use XPath:
```javascript
await frame.waitForXPath("//a[contains(., 'Google')]", { timeout: 15000 });
const [googleButton] = await frame.$x("//a[contains(., 'Google')]");
```

### 4. Handle popup and Terms of Service
```javascript
const [popup] = await Promise.all([
  new Promise(resolve => page.once('popup', resolve)),
  googleButton.click()
]);

// ToS popup appears on first login
await popup.evaluate(() => {
  const buttons = Array.from(document.querySelectorAll('button'));
  const confirmBtn = buttons.find(btn => 
    btn.textContent.includes('Confirm') || 
    btn.textContent.includes('I agree')
  );
  if (confirmBtn) confirmBtn.click();
});
```

## Full Working Code

```javascript
import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteer.use(StealthPlugin());

async function loginCodeBuddy(page, email, password) {
  // Navigate and wait for iframe
  await page.goto('https://www.codebuddy.ai/login', { 
    waitUntil: 'networkidle2', 
    timeout: 30000 
  });
  
  await page.waitForSelector('iframe#login-iframe', { timeout: 20000 });
  await page.waitForTimeout(3000); // Let iframe content render
  
  // Access iframe
  const frameHandle = await page.$('iframe#login-iframe');
  const frame = await frameHandle.contentFrame();
  
  // Find and click Google button (XPath required)
  await frame.waitForXPath("//a[contains(., 'Google')]", { timeout: 15000 });
  const [googleButton] = await frame.$x("//a[contains(., 'Google')]");
  
  const [popup] = await Promise.all([
    new Promise(resolve => page.once('popup', resolve)),
    googleButton.click()
  ]);
  
  await page.waitForTimeout(3000);
  
  // Handle ToS popup if present
  try {
    await popup.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const confirmBtn = buttons.find(btn => 
        btn.textContent.includes('Confirm') || 
        btn.textContent.includes('I agree')
      );
      if (confirmBtn) confirmBtn.click();
    });
    await page.waitForTimeout(2000);
  } catch (e) {}
  
  // Google OAuth flow
  await popup.waitForSelector('input[type="email"]', { timeout: 15000 });
  await popup.type('input[type="email"]', email, { delay: 100 });
  await popup.keyboard.press('Enter');
  await page.waitForTimeout(4000);
  
  await popup.waitForSelector('input[type="password"]', { timeout: 15000 });
  await popup.type('input[type="password"]', password, { delay: 100 });
  await popup.keyboard.press('Enter');
  await page.waitForTimeout(6000);
  
  // Wait for redirect
  await page.waitForNavigation({ timeout: 15000, waitUntil: 'networkidle2' })
    .catch(() => {});
}
```

## Pitfalls

1. **Don't use `querySelector` on main page** — buttons don't exist there
2. **Don't skip iframe wait** — iframe loads 2-5 seconds after main page
3. **XPath is required** — CSS selectors fail inside this iframe (React/Shadow DOM issue)
4. **ToS popup only appears once** — first login per account, not subsequent logins
5. **Headless detection** — use `puppeteer-extra-plugin-stealth` or site may block

## Debugging Tips

When automation fails on similar sites:

```javascript
// Check if iframe exists
const iframes = await page.$$('iframe');
console.log(`Found ${iframes.length} iframes`);

// Check main page DOM
const buttons = await page.evaluate(() => 
  Array.from(document.querySelectorAll('button, a')).map(el => el.textContent)
);
console.log('Main page buttons:', buttons); // Will be []

// Check iframe DOM
const frame = await (await page.$('iframe')).contentFrame();
const frameButtons = await frame.evaluate(() => 
  Array.from(document.querySelectorAll('button, a')).map(el => el.textContent)
);
console.log('Iframe buttons:', frameButtons); // Will show actual buttons
```

## Related Patterns

- **Iframe-based OAuth:** Many modern apps (Auth0, Clerk, Supabase) use iframes for security
- **Client-side rendering:** React/Vue/Svelte apps often have empty initial DOM
- **XPath as fallback:** When CSS selectors fail, XPath with `contains()` is more robust
