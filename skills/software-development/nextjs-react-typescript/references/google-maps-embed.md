# Google Maps Embed: Place URL → iframe Embed

## Problem
User has a Google Maps place URL (with place ID, coordinates) and wants it embedded as an iframe on their website. The place URL cannot be used directly as an iframe `src`.

## Converting Place URL to Embed URL

### Input (Google Maps Place URL)
```
```

### Extract from the URL
1. **Coordinates**: `@-6.8940143,106.8149959` → lat, lng
2. **Zoom level**: `11199m` → divide by ~200 for approximate zoom divisor
3. **Place ID**: `0x2e683135863873e5:0xf4c7ee13f4d622ad` (from `!1s` parameter)

### Build Embed URL
```
https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d15797.5!2d{LNG}!3d{LAT}!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s{PLACE_ID}!2s{PLACE_NAME}!5e0!3m2!1sid!2sid!4v1750000000000!5m2!1sid!2sid
```

### Template
```
https://www.google.com/maps/embed?pb=
  !1m18
  !1m12
  !1m3!1d{ZOOM_DIVISOR}    ← controls zoom (higher = more zoomed out)
  !2d{LNG}                 ← longitude
  !3d{LAT}                 ← latitude
  !2m3!1f0!2f0!3f0         ← rotation (always 0)
  !3m2!1i1024!2i768        ← viewport size
  !4f13.1                   ← pitch
  !3m3
  !1m2
  !1s{PLACE_ID}            ← place ID (hex:hex format)
  !2s{PLACE_NAME}          ← URL-encoded place name
  !5e0                     ← map type (0=roadmap)
  !3m2!1sid!2sid           ← language (id=Indonesian)
  !4v{TIMESTAMP}           ← version timestamp
  !5m2!1sid!2sid           ← language again
```

### Easier Method: Google Maps Embed Tool
1. Go to the place URL in browser
2. Click "Share" → "Embed a map"
3. Copy the `src` from the iframe code
4. Use that as the embed URL

This is more reliable than manual construction because Google handles the zoom, place ID encoding, and version numbers automatically.

## In Next.js (contacts.ts pattern)
```typescript
// lib/contacts.ts
export const defaultContacts: ContactSettings = {
  mapsUrl: "https://www.google.com/maps/place/...",      // clickable link (full place URL)
  mapsEmbed: "https://www.google.com/maps/embed?pb=...", // iframe src (embed URL)
};
```

Both `mapsUrl` and `mapsEmbed` should be updated together. The `mapsUrl` is what opens when the user clicks "Lihat di Google Maps", and `mapsEmbed` is what renders as the inline map.

## Pitfalls
- **Don't use the place URL as iframe src** — it won't render. Must use `/maps/embed?pb=...` format.
- **Zoom divisor** — `!1d15797.5` for 1119m zoom level. Higher divisor = more zoomed out. Adjust by feel.
- **Place ID encoding** — the colon in `0x2e683135863873e5:0xf4c7ee13f4d622ad` must be URL-encoded as `%3A` in the embed URL, but NOT in the mapsUrl.
- **mapsUrl update** — when user provides a full Google Maps place URL, update BOTH mapsUrl and mapsEmbed. The shortened goo.gl link may expire or redirect differently.
- **Vercel auto-deploy** — changes to contacts.ts trigger auto-deploy via GitHub push. No manual Vercel deploy needed.
