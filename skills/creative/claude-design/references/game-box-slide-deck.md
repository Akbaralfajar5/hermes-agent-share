# Game Box Interactive Slide Deck Pattern

## Overview
A single-file HTML presentation where Slide 1 is a "game box menu" — a grid of clickable cards that navigate directly to specific slides. Each content slide has a "Back to Menu" button. Used for academic presentations (seminar proposal, thesis defense) with a modern/interactive feel.

## Architecture

### Slide Structure
- `slide-0`: Game Box Menu (hub) — grid of clickable cards
- `slide-1` through `slide-N`: Content slides
- Each slide is a full-viewport `<div>` with `position: fixed; inset: 0`
- Only one slide has `.active` class at a time

### Navigation State Machine
```
Menu (slide-0) --[click card]--> Content Slide (slide-N)
Content Slide --[← Kembali ke Menu]--> Menu (slide-0)
Content Slide --[← →]--> Adjacent Content Slide
Content Slide --[Escape]--> Menu (slide-0)
```

### Critical Bug: isAnimating Lock After goToMenu()

**Problem:** After navigating to a content slide and back to menu, clicking cards again does nothing. The `isAnimating` flag gets stuck as `true`.

**Root Cause:** The `goToMenu()` function's cleanup timeout doesn't properly reset all element styles, causing the next `goToSlide()` call to see stale state or the `isAnimating` guard to block.

**Fix — goToMenu() must:**
1. Set `menuEl.style.visibility = 'visible'` before adding `.active`
2. Reset `menuEl.style.filter = 'none'` in the animation frame
3. Set `card.style.pointerEvents = 'auto'` for all game cards
4. In cleanup timeout, reset ALL inline styles on both `currentEl` and `menuEl`:
   - `.transform`, `.opacity`, `.visibility`, `.filter`
5. Set `isAnimating = false` LAST in the timeout

```javascript
function goToMenu() {
  if (currentSlide === 0) return;
  if (isAnimating) return;
  isAnimating = true;

  const currentEl = document.getElementById(`slide-${currentSlide}`);
  const menuEl = document.getElementById('slide-0');

  currentEl.classList.remove('active');
  currentEl.classList.add('exit-menu');

  menuEl.style.transform = 'scale(0.85)';
  menuEl.style.opacity = '0';
  menuEl.style.visibility = 'visible';  // CRITICAL
  menuEl.classList.add('active');
  void menuEl.offsetWidth;

  requestAnimationFrame(() => {
    menuEl.style.transform = 'scale(1) rotateY(0deg)';
    menuEl.style.opacity = '1';
    menuEl.style.filter = 'none';  // CRITICAL
  });

  currentSlide = 0;
  updateUI();

  // Re-enable card interactions
  const cards = document.querySelectorAll('.game-card');
  cards.forEach((card, i) => {
    card.style.animation = 'none';
    card.style.pointerEvents = 'auto';  // CRITICAL
    void card.offsetWidth;
    card.style.animation = `cardAppear 0.6s ease ${0.1 + i * 0.05}s backwards`;
  });

  setTimeout(() => {
    // Reset ALL inline styles
    currentEl.classList.remove('exit-menu');
    currentEl.style.transform = '';
    currentEl.style.opacity = '';
    currentEl.style.visibility = '';
    currentEl.style.filter = '';
    menuEl.style.transform = '';
    menuEl.style.opacity = '';
    menuEl.style.filter = '';
    menuEl.style.visibility = '';
    isAnimating = false;  // MUST be last
  }, 650);
}
```

### goToSlide() Guard
Always validate index bounds:
```javascript
function goToSlide(index, direction = 'forward') {
  if (isAnimating || index === currentSlide) return;
  if (index < 0 || index >= totalSlides) return;  // bounds check
  isAnimating = true;
  // ...
}
```

## Design Elements

### Game Card Grid
- CSS Grid: `grid-template-columns: repeat(5, 1fr)` → responsive to 3 → 2 cols
- Each card: glassmorphism (`backdrop-filter: blur`), gradient border on hover
- Hover: `transform: scale(1.05)`, `box-shadow` glow, icon rotation
- Staggered entrance: `animation: cardAppear 0.6s ease ${delay}s backwards`

### Transitions Between Slides
- Forward: `translateX(80%) rotateY(10deg) scale(0.85)` → `scale(1) rotateY(0deg)`
- Backward: `translateX(-80%) rotateY(-10deg) scale(0.85)` → same
- To menu: `scale(0.8) blur(5px)` → `scale(1)`
- Duration: 650ms (match cleanup timeout)

### Embedding Images (Logo)
Convert image to base64 and embed as data URI:
```html
<img src="data:image/jpeg;base64,{b64_string}" alt="Logo" 
     style="width:80px;height:80px;border-radius:50%;box-shadow:0 4px 20px rgba(255,255,255,0.2);">
```

## Typical Slide Count for Indonesian Seminar Proposal
1. Menu Hub (game box)
2. Latar Belakang
3. Rumusan Masalah
4. Tujuan Penelitian
5. Manfaat Penelitian
6. Kajian Pustaka
7. Metodologi
8. Desain Produk
9. Demo Website
10. Timeline
11. Penutup & Terima Kasih

## Hybrid Light/Dark Slide Pattern (Polished Academic Look)

**Anti-monotony technique.** Don't make all 14 content slides the same dark navy. Mix dark and light slides intentionally to create visual rhythm and let key slides "pop":

```
Slide 0  (Menu)        — Dark + glassmorphism (gradient navy)
Slide 1  (Cover)       — Dark + gradient (full impact opening)
Slide 2  (Latar Bel.)  — Light (problem statement, easy to read)
Slide 3  (Rumusan)     — Light (numbered cards)
Slide 4  (Theory 1)    — Dark (concept emphasis, pyramid diagram)
Slide 5  (Theory 2)    — Light (stats cards work better on light)
Slide 6  (Lit Review)  — Light (table readability)
Slide 7  (Framework)   — Light (flow diagram)
Slide 8  (Methodology) — Dark (formula slot, math notation)
Slide 9  (Procedure)   — Light (5-step horizontal flow)
Slide 10 (Sampling)    — Light (big stat numbers)
Slide 11 (Instruments) — Light (table)
Slide 12 (Analysis)    — Dark (metrics list with icons, formula cards)
Slide 13 (Product)     — Light (tech stack badges)
Slide 14 (Closing)     — Dark + gradient (full impact closing)
```

**Why this works:**
- Dark for **emotion** (cover, theory emphasis, methodology, closing)
- Light for **information density** (tables, lists, stats, comparison)
- Roughly 60% light / 40% dark prevents committee fatigue
- Glassmorphism cards on dark slides + clean borders on light slides

## Slide Polish Patterns

These patterns elevate the deck from "AI default" to "designed":

### Eyebrow + Title Pattern
Every content slide starts with:
```html
<div class="slide-eyebrow">02 · Pendahuluan</div>  <!-- 11px gold, 3px letter-spacing -->
<h2 class="slide-title">Latar Belakang</h2>          <!-- 42px Plus Jakarta Sans 800 -->
<p class="slide-tagline">One-line summary.</p>       <!-- 16px secondary text -->
```
Gold horizontal line before eyebrow text. This is the most consistent visual anchor.

### Watermark Year
On cover slide, place the year as a giant translucent number in the bottom-right corner:
```css
.cover-year {
  position: absolute; bottom: 40px; right: 60px;
  font-size: 80px; font-weight: 800;
  color: rgba(212, 168, 67, 0.15);  /* gold @ 15% opacity */
}
```
Visually anchors the slide without being loud.

### Numbered Card Squares (instead of bullets)
For rumusan masalah / tujuan / manfaat — use small numbered squares instead of bullets:
```html
<div style="display:flex; gap:14px;">
  <div style="width:32px; height:32px; background:var(--navy);
              color:var(--gold-bright); border-radius:8px;
              display:flex; align-items:center; justify-content:center;
              font-weight:800;">1</div>
  <div>...question text...</div>
</div>
```
More distinctive than `<ol>` and easier to scan.

### Mathematical Formula Display
For statistical formulas (Gain Score, p-value, eksperimen design O₁→X→O₂), use JetBrains Mono in gold on dark card:
```html
<div style="font-family: 'JetBrains Mono', monospace;
            font-size: 36px; color: var(--gold-bright);
            letter-spacing: 4px;">O₁ → X → O₂</div>
```

### Metric Row (for analytics dashboards)
Web analytics or KPI metrics look better as rows than tables:
```html
<div class="metric-row">
  <div class="metric-icon">🚪</div>
  <div>
    <div class="metric-name">Bounce Rate</div>
    <div class="metric-desc">% pengunjung keluar... (target <40%)</div>
  </div>
</div>
```
Icon in colored square + name + threshold annotation in gold.

## Font Stack for Academic Decks

Avoid Arial/default sans. Use this combo (from Google Fonts):
- **Headlines:** Plus Jakarta Sans 800 (modern, geometric)
- **Body:** Inter 400/500/600 (readable, neutral)
- **Code/Mono:** JetBrains Mono 400/600 (formulas, NIM, URLs)

Single Google Fonts request:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
```

## Color Palette: Navy + Gold Academic

Reusable across Indonesian academic decks (UPI, ITB, UI, etc. — adjust hue):
```css
:root {
  --navy-deep: #0A0E27;        /* darkest, deck backgrounds */
  --navy: #1E2761;             /* primary, headings, badges */
  --navy-light: #2A3A7D;       /* gradients, hover states */
  --gold: #D4A843;             /* accent, dividers, eyebrows */
  --gold-bright: #F0C75A;      /* highlights, emphasis */
  --gold-soft: rgba(212, 168, 67, 0.15);  /* subtle backgrounds */
  --cream: #FAF8F3;            /* light slide bg (warmer than white) */
  --surface: #FFFFFF;          /* card backgrounds on light slides */
  --text-primary: #0F172A;     /* slate-900, body text on light */
  --text-secondary: #475569;   /* slate-600, secondary on light */
  --text-muted: #94A3B8;       /* slate-400, captions */
}
```

## Game Card Performance Pattern

When building 14+ game cards, use staggered animation delays for cinematic entrance:
```html
<div class="game-card" style="animation-delay: 0.10s;">...</div>
<div class="game-card" style="animation-delay: 0.15s;">...</div>
<div class="game-card" style="animation-delay: 0.20s;">...</div>
```
Increment by 0.05s, not 0.1s — too slow feels laggy. Cap at ~0.7s total (after ~14 cards).

## Verification Checklist Before Delivery

- [ ] Total slides count: 1 menu + N content slides
- [ ] Game cards count == content slide count
- [ ] HTML structure valid (run `html.parser` check or `tidy`)
- [ ] All slides have `id="slide-N"` matching the goToSlide(N) calls in cards
- [ ] Cover slide year matches current year (verify against memory)
- [ ] Pembimbing names spelled correctly (verify against latest skripsi document)
- [ ] No emoji as primary icons (use SVG or styled text); emojis as decorative accents are OK in academic context
- [ ] Each slide has `slide-eyebrow` + `slide-title` + `slide-tagline` (consistency)
- [ ] No flow diagram with 5+ horizontal items unless using `display: grid` (the flex-overflow pitfall)
- [ ] At least one mid-deck slide breaks the pattern (e.g., dark accent slide, big stat callout)
