# Adding Image Support to Static Next.js CRUD (No Backend)

## Problem
Static Next.js sites on Vercel free tier have no backend/API routes for file uploads. Admin panels using localStorage for CRUD can only store text fields (like a `color` placeholder). Users need to add product photos.

## Solution: URL-Based Image Input

Since there's no server to receive file uploads, use **image URLs** from external hosting (ImgBB, Imgur, Google Drive, Cloudinary free tier).

### Implementation Pattern

#### 1. Add `image` field to data interface
```typescript
// lib/products.ts
export interface Product {
  // ... existing fields
  color: string;      // fallback placeholder color
  image?: string;     // URL to product image (optional)
}
```

#### 2. Add form state + URL input with live preview
```typescript
// Admin form state
const [formImage, setFormImage] = useState("");

// In the form JSX
<div>
  <label>Gambar Produk (URL)</label>
  <input
    type="url"
    value={formImage}
    onChange={(e) => setFormImage(e.target.value)}
    placeholder="https://example.com/gambar.jpg"
  />
  {formImage && (
    <div className="mt-2 h-40 rounded-xl overflow-hidden border bg-gray-50">
      <img
        src={formImage}
        alt="Preview"
        className="w-full h-full object-contain"
        onError={(e) => {
          (e.target as HTMLImageElement).style.display = 'none';
        }}
      />
    </div>
  )}
  <p className="text-xs text-gray-400 mt-1">
    Upload gambar ke ImgBB / Imgur / Google Drive, lalu paste URL-nya
  </p>
</div>
```

#### 3. Conditional rendering: image vs color placeholder
```tsx
{product.image ? (
  <img
    src={product.image}
    alt={product.name}
    className="w-full h-full object-cover"
  />
) : (
  <div style={{ backgroundColor: product.color }}>
    <SvgPlaceholderIcon />
  </div>
)}
```

### Checklist When Adding a New Field to Full-Stack Feature
1. **Data interface** (lib/types or lib/products.ts) — add field
2. **Admin interface** (AdminProduct) — add field
3. **Form state** — add useState + resetForm + handleEdit + handleSubmit
4. **Data loading** — add fallback in loadProducts mapping (`p.image || ""`)
5. **Form UI** — add input field with preview
6. **All display components** — ProductCard, detail page, related products, admin table (desktop + mobile)
7. **Build** — `npm run build` to catch TypeScript errors
8. **Deploy** — push to production

### Why `<img>` Instead of Next.js `<Image>`
- `<Image>` requires whitelisting domains in `next.config.mjs` (`images.remotePatterns`)
- Since admin can paste ANY URL from any host, you'd need a wildcard pattern
- Using plain `<img>` avoids this config requirement entirely
- ESLint warnings about `<img>` are acceptable for this use case
- Trade-off: no automatic optimization, but simpler for user-uploaded URLs

### Alternative: Base64 in localStorage
Could encode images as base64 and store in localStorage, but:
- localStorage has ~5-10MB limit per origin
- Large images quickly exhaust this
- URL approach is more scalable and doesn't bloat localStorage
