# Behavioral Simulation — Human-Like Actions in Playwright

## When You Need This

Fingerprint patches (Layer 3) fix **what the browser reports about itself**. Behavioral simulation fixes **how the browser acts**. Sites like Vant.js, Kasada, PerimeterX, and Cloudflare advanced analyze:

- Mouse movement patterns (linear = bot, curved = human)
- Timing between actions (fixed delays = bot, random = human)
- Scroll behavior (instant = bot, chunked with overshoot = human)
- Typing speed (instant fill = bot, char-by-char with pauses = human)
- Click position (dead center = bot, offset within element = human)

**Rule of thumb:** If you have 25 stealth patches but still get blocked after login/form submission → add behavioral simulation.

---

## Core Functions (Playwright + Python)

### 1. Human Delay

Replace ALL fixed `asyncio.sleep(N)` with random ranges:

```python
import random

async def human_delay(min_s=0.5, max_s=2.0):
    """Random delay to simulate human thinking/reading time."""
    await asyncio.sleep(random.uniform(min_s, max_s))
```

**Timing guidelines:**
| Action | Min | Max | Why |
|--------|-----|-----|-----|
| Before click | 0.3 | 1.2 | Eye-hand coordination |
| After page load | 1.5 | 3.0 | Reading/processing |
| Between form fields | 0.5 | 1.5 | Tab/eye movement |
| Before submit | 0.8 | 2.0 | Review before action |
| After submit | 1.5 | 3.5 | Wait for response |

### 2. Mouse Movement (Bezier Curve)

Real humans don't teleport the cursor. Move in a quadratic bezier curve with random control point:

```python
async def human_click(page, selector_or_eval, is_eval=True, viewport_w=414, viewport_h=500):
    """Click with natural mouse movement via bezier curve."""
    try:
        if is_eval:
            box = await page.evaluate(f"""
                () => {{
                    const el = {selector_or_eval};
                    if (!el) return null;
                    const r = el.getBoundingClientRect();
                    return {{x: r.x + r.width/2, y: r.y + r.height/2, w: r.width, h: r.height}};
                }}
            """)
        else:
            el = await page.wait_for_selector(selector_or_eval, timeout=10000)
            if not el:
                return False
            b = await el.bounding_box()
            if not b:
                return False
            box = {'x': b['x'] + b['width']/2, 'y': b['y'] + b['height']/2, 'w': b['width'], 'h': b['height']}

        if not box:
            return False

        # Offset within element (humans don't click dead center)
        target_x = box['x'] + random.uniform(-box['w']*0.2, box['w']*0.2)
        target_y = box['y'] + random.uniform(-box['h']*0.2, box['h']*0.2)

        # Random start position (or use previous mouse position if tracked)
        start_x = random.uniform(100, viewport_w - 100)
        start_y = random.uniform(100, viewport_h - 100)

        # Bezier curve: 3-5 steps with wobble
        steps = random.randint(3, 5)
        for i in range(1, steps + 1):
            t = i / steps
            cx = (start_x + target_x) / 2 + random.uniform(-30, 30)
            cy = (start_y + target_y) / 2 + random.uniform(-30, 30)
            mx = (1-t)**2 * start_x + 2*(1-t)*t*cx + t**2 * target_x
            my = (1-t)**2 * start_y + 2*(1-t)*t*cy + t**2 * target_y
            await page.mouse.move(mx, my)
            await asyncio.sleep(random.uniform(0.02, 0.08))

        await asyncio.sleep(random.uniform(0.05, 0.2))  # Reaction time
        await page.mouse.click(target_x, target_y)
        return True
    except Exception:
        # Fallback: direct click
        if is_eval:
            await page.evaluate(f"(() => {{ const el = {selector_or_eval}; if(el) el.click(); }})()")
        return True
```

### 3. Smooth Scroll

Humans scroll in chunks with slight overshoot and correction:

```python
async def human_scroll(page, direction='down', distance=None):
    """Smooth scroll like a human — variable speed, slight overshoot."""
    if distance is None:
        distance = random.randint(80, 200)
    if direction == 'up':
        distance = -distance

    chunks = random.randint(2, 3)
    chunk_size = distance // chunks
    for i in range(chunks):
        await page.mouse.wheel(0, chunk_size + random.randint(-10, 10))
        await asyncio.sleep(random.uniform(0.05, 0.15))

    # Overshoot correction
    overshoot = random.randint(-15, 15)
    if overshoot != 0:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        await page.mouse.wheel(0, overshoot)
```

### 4. Human Typing

Replace `.fill()` with character-by-character typing on sensitive fields:

```python
async def human_type(page, locator, text, timeout=10000):
    """Type text char-by-char with human-like delays."""
    try:
        await locator.click(timeout=timeout)
        await asyncio.sleep(random.uniform(0.2, 0.5))
        for char in text:
            await page.keyboard.type(char, delay=random.randint(50, 150))
            if random.random() < 0.1:  # 10% chance of thinking pause
                await asyncio.sleep(random.uniform(0.2, 0.5))
        return True
    except Exception:
        await locator.fill(text, timeout=timeout)  # Fallback to fast fill
        return True
```

**When to use human_type vs fill:**
- Login forms (phone, password) → human_type
- OTP/PIN fields → human_type
- Amount fields → human_type
- Search bars → fill is fine (users type fast in search)
- Hidden/non-visible fields → fill (no human interaction)

---

## Integration Pattern

Replace actions in this order of priority:

1. **Login/auth flows** — highest detection risk
2. **Form submissions** — payment, deposit, registration
3. **Navigation clicks** — menu items, tabs
4. **Low-risk actions** — dismiss popups, scroll past content

```python
# ❌ BEFORE (bot-like)
await safe_eval(page, "document.querySelector('.login-btn')?.click()")
await asyncio.sleep(2)
await phone_loc.fill(phone)
await asyncio.sleep(1)

# ✅ AFTER (human-like)
await human_delay(0.5, 1.2)
await human_scroll(page, 'down', random.randint(30, 80))
await human_delay(0.3, 0.8)
await human_click(page, "document.querySelector('.login-btn')")
await human_delay(1.5, 2.5)
await human_type(page, phone_loc, phone)
await human_delay(0.8, 1.5)
```

---

## Pitfalls

1. **Don't humanize everything** — Background polling, popup dismissal, and retry loops should stay fast. Only humanize user-visible actions.

2. **human_click fallback** — If bezier movement fails (element moved, page changed), always fall back to direct `.click()` or `safe_eval`. Don't let the humanize function break the flow.

3. **human_type fallback** — If char-by-char typing times out (keyboard didn't appear, virtual keyboard intercepted), fall back to `.fill()`. Some mobile sites have custom keyboards that don't respond to `page.keyboard.type()`.

4. **Scroll before click, not after** — Humans scroll to find the element, then click. Scrolling after clicking is suspicious.

5. **Don't make delays too long** — Total added delay per flow should be 5-15 seconds. Over 30 seconds and the session feels unnatural (real users don't wait 5 seconds between every field).

6. **Randomize start position in human_click** — Don't always start from (0,0) or viewport center. Use random or track previous mouse position.

7. **Mobile vs desktop timing** — Mobile users are slower (thumb typing, smaller screen). Use longer delays for mobile emulation (1.5x multiplier).

8. **Test with `bot.sannysoft.com` AFTER adding behavioral code** — Sometimes Playwright mouse.move() triggers new detection vectors. Always verify fingerprint is still clean.

---

## Confirmed Results (June 2026)

**Target:** example-target.com (Vant.js / Vue framework)
**Detection level:** Medium (not Cloudflare, but has bot detection)

```
Without behavioral simulation:
✅ Fingerprint: 56/57 passed
❌ Login flow: Sometimes blocked (timing patterns detected)

With behavioral simulation (v6):
✅ Fingerprint: 56/57 passed
✅ Login flow: Human-like timing
✅ Form fill: Character-by-character
✅ Mouse movement: Bezier curves
✅ Scroll: Chunked with overshoot
```
