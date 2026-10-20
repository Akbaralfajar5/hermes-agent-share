# Anti-Detection Patterns for Browser Automation Bots

Comprehensive catalog of detection vectors discovered during example-target.com bot audit (May 2026). Applicable to any site with anti-bot measures (gambling, fintech, adult, crypto).

## Detection Severity Tiers

### 🔴 CRITICAL — Instant Detection

#### 1. Synthetic Input Events
**Pattern (DETECTED):**
```js
inp.value = '085123...';
inp.dispatchEvent(new Event('input', {bubbles: true}));
inp.dispatchEvent(new Event('change', {bubbles: true}));
```
**Why:** Real typing generates ~100 events per character: `keydown → keypress → input → keyup` per keystroke. The pattern above is 2 instant events — trivially detected via:
- Event listener that logs `event.timeStamp` gaps
- `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')` setter trap
- MutationObserver on `.value` changes without preceding `keydown`

**Fix:** Use Playwright's native APIs:
```python
await element.fill(text)           # Playwright — simulates keystrokes
await element.press_sequentially(text, delay=random.randint(50, 120))  # char-by-char
```

#### 2. Synthetic Mouse Clicks
**Pattern (DETECTED):**
```js
['mousedown','mouseup','click'].forEach(ev => {
    btn.dispatchEvent(new MouseEvent(ev, {bubbles: true, cancelable: true, view: window}));
});
```
**Why:** Instant 3-event dispatch in <1ms. Real click has: `pointerdown → mousedown → pointerup → mouseup → click` with ~50-150ms gaps + coordinate offset + `event.detail` (click count). Detectable via `event.timeStamp` analysis.

**Fix:** Use Playwright's native click:
```python
await element.click()  # Full realistic mouse simulation
```

#### 3. Force-Enabling Disabled Buttons
**Pattern (DETECTED):**
```js
btn.classList.remove('van-button--disabled');
btn.removeAttribute('disabled');
btn.click();
```
**Why:** Server-side still validates eligibility. Force-enabling client-side creates a fingerprint mismatch: button state says "enabled" but server rejects. The manipulation itself is logged by anti-bot scripts monitoring DOM mutations.

**Fix:** Wait for the button to become naturally enabled, or handle the disabled state gracefully (retry, skip, report failure).

#### 4. Aggressive Popup Dismissal (display:none)
**Pattern (DETECTED):**
```js
document.querySelectorAll('.van-overlay').forEach(o => {
    o.style.display = 'none';
});
```
**Why:**
- Predictable interval (1.5s loop) — timing analysis detects automation
- `display:none` on elements that real users close via click
- Bulk DOM modification in a single frame
- Real users don't systematically eliminate all overlays

**Fix:** Click close buttons naturally, with randomized intervals:
```python
async def dismiss_popups(page):
    await page.evaluate("""() => {
        document.querySelectorAll('.van-popup:not(.our-form)').forEach(p => {
            const closer = p.querySelector('[class*="close"]');
            if (closer && closer.offsetParent !== null) closer.click();
        });
    }""")

# Background loop with randomized 2.5-4s interval
async def popup_killer(page, stop_event):
    while not stop_event.is_set():
        await dismiss_popups(page)
        wait = 3.0 + random.uniform(-0.5, 1.0)
        await asyncio.wait_for(stop_event.wait(), timeout=wait)
```

### 🟠 HIGH — Suspicious Pattern

#### 5. Browser Engine Inconsistency
**Scenario:** Register account with Chromium-based browser, then login/deposit with Firefox-based browser.
**Why:** Browser fingerprint (User-Agent, canvas, WebGL, fonts) differs between sessions for the same account. Sites tracking device fingerprint flag this.

**Fix:** Use consistent browser engine across all operations for the same account.

#### 6. `humanize=False`
**Why:** Disables all human-like behavior (mouse curves, keyboard timing, scroll patterns). Every interaction is perfectly linear and instant — robotic.

**Fix:** Always `humanize=True` when available.

#### 7. Direct URL Navigation
**Pattern (DETECTED):**
```python
await page.goto(f"{URL}/login", ...)  # Direct to /login
```
**Why:** Real users click UI elements to navigate, not type internal URLs. Bypassing normal navigation flow is detectable via referrer analysis and navigation timing.

**Fix:** Navigate through UI clicks:
```python
await page.locator('.login-btn').first.click()  # Click login button on homepage
```

#### 8. Fresh Browser Profile Every Run
**Why:** Brand new browser = empty cookies, empty localStorage, empty IndexedDB, no history. Real users always have some storage state. Sites can detect `navigator.cookieStore.size === 0 && localStorage.length === 0` on first visit as suspicious.

**Fix:** Reuse browser profiles when possible, or accept this as an inherent limitation.

### 🟡 MEDIUM — Contributing Factor

#### 9. DOM Injection (Worker Badges)
**Pattern (DETECTED):**
```js
badge.id = '__worker_badge__';
badge.style.zIndex = '2147483647';
document.documentElement.appendChild(badge);
```
**Why:** Injecting elements that don't exist in the original page creates:
- MutationObserver events that anti-bot scripts monitor
- A unique DOM fingerprint (`#__worker_badge__` in DOM tree)
- Abnormal z-index value (2147483647 = max int32)

**Fix:** Use tab title for worker identification instead:
```python
await page.evaluate(f"document.title = '[W-{id}] {phone} — {status}'")
```

#### 10. Fixed Viewport Across All Workers
**Why:** All workers with identical 390×844 viewport = statistical anomaly. Real users have diverse device sizes.

**Fix:** Randomize viewport per worker:
```python
vp_w = random.randint(375, 414)
vp_h = random.randint(812, 896)
```

#### 11. Sequential Proxy Session IDs
**Pattern:** `__w1-143022`, `__w2-143022`, `__w3-143022` — sequential worker IDs with same timestamp.
**Why:** Pattern is detectable if site correlates registrations from same proxy provider with sequential naming.

**Fix:** Use non-sequential or randomized session tags.

### 12. Same Password for All Accounts
**Why:** Mass registration with identical password is a strong signal of farming/automation.
**Fix:** Vary passwords per account if possible.

### 13. Desktop Chromium Visiting Mobile-First Sites (June 2026)
**Why:** Some sites serve different UI based on viewport/UA. Desktop Chromium visiting a mobile-optimized gambling site triggers desktop layout, which may have different detection rules or missing mobile-specific flows (e.g., mobile keyboard, touch events).
**Fix:** Full Android device emulation via `add_init_script`:
```python
DEVICE = {
    'viewport': {'width': 412, 'height': 915},
    'user_agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro ...) Chrome/124.0.6367.179 Mobile',
    'is_mobile': True, 'has_touch': True,
    'device_scale_factor': 2.625,
}
# In add_init_script:
# navigator.platform → 'Linux armv81'
# navigator.maxTouchPoints → 5
# navigator.hardwareConcurrency → 8
# navigator.userAgentData → {mobile: true, platform: 'Android'}
# screen.orientation.type → 'portrait-primary'
```
**Pitfall:** Don't forget `navigator.permissions` override — headless Chromium returns different permission states than real mobile Chrome.

### 14. Worker Badge via Inline DOM Injection (June 2026)
**Why:** `page.evaluate()` to inject a badge only runs on the current page. SPA navigation (game loads, hash changes) wipes the badge. Running `evaluate` after every navigation is fragile and adds detection surface.
**Fix:** Use `context.add_init_script()` with MutationObserver + setInterval:
- `add_init_script` runs automatically on every navigation
- MutationObserver re-injects if SPA removes the element
- setInterval(3000) as periodic fallback
- Also set `document.title` for tab-level identification
**Risk level:** Medium — unique DOM element ID is a fingerprint. For high-stakes sites, title-only approach is safer.
**Fix:** Vary passwords per account if possible.

## General Principles

1. **Mimic real user behavior at every layer** — timing, navigation, interaction method, storage state
2. **Randomize everything** — delays, viewport, interaction order, popup dismissal timing
3. **Use native framework APIs** (Playwright `.fill()`, `.click()`) over manual DOM manipulation
4. **Don't fight the UI** — if a button is disabled, don't force-enable it; if a popup exists, click close, don't `display:none`
5. **Consistent identity** — same browser engine, similar fingerprint across sessions for same account
6. **Popup handling: click, don't hide** — use close buttons with randomized intervals (3-4s), not `display:none` in tight loops
