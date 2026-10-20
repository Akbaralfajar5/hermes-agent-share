#!/usr/bin/env python3
"""
Generate a custom favicon set without external image API.

Produces:
- /tmp/favicon_new.ico         — multi-size ICO (16, 32, 48, 64, 128, 256)
- /tmp/apple-touch-icon.png    — 180x180 for iOS home screen
- /tmp/icon-192.png            — 192x192 for PWA manifest
- /tmp/favicon_preview_new.png — 512x512 preview to show user before deploy

Default design: Erlenmeyer flask with emerald liquid on emerald-teal gradient.
Customize colors and shape via the constants at the top.

Run:  python3 gen_favicon_flask.py
"""
from PIL import Image, ImageDraw

# ===== Brand colors (override per project) =====
BG_TOP = (16, 185, 129)       # emerald-500
BG_BOT = (13, 148, 136)       # teal-600
LIQUID_COLOR = (167, 243, 208, 230)
OUTLINE_COLOR = (255, 255, 255, 255)
FILL_COLOR = (255, 255, 255, 60)
BUBBLE_COLOR = (255, 255, 255, 200)


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(len(c1)))


def make_icon(size: int) -> Image.Image:
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ----- Rounded gradient background -----
    radius = int(size * 0.22)
    for y in range(size):
        t = y / size
        color = lerp_color(BG_TOP, BG_BOT, t)
        draw.line([(0, y), (size, y)], fill=color)

    # Apply rounded mask
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [(0, 0), (size, size)], radius=radius, fill=255
    )
    bg_only = img.copy()
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    img.paste(bg_only, (0, 0), mask)

    # ----- Foreground shape: Erlenmeyer flask -----
    # To customize for other apps: replace this section with your shape's
    # polygon points. Keep the foreground centered around (cx, size*0.5)
    # and within ~70% of canvas for visibility at 16x16.
    draw = ImageDraw.Draw(img)
    cx = size / 2

    neck_w = size * 0.18
    neck_h = size * 0.18
    neck_top_y = size * 0.20
    neck_bot_y = neck_top_y + neck_h

    body_top_w = neck_w
    body_bot_w = size * 0.55
    body_top_y = neck_bot_y
    body_bot_y = size * 0.78

    liquid_top_y = size * 0.55

    flask_points = [
        (cx - neck_w / 2, neck_top_y),
        (cx + neck_w / 2, neck_top_y),
        (cx + neck_w / 2, neck_bot_y),
        (cx + body_bot_w / 2, body_bot_y),
        (cx - body_bot_w / 2, body_bot_y),
        (cx - neck_w / 2, neck_bot_y),
    ]
    draw.polygon(flask_points, fill=FILL_COLOR)

    # Liquid (lower portion)
    t_liquid = (liquid_top_y - neck_bot_y) / (body_bot_y - neck_bot_y)
    liquid_top_w = body_top_w + (body_bot_w - body_top_w) * t_liquid
    liquid_points = [
        (cx - liquid_top_w / 2, liquid_top_y),
        (cx + liquid_top_w / 2, liquid_top_y),
        (cx + body_bot_w / 2, body_bot_y),
        (cx - body_bot_w / 2, body_bot_y),
    ]
    draw.polygon(liquid_points, fill=LIQUID_COLOR)

    # Outline thickness scales with size
    outline_w = max(1, int(size * 0.025))
    for i in range(len(flask_points)):
        p1 = flask_points[i]
        p2 = flask_points[(i + 1) % len(flask_points)]
        draw.line([p1, p2], fill=OUTLINE_COLOR, width=outline_w)

    # Bubbles (only at >=32 to avoid noise on small sizes)
    if size >= 32:
        bubbles = [
            (cx - body_bot_w * 0.18, body_bot_y - size * 0.08, size * 0.025),
            (cx + body_bot_w * 0.10, body_bot_y - size * 0.14, size * 0.018),
            (cx - body_bot_w * 0.05, body_bot_y - size * 0.05, size * 0.015),
        ]
        for bx, by, br in bubbles:
            draw.ellipse([bx - br, by - br, bx + br, by + br], fill=BUBBLE_COLOR)

    # Mouth opening line at top of neck
    mouth_w = neck_w * 1.15
    draw.line(
        [(cx - mouth_w / 2, neck_top_y), (cx + mouth_w / 2, neck_top_y)],
        fill=OUTLINE_COLOR, width=outline_w,
    )

    return img


# ===== Render & save =====
sizes = [16, 32, 48, 64, 128, 256]
images = []
for s in sizes:
    img = make_icon(s)
    img.save(f'/tmp/favicon_{s}.png')
    images.append(img)

# Multi-size ICO — IMPORTANT: use `sizes=` parameter, NOT `append_images`
# The append_images approach silently produces a single-size ICO.
images[-1].save(  # save from biggest source
    '/tmp/favicon_new.ico',
    format='ICO',
    sizes=[(s, s) for s in sizes],
)

# Apple touch icon (iOS home screen, 180x180 standard)
make_icon(180).save('/tmp/apple-touch-icon.png')

# PWA manifest icon (192x192)
make_icon(192).save('/tmp/icon-192.png')

# Preview for visual confirmation
make_icon(512).save('/tmp/favicon_preview_new.png')

# Verify multi-size embedding worked
ico = Image.open('/tmp/favicon_new.ico')
embedded = sorted(ico.ico.sizes())
print(f"Generated /tmp/favicon_new.ico")
print(f"Sizes embedded: {embedded}")
import os
print(f"File size: {os.path.getsize('/tmp/favicon_new.ico'):,} bytes")
print(f"Preview: /tmp/favicon_preview_new.png (send to user via MEDIA: for confirmation)")
