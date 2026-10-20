# Favicon & Logo Deployment Patterns

## Logo Background Removal (PIL/Pillow)

When user provides a logo with white/light background and needs transparent background:

```python
from PIL import Image
import numpy as np

img = Image.open("logo.jpg").convert("RGBA")
pixels = np.array(img)
r, g, b = pixels[:,:,0].astype(int), pixels[:,:,1].astype(int), pixels[:,:,2].astype(int)
brightness = (r + g + b) / 3
bg_mask = brightness > 232  # threshold for near-white
pixels[bg_mask] = [0, 0, 0, 0]
result = Image.fromarray(pixels)
result.save("logo_transparent.png")
```

**Pitfall:** `PIL`/`Pillow` is NOT pre-installed in the hermes-agent venv. Always `pip install Pillow` first.

### Favicon Generation Script

```python
from PIL import Image
src = Image.open("logo_transparent.png")

# Multi-size ICO
sizes = [16, 32, 48, 64]
imgs = [src.resize((s, s), Image.LANCZOS) for s in sizes]
imgs[0].save("favicon.ico", format="ICO", sizes=[(s,s) for s in sizes], append_images=imgs[1:])

# Individual PNGs
for name, size in {"favicon-16x16.png": 16, "favicon-32x32.png": 32, 
                     "apple-touch-icon.png": 180, "android-chrome-192x192.png": 192,
                     "android-chrome-512x512.png": 512}.items():
    src.resize((size, size), Image.LANCZOS).save(name)
```

## Next.js + Vercel Favicon Deployment

### The Vercel CDN Cache Problem

Vercel aggressively caches static assets at the edge. Replacing `favicon.ico` with a new file of the **same name** may NOT bust the cache even after git push + redeploy. The edge continues serving the stale version.

**Solution: Rename the file.**
1. Use a new filename: `favicon-v2.ico`
2. Update metadata AND `<head>` tags to reference the new name
3. Push and deploy

### Next.js Double Favicon Injection

Next.js automatically adds `<link rel="icon" href="/favicon.ico" sizes="16x16" type="image/x-icon">` to the HTML head, regardless of what's in the metadata. This means even if you remove `favicon.ico` from metadata, the old file still gets referenced.

**Fix:** Add explicit `<link>` tags in the layout's `<head>` section (not just metadata `icons` config) to ensure the correct favicon takes priority. The browser uses the last-declared matching icon.

### Correct Next.js Metadata + Head Setup

```tsx
// In layout.tsx metadata export
icons: {
  icon: [
    { url: "/favicon-v2.ico", sizes: "any" },
    { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
  ],
  apple: "/apple-touch-icon.png",
},

// In the <head> JSX (inside the component)
<link rel="icon" href="/favicon-v2.ico" sizes="any" />
<link rel="icon" href="/favicon-32x32.png" type="image/png" sizes="32x32" />
<link rel="icon" href="/favicon-16x16.png" type="image/png" sizes="16x16" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
```

### Verification Pattern

After deploying, verify the ACTUAL file served (not just local file):
```bash
curl -s -o /tmp/test.ico https://site.com/favicon-v2.ico
python3 -c "
from PIL import Image; import numpy as np
img = Image.open('/tmp/test.ico')
p = np.array(img.convert('RGB')).reshape(-1,3)
dark = np.sum(p.mean(axis=1) < 50)
print(f'Size: {img.size}, dark%={dark/len(p)*100:.1f}%')
"
```

If dark% > 80% when expecting a colorful logo → Vercel is still serving cached/default version.

## Browser Cache Note

Even after server-side fix, user's browser may cache the old favicon. Tell user:
- Hard refresh: Ctrl+Shift+R (Win/Linux) or Cmd+Shift+R (Mac)
- Or test in incognito/private window
- Nuclear option: `chrome://favicon/site.com` → clear
