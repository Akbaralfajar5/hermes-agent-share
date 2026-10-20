# Claymorphism for Educational / Interactive Content

## When To Use
Educational artifacts (eJobsheet, learning modules, interactive guides) where the audience is students (SMK/university). The style is warm, approachable, tactile — not childish but friendly.

## Design Tokens

```css
:root {
  /* Warm Brown + Cream — food/craft-inspired */
  --clr-primary: #D97706;       /* amber-600 */
  --clr-primary-light: #F59E0B; /* amber-500 */
  --clr-primary-dark: #B45309;  /* amber-700 */
  --clr-primary-50: #FFFBEB;
  --clr-primary-100: #FEF3C7;
  --clr-primary-200: #FDE68A;
  --clr-secondary: #78350F;     /* brown-800 */
  --clr-surface: #FFFFFF;
  --clr-bg: #F5EDE3;            /* warm cream */
  --clr-bg-dots: #E8DDD0;       /* dot pattern color */
  --clr-ink: #1C1917;           /* stone-900 */
  --clr-ink-muted: #57534E;     /* stone-600 */

  /* Clay shadows — the signature look */
  --shadow-clay: 4px 4px 0 0 #D6CFC4, 8px 8px 0 0 rgba(0,0,0,0.04);
  --shadow-clay-sm: 2px 2px 0 0 #D6CFC4, 4px 4px 0 0 rgba(0,0,0,0.03);
  --shadow-clay-lg: 6px 6px 0 0 #D6CFC4, 12px 12px 0 0 rgba(0,0,0,0.05);
  
  --border-thick: 3px solid #1C1917;
  --border-thin: 2px solid #D6CFC4;
  
  --radius-md: 16px;
  --radius-lg: 24px;
  --radius-full: 9999px;
  
  /* Typography */
  --font-display: 'Baloo 2', cursive;  /* headings — playful but not childish */
  --font-body: 'DM Sans', sans-serif;  /* body — clean, modern */
  
  /* Motion */
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
}
```

## Background Pattern (Dotted)
```css
body {
  background-image: radial-gradient(var(--clr-bg-dots) 1px, transparent 1px);
  background-size: 24px 24px;
}
```

## Key Component Patterns

### Clay Card
```css
.clay {
  background: var(--clr-surface);
  border: var(--border-thick);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-clay);
  padding: var(--sp-8);
  transition: transform var(--dur-fast) var(--ease-bounce), box-shadow var(--dur-fast);
}
.clay:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-clay-lg);
}
```

### Pill Tabs (better than underline tabs for this style)
```css
.tab {
  padding: 8px 16px;
  border: 2px solid var(--clr-primary-200);
  border-radius: var(--radius-full);
  background: var(--clr-surface);
  font-family: var(--font-display);
  box-shadow: 2px 2px 0 0 #D6CFC4;
  transition: all 150ms var(--ease-bounce);
}
.tab.active {
  background: var(--clr-primary);
  color: white;
  border-color: var(--clr-primary-dark);
  box-shadow: 2px 2px 0 0 var(--clr-primary-dark);
}
```

### Buttons with Clay Shadow
```css
.btn {
  border-radius: var(--radius-full);
  border: var(--border-thick);
  box-shadow: 3px 3px 0 0 var(--clr-primary-dark);
  transition: all 150ms var(--ease-bounce);
}
.btn:hover { transform: translateY(-2px); box-shadow: 5px 5px 0 0 var(--clr-primary-dark); }
.btn:active { transform: scale(0.96); }
```

## SVG Icons (NOT Emoji)
Per `ui-ux-pro-max` skill: never use emoji as UI icons. Use inline SVG from Lucide/Heroicons. The icon system:
```css
.icon { width: 24px; height: 24px; display: inline-flex; flex-shrink: 0; }
.icon svg { width: 100%; height: 100%; }
```

## Anti-Pattern Checklist
- ❌ Aggressive gradients (use solid colors + shadows for depth)
- ❌ Glassmorphism (doesn't fit educational warmth)
- ❌ Emoji as functional icons (use SVG)
- ❌ Pure white background (use warm cream with dot pattern)
- ❌ Flat design without depth (clay shadows give tactile feel)
