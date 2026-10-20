# JSONBlob Cloud Sync for Static Sites (No Backend)

## Problem
localStorage-only CMS means admin edits are only visible in the admin's browser. Other visitors see hardcoded defaults.

## Solution: JSONBlob.com
Free JSON storage API — no account, no auth, no expiry, unlimited reads/writes.

### API
```
Base URL: https://jsonblob.com/api/jsonBlob

POST   /              → Create blob (returns ID in Location header + x-jsonblob-id)
GET    /{id}           → Read blob
PUT    /{id}           → Update blob (full replace)
DELETE /{id}           → Delete blob

Headers: Content-Type: application/json, Accept: application/json
```

### Creating Blobs
```bash
# Write data to temp file to avoid shell escaping issues
echo '{"key": "value"}' > /tmp/data.json
curl -s -X POST https://jsonblob.com/api/jsonBlob \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d @/tmp/data.json -i
# Extract ID from Location header: /api/jsonBlob/{ID}
```

### Architecture: Dual-Layer (Cloud + localStorage Fallback)

```
lib/jsonblob.ts          — API helper with in-memory cache (30s TTL)
lib/contacts.ts          — getContacts() [sync/localStorage] + fetchContacts() [async/cloud]
lib/siteSettings.ts      — getSiteSettings() [sync] + fetchSiteSettings() [async]
lib/products.ts          — re-exports, default data

Admin saves → updateBlob() → cloud + localStorage
Pages load  → sync render (localStorage) → async fetch (cloud) → re-render
```

### Key Pattern: Sync Initial + Async Update

Every component follows this pattern for zero-flash rendering:

```tsx
const [data, setData] = useState<T>(defaultValue);

useEffect(() => {
  // 1. Instant render from localStorage (no flash)
  setData(getSyncVersion());
  // 2. Then fetch from cloud and update
  fetchAsyncVersion().then(setData);
}, []);
```

### jsonblob.ts Helper (Uses API Proxy)

```typescript
// lib/jsonblob.ts — calls /api/data/[key] proxy, NOT jsonblob.com directly
export type BlobKey = "products" | "contacts" | "siteSettings" | "password";

function getApiUrl(key: BlobKey): string {
  return `/api/data/${key}`; // Same-origin proxy — no CORS issues
}

// In-memory cache to avoid re-fetching on every component mount
const cache: Record<string, { data: unknown; ts: number }> = {};
const CACHE_TTL = 30_000; // 30 seconds

export async function fetchBlob<T>(key: BlobKey, fallback: T): Promise<T> {
  // Check cache → fetch from proxy → fallback to localStorage → fallback to defaults
}

export async function updateBlob<T>(key: BlobKey, data: T): Promise<boolean> {
  // PUT to proxy → update cache → update localStorage as backup
}
```

### Save Pattern (Admin)

```typescript
const handleSave = async (e: React.FormEvent) => {
  e.preventDefault();
  const ok = await saveToCloud(formData);
  showSuccess(ok 
    ? "✅ Tersimpan ke cloud!" 
    : "⚠️ Tersimpan lokal, gagal sync ke cloud.");
};
```

### Typical Blob Structure

Create one blob per data domain:
- **Products** — array of product objects
- **Contacts** — flat object (whatsapp, instagram, address, maps)
- **Site Settings** — nested object (hero, stats, about, school, visionMission, CTA)
- **Password** — `{ password: "xxx" }` (client-side only, fine for school projects)

### CRITICAL: CORS Issue — API Proxy Required

JSONBlob does **NOT** properly handle CORS preflight (OPTIONS) requests from browsers. Direct PUT/POST from `fetch()` in a browser will fail with CORS errors, even though GET may work. **Confirmed May 2026.**

**Solution:** Create a Next.js API route as a proxy:

```
Browser → /api/data/[key] (same-origin, no CORS) → JSONBlob.com (server-to-server, no CORS)
```

```typescript
// src/app/api/data/[key]/route.ts
import { NextRequest, NextResponse } from "next/server";

const BLOB_IDS: Record<string, string> = {
  products: "xxx",
  contacts: "xxx",
  siteSettings: "xxx",
  password: "xxx",
};

export async function GET(_req: NextRequest, { params }: { params: { key: string } }) {
  const blobId = BLOB_IDS[params.key];
  if (!blobId) return NextResponse.json({ error: "Invalid key" }, { status: 400 });
  const res = await fetch(`https://jsonblob.com/api/jsonBlob/${blobId}`, {
    headers: { Accept: "application/json" }, cache: "no-store",
  });
  return NextResponse.json(await res.json());
}

export async function PUT(req: NextRequest, { params }: { params: { key: string } }) {
  const blobId = BLOB_IDS[params.key];
  if (!blobId) return NextResponse.json({ error: "Invalid key" }, { status: 400 });
  const body = await req.json();
  const res = await fetch(`https://jsonblob.com/api/jsonBlob/${blobId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  return res.ok ? NextResponse.json({ success: true }) : NextResponse.json({ error: "Failed" }, { status: res.status });
}
```

Then update `lib/jsonblob.ts` to call `/api/data/${key}` instead of `jsonblob.com` directly.

**This is NOT optional** — without the proxy, admin saves will fail silently or show "⚠️ gagal sync ke cloud" errors.

### Pitfalls

1. **~~CORS~~: JSONBlob DOES have CORS issues** — PUT/POST from browsers fail. Always use the API proxy route above.
2. **No auth on blobs**: Anyone with the blob ID can read/write. Fine for school/demo sites. For production, use Supabase or Firebase instead.
3. **Rate limits**: JSONBlob is generous but undocumented. Cache aggressively (30s TTL minimum).
4. **Blob IDs are permanent**: Once created, the ID never changes. Store them as constants.
5. **Create blobs via curl first**: Don't create from the app — create once via terminal, hardcode IDs.
6. **Shell escaping**: Use `curl -d @/tmp/file.json` instead of inline JSON to avoid escaping issues with complex data.
7. **Fallback chain**: Always implement cloud → localStorage → hardcoded defaults. Never let a cloud failure break the site.
8. **Vercel free tier**: API routes work on Vercel free tier as serverless functions. The proxy route shows as `ƒ (Dynamic)` in build output.

### Alternatives Considered

| Service | Auth Required | Free Tier | Notes |
|---------|--------------|-----------|-------|
| JSONBlob.com | No | Unlimited | Simplest, but needs API proxy for CORS |
| npoint.io | No | Limited | Unreliable — returned 500 errors (May 2026) |
| JSONBin.io | Yes (API key) | 10K req/mo | Requires account signup |
| Supabase | Yes | 500MB DB | Overkill for simple JSON, but more secure |
| Firebase RTDB | Yes | 1GB | Google account required |
