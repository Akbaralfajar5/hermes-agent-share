# Next.js + Tailwind Maintenance Patterns

## Critical Pitfall: CSS Custom Properties vs Tailwind Config Color Conflict

**Root cause:** `globals.css` defines CSS custom properties (`--primary: #2B4EA2`) while `tailwind.config.ts` defines Tailwind color utilities (`primary: #E91E7B`). Components using `bg-primary` get Tailwind's color; elements using `var(--primary)` get CSS custom property's color. Result: visual clash (e.g., hero gradient blue, buttons pink).

**Detection:**
```bash
# Check for color definitions in both files
grep -n "primary\|accent\|green\|gold" src/app/globals.css
grep -n "primary\|accent\|green\|gold" tailwind.config.ts
# If DEFAULT values differ → color conflict
```

**Fix:** Align `globals.css` CSS custom properties to match `tailwind.config.ts` Tailwind color values. The Tailwind config is the source of truth for component styling; CSS custom properties should match.

**Prevention:** When changing Tailwind color config, ALWAYS update `globals.css` custom properties, scrollbar colors, hero gradients, and shadow colors to match. Treat them as a single color system.

## Full Audit Checklist for Next.js Websites

When user asks to "audit everything" or reports multiple bugs:

1. **Build check:** `npm run build` — fix all errors before proceeding
2. **Color system:** Compare `globals.css` vs `tailwind.config.ts` — align all color values
3. **Navigation:** Read `Navbar.tsx` — verify all `navLinks` match actual page routes in `src/app/`
4. **Footer links:** Read `Footer.tsx` — verify all links match actual routes
5. **localStorage keys:** Read data helper (`jsonblob.ts` or similar) — verify key mapping covers all data types
6. **Mobile menu:** Check hamburger toggle, backdrop click, body scroll lock, outside-click dismiss
7. **Static assets:** Verify `/logo.png`, favicons, videos exist in `public/`
8. **Console errors:** Deploy first, then check browser console for JS errors
9. **Link navigation:** Click-test all nav links — verify `window.location.pathname` changes

## Tailwind Class Issues to Watch

- `h-18` is NOT a standard Tailwind value → use `h-[4.5rem]`
- `opacity-85` is NOT standard → use `opacity-[0.85]`
- Dynamic class generation via string manipulation (e.g., `${item.color.replace("-50", "-500")}`) won't work — Tailwind purges unused classes at build time
- Duplicate imports (same module imported twice) are harmless but messy

## localStorage Key Mapping Pattern

When a data helper uses localStorage fallback, ensure EVERY data key has a unique localStorage key. Common bug: default/fallthrough case maps unrelated keys to the same localStorage entry (e.g., `galeri` → `myapp_admin_password`).

```typescript
// BAD: fallthrough catches unrelated keys
const localKey = key === "products" ? "myapp_products"
  : key === "contacts" ? "myapp_contacts"
  : "myapp_admin_password";  // galeri, testimonial all land here

// GOOD: explicit mapping for each key, with safe fallback
const localKey = key === "products" ? "myapp_products"
  : key === "contacts" ? "myapp_contacts"
  : key === "galeri" ? "myapp_galeri"
  : key === "testimonial" ? "myapp_testimonial"
  : key === "password" ? "myapp_admin_password"
  : `myapp_${key}`;
```

## Vercel Deploy Workflow

```bash
# 1. Fix lockfile if needed
grep -c "tencentyun" package-lock.json  # check for Tencent URLs
# If > 0: sed -i 's|http://mirrors.tencentyun.com/npm/|https://registry.npmjs.org/|g' package-lock.json

# 2. Build locally first
npm run build 2>&1 | tail -20

# 3. Deploy
vercel deploy --prod --yes --token "$VERCEL_TOKEN" 2>&1 | tail -5

# 4. Verify
# Look for: ▲ Aliased https://your-domain.vercel.app
# Look for: ✓ Ready in Xs
```
