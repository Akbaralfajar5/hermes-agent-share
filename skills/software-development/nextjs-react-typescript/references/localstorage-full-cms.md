# Full CMS via localStorage (No Backend, Vercel Free Tier)

## Problem
Static Next.js site needs ALL content editable from admin panel — not just contacts, but hero text, stats, about page, school profile, vision/mission, CTA text, brand name, and admin password. No backend, no database, Vercel free tier only.

## Architecture: Multi-Layer Settings

```
lib/siteSettings.ts    ← ALL site content: hero, stats, about, school, visi/misi, CTA, brand
lib/contacts.ts        ← Contact-specific: WhatsApp, Instagram, address, maps
lib/products.ts        ← Product data + re-exports from contacts.ts
admin/dashboard/       ← 4-tab admin: Produk | Kontak | Konten | Password
```

### localStorage Keys
- `myapp_products` — product CRUD data
- `myapp_contacts` — contact info (WA, IG, address)
- `myapp_site_settings` — all site content (hero, stats, about, school, etc.)
- `myapp_admin_password` — admin password (default fallback in code)

## 1. Site Settings Module (lib/siteSettings.ts)

### Interface Design — Nested Objects for Grouped Content

```typescript
export interface SiteSettings {
  // Brand (navbar, footer, copyright)
  brandName: string;
  brandSubtitle: string;
  brandDescription: string;
  
  // Hero section
  hero: {
    badge: string;
    heading1: string;      // white text
    heading2: string;      // gold/accent color
    heading3: string;      // pink/secondary color
    description: string;
  };
  
  // Stats (array of {number, label, icon})
  stats: { number: string; label: string; icon: string }[];
  
  // Featured products section headings
  featuredBadge: string;
  featuredHeading: string;
  featuredDescription: string;
  
  // About section (homepage)
  about: {
    badge: string;
    heading: string;
    paragraphs: string[];
    bullets: string[];
    cardTitle: string;
    cardDescription: string;
  };
  
  // About page (separate, more detailed)
  aboutPage: {
    myapp: string;
    myapp: string[];
    features: { title: string; description: string }[];
  };
  
  // School profile
  school: {
    name: string;
    level: string;
    status: string;
    district: string;
    province: string;
    address: string;
  };
  
  // Vision & Mission
  visionMission: {
    vision: string;
    missions: string[];
  };
  
  // CTA
  ctaHeading: string;
  ctaDescription: string;
}
```

### Password Management — Separate from Settings

```typescript
const PASSWORD_KEY = "myapp_admin_password";

export function getAdminPassword(): string {
  if (typeof window === "undefined") return DEFAULT_PASSWORD;
  return localStorage.getItem(PASSWORD_KEY) || DEFAULT_PASSWORD;
}

export function saveAdminPassword(password: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(PASSWORD_KEY, password);
  }
}
```

### Login Page — Dynamic Password Check

```typescript
// In admin/page.tsx handleLogin:
const savedPassword = typeof window !== "undefined"
if (username === "admin" && password === savedPassword) { /* login */ }
```

## 2. Admin Dashboard — Multi-Tab Pattern

### Tab State
```typescript
const [activeTab, setActiveTab] = useState<"produk" | "kontak" | "konten" | "password">("produk");
```

### Tab Button UI — Compact Pill Switcher
```tsx
<div className="flex gap-2 bg-white rounded-xl p-1 border w-fit">
  {[
    { key: "produk", label: "📦 Produk" },
    { key: "kontak", label: "📞 Kontak" },
    { key: "konten", label: "✏️ Konten" },
    { key: "password", label: "🔒 Password" },
  ].map(tab => (
    <button key={tab.key} onClick={() => setActiveTab(tab.key)}
      className={activeTab === tab.key ? "bg-primary text-white" : "text-gray-500"}>
      {tab.label}
    </button>
  ))}
</div>
```

### Content Tab — Grouped Sections with Colored Backgrounds
Each content group gets a distinct background color for visual separation:
- 🏷️ Brand → gray bg
- 🎯 Hero → blue bg
- 📊 Stats → purple bg
- 🎯 Visi/Misi → green bg
- 🏫 Profil Sekolah → amber bg
- 📢 CTA → pink bg

### Password Tab — 3-Field Form with Validation
```typescript
const handleChangePassword = (e: React.FormEvent) => {
  e.preventDefault();
  const current = getAdminPassword();
  if (currentPassword !== current) { showError("Password lama salah!"); return; }
  if (newPassword.length < 4) { showError("Minimal 4 karakter!"); return; }
  if (newPassword !== confirmPassword) { showError("Konfirmasi tidak cocok!"); return; }
  saveAdminPassword(newPassword);
  // Clear form fields
  showSuccess("Password berhasil diubah!");
};
```

## 3. Making ALL Pages Dynamic

### Pattern: Every Page Follows This Structure

```typescript
"use client";
import { useState, useEffect } from "react";
import { getSiteSettings, SiteSettings, defaultSettings } from "@/lib/siteSettings";

export default function SomePage() {
  const [settings, setSettings] = useState<SiteSettings>(defaultSettings);
  
  useEffect(() => {
    setSettings(getSiteSettings());
  }, []);
  
  return (
    // Use settings.hero.heading1, settings.about.paragraphs, etc.
  );
}
```

### Products — Read from localStorage on Public Pages Too

Critical bug in initial implementation: admin saves products to localStorage but public pages import from hardcoded `lib/products.ts`. Fix:

```typescript
const [productList, setProductList] = useState<Product[]>(defaultProducts);

useEffect(() => {
  const stored = localStorage.getItem("myapp_products");
  if (stored) {
    try { setProductList(JSON.parse(stored)); } catch { /* defaults */ }
  }
}, []);
```

### Footer — Dynamic Product Links

Footer product links must also read from localStorage, not hardcoded:
```typescript
{productList.slice(0, 5).map((p) => (
  <Link href={`/produk/${p.slug}`}>{p.name}</Link>
))}
```

## 4. Audit Checklist — Before Deploying "Everything Editable"

1. **Delegate audit first**: Use `delegate_task` to scan ALL files for hardcoded content
2. **Group by page**: List every hardcoded string per file
3. **Mark status**: 🔴 hardcoded, 🟡 partially dynamic, 🟢 fully dynamic
4. **Identify critical gaps**: Product pages not reading localStorage, footer address hardcoded, etc.
5. **Create central settings module** with ALL content as typed interface
6. **Update every consuming component** to read from settings
7. **Build + deploy + verify** each page reads dynamic content

## Pitfalls

- **Metadata exports**: `"use client"` pages can't have `export const metadata`. Remove it or move to layout.tsx.
- **Array fields in forms**: For missions/bullets, use textarea with `value.join("\n")` and `onChange: value.split("\n").filter(m => m.trim())`.
- **Nested state updates**: Use spread carefully: `setSiteForm({...siteForm, hero: {...siteForm.hero, badge: newValue}})`.
- **Stats array editing**: Map over array, clone, modify index, set: `const s = [...siteForm.stats]; s[i] = {...s[i], number: newVal}; setSiteForm({...siteForm, stats: s})`.
- **SSR hydration**: Always initialize with `defaultSettings` (not empty object) to match server render.
- **Password stored in localStorage**: This is client-side only security — acceptable for school project admin panels, NOT for production apps with sensitive data.
- **Product detail pages** (`/produk/[slug]`): These use `getStaticProps`/SSG and won't read localStorage at build time. They still import from `lib/products.ts` for the static generation, but client-side navigation will show localStorage data.

## Upgrading to Cloud Storage

localStorage-only CMS has a fundamental limitation: edits are only visible in the admin's browser. When the user asks "will other visitors see my changes?", the answer is no.

**Upgrade path:** Add JSONBlob.com as cloud storage layer. See `references/jsonblob-cloud-sync.md` for the full pattern. Key changes:
1. Create `lib/jsonblob.ts` with fetchBlob/updateBlob helpers + 30s cache
2. Add async `fetch*()` functions alongside sync `get*()` in each lib module
3. Components: render sync first (localStorage), then async-update from cloud
4. Admin saves: write to cloud + localStorage simultaneously
5. Login page: fetch cloud password on mount to sync localStorage
