---
name: interactive-html-presentations
description: "Single-file HTML slide decks with game-box menus, animations, transitions, and interactive navigation. Use when user wants presentation slides with rich interactivity beyond PowerPoint capabilities."
version: 1.0.0
metadata:
  hermes:
    tags: [presentation, slides, html, animation, game-box, interactive, deck]
    related_skills: [claude-design, popular-web-designs]
---

# Interactive HTML Presentations

Create single-file HTML slide decks with rich animations, game-box style menus, and interactive navigation. Use when user wants presentations that go beyond static PowerPoint — clickable hub menus, 3D transitions, particle backgrounds, etc.

## When to Use

- User asks for "game box style" presentation
- User wants clickable menu/hub slide that links to other slides
- User wants rich CSS animations and transitions between slides
- User wants a presentation that works in browser with keyboard/touch/click navigation
- User is frustrated with PowerPoint animation limitations

## Architecture Pattern: Hub + Slides

```
Slide 0 (Hub/Menu) ←→ Slide 1..N (Content)
     ↑                      |
     └── Back button ───────┘
```

### Hub Slide (Game Box Menu)
- Grid of clickable cards (CSS Grid, responsive)
- Each card: icon + title + subtitle
- Hover: scale(1.05), box-shadow glow, gradient border
- Click: navigates to target slide with transition
- Background: animated particles, gradient, or pattern

### Content Slides
- "← Kembali ke Menu" button (fixed top-left)
- ← → navigation arrows at bottom
- Progress bar at top
- Slide counter

## Critical Bug Fix: Navigation State Reset

**PITFALL**: After returning to menu via `goToMenu()`, clicking cards again fails. Root causes:
1. `isAnimating` stays `true` (animation timeout didn't fire or user clicked during transition)
2. Element inline styles (`visibility`, `pointerEvents`) not fully reset
3. `menuEl.style.visibility = ''` resets to CSS default `visibility: hidden` — menu disappears

### Fix 1: Force-Reset Pattern for `isAnimating`

**NEVER** just `return` when `isAnimating` is true. Instead, use a **force-reset on second click**:

```javascript
function goToSlide(index, direction = 'forward') {
  if (index === currentSlide) return;
  if (index < 0 || index >= totalSlides) return;
  if (isAnimating) {
    isAnimating = false;  // Force reset — next click will work
    return;
  }
  isAnimating = true;
  // ... rest of function
}

function goToMenu() {
  if (currentSlide === 0) return;
  if (isAnimating) {
    isAnimating = false;  // Force reset
    return;
  }
  isAnimating = true;
  // ... rest of function
}
```

### Fix 2: Thorough Cleanup in `goToSlide()`

```javascript
setTimeout(() => {
  currentEl.classList.remove(exitClass);
  currentEl.classList.remove('active');     // CRITICAL — remove active from old slide
  currentEl.style.transform = '';
  currentEl.style.opacity = '';
  currentEl.style.filter = '';
  currentEl.style.visibility = '';          // CRITICAL — let CSS handle it
  currentEl.style.pointerEvents = '';       // CRITICAL
  nextEl.style.transform = '';
  nextEl.style.opacity = '';
  nextEl.style.filter = '';
  nextEl.scrollTop = 0;
  isAnimating = false;
}, 650);
```

### Fix 3: `goToMenu()` Cleanup — Do NOT Reset Menu Visibility

```javascript
// In goToMenu() — re-animate cards with full style reset:
const cards = document.querySelectorAll('.game-card');
cards.forEach((card, i) => {
  card.style.animation = 'none';
  card.style.pointerEvents = 'auto';   // CRITICAL
  card.style.opacity = '1';            // CRITICAL
  card.style.visibility = 'visible';   // CRITICAL
  void card.offsetWidth;
  card.style.animation = `cardAppear 0.6s ease ${0.1 + i * 0.05}s backwards`;
});

setTimeout(() => {
  currentEl.classList.remove('exit-menu');
  currentEl.classList.remove('active');
  currentEl.style.transform = '';
  currentEl.style.opacity = '';
  currentEl.style.visibility = '';
  currentEl.style.filter = '';
  currentEl.style.pointerEvents = '';
  // Menu cleanup — keep visible via .active class
  menuEl.style.transform = '';
  menuEl.style.opacity = '';
  menuEl.style.filter = '';
  // ⚠️ Do NOT reset menuEl.style.visibility — CSS default is hidden!
  // Ensure game grid is interactive
  const grid = document.getElementById('gameGrid');
  if (grid) grid.style.pointerEvents = 'auto';
  isAnimating = false;
}, 650);
```

### Verification Test

After any fix, **always test this exact flow** before delivering:
1. Menu → click card A → slide A appears ✓
2. Click "Back to Menu" → menu appears ✓
3. Click card B → slide B appears ✓ (THIS is where the bug manifests)
4. Repeat steps 2-3 at least twice more

## Navigation Implementation

```javascript
// Keyboard
document.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowRight' || e.key === ' ') nextSlide();
  if (e.key === 'ArrowLeft') prevSlide();
  if (e.key === 'Escape') goToMenu();
});

// Touch/Swipe (60px threshold)
let touchStartX = 0;
el.addEventListener('touchstart', e => touchStartX = e.touches[0].clientX);
el.addEventListener('touchend', e => {
  const diff = touchStartX - e.changedTouches[0].clientX;
  if (Math.abs(diff) > 60) diff > 0 ? nextSlide() : prevSlide();
});
```

## Transition Effects

Good combinations:
- **Forward**: `translateX(80%) rotateY(10deg) scale(0.85)` → `scale(1) rotateY(0deg)`
- **Backward**: `translateX(-80%) rotateY(-10deg) scale(0.85)` → same
- **To menu**: `scale(0.85) blur(5px)` → `scale(1)`
- **Exit**: add class `exit-left`/`exit-right`/`exit-menu` with CSS animation

## Staggered Content Animation

```javascript
function animateSlideElements(index) {
  const items = document.querySelectorAll(`#slide-${index} .anim-item`);
  items.forEach((item, i) => {
    item.style.opacity = '0';
    item.style.transform = 'translateY(20px)';
    setTimeout(() => {
      item.style.transition = 'all 0.5s ease';
      item.style.opacity = '1';
      item.style.transform = 'translateY(0)';
    }, 150 + i * 120);
  });
}
```

## Sidang/Defense Presentations: Skip Theory Slides
For sidang skripsi (thesis defense), the user explicitly corrected: "Untuk sidang ga perlu ada teori kali, langsung aja" — meaning skip the Landasan Teori (theoretical framework) slide entirely. The defense flow should be:
1. Cover → 2. Rumusan Masalah → 3. Penelitian Terdahulu → 4. Metode → 5. Prosedur → 6-N. Results → Simpulan → Demo → Terima Kasih


## Fullscreen Font Sizing (Critical User Feedback)
User complained: "saat mode full screen seperti ppt tidak terlalu kekecilan font nya" — fonts too small in fullscreen/PPT mode. The root cause is `clamp()` with small max values:

**BAD (old):** `font-size: clamp(1.2rem, 2.8vw, 1.8rem)` → caps at 28.8px in fullscreen
**GOOD (new):** `font-size: clamp(2rem, 4vw, 3.5rem)` → reaches 56px+ in fullscreen

**Recommended minimums for presentation slides (1920px fullscreen):**
- Slide titles: `clamp(2rem, 4vw, 3.5rem)` → ~56px in fullscreen
- Subtitles: `clamp(1.2rem, 2.5vw, 2rem)` → ~32px
- Body text: `clamp(1rem, 2vw, 1.6rem)` → ~26px
- Hero stats/big numbers: `clamp(3rem, 8vw, 7rem)` → ~112px
- Small labels/captions: `clamp(0.8rem, 1.5vw, 1.2rem)` → ~19px

Always preview in fullscreen (F11) before delivering. Text that looks fine in a windowed browser may be unreadable when projected.

## Technical Requirements

- Single self-contained HTML file
- All CSS in `<style>`, all JS in `<script>`
- Only external dependency: Google Fonts (optional)
- Responsive (mobile grid: 2 cols, desktop: 4-5 cols)
- localStorage for slide position persistence (optional)
- Fullscreen hint: F11

## Fullscreen Font Sizing (Critical for Presentation Mode)

When the user will present in fullscreen browser mode (F11), fonts MUST be large enough to read from the back of a lecture room. The old pattern of `clamp(1.2rem, 2.8vw, 1.8rem)` for titles produces ~28px in fullscreen — too small.

**Recommended vw-based sizing for fullscreen readability:**

| Element | clamp() formula | Result at 1920px |
|---------|----------------|-------------------|
| Slide titles | `clamp(2rem, 4vw, 3.5rem)` | ~64px (capped at 56px) |
| Body text | `clamp(1rem, 2vw, 1.6rem)` | ~32px (capped at 25.6px) |
| Hero stats / big numbers | `clamp(3rem, 8vw, 7rem)` | ~128px (capped at 112px) |
| Card headers | `clamp(1.2rem, 2.5vw, 2rem)` | ~40px (capped at 32px) |
| Small labels / badges | `clamp(0.8rem, 1.2vw, 1rem)` | ~19px (capped at 16px) |
| Page numbers | `clamp(0.7rem, 1vw, 0.9rem)` | ~16px |

**User feedback signal**: "font nya terlalu kekecilan saat fullscreen" = fonts need to be bumped up significantly. Don't just increase by 10-20% — double the vw values.

**Testing**: Always check font readability by viewing the HTML in a browser at 1920×1080 fullscreen. If body text looks small on a laptop screen, it will be unreadable projected in a lecture hall.

## Design Tokens

Provide user's brand colors as CSS variables:
```css
:root {
  --primary: #2B4EA2;
  --accent: #E91E7B;
  --success: #2E8B3A;
  --gold: #F5C518;
  --dark: #1A1A2E;
}
```

## Post-Creation: Inserting New Slides

Users often review the presentation and ask to add a slide (e.g., "slide judulnya belum ada"). This requires renaming all subsequent slide IDs, game-card attributes, page labels, and updating totalSlides.

### CRITICAL PITFALL: Double-Replacement Bug

**NEVER do sequential string replacements like:**
```javascript
// WRONG — slide-1→slide-2, then slide-2→slide-3 catches the ALREADY-renamed slide-1!
for i in range(10, 0, -1):
    html = html.replace(f'id="slide-{i}"', f'id="slide-{i+1}"')
```

**CORRECT — Use temp placeholders to avoid collisions:**
```python
# Step 1: Rename to TEMP placeholders (high to low)
for i in range(10, 0, -1):
    html = html.replace('id="slide-%d"' % i, 'id="slide-TEMP%d"' % (i+1))

# Step 2: Replace temps back to final names
for i in range(11, 1, -1):
    html = html.replace('id="slide-TEMP%d"' % i, 'id="slide-%d"' % i)
```

### Full Slide Insertion Checklist

When inserting a new slide at position N (shifting all others +1):

**⚠️ CRITICAL ORDER OF OPERATIONS** — do steps 1-2 BEFORE step 4. If you insert the new slide HTML first and then run the TEMP rename, the new slide's ID gets shifted too (double-rename bug).

**Confirmed failure mode (May 2026):** Inserted slide with `id="slide-7"` first, then ran the TEMP rename loop. The new slide-7 got renamed to slide-8, creating two slide-8s and no slide-7. Fix: restore from backup, run TEMP rename on existing slides first, then insert the new slide HTML targeting the now-free ID.

1. **Rename slide IDs** (`id="slide-X"`) — use TEMP placeholder pattern above
2. **Rename game-card attributes** (`data-slide="X" onclick="goToSlide(X)"`) — same TEMP pattern
3. **Update page labels** (`>01 / 10<` → `>02 / 11<`) — adjust both number and total
4. **Insert new slide HTML** before the (now-renamed) next slide — assign the target ID directly (e.g., `id="slide-7"`)
5. **Update `totalSlides`** constant in JavaScript — **THIS IS THE MOST COMMONLY FORGOTTEN STEP**. If `totalSlides` is not updated, the last slide(s) become unreachable (navigation stops before them). Symptom: "slide Penutup hilang" or last N slides not accessible. Confirmed failure mode (May 2026): added slide-7 (Penelitian Terdahulu), totalSlides stayed at 15, slide-15 (Penutup) became unreachable. Fix: `const totalSlides = 16;`.
6. **Add game-card** for the new slide in the menu grid
7. **Update HTML comments** (`<!-- SLIDE N: ... -->`) for readability

**Quick check after any slide insertion:**
```bash
# Count slide IDs vs totalSlides value
grep -c 'id="slide-' index.html  # should equal totalSlides
grep 'const totalSlides' index.html  # verify the number matches
```

**Verification after insertion:**
```python
import re
slides = re.findall(r'id="slide-(\d+)"', content)
print("Slides:", sorted([int(s) for s in slides]))
# Should be a clean consecutive sequence with no gaps or duplicates
menu = re.findall(r'data-slide="(\d+)"', content)
print("Menu:", sorted([int(s) for s in menu]))
```

### Recommended: Use External Python Script

For complex modifications, write a Python script that reads the full HTML, applies all changes atomically, and writes back. Don't use incremental `patch()` calls — too error-prone with interdependent changes.

**⚠️ PITFALL: `terminal()` with `&` in Python strings** — if your Python code contains `&` (e.g., HTML entities like `&amp;`, `&middot;`, or `&mdash;`), the terminal tool will interpret `&` as shell backgrounding and fail with: `"Foreground command uses '&' backgrounding."` Always write the script to a `.py` file first with `write_file()`, then run it with `terminal("python3 /tmp/script.py")`.

### Pitfall: Reading Large HTML Files in Sandbox

`read_file()` with offset/limit returns line-numbered content (`  123|...`) that needs stripping. For files >50KB, `terminal("cat file.html")` may truncate. `base64` approach fails on files with emoji/special chars (UnicodeDecodeError).

**Best approach — write a self-contained Python script and execute via terminal:**

```python
# Write all modifications as a Python script, execute atomically
script = r'''
import re
with open('/path/to/file.html', 'r', encoding='utf-8', errors='replace') as f:
    html = f.read()
# ... all modifications using TEMP placeholder pattern ...
with open('/path/to/file.html', 'w', encoding='utf-8') as f:
    f.write(html)
# Verify
print("Slide IDs:", re.findall(r'id="slide-(\d+)"', html))
'''
terminal("python3 -c '%s'" % script.replace("'", "'\"'\"'"), timeout=30)
```

This avoids encoding issues, truncation, and line-number artifacts. Always add verification prints at the end.

### Title/Cover Slide Template

Common request for academic presentations — a cover slide with thesis title, author, institution, and supervisors. **Put supervisors and prodi in ONE box** — two separate boxes looks messy.

```html
<div class="slide bg-dark dot-pattern" id="slide-1">
  <div class="slide-content" style="text-align:center; max-width:900px;">
    <div style="margin-bottom:20px;"><span style="font-size:3rem;">🎓</span></div>
    <p style="color:rgba(255,255,255,0.5); font-size:0.85rem; letter-spacing:2px; text-transform:uppercase; margin-bottom:16px;">Seminar Proposal Skripsi</p>
    <h1 style="font-size:clamp(1.2rem, 2.8vw, 1.8rem); font-weight:800; line-height:1.4; margin-bottom:24px; background:linear-gradient(135deg, #fff 0%, #a8c0ff 50%, #E91E7B 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;">JUDUL SKRIPSI LENGKAP</h1>
    <div class="slide-divider" style="margin:20px auto;"></div>
    <div style="margin-top:20px;">
      <p style="color:#fff; font-size:1.1rem; font-weight:600;">Nama Mahasiswa</p>
      <p style="color:rgba(255,255,255,0.6); font-size:0.9rem; margin-top:4px;">NIM XXXXXXXX</p>
    </div>
    <!-- ONE box: supervisors on top, divider, then prodi/fakultas/univ/tahun -->
    <div style="margin-top:24px; padding:16px 24px; border:1px solid rgba(255,255,255,0.1); border-radius:12px; background:rgba(255,255,255,0.03); display:inline-block;">
      <p style="color:rgba(255,255,255,0.4); font-size:0.72rem; letter-spacing:1px; text-transform:uppercase; margin-bottom:8px;">Dosen Pembimbing</p>
      <p style="color:rgba(255,255,255,0.75); font-size:0.82rem;">Pembimbing I, Gelar</p>
      <p style="color:rgba(255,255,255,0.75); font-size:0.82rem; margin-top:2px;">Pembimbing II, Gelar</p>
      <div style="border-top:1px solid rgba(255,255,255,0.08); margin:12px 0;"></div>
      <p style="color:rgba(255,255,255,0.7); font-size:0.85rem;">Program Studi</p>
      <p style="color:rgba(255,255,255,0.5); font-size:0.8rem; margin-top:4px;">Fakultas</p>
      <p style="color:rgba(255,255,255,0.5); font-size:0.8rem; margin-top:4px;">Universitas</p>
      <p style="color:rgba(255,255,255,0.4); font-size:0.75rem; margin-top:8px;">Tahun</p>
    </div>
  </div>
</div>
```

**⚠️ PITFALL: Supervisor box separate from prodi box** — user will ask to merge them. Always put both in one box from the start, with a thin divider line between supervisor names and prodi info.

## Embedding Live Website in Slides (iframe Demo)

When the user asks for a "Live Website" or "Demo Website" slide, they want a **full slide page** with the website embedded — NOT just an external link card in the menu. User explicitly corrected this (June 2026): first attempt was a game-card that opened a new tab via `window.open()`, user said "jadikan halaman aja seperti di seminar proposal kemarin" — meaning a full slide with iframe preview + clickable URL button.

### Pattern: Live Website Demo Slide

```html
<!-- SLIDE N: LIVE WEBSITE DEMO -->
<div class="slide bg-gradient-1 dot-pattern" id="slide-N">
  <div class="slide-content">
    <div class="slide-icon-title">
      <span class="icon">🌐</span>
      <h2 class="slide-title dark">Live Website</h2>
    </div>
    <div class="slide-divider"></div>

    <!-- Clickable URL button — opens in new tab -->
    <div class="content-card anim-item" style="text-align:center; margin-bottom:16px;">
      <p class="text-white text-base" style="margin-bottom:12px;">
        Deskripsi singkat website...
      </p>
      <a href="https://URL" target="_blank"
         style="display:inline-block;padding:14px 32px;border-radius:12px;
                background:linear-gradient(135deg,#2B4EA2,#3d6fd4);color:#fff;
                font-size:1.1rem;font-weight:700;font-family:'Poppins';
                text-decoration:none;box-shadow:0 6px 20px rgba(43,78,162,0.4);
                transition:all 0.3s ease;"
         onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 10px 30px rgba(43,78,162,0.6)'"
         onmouseout="this.style.transform='';this.style.boxShadow='0 6px 20px rgba(43,78,162,0.4)'">
        🔗 domain.com
      </a>
    </div>

    <!-- Browser mockup frame with iframe -->
    <div class="mockup-frame anim-item">
      <div class="mockup-bar">
        <div class="mockup-dot" style="background:#ff5f57;"></div>
        <div class="mockup-dot" style="background:#ffbd2e;"></div>
        <div class="mockup-dot" style="background:#28c840;"></div>
        <div class="mockup-url">🔒 https://domain.com</div>
      </div>
      <iframe src="https://domain.com"
              style="width:100%;height:400px;border:none;background:#0f172a;"
              loading="lazy" title="Live Website"></iframe>
    </div>

    <!-- Feature highlights -->
    <div class="two-col" style="margin-top:16px;">
      <div class="content-card anim-item" style="text-align:center;">
        <h4 class="text-white font-semibold" style="margin-bottom:6px;">🌍 Custom Domain</h4>
        <p class="text-muted text-sm">domain.com — SSL aktif</p>
      </div>
      <div class="content-card anim-item" style="text-align:center;">
        <h4 class="text-white font-semibold" style="margin-bottom:6px;">📱 PWA Ready</h4>
        <p class="text-muted text-sm">Bisa di-install sebagai aplikasi</p>
      </div>
    </div>
  </div>
</div>
```

### Phone-Size Mockup (9:16 for Mobile-First Sites)

When the website being demoed is mobile-first or responsive, the user will likely ask for a phone-shaped frame instead of a wide desktop frame. Default to phone-size if the site is a mobile-first app (e.g., marketing site, PWA).

```html
<div class="mockup-frame anim-item" style="max-width:400px; margin:0 auto; border-radius:28px; border:3px solid rgba(255,255,255,0.15);">
  <div class="mockup-bar" style="border-radius:25px 25px 0 0;">
    <div class="mockup-dot" style="background:#ff5f57;"></div>
    <div class="mockup-dot" style="background:#ffbd2e;"></div>
    <div class="mockup-dot" style="background:#28c840;"></div>
    <div class="mockup-url">🔒 https://domain.com</div>
  </div>
  <iframe src="https://domain.com"
          style="width:100%;height:600px;border:none;background:#0f172a;border-radius:0 0 25px 25px;"
          loading="lazy" title="Live Website"></iframe>
</div>
```

**Dimensions guide:**
- **Phone (9:16):** `max-width:400px`, iframe `height:600px`, `border-radius:28px` — user may ask to widen (`420-440px`) or narrow (`340px`)
- **Desktop (16:9):** `max-width:700px`, iframe `height:400px`, `border-radius:16px` (default mockup-frame style)
- Always add `border-radius` to the iframe itself (`0 0 25px 25px`) so bottom corners match the frame

**User feedback pattern (June 2026):** Started with wide desktop frame → user asked "sesuaikan dengan ukuran hp 9:16" → applied 340px → user asked "agak lebaran lagi sedikit" → settled at 400px. Default to 400px for phone mockups to avoid the back-and-forth.

### Key Points
- **Always make it a full slide**, not just an external link card in the game-box menu
- The **clickable URL button** (big blue gradient) lets the presenter open the live site in a new tab for full-screen demo
- The **iframe preview** shows the website embedded in the slide for quick glance without leaving the presentation
- Place this slide **before the closing/Terima Kasih slide** — it's the natural "proof" moment near the end
- The `mockup-frame` CSS class (browser chrome with traffic-light dots) must be defined in the stylesheet

### Required CSS (if not already present)

```css
.mockup-frame {
  background: #1a1a2e; border-radius: 16px; overflow: hidden;
  border: 2px solid rgba(255,255,255,0.1); max-width: 700px; margin: 0 auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.mockup-bar {
  display: flex; align-items: center; gap: 8px; padding: 12px 16px;
  background: rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.08);
}
.mockup-dot { width: 10px; height: 10px; border-radius: 50%; }
.mockup-url {
  flex: 1; padding: 6px 14px; border-radius: 8px;
  background: rgba(255,255,255,0.06); font-size: 0.75rem;
  color: rgba(255,255,255,0.5); font-family: 'Inter', monospace;
}
```

## Embedding Live Website Screenshots into Slides

When a slide needs to show the actual website (e.g., Desain Produk slide), take screenshots via browser automation and embed as base64 PNG.

```python
import base64

# Convert screenshots to base64
with open('/path/to/screenshot.png', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

# Embed in HTML
img_tag = f'<img src="data:image/png;base64,{b64}" alt="Beranda" style="width:100%;border-radius:8px;border:1px solid rgba(255,255,255,0.1);">'
```

**Workflow:**
1. `browser_navigate(url)` → `browser_vision()` to capture screenshot (path in `screenshot_path` even if vision fails)
2. Convert to base64 with Python
3. Save b64 to `/tmp/screenshot_b64.txt` (large strings — don't inline in Python heredoc)
4. Inject into HTML via Python string replacement

**Pitfall:** Screenshots can be 1MB+ as base64 (1350740 chars for a full-page screenshot). This is fine for Vercel static deploy but makes the HTML file large. Consider resizing with Pillow before embedding if file size is a concern.

**Two-column layout for multiple screenshots:**
```html
<div class="content-card anim-item" style="margin-bottom:16px;">
  <h4 class="text-white font-semibold" style="margin-bottom:12px;">🖥️ Tampilan Website</h4>
  <div style="display:flex;gap:12px;flex-wrap:wrap;">
    <div style="flex:1;min-width:200px;">
      <p style="font-size:0.72rem;color:rgba(255,255,255,0.5);margin-bottom:6px;">Halaman Beranda</p>
      <img src="data:image/png;base64,..." alt="Beranda" style="width:100%;border-radius:8px;border:1px solid rgba(255,255,255,0.1);">
    </div>
    <div style="flex:1;min-width:200px;">
      <p style="font-size:0.72rem;color:rgba(255,255,255,0.5);margin-bottom:6px;">Halaman Produk</p>
      <img src="data:image/png;base64,..." alt="Produk" style="width:100%;border-radius:8px;border:1px solid rgba(255,255,255,0.1);">
    </div>
  </div>
</div>
```

## Cropping Embedded Images (Pillow)

When a base64-embedded image has unwanted content at the bottom (e.g., a diagram that includes a technology legend below the main content), crop it with Pillow before re-embedding.

```python
from PIL import Image
import base64, io, re

with open('/tmp/index.html', 'r') as f:
    content = f.read()

# Find the image by its alt text
match = re.search(r'src=\"data:image/jpeg;base64,([^\"]+)\" alt=\"Your Alt Text\"', content)
if match:
    b64 = match.group(1)
    img = Image.open(io.BytesIO(base64.b64decode(b64)))
    w, h = img.size
    print(f"Original: {w}x{h}")
    
    # Crop to top N% — adjust percentage based on where unwanted content starts
    crop_h = int(h * 0.75)  # keep top 75%
    img_cropped = img.crop((0, 0, w, crop_h))
    
    buf = io.BytesIO()
    img_cropped.save(buf, format='JPEG', quality=85)
    new_b64 = base64.b64encode(buf.getvalue()).decode()
    
    content = content.replace(b64, new_b64, 1)
    with open('/tmp/index.html', 'w') as f:
        f.write(content)
```

**⚠️ PITFALL: Don't guess the crop percentage.** Send the original image to the user first via `MEDIA:/path/to/image.jpg` and ask where to crop. A 60% crop that removes the legend may also remove the bottom of the main content. Always confirm before deploying.

**Workflow:**
1. Extract and save the image: `img.save('/tmp/preview.jpg')`
2. Send to user: `MEDIA:/tmp/preview.jpg`
3. Ask: "Mau crop sampai baris mana?" — user will point to the content boundary
4. Apply crop at the confirmed percentage
5. Re-embed and deploy

**Note:** If the image was already cropped in a previous session (file not on VPS), you need the original. Check `/tmp/seminar_index_backup.html` or re-download from the live URL.

## Removing Figure Captions from Embedded Images

When images are embedded as base64 in slides, captions like `<p style="...font-style:italic;">Gambar 3.4 Sitemap Website</p>` are often added below them. Users frequently ask to remove these captions while keeping the image.

**Pattern to remove:**
```python
# Exact string match — captions are inline <p> tags with italic style
caption = '<p style="font-size:0.7rem;color:rgba(255,255,255,0.4);text-align:center;margin-top:4px;font-style:italic;">Gambar 3.4 Sitemap Website</p>'
content = content.replace(caption, '')
```

Use `grep -n "Gambar 3\." index.html` to find all captions first, then remove each one. The image `<img>` tag stays untouched.

## Desain Produk Slide: Split Screenshots from Feature List

When the Desain Produk slide has both screenshots AND a feature/page list, it will be too full. Split into two slides:

- **Slide N** — Tech Stack badges + website screenshots (visual proof)
- **Slide N+1** — Halaman Website list + Fitur Utama grid (detail)

This is the natural split: "here's what it looks like" → "here's what it does".

**Trigger:** User says "terlalu penuh" or "buat beberapa slide" for the Desain Produk slide.

## Academic Presentation: ADDIE vs Desain Produk Content Split

For Indonesian skripsi seminar presentations using ADDIE methodology, the content split between slides is:

- **ADDIE Design slide** → describe *what was planned* (sitemap, wireframe, instrumen validasi) — text + planning diagrams OK
- **ADDIE Development slide** → describe *how it was built* (vibe coding, tech stack, gambar struktur project)
- **Desain Produk slide** → show *the actual result* — screenshots of the live website
- **Demo Website slide** → live demo or additional screenshots

**Do NOT** put website screenshots in the ADDIE slides. Screenshots belong in Desain Produk. The ADDIE slides can have planning diagrams (sitemap, wireframe) but not the final product screenshots.

**Storytelling arc:** Planning → Building → Result → Demo. This is the natural flow dosen non-IT can follow.

**Tech stack for non-IT dosen:** When presenting to non-IT supervisors, avoid listing TypeScript as a separate tech stack item — it's an implementation detail they won't understand. Stick to: Next.js, Tailwind CSS, Vercel. If asked about "tech stack", explain it as "alat-alat yang dipakai untuk membangun website" (tools used to build the website).

**Vibe coding explanation for non-IT:** "Pendekatan pengembangan website yang memanfaatkan tools modern sehingga proses pembuatannya lebih cepat dan efisien, tanpa harus menulis semua kode dari nol." Do NOT add "berbantuan AI" — user prefers just "vibe coding" without the AI qualifier.

**Audience-specific content:** Remove audience-specific parentheticals from ADDIE Analysis descriptions (e.g., "(warga sekitar sekolah)") — keep descriptions generic. The audience detail belongs in the Metodologi Uji Efektivitas slide, not in the ADDIE Analysis description.

## Removing a Specific Badge/Element from a Slide

When a user says "hapus X dari slide Y" (e.g., a tech-badge that belongs to a different slide), use exact string match — don't regex unless the string is dynamic.

```python
with open('/tmp/seminar_fixed.html', 'r') as f:
    content = f.read()

# Find the exact badge text first
# grep -n "Nielsen\|badge-text" /tmp/seminar_fixed.html

# Then remove by exact match
badge = '<span class="tech-badge">&#128221; Nielsen (2012) — 10 responden uji kelayakan</span>'
content = content.replace(badge, '')

with open('/tmp/seminar_fixed.html', 'w') as f:
    f.write(content)

# Verify it's gone
assert 'Nielsen' not in content, "Badge still present!"
```

**Verification:** `curl -s https://your-url.vercel.app | grep -c "Nielsen"` — should return 0 (exit code 1 = no matches = success).

**Common case:** A badge that summarizes Bagian 1 methodology (e.g., "Nielsen (2012) — 10 responden") accidentally placed on the Bagian 2 (Uji Efektivitas) slide. Remove it from Bagian 2; it belongs only on the kelayakan/implementation slide.

## Academic Slide: Penelitian Terdahulu (Prior Research)

For Indonesian skripsi seminar presentations, the **Penelitian Terdahulu** slide should come after Kajian Pustaka and before Metodologi. Structure:

- One card per prior study (border-left colored by study)
- Each card: researcher name + year, italic title, method badge, result badge
- Bottom card: "Posisi Penelitian Ini" — persamaan + perbedaan with this research

```html
<div class="content-card anim-item" style="border-left:3px solid #7B2FBE;">
  <div style="display:flex;align-items:flex-start;gap:14px;">
    <span style="font-size:1.4rem;flex-shrink:0;">📌</span>
    <div>
      <p class="text-white font-semibold text-sm">Nurmilah (2018)</p>
      <p class="text-muted text-sm" style="margin-top:4px;font-style:italic;">Judul penelitian terdahulu</p>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px;">
        <span class="tag" style="background:rgba(123,47,190,0.15);color:#c084fc;border:1px solid rgba(123,47,190,0.3);">R&amp;D · ADDIE</span>
        <span class="tag tag-green">✓ Hasil singkat</span>
      </div>
    </div>
  </div>
</div>
```

**Posisi card** (always last, pink border-top):
```html
<div class="content-card anim-item" style="border-top:2px solid rgba(233,30,123,0.4);background:rgba(233,30,123,0.05);">
  <h4 class="text-accent font-semibold" style="margin-bottom:8px;">🔗 Posisi Penelitian Ini</h4>
  <p class="text-muted text-sm">Persamaan: ... Perbedaan: penelitian ini menggunakan <strong class="text-white">Next.js + Vercel</strong>, mengukur <em><strong class="text-white">brand awareness</strong></em>, desain <strong class="text-white">pre-post test</strong>.</p>
</div>
```

## Page Label Consistency Audit

After any slide insertion or reordering, page labels (`>01 / 14<`) often become inconsistent — different denominators (`/11`, `/13`, `/14`, `/15`) and non-standard suffixes (`06b`, `08b`, `11b`). Always normalize to a single consistent scheme.

**Fix with Python (exact string replacement):**
```python
fixes = [
    ('02 / 11', '01 / 14'),
    ('03 / 11', '02 / 14'),
    ('06b / 15', '06 / 14'),
    ('07 / 13', '07 / 14'),
    ('08b / 14', '09 / 14'),
    # ... etc
]
for old, new in fixes:
    content = content.replace(f'>{old}<', f'>{new}<')
```

**⚠️ PITFALL: nav-counter vs page-label** — the `<span id="navCounter">1 / 11</span>` in the nav bar is NOT a page label — it's updated dynamically by JS. Don't try to fix it; it will update automatically when navigating. Only fix `<span class="page-label">` elements.

**⚠️ PITFALL: Inline-styled page labels** — some slides have `<span class="page-label" style="...">06b / 15</span>` with custom colors. The `grep -n "page-label"` command will find them, but the replacement must still match `>06b / 15<` exactly (the `>` and `<` delimiters ensure you don't accidentally replace text inside a style attribute).

**Verification:**
```python
import re
labels = re.findall(r'>(\d+[ab]? / \d+)<', content)
print("Labels:", labels)
# Should be a clean sequence with consistent denominator
```

## Academic Slide: Uji Efektivitas — Statistical Analysis Display

For the Uji Efektivitas slide, show the full analysis pipeline visually:

**Structure:**
1. Pre-Post Test design diagram (O₁ → X → O₂) — top card
2. Sample badge (e.g., "👥 30 Warga Sekitar Sekolah") — centered below diagram
3. Two-column analysis cards:
   - Left: Gain Score & % Peningkatan
   - Right: Uji Normalitas + Uji Signifikansi

**⚠️ PITFALL: Gain Score formula** — % Peningkatan = (Gain / O₁) × 100%, NOT (O₂ − O₁) / O₁. Display as two separate lines:
```
Gain = O₂ − O₁
% Peningkatan = Gain × 100%
               ─────
                O₁
```
Use `border-top` CSS on a `<span>` to simulate a fraction bar. Show Gain first, then % Peningkatan referencing Gain — makes the two-step calculation explicit.

**⚠️ PITFALL: Missing decision criteria** — always add the significance threshold. For slides, keep it simple: just "Signifikan jika **p < 0,05**" — no need to show the full formula (t = d̄/sd√n or Z = (T−μT)/σT). The formula belongs in the written proposal/skripsi, not the presentation slide. User will ask to remove the formula if you include it.

If the user explicitly asks for the formula, show it — but default to criteria-only.

**⚠️ PITFALL: 3 analysis cards need 3-column grid** — when the Uji Efektivitas slide has Google Analytics + Gain Score + Uji Normalitas (3 cards), switch from `class="two-col"` to an explicit 3-column grid: `display:grid;grid-template-columns:repeat(3,1fr);gap:12px`. Using `two-col` with 3 cards causes the third card to overflow or wrap awkwardly.

**⚠️ PITFALL: Purposive Sampling badge on Uji Efektivitas slide** — sampling methodology belongs on the Partisipan/Metodologi slide, not on the Uji Efektivitas slide. Remove it if it appears there.

**⚠️ PITFALL: Nielsen (2012) badge on Uji Efektivitas slide** — Nielsen's 10-responden rule applies to uji kelayakan (Bagian 1), not uji efektivitas (Bagian 2). Remove from Bagian 2 slide.

**Uji Normalitas decision tree** (Shapiro-Wilk for n < 50):
```
H₀: data berdistribusi normal
p ≥ 0,05 → normal → Uji T Berpasangan
p < 0,05 → tidak normal → Uji Wilcoxon
```

### Google Analytics on Uji Efektivitas Slide

When the proposal includes web analytics as part of efektivitas measurement (check docx for "Google Analytics" or "web analytics"), add a Google Analytics card to the Uji Efektivitas slide. Use a 3-column grid (`display:grid;grid-template-columns:repeat(3,1fr)`) instead of two-col when adding this third card.

Metrik to display with their thresholds:
- Bounce Rate → < 40%
- Avg. Session Duration → > 2 menit
- Pages per Session → > 2 halaman
- Unique Visitors → deskriptif
- Returning Visitors → deskriptif

Use cyan (#00BCD4) as the accent color for the Google Analytics card.

**⚠️ PITFALL: Don't add Google Analytics if it's not in the proposal** — check the docx first with `grep -i "analytic\|web analytics"`. If the proposal only mentions pre-post test, don't add it. If it mentions "dua pendekatan: web analytics dan pre-post test", add it.

## Pitfall: Stray Elements on Wrong Slides

When building academic presentations, summary badges (e.g., `🔬 R&D — ADDIE`, `👥 30 Responden`) sometimes get placed on the wrong slide (e.g., Tujuan Penelitian instead of Metodologi). This happens when copy-pasting slide blocks during construction.

**Always audit** after building: read each slide's content and verify the elements belong there. If a slide has a `<div>` with tech-badges or methodology info that doesn't match the slide title, remove it.

```python
# Quick audit — grep for badge elements and check which slide they're in
grep -n "tech-badge\|badge\|🔬\|👥\|📋" index.html
# Then check the nearest slide id above each match
```

## Splitting an Overfull Slide into Two

When a slide has too much content (e.g., Development + Implementation + Evaluation all in one), split it by:
1. Extracting the bottom section into a new slide
2. Renumbering all subsequent slides using `sed` with TEMP placeholders
3. Adding a new game-card to the menu

**Pattern:**
```bash
# Step 1: Rename new slide to temp ID first
sed -i 's/id="slide-8b"/id="slide-8b-tmp"/g' index.html

# Step 2: Shift existing slides 9→10, 10→11, etc. (high to low to avoid collision)
sed -i 's/id="slide-12"/id="slide-13"/g; s/id="slide-11"/id="slide-12"/g; ...' index.html

# Step 3: Rename temp to final
sed -i 's/id="slide-8b-tmp"/id="slide-9"/g' index.html

# Step 4: Update goToSlide() calls and data-slide attributes the same way
sed -i 's/goToSlide(12)/goToSlide(13)/g; ...' index.html
sed -i 's/data-slide="12"/data-slide="13"/g; ...' index.html

# Step 5: Update totalSlides
sed -i 's/const totalSlides = 13;/const totalSlides = 14;/' index.html
```

**Then add the new game-card** to the menu grid between the two split slides.

**⚠️ PITFALL:** The `sed` approach with multiple substitutions in one command processes left-to-right, so always go high-to-low (12→13 before 11→12) to avoid double-renaming. Verify with `grep -n 'id="slide-'` after.

## Replacing a User-Cropped Image

When the user sends a cropped version of an embedded image (via Telegram/WhatsApp), replace the base64 in the HTML:

```python
import base64, re

# Encode the user's image
with open('/home/ubuntu/.hermes/image_cache/img_XXXX.jpg', 'rb') as f:
    new_b64 = base64.b64encode(f.read()).decode()

with open('/tmp/index.html', 'r') as f:
    content = f.read()

# Find the old base64 by alt text
match = re.search(r'src="data:image/jpeg;base64,([^"]+)" alt="Your Alt Text"', content)
if match:
    old_b64 = match.group(1)
    content = content.replace(old_b64, new_b64, 1)
    with open('/tmp/index.html', 'w') as f:
        f.write(content)
```

**Workflow:** User sends image → it lands in `/home/ubuntu/.hermes/image_cache/` → check size with `python3 -c "from PIL import Image; img=Image.open('path'); print(img.size)"` → encode and replace.

## Reordering Slides (DOM Order Fix)

When slide IDs are correct but DOM order is wrong (e.g., slide-12 appears before slide-10 in the HTML), navigation breaks because the browser renders them out of sequence.

**Diagnosis:**
```bash
grep -n 'id="slide-' index.html | grep -E "slide-(9|10|11|12)"
# If output shows slide-12 before slide-10 → DOM order is wrong
```

**Fix — Python block extraction and reorder:**
```python
import re

with open('/tmp/index.html', 'r') as f:
    content = f.read()

# Find start position of each slide by regex
starts = {}
for sid in [9, 10, 11, 12]:
    m = re.search(r'<div class="slide[^"]*"[^>]*id="slide-' + str(sid) + r'"', content)
    if m:
        starts[sid] = m.start()

body_end = content.rfind('</body>')

# Extract blocks (each block = from its start to next slide's start)
# Adjust slice boundaries based on actual order in DOM
block_before = content[:starts[9]]
block_9  = content[starts[9]:starts[12]]   # slide-9 to where slide-12 starts
block_12 = content[starts[12]:starts[11]]  # Desain Produk (wrongly placed)
block_11 = content[starts[11]:starts[10]]  # Demo Website
block_10 = content[starts[10]:body_end]    # Penutup
block_after = content[body_end:]

# Rename IDs to match correct order
block_12_renamed = block_12.replace('id="slide-12"', 'id="slide-10"', 1)
block_10_renamed = block_10.replace('id="slide-10"', 'id="slide-12"', 1)

# Reassemble in correct order
new_content = block_before + block_9 + block_12_renamed + block_11 + block_10_renamed + block_after

with open('/tmp/index_fixed.html', 'w') as f:
    f.write(new_content)

# Verify
for sid in [9, 10, 11, 12]:
    m = re.search(r'id="slide-' + str(sid) + r'"', new_content)
    print(f"slide-{sid} at {m.start() if m else 'NOT FOUND'}")
```

**Key points:**
- Slice boundaries depend on the *actual* (wrong) DOM order, not the desired order
- Rename IDs *after* extracting blocks, not before — avoids collision
- Always verify final positions with regex after reorder
- This is separate from the TEMP placeholder pattern (which is for shifting all slides +1)

## Swapping Two Adjacent Slides (Content Reorder)

When the user asks to swap the order of two slides (e.g., "slide 12 ke slide 11"), extract both blocks and reassemble in reversed order, renaming IDs in the process.

```python
with open('/tmp/index.html', 'r') as f:
    content = f.read()

pos11 = content.find('  <div class="slide ... id="slide-11">')  # adjust class
pos12 = content.find('  <div class="slide ... id="slide-12">')
pos_next = content.find('  <!-- SLIDE 12: ...')  # comment after slide-12

block11 = content[pos11:pos12]
block12 = content[pos12:pos_next]

# Swap IDs
block11_new = block11.replace('id="slide-11"', 'id="slide-12"', 1)
block12_new = block12.replace('id="slide-12"', 'id="slide-11"', 1)

# Reassemble: before + block12(now slide-11) + block11(now slide-12) + after
new_content = content[:pos11] + block12_new + block11_new + content[pos_next:]
```

**⚠️ PITFALL:** The `find()` call must match the exact opening tag including class names. Use `grep -n 'id="slide-11"'` first to see the exact line, then construct the search string accordingly. If the two slides have different CSS classes (e.g., `bg-dark-alt` vs `bg-gradient-1`), the find strings will differ.

**Verify after swap:**
```bash
grep -n 'id="slide-11"\|id="slide-12"\|slide-title' index.html | grep -E "slide-11|slide-12|Desain"
```

## Pitfall: Vercel Project Files Not on VPS

When a Vercel project was deployed from a temp directory (e.g., `/tmp/seminar-deploy/`), the source files are **gone after session end**. To edit the presentation later, you must:
1. Download current live version: `curl -s https://project.vercel.app/ -o /tmp/index.html`
2. Edit the downloaded file
3. Re-deploy from a new temp directory

**Best practice:** Always keep a persistent copy at a stable path like `/home/ubuntu/seminar-deck/index.html`. If the project was deployed from `/tmp/`, move it to a permanent location immediately after first deploy.

**Working copy pattern:** Keep `/tmp/seminar_fixed.html` as the working copy throughout a session. Always `cp /tmp/seminar_fixed.html /tmp/seminar-deploy/index.html` before each deploy — never edit the deploy directory directly. This way the working copy survives across multiple deploys in the same session.

## Presenting via Zoom (Fullscreen Without URL Visible)

When the user wants to present the HTML slide deck via Zoom screen share without showing the Vercel URL:

**Option 1 — F11 + Share Window (recommended):**
1. Open the URL or local HTML file in Chrome
2. Press **F11** → browser goes fullscreen (address bar hidden)
3. In Zoom → Share Screen → select the **Chrome window** (not "Entire Screen")
4. Audience only sees the slide content

**Option 2 — Chrome Kiosk Mode (Windows):**
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk https://your-url.vercel.app
```
Or via Win+R: `chrome --kiosk https://your-url.vercel.app`
Note: `chrome` alone won't work in Windows CMD — needs full path or Win+R.

**Option 3 — Local HTML file (no URL at all):**
Send the `.html` file to the user. When opened locally, address bar shows `file:///C:/Users/...` — not a domain. Still use F11 + share window.

**Option 4 — Zoom Portion of Screen (crop address bar):**
Zoom → Share Screen → Advanced tab → **Portion of Screen** → drag the green box to cover only the slide area, excluding the browser address bar.

**Viewing speaker notes while presenting:**
- **Dual monitor**: slide fullscreen on monitor 1 (shared), notes on monitor 2
- **Phone as notes**: open naskah/notes on phone, place beside laptop — most practical for single-monitor setups
- **Print notes**: classic fallback
- **Zoom Portion of Screen**: share only part of screen, keep notes visible in uncropped area (cramped but works)

**⚠️ PITFALL:** Sending `.html` files via Telegram fails ("Unsupported document type"). Always zip first: `zip PRESENTASI.zip PRESENTASI.html` then send the `.zip`.

## Delivery

- See `references/dark-theme-readability-fix.md` for fixing dark-theme contrast/readability issues (font sizes, rgba opacity thresholds, card visibility on dark backgrounds).

- See `references/seminar-hasil-the operator-session.md` for the June 2026 redesign session: v2 design system (glassmorphism, vw-based fonts), slide structure, data, deployment notes.

- Save as single `.html` file
- Test: open in browser, verify all cards clickable, back button works, repeat navigation works without refresh
- Always test the "click card → back to menu → click another card" flow before delivering

### Deploy to Vercel (Online Access)

Users often want the presentation accessible via URL (no download/extract needed). Deploy the single HTML file as a static site to Vercel:

```bash
# 1. Create a deploy directory with index.html + vercel.json
mkdir -p /tmp/seminar-deploy
cp /tmp/seminar_fixed.html /tmp/seminar-deploy/index.html

cat > /tmp/seminar-deploy/vercel.json << 'EOF'
{
  "version": 2,
  "builds": [{"src": "index.html", "use": "@vercel/static"}],
  "routes": [{"src": "/(.*)", "dest": "/index.html"}]
}
EOF

# 2. Deploy to Vercel (static site — no build step needed)
cd /tmp/seminar-deploy
npx vercel --prod --yes --token=$VERCEL_TOKEN --name=presentasi-seminar
```

**Note:** The `vercel.json` with `@vercel/static` builder is required when deploying a bare HTML file from a temp directory. Without it, Vercel may not detect the file correctly. The `--name` flag must match the existing project name if you want to update the same URL.

**Result:** Vercel auto-detects it as a static site, deploys in ~2-7 seconds, gives a URL like `https://presentasi-seminar.vercel.app`.

**Key points:**
- File MUST be named `index.html` in the deploy directory
- No `package.json` needed — Vercel serves it as plain static HTML
- The `--name` flag sets the subdomain (e.g., `presentasi-seminar.vercel.app`)
- If Vercel token expired, user needs to generate a new one at https://vercel.com/account/tokens
- This is separate from the Next.js website project — deploy from a different directory to avoid conflicts

### Deploy to Existing Vercel Project (Specific URL)

When the project already exists on Vercel (e.g., `seminar-deck.vercel.app`) and you need to update it, link the deploy directory to the specific project using `.vercel/project.json`:

```bash
# 1. Get project ID and user ID
PROJECT_ID=$(curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v9/projects/PROJECT-NAME" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")

ORG_ID=$(curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v2/user" | python3 -c "import json,sys; print(json.load(sys.stdin)['user']['id'])")

# 2. Create .vercel/project.json in the deploy directory
mkdir -p /tmp/seminar-deploy/.vercel
cat > /tmp/seminar-deploy/.vercel/project.json << EOF
{"projectId":"$PROJECT_ID","orgId":"$ORG_ID"}
EOF

# 3. Deploy — Vercel will update the existing project's production URL
cd /tmp/seminar-deploy
npx vercel --token $VERCEL_TOKEN --prod --yes 2>&1 | tail -10
```

**⚠️ PITFALL: `orgId` is NOT `uid`** — the `/v2/user` endpoint returns `user.id` (not `user.uid` which is null). Use `user.id` as the `orgId` value.

**⚠️ PITFALL: `--name` flag creates a NEW project** — if you use `--name=seminar-deck` without `.vercel/project.json`, Vercel may create a duplicate project instead of updating the existing one. Always use `.vercel/project.json` to target an existing project.

**Verification:** After deploy, check the aliased URL matches the expected domain:
```
▲ Aliased     https://seminar-deck.vercel.app  ← this line confirms correct project
```

### Messaging Platform Delivery

**Telegram/WhatsApp:** `.html` files are NOT supported as document uploads. Telegram rejects them with "Unsupported document type". Solution:
```bash
zip PRESENTASI.zip PRESENTASI.html
# Then send the .zip file
```
Always proactively zip HTML presentations before sending via messaging platforms. The user shouldn't have to ask twice.

### Companion Speaker Notes (Naskah Presentasi)

When delivering an HTML presentation for a seminar/sidang, **always pair it with speaker notes**. Users need a script to practice with. Deliver both files together:
1. `.zip` containing the HTML presentation
2. `.md` naskah/skrip with narasi per slide + anticipated Q&A

**Naskah structure per slide:**
```markdown
## 🎯 SLIDE N — JUDUL SLIDE

*[Petunjuk aksi dalam kurung — klik, tunjuk gambar, dll]*

"Narasi yang diucapkan, ditulis dalam tanda kutip.
Gunakan **bold** untuk poin penting.
Sebutkan referensi/nama peneliti saat relevan."

---
```

**Always include a Q&A tips section** at the end with anticipated questions and model answers. For skripsi seminar, common questions:
- Kenapa jumlah responden X?
- Apa itu [istilah teknis]? (vibe coding, tech stack, Gain Score, dll)
- Kenapa pakai model ADDIE?
- Apa bedanya Bagian 1 dan Bagian 2?

**Generate naskah from HTML content** by parsing slide text with Python HTMLParser, then writing narasi for each slide. Save as `.txt` file (not `.md`) — `.txt` is more universally readable and Telegram supports it natively. Send via `MEDIA:` path.


**⚠️ PITFALL: User uploads a newer docx mid-session** — when auditing slide content against the proposal, always check if the user has uploaded a newer version of the docx. The newer file may have additional sections (e.g., Google Analytics, updated penelitian terdahulu table) not in the original. Use the most recently uploaded docx for content audits.

**Naskah file format** (plain text, not markdown):
```
NASKAH PRESENTASI SEMINAR PROPOSAL SKRIPSI
Nama — NIM
Program Studi, Fakultas, Universitas
Tahun
================================================================

[SLIDE N — JUDUL SLIDE]
================================================================

Narasi yang diucapkan...
Sebutkan referensi saat relevan.
```

**Always include a CATATAN TEKNIS section** at the end:
- Estimasi durasi
- Urutan slide
- Tips teknis (browser tab terpisah untuk demo, dll)

