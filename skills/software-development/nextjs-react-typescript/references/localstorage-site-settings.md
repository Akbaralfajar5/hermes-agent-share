# Site-Wide Settings via localStorage (No Backend)

## Problem
Static Next.js sites on Vercel free tier have hardcoded contact info (WhatsApp number, Instagram handle, address) scattered across multiple components. The admin wants to change these without code deploys.

## Solution: Centralized Settings Module + Admin UI Tab

### Architecture
```
lib/contacts.ts          ← central config: interface, defaults, get/save, helper functions
admin/dashboard/page.tsx  ← admin UI with tab switcher (Produk | Kontak)
components/Footer.tsx     ← reads from getContacts()
components/WhatsAppButton.tsx ← reads from getContacts()
app/kontak/page.tsx       ← reads from getContacts()
```

### 1. Create a Settings Module (lib/contacts.ts)

```typescript
export interface ContactSettings {
  whatsappNumber: string;   // "6287833586843" (international, no +)
  whatsappDisplay: string;  // "087833586843" (display format)
  instagram: string;        // "exampleapp" (no @)
  address: string;
  mapsUrl: string;
  mapsEmbed: string;        // Google Maps embed URL
}

export const defaultContacts: ContactSettings = { /* hardcoded defaults */ };

const STORAGE_KEY = "myapp_contacts";

export function getContacts(): ContactSettings {
  if (typeof window === "undefined") return defaultContacts;
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    try {
      return { ...defaultContacts, ...JSON.parse(stored) };
    } catch { return defaultContacts; }
  }
  return defaultContacts;
}

export function saveContacts(contacts: ContactSettings): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(contacts));
  }
}

// Helper functions that accept optional contacts param
export function formatWhatsAppLink(productName: string, contacts?: ContactSettings): string {
  const c = contacts || getContacts();
  return `https://wa.me/${c.whatsappNumber}?text=${encodeURIComponent(...)}`;
}
```

**Key pattern:** `{ ...defaultContacts, ...JSON.parse(stored) }` — merge with defaults so new fields added later don't break existing stored data.

### 2. Re-export from Existing Module

If other files already import helpers from `lib/products.ts`, re-export:
```typescript
// lib/products.ts
export { formatWhatsAppLink, formatWhatsAppLinkGeneral } from "./contacts";
```
This avoids changing imports across the codebase.

### 3. Convert Server Components to Client Components

Components that were server-rendered but now need localStorage must become client components:

```typescript
// BEFORE (server component)
import { formatWhatsAppLinkGeneral } from "@/lib/products";
export default function Footer() { ... }

// AFTER (client component)
"use client";
import { useState, useEffect } from "react";
import { getContacts, ContactSettings, defaultContacts } from "@/lib/contacts";

export default function Footer() {
  const [contacts, setContacts] = useState<ContactSettings>(defaultContacts);
  useEffect(() => { setContacts(getContacts()); }, []);
  // Now use contacts.whatsappNumber, contacts.instagram, etc.
}
```

**Pitfall:** Server components with `export const metadata` can't have `"use client"`. Remove the metadata export when converting (metadata can be set in layout.tsx or a parent page instead).

### 4. Admin UI: Tab Switcher Pattern

Add tabs to the existing admin dashboard rather than a separate page:

```typescript
const [activeTab, setActiveTab] = useState<"produk" | "kontak">("produk");

// Tab buttons
<div className="flex gap-2 bg-white rounded-xl p-1 border w-fit">
  <button onClick={() => setActiveTab("produk")}
    className={activeTab === "produk" ? "bg-primary text-white" : "text-gray-500"}>
    📦 Kelola Produk
  </button>
  <button onClick={() => setActiveTab("kontak")}
    className={activeTab === "kontak" ? "bg-primary text-white" : "text-gray-500"}>
    📞 Pengaturan Kontak
  </button>
</div>

// Conditional rendering
{activeTab === "kontak" && ( <ContactSettingsForm /> )}
{activeTab === "produk" && ( <ProductCRUD /> )}
```

### 5. Contact Form: Grouped by Service

Group fields visually with colored backgrounds:
- **WhatsApp** (green bg): number (international), number (display), contact name
- **Instagram** (pink bg): username with @ prefix shown
- **Address** (blue bg): full address textarea, Google Maps URL

### Checklist: Adding Site-Wide Settings

1. Create `lib/<settings>.ts` with interface, defaults, get/save, helpers
2. Re-export helpers from existing modules to avoid import changes
3. Convert consuming server components to `"use client"` with useState/useEffect
4. Replace ALL hardcoded values (search codebase: `grep -r "old_value" src/`)
5. Add admin UI (tab or section) with form state mirroring the interface
6. Include success message on save
7. Build + deploy
8. Test: change value in admin → refresh other pages → verify update

### Pitfalls

- **SSR hydration mismatch:** Initialize state with `defaultContacts` (not empty), so server-rendered HTML matches initial client render. The useEffect updates after hydration.
- **Metadata export conflict:** `"use client"` and `export const metadata` can't coexist. Move metadata to layout.tsx or remove it.
- **Unused state warning:** If you have `const [contacts, setContacts]` where `contacts` is only used via `setContacts` in a handler, add `// eslint-disable-next-line` or restructure.
- **Multiple localStorage keys:** Keep keys namespaced (e.g., `myapp_contacts`, `myapp_products`) to avoid collisions.
