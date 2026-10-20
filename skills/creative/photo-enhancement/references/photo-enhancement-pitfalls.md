# Photo Enhancement Pitfalls — Session Notes (May 2026)

## Failure: Over-Processing

**User feedback:** "Jelek bro foto tidak natural"

### What went wrong (first attempt)

Settings used:
- `ImageEnhance.Brightness(img).enhance(1.20)` — +20%
- `ImageEnhance.Contrast(img).enhance(1.15)` — +15%
- `ImageEnhance.Color(img).enhance(1.20)` — +20% saturation
- Gamma correction 0.90
- Warm: R+4%, G+1%, B-4%
- `UnsharpMask(radius=1.5, percent=120, threshold=3)`

Result: oversaturated colors, unnatural skin tones, plastic-looking faces.

### Root cause

Stacking multiple aggressive boosts compounds the effect. Each individual setting seemed moderate, but combined they pushed the image far from natural.

### Fix applied (second attempt)

Switched to proper tone mapping (shadow lift + highlight recovery) instead of blanket brightness boost:

```python
def tone_map(c):
    shadow_lift = 0.08 * (1.0 - c) ** 2
    highlight_pull = -0.06 * c ** 2
    return np.clip(c + shadow_lift + highlight_pull, 0, 1)
```

Reduced all other parameters significantly:
- Saturation: 1.20 → 1.12
- Contrast: 1.15 → 1.08
- Warmth: R+4% → R+2.5%
- UnsharpMask: percent=120 → percent=80

## Lesson

**Analyze first, edit second.** Run `vision_analyze` on the original to understand:
1. Is it actually underexposed, or just has dark shadows?
2. What's the white balance (warm/cool/neutral)?
3. Which specific areas need fixing?

Then apply targeted, minimal adjustments. The goal is "looks like a better version of the original", not "looks like a different photo."

## execute_code vs terminal

`execute_code` sandbox fails with ModuleNotFoundError for Pillow even after pip install.
Always use `terminal()` with heredoc:
```
terminal(command="python3 << 'EOF'\n...\nEOF")
```

Also: use full absolute paths (`/home/ubuntu/...`), not `~` — heredoc scripts can fail with "Could not determine home directory".
