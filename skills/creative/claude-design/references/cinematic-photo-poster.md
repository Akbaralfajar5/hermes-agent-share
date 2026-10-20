# Cinematic Photo Poster / Fan-Art Composite Design

Technique for creating dramatic, cinematic poster designs in pure HTML/CSS using a user's photo as the hero image. Common for sports fan-art, motivational posters, event posters, and social media content.

## When to Use

- User provides a photo and wants a dramatic/cinematic poster
- Fan-art style composites (sports, music, events)
- Motivational/inspirational poster designs
- Social media content with dramatic effects
- Any "make this photo look epic" request

## Layer Architecture (z-index order)

Build the poster as stacked layers, each with a specific role:

```
z-index  1: Background base (dark gradient)
z-index  2: Fire/color glow blobs (blurred radial-gradients, animated)
z-index 10: Photo (with mask/fade edges)
z-index 11: Color grade overlays (mix-blend-mode: color + overlay)
z-index 12: Vignette (radial-gradient, transparent center → dark edges)
z-index 13: Top/bottom fade gradients (for text readability zones)
z-index 14: Effects layer (lens flares, heat lines, light streaks)
z-index 16: Particle system (sparks, embers, bokeh — JS-generated)
z-index 20: Typography + decorative elements (borders, corners, lines)
z-index 25: Film grain overlay
```

## Photo Placement — Critical Pitfalls

### Masking
Use `-webkit-mask-image` with `radial-gradient` for soft edge fade:
```css
.photo-wrap {
  -webkit-mask-image: radial-gradient(ellipse 75% 60% at 50% 45%, black 50%, transparent 85%);
}
```

**PITFALL: Mask too tight hides subjects.** Start with large ellipse (75%+ width) and shrink only if needed. Always verify with browser_vision that ALL people/subjects are visible.

### Object-fit for group photos
```css
.photo-wrap img {
  object-fit: cover;
  object-position: center 20%; /* Adjust to show faces, not feet */
  filter: contrast(1.4) saturate(0.75) brightness(1.1);
}
```

**PITFALL: Text overlapping faces.** The main title text at the bottom WILL overlap foreground subjects if the photo extends too low. Solutions:
1. Reduce photo container height (leave gap for text)
2. Move photo up (lower `top` value)
3. Reduce font size of main title
4. Use `object-position` to shift subjects upward within the frame

**PITFALL: Portrait photo in portrait poster seems easy but isn't.** Even when aspect ratios match, the photo's subject area rarely aligns with the poster's text zones. Always iterate positioning.

### Iterative verification is mandatory
Photo composite posters ALWAYS need 2-3 rounds of adjustment. Budget for this. Check after each round:
- Are all subjects visible?
- Does text overlap any faces?
- Is the photo large enough to be impactful?
- Do the edges fade naturally into the background?

## Color Grading

### Warm/Fire theme
```css
/* Color tint */
.color-grade {
  background: linear-gradient(160deg,
    rgba(255,40,0,.38),
    rgba(255,80,0,.22) 30%,
    rgba(200,40,0,.28) 60%,
    rgba(255,100,0,.22));
  mix-blend-mode: color;
}
/* Contrast boost */
.color-overlay {
  background: linear-gradient(180deg,
    rgba(255,60,0,.08),
    rgba(255,100,0,.05) 50%,
    rgba(200,30,0,.1));
  mix-blend-mode: overlay;
}
```

### Cool/Blue theme (sports, tech)
Replace reds/oranges with blues: `rgba(0,60,255,...)`, `rgba(0,120,255,...)`

### Split-tone (like the Persib example)
Left side warm, right side cool — use `linear-gradient(90deg, warm, cool)` on the color grade layer.

## Fire/Spark Particle System (JavaScript)

Generate 3 tiers of particles for depth:

```javascript
// Tier 1: Dense small sparks (100+)
size: 1.5-5px, animation: 3-5s, bottom 50% of poster

// Tier 2: Medium glowing embers (30+)
size: 5-15px, radial-gradient fill, animation: 5-12s, opacity: 0.7

// Tier 3: Large soft bokeh (12-15)
size: 15-40px, very transparent, blur(3px), animation: 7-16s
```

Animation keyframes should include lateral drift (translateX) for realism:
```css
@keyframes spark-rise {
  0%   { transform: translateY(0) translateX(0) scale(1); opacity: 1; }
  40%  { transform: translateY(-180px) translateX(-18px) scale(.75); opacity: .75; }
  100% { transform: translateY(-580px) translateX(6px) scale(.08); opacity: 0; }
}
```

Fire color palette: `#ff2200, #ff4400, #ff6600, #ff8800, #ffaa00, #ffcc00, #ffee00`

## Typography Stack

### Gothic/dramatic header
```css
font-family: 'UnifrakturMaguntia', cursive; /* Google Fonts */
text-shadow: 0 0 25px rgba(255,80,0,1), 0 0 50px rgba(255,40,0,.8), 0 0 80px rgba(200,20,0,.5);
```

### Main title (bold impact)
```css
font-family: 'Anton', sans-serif; /* Google Fonts */
font-size: 140-165px;
text-shadow: /* multiple layers for fire glow */
  0 0 15px rgba(255,80,0,1),
  0 0 60px rgba(255,40,0,.7),
  0 0 100px rgba(255,30,0,.5),
  6px 6px 0 rgba(150,15,0,.95); /* hard shadow for depth */
```

### Tagline
```css
font-family: 'Bebas Neue', sans-serif;
letter-spacing: 14-16px;
color: rgba(255,190,80,.9);
```

## Decorative Elements

- **Side fire bars**: 5-6px wide, gradient with box-shadow glow
- **Corner accents**: 3px border on two sides of a 55px box
- **Decorative lines**: `linear-gradient(90deg, color, transparent)` — 1-2px height
- **Film grain**: SVG feTurbulence as background-image, opacity 0.04-0.06

## Export to PNG

Use Playwright (available in Hermes) to screenshot:
```javascript
const { chromium } = require('/home/ubuntu/.hermes/hermes-agent/node_modules/playwright');
const browser = await chromium.launch();
const page = await browser.newPage();
await page.setViewportSize({ width: 1080, height: 1350 });
await page.goto('file:///path/to/poster.html');
await page.waitForTimeout(2000); // let animations settle
await page.screenshot({ path: 'poster.png', fullPage: false });
await browser.close();
```

Standard poster sizes:
- Instagram post: 1080×1350 (4:5)
- Instagram story: 1080×1920 (9:16)
- Square: 1080×1080
- YouTube thumbnail: 1280×720

## Poster Size Matching

Match the poster dimensions to the photo's aspect ratio when possible. For a 720×1280 portrait photo, a 1080×1350 or 1080×1920 poster works well. For landscape group photos, consider 1280×720 or 1920×1080.

## Checklist Before Delivery

- [ ] All subjects in photo clearly visible (verify with browser_vision)
- [ ] Text does NOT overlap any faces
- [ ] Color grading applied consistently
- [ ] Particle effects visible and animated
- [ ] Typography readable against background
- [ ] Vignette focuses attention on subjects
- [ ] Exported to PNG if user needs shareable image
- [ ] File path reported to user
