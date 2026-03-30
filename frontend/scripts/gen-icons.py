"""Generate PWA icons for EchoMie using Pillow."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

OUT = Path(__file__).resolve().parent.parent / "public" / "icons"
OUT.mkdir(parents=True, exist_ok=True)

SIZES = [192, 512]
BG_COLOR = (155, 126, 203)  # --color-primary #9b7ecb
PETAL_COLOR = (255, 200, 210)
CENTER_COLOR = (255, 235, 180)


def draw_sakura(draw, cx, cy, r):
    """Draw a simple 5-petal sakura flower."""
    for i in range(5):
        angle = math.radians(i * 72 - 90)
        px = cx + r * 0.55 * math.cos(angle)
        py = cy + r * 0.55 * math.sin(angle)
        pr = r * 0.38
        draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=PETAL_COLOR)
    cr = r * 0.22
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=CENTER_COLOR)


def make_icon(size, maskable=False):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if maskable:
        draw.rectangle([0, 0, size, size], fill=BG_COLOR)
        safe = size * 0.4
    else:
        margin = size * 0.06
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=size * 0.22,
            fill=BG_COLOR,
        )
        safe = size * 0.35

    cx, cy = size / 2, size / 2
    draw_sakura(draw, cx, cy - safe * 0.08, safe)

    try:
        font_size = int(size * 0.11)
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        font_size = int(size * 0.11)
        font = ImageFont.load_default()

    text = "EchoMie"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    tx = cx - tw / 2
    ty = cy + safe * 0.52
    draw.text((tx, ty), text, fill="white", font=font)

    return img


for s in SIZES:
    make_icon(s, maskable=False).save(OUT / f"icon-{s}.png")
    make_icon(s, maskable=True).save(OUT / f"icon-maskable-{s}.png")
    print(f"Generated {s}x{s} icons")

# Also generate apple-touch-icon (180x180)
make_icon(180, maskable=True).save(OUT / "apple-touch-icon.png")
print("Generated apple-touch-icon 180x180")
print("Done!")
