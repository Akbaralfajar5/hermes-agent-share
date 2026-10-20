"""
NFT Avatar Generator — illustrated cartoon character (no real human face).
Produces an 800x800 PNG suitable for Twitter PFP / NFT profile picture.
Optionally applies a mosaic grid effect.

Usage:
    python nft_avatar_generator.py [output.png] [--mosaic] [--mosaic-size 12]

Or import:
    from nft_avatar_generator import generate_nft_avatar, apply_mosaic
    generate_nft_avatar("/tmp/avatar.png")
    apply_mosaic("/tmp/avatar.png", "/tmp/avatar_mosaic.png", block_size=12)
"""

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance


def generate_nft_avatar(output_path: str, seed: int = 99, size: int = 800) -> Image.Image:
    """Generate an illustrated NFT avatar character and save to output_path."""
    random.seed(seed)
    SIZE = size

    img = Image.new("RGB", (SIZE, SIZE), (8, 5, 20))
    draw = ImageDraw.Draw(img)

    # --- Background gradient (dark purple → dark blue) ---
    for y in range(SIZE):
        t = y / SIZE
        draw.line([(0, y), (SIZE, y)], fill=(int(8 + t*12), int(5 + t*8), int(20 + t*35)))

    # --- Hexagon grid pattern ---
    hex_color = (25, 15, 50)
    for row in range(-1, 12):
        for col in range(-1, 10):
            cx = col * 90 + (45 if row % 2 else 0)
            cy = row * 78
            pts = [(cx + 38*math.cos(math.pi/3*i - math.pi/6),
                    cy + 38*math.sin(math.pi/3*i - math.pi/6)) for i in range(6)]
            draw.polygon(pts, outline=hex_color, fill=None)

    # --- Glow behind head ---
    for r in range(120, 0, -10):
        a = int(30 * (1 - r/120))
        draw.ellipse([SIZE//2-r, SIZE//2-r-60, SIZE//2+r, SIZE//2+r-60],
                     fill=(a, a//2, a*3))

    # --- Body / hoodie ---
    draw.rectangle([120, 480, 680, 800], fill=(35, 15, 65))
    draw.rectangle([280, 600, 520, 720], fill=(45, 20, 80))
    draw.rectangle([285, 605, 515, 715], fill=(30, 12, 55))
    draw.line([(340, 480), (310, 620)], fill=(60, 30, 100), width=6)
    draw.line([(460, 480), (490, 620)], fill=(60, 30, 100), width=6)

    # --- Neck ---
    draw.rectangle([340, 420, 460, 490], fill=(220, 160, 90))

    # --- Head ---
    head_pts = [
        (200,200),(220,150),(280,120),(400,110),(520,120),(580,150),(600,200),
        (610,280),(590,360),(540,410),(480,440),(400,450),(320,440),(260,410),(210,360),(190,280)
    ]
    draw.polygon(head_pts, fill=(225, 165, 95))

    # --- Hair ---
    hair_color = (20, 12, 8)
    draw.ellipse([185, 90, 615, 260], fill=hair_color)
    draw.rectangle([185, 160, 615, 230], fill=hair_color)
    spikes = [(280,90),(260,40),(310,80),(340,30),(380,75),(420,25),(460,75),(490,40),(520,85),(550,50),(580,90)]
    for i in range(0, len(spikes)-2, 2):
        draw.polygon([spikes[i], spikes[i+1], spikes[i+2]], fill=hair_color)
    for i in range(6):
        draw.line([(220+i*60, 100), (235+i*60, 200)], fill=(60, 35, 20), width=4)
    draw.rectangle([185, 200, 215, 340], fill=hair_color)
    draw.rectangle([585, 200, 615, 340], fill=hair_color)

    # --- Eyebrows ---
    draw.polygon([(215,255),(310,240),(315,255),(220,270)], fill=(15,8,5))
    draw.polygon([(485,240),(580,255),(580,270),(490,255)], fill=(15,8,5))

    # --- Eyes (cyan iris) ---
    for ex, ey in [(220,265),(480,265)]:
        draw.ellipse([ex, ey, ex+100, ey+55], fill=(255,255,255))
        draw.ellipse([ex+20, ey+5, ex+85, ey+50], fill=(0,150,200))
        draw.ellipse([ex+38, ey+13, ex+70, ey+43], fill=(5,5,15))
        draw.ellipse([ex+45, ey+17, ex+58, ey+30], fill=(255,255,255))
    for i in range(5):
        draw.line([(225+i*18, 265), (222+i*18, 252)], fill=(10,5,5), width=3)
        draw.line([(485+i*18, 265), (482+i*18, 252)], fill=(10,5,5), width=3)

    # --- Nose ---
    draw.polygon([(385,300),(370,360),(415,360),(400,300)], fill=(200,140,75))
    draw.ellipse([362,352,390,372], fill=(185,125,65))
    draw.ellipse([408,352,436,372], fill=(185,125,65))

    # --- Mouth ---
    draw.ellipse([330,375,470,415], fill=(170,70,70))
    draw.ellipse([335,375,465,400], fill=(210,110,90))
    draw.rectangle([360,385,440,400], fill=(245,240,235))

    # --- Ears + earrings ---
    for ex in [175, 585]:
        draw.ellipse([ex, 270, ex+40, 360], fill=(215,155,85))
        draw.ellipse([ex+7, 280, ex+33, 350], fill=(190,130,70))
        draw.ellipse([ex+3, 330, ex+25, 355], outline=(220,180,50), width=4)

    # --- Sunglasses (pushed up) ---
    gf = (200,160,40)
    draw.rectangle([215,230,325,260], fill=(10,5,20), outline=gf, width=3)
    draw.rectangle([475,230,585,260], fill=(10,5,20), outline=gf, width=3)
    draw.line([(325,245),(475,245)], fill=gf, width=3)
    draw.line([(215,245),(185,240)], fill=gf, width=3)
    draw.line([(585,245),(615,240)], fill=gf, width=3)
    draw.line([(225,235),(240,250)], fill=(255,220,100), width=2)
    draw.line([(485,235),(500,250)], fill=(255,220,100), width=2)

    # --- Gold chain ---
    for i in range(30):
        x = 200 + i*14
        y = 530 + int(math.sin(i*0.4)*15)
        draw.ellipse([x-6,y-6,x+6,y+6], fill=(200,160,40))
        draw.ellipse([x-5,y-5,x+5,y+5], outline=(255,215,0), width=2)
    draw.polygon([(390,560),(400,590),(410,560),(400,545)], fill=(255,215,0))

    # --- Neon border frame ---
    draw.rectangle([0,0,SIZE-1,SIZE-1], outline=(0,180,220), width=4)
    draw.rectangle([6,6,SIZE-7,SIZE-7], outline=(255,200,0), width=2)
    for cx, cy in [(0,0),(SIZE-60,0),(0,SIZE-60),(SIZE-60,SIZE-60)]:
        draw.rectangle([cx,cy,cx+55,cy+55], outline=(0,220,255), width=2)
        draw.rectangle([cx+5,cy+5,cx+50,cy+50], outline=(255,200,0), width=1)

    # --- Enhance ---
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageEnhance.Color(img).enhance(1.25)
    img = ImageEnhance.Sharpness(img).enhance(1.1)

    img.save(output_path)
    print(f"Saved: {output_path}")
    return img


def apply_mosaic(input_path: str, output_path: str, block_size: int = 12) -> Image.Image:
    """Apply mosaic/pixelate effect with grid lines to an image."""
    img = Image.open(input_path).convert("RGB")
    mosaic = img.copy()
    draw = ImageDraw.Draw(mosaic)
    w, h = img.size

    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            block = img.crop((x, y, min(x+block_size, w), min(y+block_size, h)))
            avg = block.resize((1, 1), Image.LANCZOS).getpixel((0, 0))
            x2, y2 = min(x+block_size-1, w-1), min(y+block_size-1, h-1)
            draw.rectangle([x, y, x2, y2], fill=avg)
            draw.rectangle([x, y, x2, y2], outline=(0, 0, 0), width=1)

    mosaic.save(output_path)
    print(f"Mosaic saved: {output_path}")
    return mosaic


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate NFT avatar illustration")
    parser.add_argument("output", nargs="?", default="/tmp/nft_avatar.png")
    parser.add_argument("--mosaic", action="store_true", help="Apply mosaic effect")
    parser.add_argument("--mosaic-size", type=int, default=12)
    parser.add_argument("--seed", type=int, default=99)
    parser.add_argument("--size", type=int, default=800)
    args = parser.parse_args()

    generate_nft_avatar(args.output, seed=args.seed, size=args.size)

    if args.mosaic:
        mosaic_path = args.output.replace(".png", "_mosaic.png")
        apply_mosaic(args.output, mosaic_path, block_size=args.mosaic_size)
