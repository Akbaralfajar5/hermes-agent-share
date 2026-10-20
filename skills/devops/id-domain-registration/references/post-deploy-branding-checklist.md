# Post-Deploy Branding Checklist

After custom domain goes live, the user will often follow up asking about
**favicon, app icon, theme color, PWA installability** — usually phrased as
"masih logo Vercel atau sudah ganti?" or "icon nya bisa dipasang di home
screen?". These are quick-win polish items that take a deploy from "techy MVP"
to "feels like a real product." Bundle them as one motion when finishing a
custom-domain rollout.

---

## 1. Detect: Is Favicon Still Default Next.js?

Don't guess from the file size — Next.js default favicon and a custom one can
both be ~25KB. Use these tells:

```bash
# Pull live favicon
curl -s "https://<domain>/favicon.ico?v=$(date +%s)" -o /tmp/favicon_live.ico
md5sum /tmp/favicon_live.ico

# Compare to repo source
md5sum ~/<project>/src/app/favicon.ico
# If hashes match → file IS what's in repo (no Vercel injection)

# Sample center pixel — Next.js default has white center, gradient "N"
python3 -c "
from PIL import Image
img = Image.open('/tmp/favicon_live.ico')
for size in [(16,16),(32,32),(256,256)]:
    img.size = size; img.load()
    print(size, 'center:', img.getpixel((size[0]//2, size[1]//2)))
"
```

Default Next.js favicon center pixel is `(255, 255, 255, 255)` (pure white)
across all sizes — the dark "N" is at corners. If you see all-white centers, it's still default.

---

## 2. Generate Custom Favicon Without External Image API

When `image_generate` (FAL) is rate-limited / out of credits, render a minimal
icon with PIL directly. Pattern that's worked: rounded gradient background +
simple geometric foreground + white outline.

Template script: `scripts/gen_favicon_flask.py` (this skill).

The script:
- Generates 6 sizes (16, 32, 48, 64, 128, 256) into a single `.ico`
- Generates `apple-touch-icon.png` (180×180) for iOS
- Generates `icon-192.png` for PWA manifest
- Saves a 512px preview for visual confirmation before deploy

Customize the foreground shape and colors at the top of the script. Default is
an Erlenmeyer flask with emerald liquid — fits chemistry/lab apps. For other
domains, replace the flask polygon with a different shape (book, gear, leaf,
etc.) and pick brand colors.

**Multi-size ICO save gotcha**: PIL's `append_images` parameter doesn't actually
embed sizes into the ICO. Use the `sizes` parameter instead:

```python
img = Image.open('/tmp/favicon_256.png')  # biggest source
img.save('/tmp/favicon.ico', format='ICO',
         sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
# Verify:
ico = Image.open('/tmp/favicon.ico')
print(ico.ico.sizes())  # should list all 6
```

If the resulting ICO is < 1KB, sizes weren't embedded — re-check.

---

## 3. Drop Files Into Next.js Project

```bash
# Backup old favicon first
cp ~/<project>/src/app/favicon.ico ~/<project>/src/app/favicon.ico.bak

# Replace
cp /tmp/favicon_new.ico ~/<project>/src/app/favicon.ico

# PWA / iOS icons go in public/
mkdir -p ~/<project>/public
cp /tmp/apple-touch-icon.png ~/<project>/public/apple-touch-icon.png
cp /tmp/icon-192.png ~/<project>/public/icon-192.png
```

---

## 4. Wire Up `metadata` in `layout.tsx`

```tsx
export const metadata: Metadata = {
  title: '...',
  description: '...',
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
  themeColor: '#10b981',  // pick brand accent
  manifest: '/manifest.json',
};
```

Next.js 14 picks up `src/app/favicon.ico` automatically without explicit
`icons` config, but adding `apple` + `themeColor` + `manifest` enables PWA.

---

## 5. PWA Manifest

Create `public/manifest.json`:

```json
{
  "name": "<Full Name>",
  "short_name": "<≤12 chars>",
  "description": "...",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FAFAF9",
  "theme_color": "#10b981",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable" },
    { "src": "/apple-touch-icon.png", "sizes": "180x180", "type": "image/png" }
  ]
}
```

That's it — no service worker needed for "Add to Home Screen" to work. It's
just a bookmarked PWA shell that opens in standalone mode (no browser chrome).

For full offline support you'd add a service worker, but for a school/internal
tool it's overkill — manifest alone is enough to feel native.

---

## 6. Deploy + Verify

```bash
cd ~/<project>
npx vercel build --prod
npx vercel deploy --prebuilt --prod --token <TOKEN> --yes
```

Verify post-deploy:

```bash
curl -s "https://<domain>/favicon.ico?v=$(date +%s)" -o /tmp/check.ico
md5sum /tmp/check.ico
# Compare to ~/<project>/src/app/favicon.ico hash — must match

curl -sI "https://<domain>/apple-touch-icon.png" | head -3   # 200
curl -sI "https://<domain>/manifest.json" | head -3          # 200
```

Browser tab favicon updates after a hard refresh (cache-busting query string
forces it). On HP, user might need to remove/re-add bookmark to see new icon.

---

## 7. Tell User How to Install PWA

After deploy, proactively explain:

> Aplikasi sekarang bisa di-**add to home screen**. Tap menu Chrome (titik 3 di kanan atas) → "Add to Home screen" / "Install app" → konfirmasi. Icon muncul di home screen, dibuka tampak fullscreen tanpa address bar — feel like native app.
>
> iOS Safari: Share button (kotak panah ke atas) → "Add to Home Screen".

Most Indonesian users don't know PWA exists; flagging this turns a normal web
app into a "real app" experience for free.

---

## 8. Common Vision-Tool Failure Workaround

When showing favicon preview to user, `vision_analyze` and `browser_vision`
sometimes fail with:

```
invalid model 'claude-sonnet-4.5': use provider/model_id format
```

Fallback options:

1. **Just send the file via MEDIA:** — user can view it themselves on Telegram/HP.
2. **OCR for text-heavy images** with `tesseract`.
3. **Pixel-level inspection with PIL** (size, mode, center color) for icon validation without seeing.

Don't block on vision tool errors — pivot to one of these and keep moving.
