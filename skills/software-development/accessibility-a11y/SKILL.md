---
name: accessibility-a11y
description: WCAG 2.1 AA compliance for web applications — keyboard navigation, screen reader support, ARIA attributes, color contrast, focus management. Use when building UI components, when reviewing for accessibility, or when users report usability issues. Covers Next.js/React patterns.
---

# Accessibility (a11y)

## Overview

Accessibility is not optional — it's a legal requirement in many jurisdictions and a professional standard. The goal is WCAG 2.1 AA compliance: every user can navigate, understand, and interact with your application regardless of ability.

## When to Use

- Building any user-facing component
- Forms with validation
- Navigation menus
- Modal dialogs and overlays
- Dynamic content updates
- Images, icons, and media

**When NOT to use:** Internal admin tools with known users (still good practice, but lower priority).

## The Quick Checklist

```
□ All images have alt text (or alt="" for decorative)
□ All form inputs have labels
□ Interactive elements are keyboard-accessible
□ Focus is visible on all interactive elements
□ Color contrast meets 4.5:1 ratio (text) / 3:1 (large text)
□ Page has proper heading hierarchy (h1 → h2 → h3)
□ Dynamic content announced to screen readers
□ Modals trap focus and return focus on close
□ Skip navigation link for keyboard users
```

## Keyboard Navigation

### Focusable Elements

```html
<!-- Naturally focusable -->
<a href="/about">About</a>
<button>Click me</button>
<input type="text" />
<select><option>...</option></select>
<textarea></textarea>

<!-- Make focusable (use carefully) -->
<div tabindex="0" role="button" onclick="handleClick()">Custom button</div>

<!-- Remove from tab order (last resort) -->
<button tabindex="-1">Skip this</button>
```

### Focus Management

```tsx
// Focus trap for modals
import { useEffect, useRef } from 'react';

function Modal({ isOpen, onClose, children }: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousFocus.current = document.activeElement as HTMLElement;
      modalRef.current?.focus();
    } else {
      previousFocus.current?.focus(); // return focus on close
    }
  }, [isOpen]);

  // Trap focus inside modal
  useEffect(() => {
    if (!isOpen) return;

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab' || !modalRef.current) return;

      const focusable = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      const first = focusable[0] as HTMLElement;
      const last = focusable[focusable.length - 1] as HTMLElement;

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleTab);
    return () => document.removeEventListener('keydown', handleTab);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      ref={modalRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      tabIndex={-1}
    >
      {children}
    </div>
  );
}
```

### Keyboard Event Handling

```tsx
// Button that works with Enter and Space
<div
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }}
>
  Click me
</div>

// Escape to close
useEffect(() => {
  const handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  };
  document.addEventListener('keydown', handleEscape);
  return () => document.removeEventListener('keydown', handleEscape);
}, [onClose]);
```

## ARIA Attributes

### Landmarks

```html
<header role="banner">Site header</header>
<nav role="navigation" aria-label="Main navigation">...</nav>
<main role="main">Page content</main>
<aside role="complementary">Sidebar</aside>
<footer role="contentinfo">Site footer</footer>
```

### Labels and Descriptions

```tsx
// aria-label — when no visible label
<button aria-label="Close dialog">
  <XIcon />
</button>

// aria-labelledby — reference visible label
<div id="search-label">Search products</div>
<input aria-labelledby="search-label" />

// aria-describedby — additional description
<input aria-describedby="password-hint" type="password" />
<p id="password-hint">Must be at least 8 characters</p>

// aria-required
<input aria-required="true" />

// aria-invalid
<input aria-invalid="true" aria-describedby="email-error" />
<p id="email-error" role="alert">Invalid email address</p>
```

### Live Regions (Dynamic Content)

```tsx
// Announce changes to screen readers
<div aria-live="polite">
  {isLoading ? 'Loading...' : `${results.length} results found`}
</div>

// Assertive — interrupts current announcement
<div aria-live="assertive" role="alert">
  Error: Connection lost
</div>

// Status — polite, non-interrupting
<div role="status">
  Cart updated: 3 items
</div>
```

### States and Properties

```tsx
// Expanded/collapsed
<button aria-expanded={isOpen} aria-controls="dropdown-menu">
  Menu
</button>
<ul id="dropdown-menu" hidden={!isOpen}>...</ul>

// Selected (tabs, options)
<button role="tab" aria-selected={isActive}>Tab 1</button>

// Checked (custom checkboxes)
<div role="checkbox" aria-checked={isChecked} tabIndex={0}>...</div>

// Busy/loading
<div aria-busy={isLoading}>...</div>

// Hidden from screen readers
<svg aria-hidden="true">...</svg>  {/* decorative icon */}
<span className="sr-only">Screen reader only text</span>
```

## Color Contrast

```
WCAG AA Requirements:
- Normal text (<18pt):   4.5:1 contrast ratio
- Large text (≥18pt):    3:1 contrast ratio
- UI components/graphics: 3:1 contrast ratio

Tools:
- Chrome DevTools → Rendering → Emulate vision deficiencies
- WebAIM Contrast Checker: webaim.org/resources/contrastchecker
- axe DevTools extension
```

### Common Fixes

```css
/* BAD: gray on white */
color: #999; background: #fff; /* ratio: 2.8:1 — FAIL */

/* GOOD: darker gray */
color: #595959; background: #fff; /* ratio: 7:1 — PASS */

/* Focus indicators — must be visible */
:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

/* Don't do this */
:focus { outline: none; } /* ← removes focus indicator — BAD */
```

## Forms

```tsx
// Accessible form with validation
function ContactForm() {
  const [errors, setErrors] = useState<Record<string, string>>({});

  return (
    <form noValidate onSubmit={handleSubmit}>
      {/* Label always associated with input */}
      <div>
        <label htmlFor="email">Email address</label>
        <input
          id="email"
          type="email"
          aria-required="true"
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? 'email-error' : undefined}
        />
        {errors.email && (
          <p id="email-error" role="alert" className="text-red-600">
            {errors.email}
          </p>
        )}
      </div>

      {/* Group related fields */}
      <fieldset>
        <legend>Preferred contact method</legend>
        <label>
          <input type="radio" name="contact" value="email" /> Email
        </label>
        <label>
          <input type="radio" name="contact" value="phone" /> Phone
        </label>
      </fieldset>

      <button type="submit">Send</button>
    </form>
  );
}
```

### Form Validation Announcements

```tsx
// Announce errors to screen readers
function ErrorSummary({ errors }: { errors: string[] }) {
  if (!errors.length) return null;

  return (
    <div role="alert" aria-live="assertive" className="bg-red-50 p-4 rounded">
      <h2>There {errors.length === 1 ? 'is 1 error' : `are ${errors.length} errors`}</h2>
      <ul>
        {errors.map((err, i) => <li key={i}>{err}</li>)}
      </ul>
    </div>
  );
}
```

## Images and Media

```tsx
// Informative image
<img src="/chart.png" alt="Sales increased 25% from Jan to Mar 2025" />

// Decorative image
<img src="/divider.png" alt="" role="presentation" />

// Complex image (chart, diagram)
<figure>
  <img src="/architecture.png" alt="System architecture diagram" aria-describedby="arch-desc" />
  <figcaption id="arch-desc">
    The system consists of a Next.js frontend connected to Supabase...
  </figcaption>
</figure>

// Video
<video controls aria-label="Product demo video">
  <track kind="captions" src="/captions.vtt" srcLang="en" label="English" />
</video>
```

## Heading Hierarchy

```html
<!-- GOOD: Logical hierarchy -->
<h1>Product Name</h1>
  <h2>Description</h2>
  <h2>Specifications</h2>
    <h3>Technical Details</h3>
    <h3>Dimensions</h2>
  <h2>Reviews</h2>

<!-- BAD: Skipping levels -->
<h1>Product Name</h1>
<h4>Description</h4>  <!-- skipped h2, h3 -->
```

## Tailwind Accessibility Utilities

```tsx
// Screen reader only text
<span className="sr-only">Close menu</span>

// Focus styles
<button className="focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
  Submit
</button>

// Skip to content
<a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4">
  Skip to content
</a>
```

## Testing

### Manual Testing

1. **Tab through entire page** — can you reach every interactive element?
2. **Use screen reader** (VoiceOver on Mac, NVDA on Windows) — does everything make sense?
3. **Zoom to 200%** — does layout still work?
4. **Disable CSS** — is content still readable and in order?
5. **Keyboard only** — can you complete all tasks without a mouse?

### Automated Testing

```bash
# axe-core for automated checks
npm install -D @axe-core/react

# In development
import '@axe-core/react/16'; // auto-runs in dev mode
```

```typescript
// Playwright a11y test
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('homepage has no a11y violations', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

## Anti-Rationalization

| Excuse | Reality |
|--------|---------|
| "It looks fine to me" | You're not a screen reader user. Test with actual assistive tech |
| "a11y is only for blind users" | Also helps: keyboard users, motor impairments, low vision, cognitive disabilities, slow connections |
| "We'll add it later" | Retrofitting a11y is 5x more expensive than building it in |
| "It's too much work" | Most a11y is just proper HTML semantics — less work, not more |
| "Our users don't need it" | 15% of the world population has a disability. You don't know your users' abilities |

## Red Flags

- `tabindex` > 0 (messes up tab order)
- `outline: none` without visible replacement
- Click handlers on `<div>` without `role` and keyboard support
- Images without `alt` text
- Form inputs without `<label>`
- Color as the only way to convey information
- Auto-playing audio/video without controls

## Verification

- [ ] All interactive elements keyboard-accessible
- [ ] Focus visible on every focusable element
- [ ] Form inputs have associated labels
- [ ] Dynamic content announced via aria-live
- [ ] Modals trap and restore focus
- [ ] Color contrast meets WCAG AA (4.5:1)
- [ ] Heading hierarchy is logical (no skipped levels)
- [ ] Screen reader testing completed
- [ ] axe-core scan passes with 0 violations
