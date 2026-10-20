# Next.js Build Pitfalls (Batch 2026)

## Context Provider SSR Prerender Failure

When a React context provider uses `createContext(undefined)` and the hook throws when context is missing, Next.js static prerendering (SSG) fails because the page is rendered without the provider wrapper.

### Symptom
```
Error: useTheme must be used within a ThemeProvider
Error occurred prerendering page "/". Read more: https://nextjs.org/docs/messages/prerender-error
> Build failed because of webpack errors
```

### Root Cause
Next.js prerenders static pages at build time. The `page.tsx` is a Server Component that renders without the client-side `ThemeProvider` wrapper. When it calls `useTheme()`, the context is `undefined` → throws → build fails.

### Fix: Default Context Values (Never Throw)

```tsx
// ❌ Breaks prerender
const ThemeContext = createContext<ThemeType | undefined>(undefined);
export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}

// ✅ Works — default values, no throw
const ThemeContext = createContext<ThemeType>({
  theme: 'light',
  toggle: () => {},
});
export function useTheme() {
  return useContext(ThemeContext);
}
```

### Pattern for Store/State Contexts
Same pattern applies to Zustand-like store contexts (cart, auth, etc.):

```tsx
// ✅ Default empty implementations
const StoreContext = createContext<StoreType>({
  items: [],
  addItem: () => {},
  removeItem: () => {},
  clear: () => {},
});
```

### When This Fires
- Any `"use client"` context that uses `createContext<T | undefined>(undefined)`
- Any hook that throws `new Error("must be used within XProvider")`
- Especially common when subagents generate context boilerplate

### Audit Command
```bash
grep -rn "throw new Error.*must be used within\|createContext.*undefined" src/ --include="*.tsx" --include="*.ts"
```

---

## Tailwind CSS v3 vs v4 Import Syntax

### Symptom
```
Module not found: Can't resolve 'tailwindcss'
> Build failed because of webpack errors
```

### Root Cause
Tailwind v4 uses `@import "tailwindcss"` in CSS. Tailwind v3 uses `@tailwind` directives. Installing v3 but writing v4 syntax (or vice versa) causes the build to fail.

### Fix
```css
/* ❌ Tailwind v4 syntax — fails with tailwindcss@^3 */
@import "tailwindcss";

/* ✅ Tailwind v3 syntax */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Detection
```bash
# Check installed version
cat node_modules/tailwindcss/package.json | grep '"version"'

# Check CSS syntax
head -3 src/app/globals.css
```

### When This Fires
- Subagents often use v4 syntax because it's newer, but `create-next-app` installs v3
- Any project scaffolded with `npx create-next-app@14` uses Tailwind v3

---

## TypeScript `as const` Status Field Type Narrowing

### Symptom
```
Type error: Type '"active" | "archived" | "draft"' is not assignable to type '"active"'
```

### Root Cause
```tsx
const [formData, setFormData] = useState({
  status: 'active' as const,  // Type is literal 'active', not string union
});

// Later, assigning from a broader type:
setFormData({ ...formData, status: proj.status });  // ERROR: proj.status is 'active' | 'archived' | 'draft'
```

### Fix
```tsx
const [formData, setFormData] = useState({
  status: 'active' as 'active' | 'archived' | 'draft',
});
```

---

## Missing Operator Causes Cryptic Syntax Error

### Symptom
```
Caused by:
    Syntax Error
./src/app/dashboard/team/page.tsx
```

### Root Cause
```tsx
const diff = Date.now() new Date(timestamp).getTime();  // Missing `-` operator
```

SWC reports the syntax error on the **next** line (a template literal), not the actual broken line. The error message is misleading.

### Fix
```tsx
const diff = Date.now() - new Date(timestamp).getTime();
```

### Debugging Tip
When SWC reports a syntax error on a line that looks valid, check the **previous** line for missing operators, unclosed brackets, or incomplete expressions.

---

## `npm error Invalid Version:` with Empty Version

### Symptom
```
npm error Invalid Version:
```

### Root Cause
Corrupted or missing `package-lock.json`, often caused by regenerating the lockfile with a Tencent mirror or npm registry mismatch.

### Fix
```bash
# Delete lockfile and reinstall with clean registry
rm package-lock.json
npm install --registry=https://registry.npmjs.org/
```

---

## Parallel Vercel Deploys Cause QUEUE Deadlock

When deploying multiple projects simultaneously to the same Vercel account (free tier), ALL deployments stay in QUEUED state indefinitely. Vercel free tier serializes builds — deploying 6 projects at once causes a deadlock.

### Fix
Deploy sequentially with `--no-wait`:
```bash
for proj in project-a project-b project-c; do
  cd ~/projects/$proj
  vercel --token "$VERCEL_TOKEN" --prod --yes --no-wait
  sleep 5
done
```

See `vercel-operations` skill for full details.
