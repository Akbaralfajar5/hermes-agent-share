# Pillow-Based Info Cards (Dark Theme)

When the user needs small UI-style info cards as PNG images (e.g., admin credentials, program descriptions, feature highlights), generate them with Pillow. Common use case: presentation companion images, documentation cards, or social media cards.

## When to Use

- User shows a dark-themed card image and wants it recreated with modifications
- Need to mask/censor sensitive info (passwords, tokens) in an existing card image
- Creating companion visual cards for a presentation or website

## Base Pattern

```python
from PIL import Image, ImageDraw, ImageFont

# Card dimensions
width, height = 700, 130
outer_bg = (26, 29, 35)      # #1a1d23
card_bg = (43, 48, 58)       # #2b303a
border_color = (58, 63, 75)  # #3a3f4b
title_color = (232, 234, 237) # white-ish
body_color = (180, 188, 200)  # muted gray
bold_color = (208, 213, 220)  # slightly brighter for bold text

img = Image.new('RGB', (width, height), color=outer_bg)
draw = ImageDraw.Draw(img)

# Card with rounded corners + subtle border
card_margin = 12
draw.rounded_rectangle(
    [card_margin, card_margin, width - card_margin, height - card_margin],
    radius=12, fill=card_bg, outline=border_color, width=1
)

# Fonts (DejaVu is available on most Linux systems)
font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)

# Title
draw.text((title_x, title_y), "Title Text", fill=title_color, font=font_title)

# Mixed bold/regular body text on same line
x = start_x
draw.text((x, y), "Normal text ", fill=body_color, font=font_body)
x += draw.textlength("Normal text ", font=font_body)
draw.text((x, y), "Bold text", fill=bold_color, font=font_bold)

img.save("output.png")
```

## Credential Masking

Replace sensitive values with `********`:
```python
# Instead of: "User: admin · Pass: myapp"
draw.text((x, y), "User: admin · Pass: ********", fill=body_color, font=font_body)
```

## Matching an Existing Card's Style

1. Use `vision_analyze` on the original image to get exact colors, fonts, spacing
2. Map the CSS-like values to Pillow equivalents:
   - `#1e2a3a` → `(30, 42, 58)` RGB tuple
   - `border-radius: 12px` → `radius=12` in `rounded_rectangle`
   - `font-weight: 700` → use Bold font variant
   - `padding: 20px 24px` → offset text positions accordingly
3. Use `draw.textlength()` to calculate x-positions for inline mixed formatting

## Pitfalls

- Emoji rendering: Pillow's default fonts don't render emoji. Draw simple shapes (rectangles, circles) as icon substitutes, or skip emoji.
- Font availability: DejaVu fonts are at `/usr/share/fonts/truetype/dejavu/` on Ubuntu. Fall back to `ImageFont.load_default()` if missing.
- Text wrapping: Pillow has no auto-wrap. Calculate line breaks manually using `draw.textlength()`.
- Always use `vision_analyze` on the result to verify it looks correct before sending.
- **Content accuracy**: When recreating/modifying info cards, check memory/context for specific details (department names, program names, correct terminology). User corrections like "ingat pakai jurusan Pengawasan Mutu Hasil Pertanian" mean the card text must reflect their exact institutional context — don't use generic descriptions.
- **Sensitive info masking**: When user says "password nya samarkan", replace the value with `••••••••` or `********`. Use `vision_analyze` on the original to match exact styling (teal accent colors, label/value color separation, etc.).
- **Masking in HTML source**: If the card is rendered inside an HTML presentation (not a standalone image), search the HTML for the plaintext password and replace it directly: `search_files(pattern="myapp", path="file.html")` → `patch(old_string='myapp', new_string='••••••••')`. Always check both image cards AND HTML source.

