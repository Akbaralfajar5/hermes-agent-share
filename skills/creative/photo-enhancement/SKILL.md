---
name: photo-enhancement
description: "Photo editing and enhancement with Python Pillow + NumPy — brightness, contrast, color correction, tone mapping, and natural-looking results."
tags: [photo, image, pillow, PIL, enhancement, color-correction, tone-mapping]
---

# Photo Enhancement

Use when the user wants to enhance, brighten, color-correct, or retouch photos. Trigger on: "cerahkan foto", "perbagus foto", "edit pencahayaan", "foto gelap", "foto kurang cerah", "natural looking", photo enhancement.

## Stack

- **Pillow (PIL)** — brightness, contrast, color, sharpness via `ImageEnhance`
- **NumPy** — tone curves, channel manipulation, vignette
- **No OpenCV needed** for basic enhancement

```bash
pip3 install Pillow
# numpy biasanya sudah ada
```

## Critical Pitfall: Over-Processing = Unnatural

**User feedback (May 2026):** "Jelek bro foto tidak natural"

The first attempt used aggressive settings:
- Brightness +20%, Contrast +15%, Saturation +20%, Gamma 0.90, Warm +4%R/-4%B

Result: oversaturated, unnatural skin tones, blown highlights.

**Rule: Less is more. Always use subtle adjustments.**

| Parameter | Aggressive (AVOID) | Natural (USE) |
|-----------|-------------------|---------------|
| Brightness | +20% | +10-15% max |
| Contrast | +15% | +8% |
| Saturation | +20-25% | +10-12% |
| Warmth R channel | +4-5% | +2.5% |
| Warmth B channel | -4-5% | -2.5% |

## Workflow: Analyze Before Editing

**Always run `vision_analyze` on the original first** to understand:
- Is it underexposed or overexposed overall?
- Which areas are too dark (shadows)?
- Which areas are blown out (highlights)?
- Is the white balance warm, cool, or neutral?

Then apply targeted fixes, not blanket boosts.

## Recommended Pipeline (Natural Result)

```python
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

src = "/path/to/input.jpg"
out = "/path/to/output.jpg"

img = Image.open(src)
arr = np.array(img).astype(np.float32) / 255.0

# 1. Tone mapping: lift shadows, recover highlights
def tone_map(c):
    shadow_lift = 0.08 * (1.0 - c) ** 2   # angkat gelap
    highlight_pull = -0.06 * c ** 2         # turunkan terang
    return np.clip(c + shadow_lift + highlight_pull, 0, 1)

arr[:,:,0] = tone_map(arr[:,:,0])
arr[:,:,1] = tone_map(arr[:,:,1])
arr[:,:,2] = tone_map(arr[:,:,2])

# 2. Warmth subtle (koreksi cool cast)
arr[:,:,0] = np.clip(arr[:,:,0] * 1.025, 0, 1)  # R +2.5%
arr[:,:,1] = np.clip(arr[:,:,1] * 1.005, 0, 1)  # G +0.5%
arr[:,:,2] = np.clip(arr[:,:,2] * 0.975, 0, 1)  # B -2.5%

img = Image.fromarray((arr * 255).astype(np.uint8))

# 3. Vibrance gentle (bukan saturation penuh)
img = ImageEnhance.Color(img).enhance(1.12)

# 4. Contrast ringan
img = ImageEnhance.Contrast(img).enhance(1.08)

# 5. Sharpness subtle
img = ImageEnhance.Sharpness(img).enhance(1.10)

# 6. Vignette ringan (fokus ke subjek)
arr2 = np.array(img).astype(np.float32)
h, w = arr2.shape[:2]
Y, X = np.ogrid[:h, :w]
cx, cy = w / 2, h / 2
dist = np.sqrt(((X - cx) / (w * 0.6)) ** 2 + ((Y - cy) / (h * 0.6)) ** 2)
vignette = np.clip(1.0 - 0.18 * (dist ** 2), 0.82, 1.0)[:, :, np.newaxis]
arr2 = np.clip(arr2 * vignette, 0, 255)
img = Image.fromarray(arr2.astype(np.uint8))

# 7. Unsharp mask halus
img = img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=80, threshold=4))

img.save(out, quality=96, optimize=True)
```

## Tone Mapping Explained

The `tone_map` function is the key to natural results:
- **Shadow lift** `0.08 * (1-c)²` — dark pixels get lifted more, bright pixels barely change
- **Highlight pull** `-0.06 * c²` — bright pixels pulled down, dark pixels barely change
- Net effect: compressed dynamic range, like Lightroom's Shadows+/Highlights- sliders

## Vignette

Subtle vignette (max 18% darkening at edges) draws attention to subjects without being obvious. Adjust `0.18` for strength and `0.6` for radius.

## Common Scenarios

| Situation | Key Adjustment |
|-----------|---------------|
| Foto outdoor siang, wajah gelap | Shadow lift + tone_map |
| Foto cool/kebiruan | Warmth: R+2.5%, B-2.5% |
| Warna pucat/flat | Color enhance 1.12 |
| Foto blur/soft | UnsharpMask radius=1.0, percent=80-100 |
| Highlight blown out | Highlight pull dalam tone_map |

## Pitfall: execute_code vs terminal

`execute_code` tool may fail with `ModuleNotFoundError` even after `pip install` because it runs in a sandbox. **Always use `terminal()` with `python3 << 'EOF'` heredoc** for photo processing scripts.

Also: heredoc scripts that use `~` in paths may fail with "Could not determine home directory" — use full absolute paths like `/home/ubuntu/...` instead.

## References

- `references/photo-enhancement-pitfalls.md` — session notes on over-processing failure
