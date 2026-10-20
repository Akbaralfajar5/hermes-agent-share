# Next.js 14 Build Fixes — Common Pitfalls

## Context Provider SSR Crash
**Error**: `useTheme must be used within a ThemeProvider` during `next build` static prerender.

**Root cause**: `createContext(undefined)` + `if (!ctx) throw new Error(...)` in the hook.
During SSR/prerender, the provider returns `<>{children}</>` without setting context,
so the hook gets `undefined` and throws.

**Fix**: Always provide a default value object:
```tsx
// ❌ Breaks SSR
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);
export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within a ThemeProvider');
  return ctx;
}

// ✅ Works with SSR
const ThemeContext = createContext<ThemeContextType>({
  theme: 'light',
  toggleTheme: () => {},
});
export function useTheme() {
  return useContext(ThemeContext);  // no throw needed
}
```

## Tailwind CSS Import Syntax Mismatch
**Error**: `Module not found: Can't resolve 'tailwindcss'` in webpack.

**Root cause**: `create-next-app@14` installs Tailwind v3, but the CSS file uses v4 syntax.

| Version | Syntax in globals.css |
|---------|----------------------|
| v3      | `@tailwind base; @tailwind components; @tailwind utilities;` |
| v4      | `@import "tailwindcss";` |

**Fix**: Check `node_modules/tailwindcss/package.json` version. Use matching syntax.

## ESLint Blocks Build
**Error**: `Type error: ...` or ESLint warnings treated as errors.

**Fix**: Add to `next.config.mjs`:
```js
const nextConfig = {
  eslint: { ignoreDuringBuilds: true },
};
```

## TypeScript Strict Type Errors
**Error**: `Type 'X' is not assignable to type 'Y'` — common with `as const` narrowing.

**Fix**: Use explicit union types instead of `as const`:
```tsx
// ❌ Too narrow
const [status, setStatus] = useState('active' as const);

// ✅ Correct
const [status, setStatus] = useState<'active' | 'archived' | 'draft'>('active');
```

## SIGBUS Error on Low-RAM VPS
**Error**: `Bus error (core dumped)` during `next build`.

**Root cause**: SWC binary mmap issue on VPS with <2GB RAM. `NODE_OPTIONS=--max-old-space-size` does NOT help.

**Fix**: Don't build locally. Use Vercel cloud build or prebuilt approach:
```bash
vercel build --yes   # might still fail locally
vercel deploy --prebuilt --prod --yes  # if .vercel/output exists
```

## Bulk Project Scaffolding Pattern
When building many Next.js projects at once:
1. Scaffold all with `create-next-app` (3-4 at a time max)
2. Add `.npmrc` with `registry=https://registry.npmjs.org/` to each
3. Fix globals.css Tailwind syntax
4. Add `eslint: { ignoreDuringBuilds: true }` to next.config
5. Verify build locally
6. Deploy with `--no-wait` in batches of 2-3

## Lucide-React Missing Icons
**Error**: `Module '"lucide-react"' has no exported member 'Github'` (also `Linkedin`, `Twitter`).

**Root cause**: Newer lucide-react removed brand icons (trademark). Check: `node -e "const l = require('lucide-react'); console.log('Github:', !!l.Github)"`

**Fix**: Create custom SVG components in `src/components/icons.tsx`:
```tsx
export function GithubIcon({ size = 24, className = '' }: { size?: number; className?: string }) {
  return (<svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" className={className}><path d="M12 0c-6.626 0-12 5.373-12 12..."/></svg>);
}
// Same pattern for LinkedinIcon, TwitterIcon
```
Import from `'./icons'` instead of `'lucide-react'`.

## Subagent File Corruption (Line Numbers Embedded)
**Symptom**: `     1|'use client';` in source files → build syntax errors.

**Root cause**: Subagent reads via `read_file` (returns `LINE_NUM|CONTENT`), writes back via `write_file` without stripping line numbers.

**Fix**: `sed -i 's/^[[:space:]]*[0-9]*|//' *.tsx` in affected directory.

**Prevention**: Subagents should use `terminal("cat <file>")` for raw reads, or strip line numbers before writing.

## Dark/Light Mode ThemeProvider Pattern
```tsx
// src/components/ThemeProvider.tsx — 'use client'
const ThemeContext = createContext<ThemeContextType>({ theme: 'dark', toggleTheme: () => {} });
// useState + useEffect for localStorage + matchMedia
// useEffect to toggle 'dark'/'light' class on document.documentElement
```

**CSS variables** (preferred over Tailwind `dark:` classes):
```css
:root { --bg: #0a0a0a; --text: #e5e7eb; }
:root.light { --bg: #ffffff; --text: #111827; }
body { background: var(--bg); color: var(--text); }
```

**layout.tsx**: Add `suppressHydrationWarning` to `<html>` to prevent SSR mismatch.

## Dark Mode Text Contrast Pitfalls
**Symptom**: Text invisible or hard to read in dark mode — text color clashes with background.

**Common mistakes** (Tailwind classes):
| Class | Problem on dark bg |
|-------|-------------------|
| `text-gray-500 dark:text-gray-500` | Same shade in both modes — too dark on `#0a0a0a` |
| `text-gray-400 dark:text-gray-600` | 600 is nearly invisible on dark backgrounds |
| `text-gray-500 dark:text-gray-500` | Should be `dark:text-gray-400` or `dark:text-gray-300` |

**Fix — safe dark-mode text classes**:
```
Body text:       text-gray-600 dark:text-gray-300
Secondary text:  text-gray-500 dark:text-gray-400
Muted text:      text-gray-500 dark:text-gray-400 (NOT gray-600)
Footer/caption:  text-gray-500 dark:text-gray-400
Hover states:    hover:text-gray-900 dark:hover:text-white
```

**Rule of thumb**: Dark mode text should be `gray-300` or `gray-400` minimum. Never `gray-600` on dark.

## Portfolio Design Anti-Patterns
When building developer portfolios, avoid:
- **Emoji as project card images** — looks AI-generated, unprofessional
- **Large gradient banner placeholders** — adds no value, looks like template
- **GitHub/Source Code links** on personal branding sites — exposes code, enables copying
- **3-column grid for project cards** — too narrow for descriptions, use 2-column

**Professional portfolio card pattern**: Clean card with title, description, tech tags, single CTA button (solid gradient, not outlined). No decorative header area.

**Personal branding repos**: Keep GitHub repos PRIVATE. Portfolio shows Live Demo links only.

**Skills section layout**: User prefers card grid with tech tag pills (NOT progress bars / skill bars). Progress bars look dated and imply false precision. Card grid is cleaner:
```
[Frontend]           [Backend]           [Blockchain & Trading]
React  Next.js       Node.js  Python      Solana  Web3.js
TypeScript           FastAPI  REST API     Trading Bots  DeFi
```
Each card: category name with colored dot, then flex-wrap of pill-shaped tech tags.

## Mobile Hamburger Menu Bug Fix
**Symptom**: Hamburger menu click doesn't work when page is scrolled down.

**Root cause**: Z-index conflicts between fixed navbar, backdrop overlay, and menu content. When scrolled, the backdrop may intercept clicks before they reach the button.

**Fix pattern** in `Navbar.tsx`:
```tsx
// Button: highest z-index
<button onClick={() => setMobileOpen(prev => !prev)}
        className="relative z-[60] ..." />

// Backdrop: behind button but above content
{mobileOpen && (
  <div className="fixed inset-0 z-[45] bg-black/50 backdrop-blur-sm"
       onClick={() => setMobileOpen(false)} />
)}

// Menu panel: between backdrop and button
<div className="fixed inset-x-0 top-0 z-[55] ...">
```

Also add `e.stopPropagation()` on the button click handler to prevent event bubbling to the backdrop.

**Functional state update** is important: use `setMobileOpen(prev => !prev)` not `setMobileOpen(!mobileOpen)` — the stale closure of `mobileOpen` can cause missed toggles.

## npm "Exit handler never called" on Vercel

**Error**: Vercel cloud build fails during `npm install` with:
```
npm error Exit handler never called!
npm error This is an error with npm itself. Please report this error at:
npm error   <https://github.com/npm/cli/issues>
Error: Command "npm install" exited with 1
```

**Root cause**: Generic npm/Vercel infra race condition. NOT a code or dependency problem. Local `npm run build` and `npm install` work fine. Happens intermittently on Vercel's build infrastructure.

**Fix**: Use prebuilt deploy — build locally, upload output:
```bash
cd ~/project
npm run build                    # or: npx next build
vercel build --prod --yes        # produces .vercel/output/
vercel deploy --prebuilt --prod --yes --token "$VERCEL_TOKEN"
```

**Distinguish from Tencent mirror issue**: Tencent mirror errors show `http://mirrors.tencentyun.com` in the npm error output. "Exit handler never called" has no such URL — it's a pure npm infra flake.
