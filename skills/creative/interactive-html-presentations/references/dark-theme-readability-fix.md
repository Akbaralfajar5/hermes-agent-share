# Dark Theme Readability Fix Patterns

When users report dark-theme presentations are hard to read (text too small, colors too dim), apply these fixes systematically.

## Common Problems

1. **rgba opacity too low** — text with `rgba(255,255,255,0.3-0.5)` is nearly invisible on dark backgrounds
2. **Font sizes too small on desktop** — `clamp()` values set too low, body text under 1rem
3. **Card borders invisible** — `rgba(255,255,255,0.08)` borders disappear into dark backgrounds

## Fix Map (Before → After)

### Text Opacity (minimum thresholds for readability on dark bg)
| Element | Bad | Good |
|---------|-----|------|
| Body text | 0.55 | 0.85-0.95 |
| Secondary/label text | 0.4-0.5 | 0.7-0.8 |
| Card subtitle | 0.35 | 0.7 |
| Dimmed helper text | 0.3-0.4 | 0.65-0.75 |

**Rule:** Never go below `0.65` for any text the user needs to read on dark backgrounds. `0.35-0.5` is only acceptable for decorative elements (card numbers, page counters).

### Font Size Minimums (desktop)
| Element | Bad | Good |
|---------|-----|------|
| Card title | `clamp(0.7rem, 1.3vw, 0.85rem)` | `clamp(0.85rem, 1.5vw, 1rem)` |
| Card subtitle | `0.6rem` | `0.75rem` |
| Body text | `0.85-0.95rem` | `1.05rem` |
| List items | `0.95rem` | `1.05rem` |
| Tech badges | `0.8rem` | `0.9rem` |
| Feature items | `0.85rem` | `0.95rem` |
| Labels (university, etc.) | `0.75rem` | `0.9rem` |
| Nav counter | `0.75rem` | `0.85rem` |

**Rule:** Minimum body text = `1rem`. Minimum labels = `0.75rem`. Below these, dosen will complain.

### Card Background & Border
```css
/* Too subtle */
background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);

/* Better — more visible cards */
background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
```

## Batch Fix Script Pattern

Use `execute_code` with a list of string replacements. Group into two categories:

1. **CSS class fixes** — change in `<style>` block
2. **Inline style fixes** — change in HTML body (more numerous, pattern-based)

```python
# Pattern: fix all inline rgba(255,255,255,0.XX) below threshold
import re

def boost_opacity(match):
    val = float(match.group(1))
    if val < 0.6:
        new_val = max(0.7, val + 0.3)  # boost by 0.3, minimum 0.7
        return f'rgba(255,255,255,{new_val:.1f})'
    return match.group(0)

content = re.sub(r'rgba\(255,255,255,(\d+\.\d+)\)', boost_opacity, content)
```

## Verification

After applying fixes, use `browser_vision()` to verify:
- Text visible from normal viewing distance
- Cards clearly distinguishable from background
- Labels and secondary text readable without squinting
- No "dark on dark" collision anywhere
