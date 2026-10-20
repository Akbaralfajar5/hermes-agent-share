# Next.js Portfolio / Landing Page Pattern

Single-page portfolio with scroll sections, animations, and theme toggle.

## Stack
- Next.js 14 (App Router)
- Tailwind CSS
- Framer Motion (scroll animations)
- Lucide icons (UI) + custom SVG (brand icons)
- Vercel (deploy)

## Section Architecture
```
src/
├── app/
│   ├── layout.tsx          ← ThemeProvider wrapper
│   ├── page.tsx            ← Compose all sections
│   └── globals.css         ← CSS variables for both themes
├── components/
│   ├── ThemeProvider.tsx    ← Context + localStorage + data-theme
│   ├── Navbar.tsx           ← Sticky, blur backdrop, theme toggle
│   ├── Hero.tsx             ← Full-screen, status badge, CTAs, socials
│   ├── About.tsx            ← Highlight cards + stats grid
│   ├── Skills.tsx           ← Category grid with skill tags
│   ├── Portfolio.tsx        ← Project cards (2-col grid)
│   ├── Experience.tsx       ← Timeline (alternating sides on desktop)
│   ├── Contact.tsx          ← Contact cards + CTA button
│   ├── Footer.tsx           ← Brand + social + copyright
│   └── SocialIcons.tsx      ← Custom SVG for Github, LinkedIn
```

## Key Patterns

### Section component template
```tsx
"use client";
import { motion } from "framer-motion";

export default function SectionName() {
  return (
    <section id="name" className="section-padding relative">
      <div className="max-w-6xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <span className="text-sm font-semibold tracking-widest uppercase mb-4 block"
            style={{ color: "var(--accent)" }}>Label</span>
          <h2 className="text-3xl sm:text-4xl font-bold" style={{ color: "var(--text-primary)" }}>
            Heading <span className="gradient-text">Accent</span>
          </h2>
        </motion.div>
        {/* Content */}
      </div>
    </section>
  );
}
```

### Glass card style
```tsx
<div className="glass-card rounded-2xl p-6">
  {/* card content */}
</div>
```
Defined in globals.css with `var(--bg-card)`, `var(--border)`, `var(--shadow-card)`.

### Skill tags
```tsx
<span className="skill-tag px-3 py-1.5 rounded-lg text-xs font-medium cursor-default"
  style={{ background: "var(--tag-bg)", color: "var(--tag-text)" }}>
  {skill}
</span>
```

### Timeline layout
- Mobile: single column with `pl-14` for dot + line on left
- Desktop: alternating sides with `md:flex md:items-start`
- Line: absolute positioned, gradient from accent to transparent
- Dots: 18px circles with accent border, bg-primary fill

## Pitfalls
- **Framer Motion `whileInView`** doesn't fire in headless browsers (Playwright, Puppeteer) because Intersection Observer doesn't trigger without real viewport interaction. The sections render but stay at `opacity: 0`. This is a testing artifact only — works fine in real browsers.
- **Build before deploy**: Always `npm run build` locally first to catch TypeScript/import errors. The Vercel build environment won't show friendly error context.
- **`section-padding`**: 120px desktop, 80px mobile. Defined in globals.css. Don't use Tailwind's `py-24` — it doesn't responsive-adapt.
