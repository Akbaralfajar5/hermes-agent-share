---
name: nextjs-react-typescript
description: Expert in TypeScript, Node.js, Next.js App Router, React, Shadcn UI, Radix UI and Tailwind
---

# Next.js React TypeScript

You are an expert in TypeScript, Node.js, Next.js App Router, React, Shadcn UI, Radix UI and Tailwind.

## Code Style and Structure

- Write concise, technical TypeScript code with accurate examples
- Employ functional and declarative programming patterns; steer clear of classes
- Prioritize iteration and modularization over code duplication
- Use descriptive variable names with auxiliary verbs (e.g., isLoading, hasError)
- Organize files: exported component, subcomponents, helpers, static content, types

## Naming Conventions

- Use lowercase with dashes for directories (e.g., components/auth-wizard)
- Favor named exports for components

## TypeScript Usage

- Use TypeScript for all code; prefer interfaces over types
- Avoid enums; use maps instead
- Use functional components with TypeScript interfaces

## Syntax and Formatting

- Use the "function" keyword for pure functions
- Avoid unnecessary curly braces in conditionals
- Use declarative JSX

## UI and Styling

- Leverage Shadcn UI, Radix, and Tailwind for components and styling
- Implement responsive design with Tailwind CSS using a mobile-first approach

## Performance Optimization

- Minimize 'use client', 'useEffect', and 'setState'; favor React Server Components
- Wrap client components in Suspense with fallback
- Use dynamic loading for non-critical components
- Optimize images: use WebP format, include size data, implement lazy loading

## Key Conventions

- Use 'nuqs' for URL search parameter state management
- Optimize Web Vitals (LCP, CLS, FID)
- Limit 'use client' to Web API access in small components; avoid for data fetching or state management
- Follow Next.js documentation for Data Fetching, Rendering, and Routing

## Vercel Deployment

### Quick Deploy (When It Works)
```bash
npx vercel --prod --yes --token=xxx
```
Try this first. Only use workarounds below if it fails.

### Pre-built Deploy (Bypasses npm install failures)
When remote build fails with `npm error Exit handler never called!`:
```bash
VERCEL_TOKEN=xxx vercel pull --yes
VERCEL_TOKEN=xxx vercel build --prod
VERCEL_TOKEN=xxx vercel deploy --prebuilt --prod --yes
```

### Yarn Workaround (Alternative)
Add `vercel.json`: `{"installCommand": "yarn install", "buildCommand": "yarn build"}`
See `references/vercel-yarn-workaround.md`.

### Auto-Deploy from GitHub

Connect a Vercel project to a GitHub repo so every `git push` triggers automatic deployment:

1. **Push code to GitHub** — init repo, add remote, push
2. **Link via Vercel API:**
```bash
curl -s -X POST "https://api.vercel.com/v13/projects/PROJECT_NAME/link?teamId=TEAM_ID" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"github","repo":"OWNER/REPO"}'
```
3. **Verify:** Check `link.type` and `link.repo` in project GET response
4. After linking, `git push origin main` → Vercel auto-builds and deploys

**Pitfall:** The Vercel dashboard login approach requires browser auth. Use the REST API (`v13/projects/{name}/link`) instead — works with just the Vercel token.

**Pitfall:** Environment variables (like `GITHUB_TOKEN`) must be added BEFORE linking or re-deployed after linking. Use `vercel env add VAR_NAME production`.

### Common Failures

| Error | Fix |
|-------|-----|
| `npm error Exit handler never called!` | (1) Add project `.npmrc` with `registry=https://registry.npmjs.org/`, (2) regenerate lockfile with `--lockfile-version=2`, (3) if still failing after 3+ attempts, use `--prebuilt` deploy: `vercel build --prod --yes && vercel deploy --prebuilt --prod --yes`. Both `build` and `deploy` must use `--prod` — mismatch causes "environment mismatch" error. |
| `Node.js Version "18.x" is discontinued` | Set `"engines": {"node": "20.x"}` in package.json |
| `No Project Settings found locally` | Run `vercel pull --yes` first |
| Token expired between sessions | Ask user for new token from vercel.com/account/tokens |
| `Bus error (core dumped)` on build | OOM or SWC issue on low-RAM VPS (<2GB). Deploy to Vercel directly — their build servers have 8GB. Don't waste time retrying locally. |
| `npm error ENOTFOUND mirrors.tencentyun.com` on Vercel | Tencent VPS has global `.npmrc` with mirror. Fix: add project `.npmrc` with `registry=https://registry.npmjs.org/` AND `sed -i 's|http://mirrors.tencentyun.com/npm/|https://registry.npmjs.org/|g' package-lock.json` to purge baked-in URLs. |

### Tencent Cloud VPS + Vercel Deploy Pitfall

When developing on Tencent Cloud VPS, the global `~/.npmrc` contains `registry=https://mirrors.tencentyun.com/npm`. This causes TWO problems:

1. **package-lock.json** gets Tencent mirror URLs baked into `resolved` fields
2. **Vercel build** fails with `ENOTFOUND mirrors.tencentyun.com` because Vercel can't reach Tencent internal mirrors

**Fix (both required):**
```bash
# 1. Project-level .npmrc overrides global
echo "registry=https://registry.npmjs.org/" > .npmrc

# 2. Purge existing lock file URLs
sed -i 's|http://mirrors.tencentyun.com/npm/|https://registry.npmjs.org/|g' package-lock.json
# OR regenerate: rm package-lock.json && npm install --registry=https://registry.npmjs.org/
```

Note: `npm install --userconfig ./.npmrc` does NOT override global config for resolved URLs already in lock file. The sed approach is the only reliable fix.

### npm install Warnings (Safe to Ignore)

After `npm install`, users often see scary-looking output that is NOT an error:

1. **EBADENGINE warnings** (yellow) — a transitive dependency wants a slightly newer Node. If it's a linting/dev tool (e.g. `eslint-visitor-keys`), it won't affect the app. Fix: `nvm install <required>` or just ignore.
2. **"X vulnerabilities (moderate/high)"** — almost always from framework internals (Next.js, webpack, postcss). Not exploitable in a dev/school context. Fix: ignore, or `npm audit fix --force` (may cause breaking changes).
3. **"packages are looking for funding"** — informational only.

**Tell the user:** These are warnings, not errors. Run `npm run dev` — the app will work fine.

### Finding a Deployed URL
Check `.vercel/project.json` → `projectName` → `https://{projectName}.vercel.app`

### create-next-app Timeout
If `npx create-next-app` times out but dir was created, just run `npm install` separately.

### Low-RAM VPS Build Strategy (<2GB RAM)

On VPS with <2GB RAM (like Tencent Cloud 2GB), Next.js builds frequently crash with `Bus error (core dumped)` — especially Next.js 15+/16+ with SWC. Strategy:

1. **Don't waste time retrying locally** — `NODE_OPTIONS=--max-old-space-size=512` won't help Bus errors (SWC/mmap issue, not JS heap)
2. **Deploy directly to Vercel** — their build servers have 8GB RAM
3. **If local build needed**: stop all PM2 processes first (`pm2 stop all`), use Next.js 14 (more stable SWC), avoid Tailwind v4 (uses more memory during build)
4. **Next.js 16 + Tailwind v4** = highest memory usage combo. Downgrade to Next.js 14 + Tailwind v3 for low-RAM environments.

```bash
# Quick deploy without local build
git init && git add -A && git commit -m "init"
vercel --token "$TOKEN" --prod --yes
```

See `references/vercel-prebuilt-deploy.md` for detailed pre-built pattern.

## Static Site CRUD: Adding Images Without a Backend

On Vercel free tier (no API routes / no file upload server), use **URL-based image input** instead of file upload. Admin pastes a URL from ImgBB/Imgur/Cloudinary, stored in localStorage alongside other product data. Use plain `<img>` tags (not Next.js `<Image>`) to avoid needing domain whitelisting in `next.config.mjs`. Always implement conditional rendering: show image if URL exists, fall back to color placeholder if not.

See `references/static-site-image-crud.md` for the full implementation pattern and checklist for adding a new field across all layers (interface → form → display).

## Site-Wide Settings via localStorage (No Backend)

For static sites needing admin-editable global settings (contact info, social links, address), create a centralized settings module (`lib/contacts.ts`) with interface, defaults, get/save helpers. Key patterns:
- **Merge with defaults** on load: `{ ...defaults, ...JSON.parse(stored) }` — future-proofs against new fields
- **Re-export helpers** from existing modules to avoid changing imports across codebase
- **Convert server → client components** that consume settings (add `"use client"`, useState, useEffect)
- **Tab-based admin UI** — add tabs to existing dashboard rather than separate pages
- **Search codebase** for ALL hardcoded values before deploying (`grep -r "old_value" src/`)

See `references/localstorage-site-settings.md` for the contacts-only pattern.

## Full CMS via localStorage (No Backend)

When the user wants **everything** editable from admin panel (hero text, stats, about page, school profile, vision/mission, CTA, brand name, password), scale up to a multi-module architecture:

1. **`lib/siteSettings.ts`** — typed interface for ALL site content with nested objects (hero, stats, about, school, visionMission, CTA)
2. **`lib/contacts.ts`** — contact-specific settings (WhatsApp, Instagram, address, maps)
3. **Multi-tab admin** — 4 tabs: 📦 Produk | 📞 Kontak | ✏️ Konten | 🔒 Password
4. **Password management** — stored in localStorage with `getAdminPassword()`/`saveAdminPassword()`, login page reads dynamically
5. **Audit first** — use `delegate_task` to scan ALL files for hardcoded content before starting, group by page, mark 🔴/🟡/🟢 status
6. **Critical: public product pages** must also read from localStorage, not just import from hardcoded `lib/products.ts`

Key pitfalls: metadata exports conflict with `"use client"`, array fields need textarea with join/split, nested state updates need careful spreading, password in localStorage is client-side only (fine for school projects, not production).

See `references/localstorage-full-cms.md` for the complete architecture, code patterns, admin UI design, and audit checklist.

## Adding a New Field to a Full-Stack Feature (Checklist)

When adding a field (e.g., `image`) to an existing CRUD feature, touch ALL layers:
1. Data interface/type definition (lib module)
2. Admin/form interface (if separate from data interface)
3. Form state (useState, resetForm, handleEdit, handleSubmit)
4. Data loading/mapping (add fallback for existing records: `p.image || ""`)
5. Form UI (input + preview if applicable)
6. ALL display components (cards, detail pages, lists, related items, mobile views)
7. **Public pages** — verify they read from localStorage, not just hardcoded imports
8. **Footer/Navbar** — often forgotten; check if they display the data too
9. Build verification (`npm run build`)
10. Deploy

Missing any layer causes silent bugs (field exists but never shown, or shown but never saved).

**Workflow tip:** Use `search_files` with content pattern to find ALL references to the related field/value across the codebase before starting. Example: `search_files(pattern="product.color|ProductCard", target="content", path="src/")` to find every place that renders product data.

## Cloud Sync for Static Site CMS

When localStorage-only CMS isn't enough (admin edits must be visible to ALL visitors, not just the admin's browser), upgrade to cloud storage.

### Option 1: GitHub as Database (RECOMMENDED)

Store JSON files in a GitHub repo. Admin edits → API proxy → GitHub Contents API → repo file updated. All visitors fetch from the same source.

**Why GitHub wins:** permanent storage, version history, user owns the repo, free unlimited, token-based auth. JSONBlob anonymous blobs expire in 1 day.

**Setup:** Create repo, create JSON files, add API proxy route at `/api/data/[key]/route.ts`, add `GITHUB_TOKEN` as Vercel env var.

**Critical:** GitHub Contents API requires the current file SHA for every PUT. Always GET first to obtain it.

See `references/github-as-database.md` for complete setup, API route code, client helper, and migration guide.

### Option 2: JSONBlob (NOT recommended for anything persistent)

JSONBlob.com is free but **anonymous blobs expire in 1 day**, free-tier in 3 days. Also has CORS issues requiring an API proxy. Only use for throwaway demos.

See `references/jsonblob-cloud-sync.md` for the pattern if needed.

### Architecture (applies to both)
```
Component mount → sync render from localStorage (instant, no flash)
                → async fetch from cloud via /api/data/[key] → re-render
Admin save      → PUT to /api/data/[key] → cloud + localStorage backup
```

### Key Pattern: Dual-Layer Rendering
1. Add async `fetch*()` functions alongside existing sync `get*()` in each lib module
2. Every component: `useEffect(() => { setData(getSync()); fetchAsync().then(setData); }, [])`
3. Admin save handlers: `await updateBlob()` + show cloud sync status feedback
4. **Always use API proxy route** — never call external APIs directly from browser (CORS)

### Pitfall: Deep Merge for Nested Settings
`{ ...defaults, ...cloudData }` is a SHALLOW merge — nested objects (hero, visionMission, school, aboutPage) get entirely replaced if the cloud data has them, or entirely missing if it doesn't. Always deep merge:
```typescript
return {
  ...defaults, ...data,
  hero: { ...defaults.hero, ...(data.hero || {}) },
  visionMission: {
    ...defaults.visionMission, ...(data.visionMission || {}),
    missions: data.visionMission?.missions || defaults.visionMission.missions,
  },
  // ... repeat for all nested objects
};
```
Apply this in BOTH `getSyncSettings()` and `fetchAsyncSettings()`.

### Rate Limiting Admin Login (Client-Side, localStorage)\n\nFor school/portfolio projects without a backend, add brute-force protection using localStorage:\n\n```typescript\nconst MAX_ATTEMPTS = 5;\nconst LOCKOUT_DURATION = 5 * 60 * 1000; // 5 minutes\n\n// On mount — restore state\nuseEffect(() => {\n  const storedAttempts = parseInt(localStorage.getItem(\"myapp_login_attempts\") || \"0\");\n  const storedLocked = parseInt(localStorage.getItem(\"myapp_login_locked_until\") || \"0\");\n  setAttempts(storedAttempts);\n  if (storedLocked > Date.now()) {\n    setLockedUntil(storedLocked);\n  } else if (storedLocked && storedLocked <= Date.now()) {\n    // Expired lockout — clean up\n    localStorage.removeItem(\"myapp_login_attempts\");\n    localStorage.removeItem(\"myapp_login_locked_until\");\n  }\n}, []);\n\n// Countdown timer\nuseEffect(() => {\n  if (!lockedUntil) return;\n  const interval = setInterval(() => {\n    const remaining = Math.ceil((lockedUntil - Date.now()) / 1000);\n    if (remaining <= 0) {\n      setLockedUntil(null); setAttempts(0); setCountdown(0);\n      localStorage.removeItem(\"myapp_login_attempts\");\n      localStorage.removeItem(\"myapp_login_locked_until\");\n      clearInterval(interval);\n    } else {\n      setCountdown(remaining);\n    }\n  }, 1000);\n  return () => clearInterval(interval);\n}, [lockedUntil]);\n\n// In handleLogin — on wrong password:\nconst newAttempts = attempts + 1;\nsetAttempts(newAttempts);\nlocalStorage.setItem(\"myapp_login_attempts\", newAttempts.toString());\nif (newAttempts >= MAX_ATTEMPTS) {\n  const lockUntil = Date.now() + LOCKOUT_DURATION;\n  setLockedUntil(lockUntil);\n  localStorage.setItem(\"myapp_login_locked_until\", lockUntil.toString());\n  setError(\"Terlalu banyak percobaan. Coba lagi dalam 5 menit.\");\n} else {\n  setError(`Username atau password salah! (${newAttempts}/${MAX_ATTEMPTS} percobaan)`);\n}\n\n// On successful login — reset:\nlocalStorage.removeItem(\"myapp_login_attempts\");\nlocalStorage.removeItem(\"myapp_login_locked_until\");\n```\n\n**UI:** Show countdown timer `{Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, \"0\")}` and disable form inputs + submit button when `isLocked`.\n\n**Limitation:** Client-side only — a determined attacker can clear localStorage. For production, use server-side rate limiting (e.g., Upstash Redis + middleware). For school projects, this is sufficient.\n\n### Pitfall: Dynamic Password Login\nWhen admin password is stored in cloud/localStorage, the login page MUST:
1. Fetch password from cloud on mount (`useEffect → fetchAdminPassword().then(setCloudPassword)`)
2. Use the fetched password in `handleLogin`, NOT a hardcoded string
3. Make `handleLogin` async — re-fetch if cloud password wasn't loaded yet
4. **Never hardcode the default password in the login check** — always read from state/cloud

Common bug: password saves to cloud successfully, but login still checks against hardcoded `"defaultPassword"` string.

## White-labeling a Forked Next.js Repo

When the user clones someone else's Next.js app and wants to rebrand it:

### 1. Bulk rename brand strings
```bash
# Find all files with old brand name
grep -rn "OldName\|oldname\|Old Name" src --include="*.tsx" --include="*.ts" -l

# Replace across all source files (Linux VPS — no '' needed after -i)
find src -type f \( -name "*.tsx" -o -name "*.ts" \) \
  -exec sed -i 's/OldName/NewName/g; s/oldname/newname/g; s/Old Name/New Name/g' {} +

# Also patch package.json name/description
sed -i 's/oldname/newname/g; s/OldName/NewName/g' package.json

# Verify clean
grep -rn "OldName\|oldname" src package.json
# Should return empty (exit 1 = no matches = ✅)
```

### 2. Remove donation/attribution popups
Forked apps often have donation popups injected via layout. Pattern:

```tsx
// src/app/detail/layout.tsx — BEFORE (has popup)
import QrisDonationPopup from '@/components/QrisDonationPopup';
export default function DetailLayout({ children }) {
  return <><{children}<QrisDonationPopup /></>;
}

// AFTER — strip the import and component
export default function DetailLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
```

Find which layout injects it: `grep -rn "DonationPopup\|PopupAd\|AdPopup" src --include="*.tsx"`

### 3. Clean footer attribution
Replace original author credit with your own:

```tsx
// Strip: "API yang digunakan: ORIGINAL_API" and "Made with ❤️ by OriginalAuthor"
// Keep: copyright line with new brand name
<p className="text-xs text-muted-foreground/80 text-center font-medium">
  © {new Date().getFullYear()} YourBrandName
</p>
```

### 4. Reorder home sections (Terbaru first)
When the API has both "latest" and "trending" hooks, put "Terbaru" (latest) above "Trending":

```tsx
// In Home component — latest section FIRST, then trending
<LatestSection ... />
<TrendingSection ... />
<InfiniteScrollSection title="Lainnya" />
```

### 5. TypeScript pitfall: tab_id type mismatch
When working with tab-based APIs (e.g. ReelShort), check the actual type of `tab_id` in the types file before filtering:

```bash
grep -n "tab_id" src/types/*.ts
# Could be number or string — must match exactly in filter
```

```tsx
// If tab_id is number:
function getBooksFromTab(tabId: number | undefined) {
  if (tabId === undefined) return [];  // NOT: if (!tabId) — 0 is falsy!
  return lists.filter(list => list.tab_id === tabId);
}
```

## UI Redesign: Entertainment/Streaming Apps

When redesigning a forked streaming/drama app for a new brand, apply this design system.

### Design System Options

**Cinematic Dark (violet/pink — energetic)**
```css
--background: 220 20% 6%;
--primary: 252 100% 68%;          /* electric violet */
--secondary: 330 100% 62%;        /* hot pink */
--gradient-primary: linear-gradient(135deg, hsl(252,100%,68%) 0%, hsl(330,100%,62%) 60%, hsl(350,100%,65%) 100%);
```
Font: `Righteous` (heading) + `Poppins` (body)

**Netflix Style (pure black + red — professional)**
```css
--background: 0 0% 4%;            /* #0A0A0A */
--card: 0 0% 8%;                  /* #141414 */
--primary: 0 100% 42%;            /* #E50914 Netflix red */
--gradient-primary: linear-gradient(135deg, #E50914 0%, #B20710 100%);
--radius: 0.375rem;               /* smaller radius = more Netflix-like */
```
Font: `Bebas Neue` (heading, uppercase, tracking-widest) + `Poppins` (body)
Platform tabs: underline style (`border-b-2 border-red-600`) not pill style
Card: `rounded-sm` not `rounded-xl`
Header: `background: linear-gradient(180deg, rgba(0,0,0,0.95) 0%, rgba(20,20,20,0.98) 100%)`

### Font Pairing (Entertainment)
- Heading: `Righteous` or `Bebas Neue` (bold, cinematic)
- Body: `Poppins` (clean, readable)
- Google Fonts Righteous: `?family=Poppins:wght@300;400;500;600;700&family=Righteous`
- Google Fonts Bebas Neue: `?family=Poppins:wght@300;400;500;600;700&family=Bebas+Neue`
- Update both `globals.css` @import AND `tailwind.config.ts` fontFamily

### Layout: Sidebar + Bottom Nav for Platform Switching

When a streaming app has 8+ platforms, a sticky top bar becomes cluttered. Move platform selection to:
- **Desktop**: fixed left sidebar (`w-56`, `top-16`, `bottom-0`, `fixed`) — list with logo + name + active dot
- **Mobile**: fixed bottom nav (`bottom-0`, `overflow-x-auto scrollbar-hide`) — horizontal scroll with logo + short name

Main content must offset accordingly:
```tsx
// home-content.tsx
<div className="min-h-screen pt-16 flex">
  <PlatformSelector />  {/* renders sidebar on desktop, bottom nav on mobile */}
  <main className="flex-1 md:ml-56 pb-24 md:pb-8 min-w-0">
    <div className="px-4 md:px-8 py-6 space-y-10">
      {/* platform content */}
    </div>
  </main>
</div>
```

Footer also needs `md:ml-56` to align with content area.

PlatformSelector renders `null` on `/watch` pages (immersive video).

```tsx
// Sidebar item — active state with red dot
<button className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-md ${
  isActive ? "bg-red-600/15 text-white" : "text-zinc-400 hover:bg-zinc-800/60"
}`}>
  <Image ... className={isActive ? "opacity-100" : "opacity-50"} />
  <span className="text-sm font-medium truncate">{platform.name}</span>
  {isActive && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-red-500" />}
</button>

// Bottom nav item — logo with ring when active
<button className="flex flex-col items-center gap-1 px-3 py-1.5 rounded-lg">
  <div className={`relative w-7 h-7 rounded-lg overflow-hidden ${isActive ? "ring-2 ring-red-500" : "opacity-50"}`}>
    <Image ... />
  </div>
  <span className="text-[9px] font-medium">{platform.name}</span>
</button>
```

### Key UI Patterns

**Netflix-style Platform Tabs (underline, not pill):**
Use `border-b-2 -mb-px` pattern for tab underline. Active = red border, inactive = transparent border with hover state. Container needs `border-b border-zinc-800` to create the baseline.

**Skeleton Shimmer (replace static pulse):**
```css
.skeleton {
  background: linear-gradient(90deg, #1a1a1a 25%, #242424 50%, #1a1a1a 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

Header — pill search bar (more premium than icon-only button):
```tsx
<button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/8">
  <Search className="w-4 h-4" />
  <span className="text-sm hidden sm:block">Cari drama...</span>
</button>
```

Logo — gradient background with glow:
```tsx
<div className="w-9 h-9 rounded-xl flex items-center justify-center"
  style={{ background: 'var(--gradient-primary)', boxShadow: '0 0 20px hsl(252,100%,68%,0.4)' }}>
  <Play className="w-4 h-4 text-white fill-white ml-0.5" />
</div>
```

Media card hover — spring cubic-bezier:
```css
.media-card:hover {
  transform: translateY(-6px) scale(1.03);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

### Skeleton Shimmer (replace static pulse)
```css
.skeleton {
  background: linear-gradient(90deg, hsl(220,18%,14%) 25%, hsl(220,18%,18%) 50%, hsl(220,18%,14%) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.6s infinite;
}
```

### Tailwind Config Additions
```ts
scale: { '108': '1.08' },  // for card hover scale-108
```

### Tailwind Opacity Pitfall
Tailwind opacity modifiers must be multiples of 5 or standard values (5, 10, 20, 25, 30, etc.).
`white/8`, `white/15` are NOT valid — Turbopack will throw `CssSyntaxError` at build time.

```bash
# Find invalid opacity values
grep -rn "white/[0-9]\b\|white/1[^0-9]\|white/[3-9][^0-9]" src --include="*.tsx" --include="*.css"
```

Fix: replace `/8` → `/10`, `/15` → `/20`, `bg-card/85` → `bg-card/80`.

```bash
# Bulk fix
find src -type f \( -name "*.tsx" -o -name "*.ts" -o -name "*.css" \) \
  -exec sed -i 's|white/8\b|white/10|g; s|white/15\b|white/20|g; s|bg-card/85\b|bg-card/80|g' {} +
```

### Vercel Non-Interactive Deploy (from VPS)
```bash
# Install globally first to avoid npx timeout at 120s
npm install -g vercel

# First deploy with explicit project name
vercel --token "$VERCEL_TOKEN" --yes --name projectname 2>&1

# Subsequent prod deploys
vercel --token "$VERCEL_TOKEN" --prod --yes 2>&1
```
Pitfall: `npx vercel` on first run downloads the package and can timeout at 120s on slow VPS. Install globally first.

## Navigation: Hamburger-Only Across All Viewports

Default Tailwind navbar pattern shows desktop center-nav + mobile hamburger drawer. Some users explicitly prefer **hamburger at ALL viewport sizes** (desktop, tablet, mobile) — single source of truth for navigation, scales when nav items grow, more screen real estate for branding/user controls. When user asks "hamburger di desktop juga sama kan?" or similar, they want the hamburger visible on every breakpoint.

### Implementation

```tsx
{/* Hamburger button — NO `lg:hidden` */}
<button
  onClick={() => setOpen(!open)}
  className="p-2 -ml-1 rounded-lg text-slate-700 hover:bg-slate-100"
  aria-label="Menu"
>
  {open ? <X size={20} /> : <Menu size={20} />}
</button>

{/* Hide desktop center nav entirely */}
<div className="flex-1" />  {/* spacer instead of <nav> */}

{/* Drawer — also remove `lg:hidden` */}
{open && (
  <div className="border-t border-slate-200 bg-white shadow-lg">
    <nav className="max-w-7xl mx-auto px-4 sm:px-6 py-3">
      {/* Responsive grid: 1 col mobile, 2 col tablet, 3 col desktop */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-0.5">
        {links.map(...)}
      </div>
      {/* Mobile-only avatar/logout block (sm:hidden) — desktop already has it in topbar */}
      <div className="sm:hidden">...</div>
    </nav>
  </div>
)}
```

### Hamburger Position

Place hamburger on the **LEFT side** before the brand/logo, not on the right next to the avatar. This matches mobile app conventions (Gmail, Twitter, Slack) and keeps the right side for user-account controls. Use `-ml-1` for optical alignment with the brand text below.

### Auto-Close on Route Change

```tsx
useEffect(() => { setOpen(false); }, [pathname]);
```

Without this, the drawer stays open after navigation and looks broken.

### Pitfall: `mousedown` vs `click` Event Timing on Mobile

When the mobile hamburger menu uses `mousedown` on a backdrop/overlay to dismiss, and the menu links use `click` for navigation, tapping a nav link on mobile fires events in this order:

1. `mousedown` on backdrop → state change → menu DOM removed
2. `click` target gone → navigation never fires

**Symptom:** Menu closes but link doesn't navigate. Works on desktop (mouse has distinct down/click), broken on mobile (touch fires both rapidly).

**Fix options:**
- Use `click` instead of `mousedown` for the outside-click dismiss handler
- Add `e.stopPropagation()` in the menu container's `mousedown` handler so outside-click doesn't fire when tapping inside
- Use `pointerdown` consistently for both dismiss and link click

**Always test mobile menu link navigation after any dismiss-outside-click change.**

### Pitfall: `animate-in slide-in-from-top` requires plugin

`animate-in`, `slide-in-from-top-2`, etc. are from `tailwindcss-animate`. If the plugin isn't installed (check `tailwind.config.ts` plugins + `package.json`), these classes silently do nothing OR can cause runtime issues. Either install the plugin or omit the animation classes — don't ship them and hope.

```bash
grep -i animate ~/project/tailwind.config.ts
grep -i tailwindcss-animate ~/project/package.json
```

## Form Inputs: Icon-Inside-Input Overlap Pitfall

The "icon absolute-positioned inside input + `pl-10` padding" pattern looks sleek in design mockups but breaks on mobile. Common bug report: "logo email dan gembok nya hapus saja soalnya tertimpa" (icons get covered by browser autofill chrome, password manager overlays, or just shift on small screens).

### The pattern that breaks

```tsx
{/* ❌ Causes overlap on mobile / with password managers */}
<div className="relative">
  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
  <input type="email" className="input pl-10" ... />
</div>
```

### Fix

When the user reports the icons are overlapping, **remove them entirely** rather than tweaking position/z-index. Plain inputs with a clear `<label>` above are cleaner and accessible:

```tsx
{/* ✅ Clean, no overlap, better a11y */}
<div>
  <label className="label">Email</label>
  <input type="email" className="input" placeholder="email@example.com" ... />
</div>
```

Don't forget to remove the now-unused icon imports (`Mail`, `Lock`, etc.) — TypeScript won't error on unused imports by default but it's clutter.

### Why this happens

- Mobile keyboards push the input → icon position shifts relative to text
- Password managers (1Password, browser autofill) inject their own icons in the same spot
- Browser chrome on iOS Safari overlays the left padding area
- Touch targets near the icon get hijacked

### When icons-in-inputs ARE OK

Desktop-only forms (admin panels with min-width), search bars where the icon IS the visual affordance, and inputs with significantly larger left padding (`pl-12+`). Default to no inline icons unless there's a specific reason.

## Next.js App Router Performance Optimization

### Conditional Data Fetching (Don't Fetch What You Don't Need)

When a page has multiple platform/tab states, hooks for inactive platforms still fire by default. Pass `enabled` flag to prevent unnecessary API calls:

```tsx
// hooks/useDramas.ts — add enabled param
export function useLatestDramas(enabled = true) {
  return useQuery({
    queryKey: ["dramas", "latest"],
    queryFn: () => fetchJson<Drama[]>(`${API_BASE}/latest`),
    staleTime: 1000 * 60 * 5,
    enabled,  // ← key addition
  });
}

// home-content.tsx — only fetch when platform is active
```

This prevents 3+ unnecessary API calls every time the user switches to a different platform.

### Disabling Next.js Route Caching (`force-dynamic`)

Next.js App Router caches fetch responses by default. API proxy routes that forward to upstream APIs must opt out:

```ts
// Add after imports in every API route that proxies dynamic data
export const dynamic = 'force-dynamic';
```

Equivalent to `cache: 'no-store'` on every fetch inside the route. Safer than adding `cache: 'no-store'` to individual fetch calls (less error-prone).

**Bulk add to multiple routes safely (Python, not sed/regex):**

```python
import os

dirs = ['src/app/api/pinedrama', 'src/app/api/melolo', 'src/app/api/my-project']

for d in dirs:
    for root, _, files in os.walk(d):
        for fname in files:
            if fname != 'route.ts':
                continue
            fpath = os.path.join(root, fname)
            with open(fpath) as f:
                content = f.read()
            if 'force-dynamic' in content or "cache: 'no-store'" in content:
                continue
            lines = content.split('\n')
            last_import_idx = max((i for i, l in enumerate(lines) if l.startswith('import ')), default=-1)
            if last_import_idx >= 0:
                lines.insert(last_import_idx + 1, "\nexport const dynamic = 'force-dynamic';")
                with open(fpath, 'w') as f:
                    f.write('\n'.join(lines))
```

⚠️ **NEVER use `sed` or regex to modify fetch() calls in API routes** — regex is greedy and WILL corrupt template literals like `` fetch(`${UPSTREAM_API}/path?cursor=${encodeURIComponent(cursor)}`) `` by inserting inside the template string or breaking parentheses. This happened in production and corrupted 16 files simultaneously.

**If this happens:** `git checkout HEAD -- src/app/api/` to restore all routes from git.

**Safe alternative:** Use `export const dynamic = 'force-dynamic'` at the top of the file (after imports) instead of modifying individual fetch calls. This achieves the same result without touching fetch syntax. Use the Python script above to add it safely.

### Cache-Control Headers via next.config.ts

Add CDN-level caching for static assets and images. For API routes, prefer `no-store` and let React Query handle client-side caching:

```ts
// next.config.ts
async headers() {
  return [
    {
      // Static assets — 1 year immutable
      source: "/_next/static/:path*",
      headers: [{ key: "Cache-Control", value: "public, max-age=31536000, immutable" }],
    },
    {
      // Optimized images — 24 hours
      source: "/_next/image",
      headers: [{ key: "Cache-Control", value: "public, max-age=86400, stale-while-revalidate=3600" }],
    },
    {
      // API routes — no CDN cache, let React Query handle client caching
      source: "/api/:path*",
      headers: [{ key: "Cache-Control", value: "no-store" }],
    },
  ];
},
```

⚠️ **CDN Cache Pitfall for Paginated APIs:** Do NOT use `s-maxage` on endpoints that accept page/cursor params (e.g., `/api/streaming-service/foryou?page=2`). Vercel CDN caches by URL path only — if the source pattern matches, ALL page params get the same cached response. This causes infinite scroll to return page 1 data for every page request. Symptoms: scroll stops working, duplicate content, or "Gagal Memuat" errors.

**Safe rule:** Only use `s-maxage` on truly static endpoints with no query params. For paginated/dynamic APIs, use `no-store` and rely on React Query's `staleTime` (5 min default) for client-side caching.

### Graceful Error Handling for Infinite Scroll API Routes

When an upstream API fails (rate limit, timeout), API proxy routes should return HTTP 200 with empty data — NOT HTTP 500. This lets the client-side infinite scroll stop gracefully without showing error messages.

```ts
// ❌ BAD — causes "Gagal Memuat Lainnya" error in UI
} catch (error) {
  return encryptedResponse({ status: 500, message: "Failed to fetch" }, 500);
}

// ✅ GOOD — infinite scroll stops gracefully (no more pages)
} catch (error) {
  console.error("PineDrama foryou fetch error:", error);
  return encryptedResponse({ has_more: false, cursor: null, collections: [] });
}
```

The client-side `getNextPageParam` sees empty data → returns `undefined` → scroll stops. No error message shown.

**Apply this pattern to:** all `/foryou`, `/trending`, `/latest` routes that serve infinite scroll sections. Keep HTTP 500 for search routes (user should see search errors).

### Background Prefetch for Multi-Platform/Tab Apps

When an app has multiple platforms/tabs and switching between them causes loading spinners, prefetch all platform data in the background after initial load:

```tsx
// hooks/usePrefetch.ts
"use client";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

export function usePrefetchPlatforms() {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Delay 2s to not compete with active platform's initial load
    const timer = setTimeout(() => {
      queryClient.prefetchQuery({
        queryKey: ["platform-a", "trending"],
        queryFn: () => fetch("/api/platform-a/trending").then(r => r.json()),
        staleTime: 5 * 60 * 1000,
      });
      queryClient.prefetchQuery({
        queryKey: ["platform-b", "homepage"],
        queryFn: () => fetchJson("/api/platform-b/homepage"),
        staleTime: 5 * 60 * 1000,
      });
      // ... repeat for each platform's primary endpoint
    }, 2000);

    return () => clearTimeout(timer);
  }, [queryClient]);
}
```

Call it once in the home/root content component:
```tsx
export default function HomeContent() {
  usePrefetchPlatforms(); // fires once on mount, prefetches after 2s delay
  // ...
}
```

**Key decisions:**
- 2s delay prevents competing with the active platform's initial fetch
- Only prefetch primary endpoints (trending/homepage) — not detail pages
- `staleTime` must match the hook's staleTime so prefetched data is reused
- `queryKey` must exactly match what the platform's hook uses

**Result:** Switching platforms feels instant because data is already in React Query cache.

### React Query Retry Config

Add exponential backoff retry to handle transient upstream failures:

```tsx
// providers.tsx
defaultOptions: {
  queries: {
    staleTime: 5 * 60 * 1000,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000), // 1s, 2s, 4s
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
  },
},
```

This handles upstream rate limiting (429) transparently — user never sees the error if retry succeeds.

### Image Optimization (next.config.ts)

```ts
images: {
  formats: ["image/avif", "image/webp"],  // AVIF ~30% smaller than WebP
  minimumCacheTTL: 86400,                 // 24h (default 2h is too short for cover images)
  remotePatterns: [ ... ],
},
```

### Performance Audit Checklist for Streaming Apps

Run this audit before optimizing:

```bash
# 1. Bundle size — find large chunks
ls -lh .next/static/chunks/*.js | sort -k5 -rh | head -10

# 2. Check which routes are missing force-dynamic
grep -rL "force-dynamic\|no-store" src/app/api/*/route.ts

# 3. Check for unconditional hooks in home component
grep -n "use[A-Z].*Dramas\|use[A-Z].*Home" src/app/home-content.tsx
```

Common findings:
- `hls.js` statically imported in watch pages (~500KB) — use dynamic import or lazy init in useEffect
- List API routes missing `force-dynamic` — may serve stale data
- Home component fetching all platform data regardless of active platform

## Removing a Platform/Feature from a Multi-Platform App

When removing a platform (or any feature that's wired into a type union + hook + multiple components), follow this exact order to avoid cascading TS errors:

### Order of Operations
1. **Type union** — remove the literal from the union type (e.g., `Platform`)
2. **Data array** — remove the entry from the config/platforms array
3. **Hook return** — remove the boolean flag (e.g., `ismy-project`) from the return object
4. **Components (each file):**
   a. Remove the import of the feature's hook/component
   b. Remove the flag from destructuring
   c. Remove the hook call that uses the flag as a condition
   d. Remove the flag from ternary chains (isSearching, searchResults)
   e. Remove the JSX render block

### Ternary Chain Cleanup

Multi-platform apps often have nested ternary chains for `isSearching` and `searchResults`. When removing a platform from the middle:

```tsx
// BEFORE — ismy-project in the chain
: isFreeReels
  ? isSearchingFreeReels
  : ismy-project
    ? isSearchingmy-project
    : isSearchingGoodShort;

// AFTER — collapse the removed branch
: isFreeReels
  ? isSearchingFreeReels
  : isSearchingGoodShort;
```

The same pattern applies to the `searchResults` chain — just remove the branch and connect the surrounding ones.

### Pitfalls
- **Don't delete API routes or page directories** unless explicitly asked — removing from UI/navigation is separate from removing backend support
- **Build after each file** if unsure — TS will catch missing references immediately
- **Search for the platform name** across the codebase before declaring done: `grep -rn "my-project\|my-project" src --include="*.tsx" --include="*.ts"`

### Verification
```bash
npm run build 2>&1 | tail -5
# Should show successful build with no TS errors
```

## Date/Time Formatting: Server Component vs Client Component Timezone Mismatch

A subtle bug that's hard to spot: the same `toLocaleDateString('id-ID', {...})` call produces different output depending on where it renders.

- **Server Component** (default in App Router): renders on Vercel's edge — `process.env.TZ` is **UTC**. So `new Date(iso).toLocaleDateString('id-ID', { hour: '2-digit', minute: '2-digit' })` returns UTC time.
- **Client Component** (`'use client'`): renders in the browser — uses the user's device timezone, so an Indonesian user sees WIB.

User symptom: "jam di Aktivitas Terbaru (dashboard) mundur 7 jam dibanding Riwayat" — both pages format the same `created_at`, but Aktivitas Terbaru is in a server component and Riwayat is in a client component (`RiwayatTable.tsx` with `'use client'`).

### Fix: always pass explicit `timeZone`

```tsx
// ❌ Renders inconsistently — UTC in RSC, browser TZ in client
new Date(p.created_at).toLocaleDateString('id-ID', {
  day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
})

// ✅ Renders WIB everywhere
new Date(p.created_at).toLocaleDateString('id-ID', {
  day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  timeZone: 'Asia/Jakarta',
}) + ' WIB'
```

Apply to BOTH server and client components — even client components benefit, because the user might be travelling abroad and you usually want the app to show local-business-time consistently regardless.

### Audit checklist

```bash
# Find every locale formatter call missing `timeZone`
grep -rn "toLocaleDateString\|toLocaleString\|toLocaleTimeString" src/ \
  | grep -v "timeZone"
```

Apply timezone fix to every match. Common forgotten spots: dashboards, activity feeds, audit logs, notification timestamps, tooltips on charts.

### Reusable helper

```ts
// lib/format.ts
export function formatJakarta(iso: string, opts: Intl.DateTimeFormatOptions = {}) {
  return new Date(iso).toLocaleDateString('id-ID', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
    timeZone: 'Asia/Jakarta',
    ...opts,
  }) + ' WIB';
}
```

Centralizing this prevents drift — if the team later needs to support a second timezone (per-user preference), it's one file to change.

### Why not just store dates as local time?

Don't. Always store UTC ISO strings in the database (Supabase `timestamptz` does this automatically). Format at the presentation layer. Storing local-tz strings creates DST bugs and makes multi-region usage impossible.

### The deeper bug: `Date` math in Server Components

`toLocaleDateString` is the *visible* tip of this iceberg. The more dangerous variant is **date arithmetic in Server Components** — `setHours`, `setDate`, `getDay`, `Date` constructors with no offset — all silently use the server's TZ (UTC on Vercel).

```tsx
// ❌ Logic bug in a Server Component — "today" actually means UTC midnight
// On Vercel that = 07:00 WIB. So pemakaian dicatat 00:00–06:59 WIB
// dihitung sebagai "kemarin" di stat hari ini.
const today = new Date();
today.setHours(0, 0, 0, 0);
const { data } = await supabase
  .from('pemakaian')
  .select('id')
  .gte('created_at', today.toISOString());
```

Same pitfall in `setDate(thisWeek.getDate() - 7)` for "7 hari" stats — the cutoff is shifted 7 hours.

### Fix: `startOfWibDay()` helper that's TZ-correct everywhere

Don't rely on the runtime's local TZ. Build the ISO string from `Intl.DateTimeFormat` parts pinned to `Asia/Jakarta`:

```ts
// lib/datetime.ts
export const WIB_TZ = 'Asia/Jakarta';
export const WIB_OFFSET = '+07:00';

export function startOfWibDay(daysAgo = 0): Date {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: WIB_TZ, year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date());
  const get = (t: string) => parts.find(p => p.type === t)?.value ?? '';
  const start = new Date(`${get('year')}-${get('month')}-${get('day')}T00:00:00${WIB_OFFSET}`);
  if (daysAgo > 0) start.setUTCDate(start.getUTCDate() - daysAgo);
  return start;
}

export function formatWib(input: string | Date, opts: Intl.DateTimeFormatOptions = {
  day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
}, withSuffix = true) {
  const d = typeof input === 'string' ? new Date(input) : input;
  const formatted = d.toLocaleDateString('id-ID', { ...opts, timeZone: WIB_TZ });
  return withSuffix ? `${formatted} WIB` : formatted;
}
```

Then in the page:
```tsx
const today = startOfWibDay();          // correct WIB midnight
const lastWeek = startOfWibDay(7);      // 7 days ago, WIB midnight
```

### Verifying the fix (TZ=UTC simulation)

The bug only reproduces when the runtime is UTC, so simulate Vercel locally:

```bash
TZ=UTC node -e "
const parts = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Jakarta', year: 'numeric', month: '2-digit', day: '2-digit',
}).formatToParts(new Date());
const get = (t) => parts.find(p => p.type === t).value;
const wib = new Date(\`\${get('year')}-\${get('month')}-\${get('day')}T00:00:00+07:00\`);
const utc = new Date(); utc.setHours(0,0,0,0);
console.log('setHours(0):', utc.toISOString());
console.log('startOfWibDay:', wib.toISOString());
console.log('diff hours:', (utc - wib) / 3600000);  // must be 7
"
```

If you see `diff hours: 7`, the helper is correctly producing WIB midnight regardless of runtime TZ.

### Expanded audit checklist

```bash
# Display layer (existing)
grep -rn "toLocaleDateString\|toLocaleString\|toLocaleTimeString" src/ | grep -v "timeZone"

# NEW: date math in server-rendered files (Server Components, API routes, Server Actions)
grep -rn "setHours(0\|setHours(\s*0\|\.setDate(\|\.setMonth(\|\.setFullYear(" src/

# Triple-check files that have BOTH `'use client'` is absent AND `new Date()`
grep -rL "'use client'" src/app | xargs grep -l "new Date(" 2>/dev/null
```

Every match in the second/third query is a candidate for the same bug. Replace `setHours(0,0,0,0)` with `startOfWibDay()` and arithmetic like `setDate(getDate() - 7)` with `startOfWibDay(7)`.

### Why this matters more than display

A display bug shows wrong text. A `setHours` bug shifts the entire dataset boundary — "Hari Ini" counter, "7 Hari" stats, daily aggregations, audit-log filters, "is_recent" flags — all silently lie by up to 7 hours. Always audit both display *and* math when timezone is suspect.

## Next.js App Router Favicon Convention

Next.js App Router auto-detects icon files placed in `src/app/`:
- `src/app/favicon.ico` — browser tab icon (auto-served at `/favicon.ico`)
- `src/app/icon.png` — modern browsers, PWA
- `src/app/apple-icon.png` — iOS bookmark/home screen

These take priority over `public/favicon.ico`. If favicon isn't updating after deploy:
1. Place files in BOTH `src/app/` AND `public/` for maximum compatibility
2. Add explicit metadata in layout.tsx with multiple sizes
3. User must hard-refresh (Ctrl+Shift+R) — browsers aggressively cache favicons

```tsx
// layout.tsx — explicit multi-size icon metadata
export const metadata: Metadata = {
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "16x16" },
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: "/icon-192.png",
  },
};
```

**Pitfall:** If `public/favicon.ico` exists but `src/app/favicon.ico` doesn't, Next.js serves the public one but may not include it in the HTML `<link>` tags. Always place in `src/app/` for App Router projects.

## Favicon Generation (PIL)

When replacing a forked app's favicon with a custom one matching the header logo:

```python
from PIL import Image, ImageDraw

size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Red rounded rectangle (Netflix red)
draw.rounded_rectangle([(8, 8), (248, 248)], radius=40, fill=(229, 9, 20, 255))

# White play triangle (offset right for visual balance)
cx, cy = 136, 128
tri_size = 70
points = [(cx - tri_size*0.4, cy - tri_size), (cx - tri_size*0.4, cy + tri_size), (cx + tri_size*0.8, cy)]
draw.polygon(points, fill=(255, 255, 255, 255))

# Multi-size ICO
sizes_ico = [16, 32, 48, 64, 128, 256]
imgs = [img.resize((s, s), Image.LANCZOS) for s in sizes_ico]
imgs[0].save('public/favicon.ico', format='ICO', sizes=[(s,s) for s in sizes_ico], append_images=imgs[1:])

# Apple touch icon + PWA icon
img.resize((192, 192), Image.LANCZOS).save('public/icon-192.png', 'PNG')
img.resize((512, 512), Image.LANCZOS).save('public/icon-512.png', 'PNG')
```

Then in layout.tsx metadata:
```ts
icons: { icon: "/favicon.ico", apple: "/icon-192.png" },
```

## Standalone Streaming App from Existing API (my-project Pattern)

When building a standalone streaming site that proxies an existing upstream API:

### Architecture
```
src/
├── app/
│   ├── api/[platform]/[endpoint]/route.ts  — proxy routes (no encryption needed for standalone)
│   ├── detail/[id]/page.tsx                — drama detail + episode list
│   ├── watch/[id]/[episodeId]/page.tsx     — fullscreen video player
│   └── page.tsx                            — home with sections + infinite scroll + search
├── components/
│   ├── header.tsx, providers.tsx, drama-card.tsx, drama-card-skeleton.tsx
├── hooks/
│   └── use[Platform].ts                    — React Query hooks (useQuery + useInfiniteQuery)
├── lib/
│   └── upstream.ts                         — centralized fetch helper for upstream API
└── types/
    └── [platform].ts                       — TypeScript interfaces
```

### Key Decisions
- **No encryption layer** — standalone site doesn't need `encryptedResponse`; just `NextResponse.json(data)`
- **Centralized upstream helper** — single `fetchUpstream(path, params)` function, DRY across all routes
- **Video proxy route** — `/api/proxy/video?url=...` to bypass CORS on video/subtitle URLs
- **Infinite scroll** — `useInfiniteQuery` + IntersectionObserver for home page
- **Watch page state** — use `window.history.pushState` for episode navigation without page remount (preserves fullscreen)
- **Quality selector** — parse `PlayInfoList`, sort by resolution, default to 720p

### Minimal Dependencies (Next.js 14 + Tailwind 3)
```json
{
  "@tanstack/react-query": "^5",
  "lucide-react": "^0.400.0",
  "next": "14.2.15",
  "react": "^18.3.1",
  "react-dom": "^18.3.1"
}
```
No shadcn/radix needed for simple streaming sites — native HTML elements + Tailwind suffice.

## Security: Hardcoded Credentials in Public GitHub Repos

When a Next.js project is pushed to a **public** GitHub repo, any hardcoded credentials in source code are immediately visible to anyone.

### Common Pitfall: Default Password in Auth Logic

```typescript
// ❌ DANGEROUS — password visible in public repo
export function getAdminPassword(): string {
}
```

**Fix:** Replace hardcoded fallback with empty string. The actual password lives in cloud storage (GitHub repo as database, or other backend) — if cloud fetch fails, deny access rather than fall back to a known password.

```typescript
// ✅ SAFE — no password in source code
export function getAdminPassword(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("myapp_admin_password") || "";
}

export async function fetchAdminPassword(): Promise<string> {
  const data = await fetchBlob<{ password: string }>("password", { password: "" });
  if (typeof window !== "undefined" && data.password) {
    localStorage.setItem("myapp_admin_password", data.password);
  }
  return data.password || "";
}
```

**Also check login page fallback** — the catch block in `handleLogin` often has its own hardcoded fallback:
```typescript
// ❌ Also dangerous
} catch {
}

// ✅ Fix
} catch {
  savedPassword = localStorage.getItem("myapp_admin_password") || "";
}
```

### Data Repo: Make Private if It Contains Sensitive Data

When using GitHub as a database (JSON files in a repo), the data repo may contain plaintext passwords:
```json
// password.json — visible to anyone if repo is public
{ "password": "actualpassword" }
```

**Fix:** Make the data repo **private**. The website still works because it accesses the repo via `GITHUB_TOKEN` (Vercel environment variable) — private repos are accessible with a valid token.

**Verification before making private:**
1. Check that `GITHUB_TOKEN` is set in Vercel project env vars
2. Confirm the API route uses `Authorization: token ${GITHUB_TOKEN}` header
3. Make repo private → test that website still reads/writes data correctly

### Audit Checklist Before Pushing to Public GitHub

```bash
# Find hardcoded passwords/secrets in source
grep -rn "password\|PASSWORD\|secret\|SECRET\|token\|TOKEN\|api_key\|API_KEY" src --include="*.ts" --include="*.tsx" | grep -v "process.env\|GITHUB_TOKEN\|getAdminPassword\|saveAdminPassword\|fetchAdminPassword"

# Check .gitignore covers .env files
cat .gitignore | grep env

# Check no .env files are tracked
git ls-files | grep "\.env"
```

**Safe:** `process.env.GITHUB_TOKEN` — env var, not in source  
**Dangerous:** `.env.local` not in `.gitignore`

## Next.js 14 + Supabase App Router (No External UI Libs)

When building a full-stack app with Supabase auth + realtime and **no external UI libraries** (no shadcn, no radix), use inline styles + global CSS classes instead of Tailwind component classes.

### Auth Setup: `@supabase/ssr` vs Manual Cookie

**⚠️ `@supabase/ssr` type conflict with Next.js 14 + `@types/react` v18:**
`@supabase/ssr` uses `ResponseCookie` from `next/dist/compiled/@edge-runtime/cookies` which conflicts with `@types/react` v18 type definitions. Build fails with type errors in `setAll()`.

**Fix: skip `@supabase/ssr` entirely, use `@supabase/supabase-js` directly with manual cookie handling:**

```ts
// lib/supabase.ts — browser client (singleton, client-side only)\nimport { createClient as createSupabaseClient } from '@supabase/supabase-js';\nlet client: ReturnType<typeof createSupabaseClient> | null = null;\nexport function createClient() {\n  if (!client) client = createSupabaseClient(\n    process.env.NEXT_PUBLIC_SUPABASE_URL!,\n    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!\n  );\n  return client;\n}\n\n// lib/auth-server.ts — server-only (uses next/headers directly)\nimport { cookies } from 'next/headers';\nimport { createClient as createSupabaseClient } from '@supabase/supabase-js';\nexport async function getSession() {\n  const cookieStore = cookies();\n  const token = cookieStore.get('sb-access-token')?.value;\n  if (!token) return null;\n  const supabase = createSupabaseClient(url, key);\n  const { data: { user } } = await supabase.auth.getUser(token);\n  return user;\n}\n\n// lib/auth-client.ts — client-side auth functions\nimport { createClient } from './supabase';\nexport async function signIn(email: string, password: string) {\n  return createClient().auth.signInWithPassword({ email, password });\n}\nexport async function signOut() {\n  return createClient().auth.signOut();\n}\n```\n\n**Middleware (manual cookie refresh, no `@supabase/ssr`):**\n```ts\n// middleware.ts\nimport { NextResponse } from 'next/server';\nimport type { NextRequest } from 'next/server';\nexport function middleware(request: NextRequest) {\n  // Protected routes — check for session cookie\n  const protectedPaths = ['/dashboard', '/pemakaian', '/riwayat', '/admin'];\n  const isProtected = protectedPaths.some(p => request.nextUrl.pathname.startsWith(p));\n  if (isProtected) {\n    const token = request.cookies.get('sb-access-token');\n    if (!token) return NextResponse.redirect(new URL('/login', request.url));\n  }\n  return NextResponse.next();\n}\n```\n\n**Split server/client auth into separate files** — `next/headers` can only be imported in server components. If a component is `'use client'`, it must use `auth-client.ts`, not `auth-server.ts`.\n\n### Auth Setup (`@supabase/ssr`) — Use Only If No Type Conflicts

Two clients needed — browser and server:

```ts
// lib/supabase.ts — browser client (singleton)
import { createBrowserClient } from '@supabase/ssr';
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

// lib/auth.ts — server client (for Server Components)
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
export function createServerSupabaseClient() {
  const cookieStore = cookies();
  return createServerClient(url, key, {
    cookies: {
      getAll() { return cookieStore.getAll(); },
      setAll(cookiesToSet) {
        try { cookiesToSet.forEach(({ name, value, options }) => cookieStore.set(name, value, options)); }
        catch { /* Server Component — handled by middleware */ }
      },
    },
  });
}
```

Middleware must refresh the session on every request — see `references/supabase-nextjs-pattern.md`.

### Multi-Route Layout Pattern (App Router)

Each route group (`/dashboard`, `/bahan`, `/pakai`, `/riwayat`, `/admin`) needs its own `layout.tsx` that:
1. Calls `getServerProfile()` (server-side auth check)
2. Redirects to `/login` if no session
3. Renders `<Sidebar profile={profile} />` + `<main>`

This is repetitive but necessary — App Router doesn't support a single shared layout across non-nested routes without a route group `(group)` folder.

**Alternative:** Use a `(app)` route group with a single layout:
```
src/app/
  (app)/
    layout.tsx        ← single auth layout for all protected routes
    dashboard/page.tsx
    bahan/page.tsx
    pakai/page.tsx
    riwayat/page.tsx
    admin/page.tsx
  login/page.tsx
  page.tsx
```

### Realtime Subscription Pattern

```tsx
// In a Client Component
useEffect(() => {
  const supabase = getSupabaseClient();
  const channel = supabase
    .channel('table_changes')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'bahan_kimia' }, (payload) => {
      if (payload.eventType === 'INSERT') setData(prev => [payload.new as T, ...prev]);
      if (payload.eventType === 'UPDATE') setData(prev => prev.map(r => r.id === payload.new.id ? payload.new as T : r));
      if (payload.eventType === 'DELETE') setData(prev => prev.filter(r => r.id !== payload.old.id));
    })
    .subscribe();
  return () => { supabase.removeChannel(channel); };
}, []);
```

Requires `ALTER PUBLICATION supabase_realtime ADD TABLE table_name;` in Supabase SQL editor.

### Stock Deduction via DB Trigger (Not Application Code)

Don't deduct stock in the API/client — use a Postgres trigger so it's atomic:

```sql
CREATE OR REPLACE FUNCTION deduct_stock() RETURNS TRIGGER AS $$
BEGIN
  UPDATE bahan_kimia SET stok_saat_ini = stok_saat_ini - NEW.jumlah WHERE id = NEW.bahan_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_pemakaian_insert
  AFTER INSERT ON pemakaian FOR EACH ROW EXECUTE FUNCTION deduct_stock();
```

Same pattern for restock (add instead of subtract).

### Inline Styles + Global CSS Classes (No Tailwind Components)

When no external UI lib is used, define reusable classes in `globals.css`:
- `.glass-card` — glassmorphism card (rgba bg + border + backdrop-blur)
- `.dark-table` / `.dark-table th` / `.dark-table td` — table styles
- `.dark-input` — form input with dark bg, focus ring
- `.btn-primary`, `.btn-accent`, `.btn-danger`, `.btn-ghost` — button variants
- `.badge-low-stock`, `.badge-ok` — status badges
- `.fade-in` — entry animation

Use inline `style={{}}` for layout/positioning, CSS classes for reusable component styles.

### Role-Based Access (Guru vs Siswa)

- Admin routes: check `profile.role !== 'guru'` in layout, redirect to `/dashboard`
- Sidebar: conditionally render admin nav items based on `profile.role`
- Supabase RLS: enforce at DB level too (don't rely on UI alone)

### Auto-Create Profile on Signup (Trigger)

```sql
CREATE OR REPLACE FUNCTION handle_new_user() RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, nama, role, kelas)
  VALUES (NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'nama', NEW.email),
    COALESCE(NEW.raw_user_meta_data->>'role', 'siswa'),
    NEW.raw_user_meta_data->>'kelas');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION handle_new_user();
```

Pass metadata in `signUp()`: `options: { data: { nama, role, kelas } }`.

### Admin User Management (Guru Creates Siswa Accounts)

When a role (e.g., `guru`) needs to create/delete other users from within the app, use Supabase **Service Role Key** — anon key cannot call `auth.admin.*`.

**Setup:**
1. Add `SUPABASE_SERVICE_ROLE_KEY` as a Vercel env var (server-only, no `NEXT_PUBLIC_` prefix)
2. Never expose this key to the browser

**API Route Pattern — `getCallerProfile()` helper:**

```ts
// Reusable helper — reads JWT from cookie, verifies via service role client
async function getCallerProfile(request: NextRequest) {
  const token = request.cookies.get('sb-access-token')?.value;
  if (!token) return null;

  const adminClient = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );

  const { data: { user }, error } = await adminClient.auth.getUser(token);
  if (error || !user) return null;

  const { data: profile } = await adminClient
    .from('profiles')
    .select('id, role')
    .eq('id', user.id)
    .single();

  return profile;
}
```

**Create user endpoint (`POST /api/admin/create-user`):**
```ts
export async function POST(request: NextRequest) {
  const profile = await getCallerProfile(request);
  if (!profile) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  if (profile.role !== 'guru') return NextResponse.json({ error: 'Forbidden' }, { status: 403 });

  const adminClient = createClient(url, serviceKey, { auth: { autoRefreshToken: false, persistSession: false } });
  const { nama, email, password, kelas } = await request.json();

  const { data: newUser, error } = await adminClient.auth.admin.createUser({
    email, password,
    email_confirm: true,  // skip email verification
    user_metadata: { nama, kelas }
  });
  if (error) return NextResponse.json({ error: error.message }, { status: 400 });

  // Insert profile (trigger may handle this, but explicit insert is safer)
  const { error: profileError } = await adminClient.from('profiles')
    .insert({ id: newUser.user.id, nama, email, kelas: kelas || null, role: 'siswa' });

  if (profileError) {
    await adminClient.auth.admin.deleteUser(newUser.user.id);  // rollback
    return NextResponse.json({ error: profileError.message }, { status: 500 });
  }

  return NextResponse.json({ success: true });
}
```

**Delete user endpoint (`DELETE /api/admin/delete-user`):**
```ts
const { userId } = await request.json();
if (userId === callerProfile.id) return NextResponse.json({ error: 'Tidak bisa hapus akun sendiri' }, { status: 400 });
await adminClient.auth.admin.deleteUser(userId);  // cascade deletes profile via FK
```

**Key pitfalls:**
- `getUser` is NOT exported from `auth-server.ts` — the helper above reads the cookie directly and calls `adminClient.auth.getUser(token)`. Don't try to import a server-only function into API routes.
- `email_confirm: true` skips the email verification step — required for school apps where students don't have real email access.
- If profile insert fails, rollback by deleting the auth user — otherwise orphaned auth users accumulate.
- Guru account must be created manually in Supabase Auth dashboard first (**Authentication > Users > Add user**), then set role via SQL: `UPDATE profiles SET role = 'guru' WHERE email = 'email@sekolah.sch.id';` — the trigger creates the profile with role='siswa' by default, so the UPDATE is always needed.
- After creating the guru account, set Supabase Auth **Site URL** and **Redirect URLs** in **Authentication > Settings** to match the deployed domain (e.g., `https://my-app.vercel.app` and `https://my-app.vercel.app/**`).

### Pitfalls

- `cookies()` in Server Components is async in Next.js 15 — use `await cookies()`. In Next.js 14 it's sync.
- Supabase RLS must be enabled on every table — inserts/updates silently fail without it if policies aren't set.
- `revalidate = 0` needed on Server Component pages that show live data (otherwise Next.js caches the page).
- Modal forms: use `onClick={(e) => { if (e.target === e.currentTarget) closeModal(); }}` on overlay to close on backdrop click.
- Stock validation: check `jumlah > stok_saat_ini` in the form BEFORE inserting — the DB trigger will still run but the UX is better with client-side guard.

See `references/supabase-nextjs-pattern.md` for the complete schema SQL and middleware code.

## Dark/Light Mode Toggle (CSS Custom Properties + data-theme)

When building a site with theme switching, use CSS custom properties scoped by `[data-theme]` attribute on `<html>`. This avoids Tailwind's `dark:` class conflicts and gives full control.

### Architecture
```
ThemeProvider (client) → reads localStorage / prefers-color-scheme
                      → sets data-theme on <html>
                      → exposes { theme, toggle } via Context

globals.css           → :root { --bg: #fff; --text: #111; }
                      → [data-theme="dark"] { --bg: #0a0a0b; --text: #ededef; }

Components            → style={{ background: "var(--bg)", color: "var(--text)" }}
```

### ThemeProvider (use client)
```tsx
"use client";
import { createContext, useContext, useEffect, useState, useCallback } from "react";

type Theme = "light" | "dark";
const ThemeContext = createContext<{ theme: Theme; toggle: () => void }>({ theme: "dark", toggle: () => {} });
export function useTheme() { return useContext(ThemeContext); }

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("theme") as Theme | null;
    const preferred = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    const initial = stored || preferred;
    setTheme(initial);
    document.documentElement.setAttribute("data-theme", initial);
    setMounted(true);
  }, []);

  const toggle = useCallback(() => {
    setTheme(prev => {
      const next = prev === "dark" ? "light" : "dark";
      localStorage.setItem("theme", next);
      document.documentElement.setAttribute("data-theme", next);
      return next;
    });
  }, []);

  if (!mounted) return <div style={{ visibility: "hidden" }}>{children}</div>;
  return <ThemeContext.Provider value={{ theme, toggle }}>{children}</ThemeContext.Provider>;
}
```

### CSS Pattern (globals.css)
```css
:root {
  --bg-primary: #ffffff;
  --text-primary: #111111;
  --accent: #2563eb;
  --border: rgba(0, 0, 0, 0.08);
  --shadow-card: 0 1px 3px rgba(0,0,0,0.06);
}
[data-theme="dark"] {
  --bg-primary: #0a0a0b;
  --text-primary: #ededef;
  --accent: #3b82f6;
  --border: rgba(255, 255, 255, 0.06);
  --shadow-card: 0 1px 3px rgba(0,0,0,0.3);
}
body {
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
}
```

**Pitfall:** Add `suppressHydrationWarning` to `<html>` in layout.tsx — without it, Next.js hydration fails because the server renders without `data-theme` but the client sets it immediately on mount.

```tsx
// layout.tsx
<html lang="en" suppressHydrationWarning>
  <body><ThemeProvider>{children}</ThemeProvider></body>
</html>
```

**Pitfall:** The `if (!mounted) return <div style={{ visibility: "hidden" }}>{children}</div>` prevents flash of wrong theme. Don't return `null` — that causes layout shift.

## Pitfalls

### lucide-react Icon Names Change Across Versions
`Github` and `Linkedin` are NOT exported from lucide-react in recent versions (v0.400+). The barrel export silently drops them. Build fails with:
```
'Github' is not exported from '__barrel_optimize__?names=...Github!=!lucide-react'
```

**Fix:** Create custom SVG components for brand icons. Lucide is unreliable for brand logos — use inline SVGs from the brand's icon set or simple SVG paths:
```tsx
// components/SocialIcons.tsx
"use client";
export function GithubIcon({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </svg>
  );
}
```
Also note: LSP diagnostics may show stale errors after fixing imports — the TypeScript server caches old import paths. Rebuild (`npm run build`) to verify, don't trust the LSP diagnostics overlay.

## References

- See `references/supabase-nextjs-pattern.md` for complete Supabase schema SQL, RLS policies, triggers, and middleware
- See `references/github-as-database.md` for using GitHub as a database — API route code, setup steps, SHA handling, migration from JSONBlob
- See `references/jsonblob-cloud-sync.md` for JSONBlob cloud sync (NOT recommended — blobs expire in 1 day)
- See `references/localstorage-full-cms.md` for full CMS via localStorage — site-wide content editing, multi-tab admin, password management, audit workflow
- See `references/localstorage-site-settings.md` for the simpler contacts-only localStorage pattern
- See `references/google-maps-embed.md` for converting Google Maps place URLs to embed URLs for iframe src
- See `references/static-site-image-crud.md` for adding image support to static Next.js CRUD without a backend
- See `references/vercel-prebuilt-deploy.md` for the full pre-built deployment pattern when Vercel's remote npm install fails
- See `references/nextjs-build-pitfalls.md` for context provider SSR failures, Tailwind v3/v4 mismatch, TypeScript `as const` narrowing, and other batch build pitfalls
