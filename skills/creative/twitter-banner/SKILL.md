---
name: twitter-banner
description: "Generate Twitter/X profile banners (1500x500) with PIL — color-matched to profile pic, crypto/Web3 aesthetic."
version: 1.0.0
author: hermes
license: MIT
metadata:
  hermes:
    tags: [creative, twitter, banner, social-media, crypto, nft, PIL]
    category: creative
---

# Twitter/X Banner Generator

Create professional Twitter/X header banners (1500x500px) using PIL — no external API needed.
Supports crypto/Web3 aesthetic with neon glows, circuit lines, hex patterns, and mosaic accents.

## When to Use

- User wants a Twitter/X profile banner/header image
- User wants banner to match their profile picture colors
- User wants crypto/Web3 themed social media graphics
- fal.ai or other image gen APIs are unavailable/out of credits

## Workflow

### Step 1 — Extract dominant colors from profile pic

If user provides a reference screenshot or profile pic, extract palette first:

```python
from PIL import Image
import numpy as np
from collections import Counter

img = Image.open('/path/to/reference.jpg')
arr = np.array(img)
h, w = arr.shape[:2]

# Focus on header/profile area (non-white pixels)
region = arr[0:int(h*0.45), :, :]
mask = (region[:,:,0] < 220)
nw = region[mask]
rounded = (nw // 20 * 20)
tuples = [tuple(r) for r in rounded]
top = Counter(tuples).most_common(8)
for col, cnt in top:
    print(f'RGB{col} - {cnt}px')
```

Map the dominant colors to your background gradient and accent colors.

### Step 2 — Generate banner

Twitter banner spec: **1500x500px**

Key elements for crypto/Web3 aesthetic:
- Dark gradient background (match profile pic palette)
- Subtle grid lines (40px spacing)
- Glow orbs (blend overlays at low alpha)
- Circuit board lines with dot nodes
- Hexagon outlines
- Main username text with neon glow layers
- Mosaic/pixel accent in one corner
- Neon border frame

### Step 3 — Text rendering

Always try system fonts first, fall back to default:
```python
try:
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
    font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
except:
    font_large = ImageFont.load_default()
    font_sub = font_large
```

For neon glow text effect — draw multiple offset copies in darker color first, then main text on top:
```python
for off in range(6, 0, -1):
    gc = (int(180*(1-off/6)), 0, int(255*(1-off/6)))
    draw.text((x+off, y+off), text, font=font_large, fill=gc)
    draw.text((x-off, y-off), text, font=font_large, fill=gc)
draw.text((x, y), text, font=font_large, fill=(220, 180, 255))
```

### Step 4 — Mosaic corner accent

Apply mosaic to one corner for pixel art tie-in:
```python
mosaic_size = 18
corner = img.crop((1200, 0, 1500, 200))
draw_c = ImageDraw.Draw(corner)
cw, ch = corner.size
for y in range(0, ch, mosaic_size):
    for x in range(0, cw, mosaic_size):
        block = corner.crop((x, y, min(x+mosaic_size,cw), min(y+mosaic_size,ch)))
        avg = block.resize((1,1), Image.LANCZOS).getpixel((0,0))
        draw_c.rectangle([x, y, min(x+mosaic_size-1,cw-1), min(y+mosaic_size-1,ch-1)], fill=avg)
        draw_c.rectangle([x, y, min(x+mosaic_size-1,cw-1), min(y+mosaic_size-1,ch-1)],
                         outline=(40, 0, 80), width=1)
img.paste(corner, (1200, 0))
```

## Color Palettes

### Crypto Purple (the user profile — dark purple/violet)
- Background: `(5, 0, 15)` → `(13, 3, 25)`
- Grid: `(30, 10, 50)`
- Accent/circuit: `(100, 0, 200)`
- Glow: `(80, 0, 160)`
- Text: `(220, 180, 255)`
- Border: `(80, 0, 160)`

### Crypto Blue/Cyan
- Background: `(5, 10, 25)` → `(8, 15, 35)`
- Accent: `(0, 180, 220)`
- Text: `(180, 230, 255)`

### Crypto Gold/Dark
- Background: `(10, 8, 5)` → `(20, 15, 8)`
- Accent: `(220, 180, 50)`
- Text: `(255, 215, 0)`

## Pitfalls

- Twitter crops banner on mobile — keep important content in center 60% horizontally and avoid top/bottom 10%
- PIL default font is tiny — always try DejaVu or system fonts first
- Glow orb blending: use `Image.blend()` at low alpha (0.05-0.15 per layer) to avoid washing out
- Output must be exactly 1500x500 — Twitter rejects other sizes
- Save as PNG for best quality; JPEG introduces artifacts on dark gradients

## Verification

```bash
python3 -c "from PIL import Image; img=Image.open('/tmp/banner.png'); print(img.size)"
# Should print: (1500, 500)
```

## Dependencies

- Python 3.9+
- Pillow (`pip install Pillow`)
- DejaVu fonts: `/usr/share/fonts/truetype/dejavu/` (usually pre-installed on Ubuntu)
