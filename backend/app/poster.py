"""
EchoMie — Generate share poster image from emotion card data.
Combines styled image + emotion badge + healing text into a single shareable image.
"""

import os
import textwrap
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .logging_config import get_logger

logger = get_logger("app.poster")

POSTER_W = 1080
CARD_PADDING = 60
BG_COLOR = (254, 247, 240)
PRIMARY_COLOR = (155, 126, 203)
TEXT_COLOR = (45, 38, 64)
MUTED_COLOR = (168, 155, 181)

EMOTION_COLORS = {
    "happy": (255, 217, 61), "calm": (168, 216, 234), "sad": (176, 196, 222),
    "lonely": (221, 160, 221), "tired": (211, 211, 211), "anxious": (255, 179, 71),
    "hopeful": (152, 251, 152), "nostalgic": (244, 164, 96),
    "peaceful": (144, 238, 144), "excited": (255, 105, 180),
}


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    if bold:
        bold_candidates = [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
        ]
        candidates = bold_candidates + candidates

    for fp in candidates:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_poster(
    title: str,
    healing_text: str,
    emotion: str,
    emotion_emoji: str,
    image_path: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    font_title = _get_font(48, bold=True)
    font_body = _get_font(32)
    font_small = _get_font(24)
    font_emoji = _get_font(40)
    font_brand = _get_font(28, bold=True)

    sections = []
    top_margin = CARD_PADDING

    if image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path).convert("RGB")
            ratio = POSTER_W / img.width
            img = img.resize((POSTER_W, int(img.height * ratio)), Image.LANCZOS)
            if img.height > 720:
                img = img.crop((0, 0, POSTER_W, 720))
            sections.append(("image", img))
            top_margin = 30
        except Exception as e:
            logger.warning("Failed to load poster image: %s", e)

    emotion_color = EMOTION_COLORS.get(emotion.lower(), PRIMARY_COLOR)

    total_h = top_margin + 20
    if any(s[0] == "image" for s in sections):
        total_h += sections[0][1].height + 30

    total_h += 60 + 30

    wrapped_title = textwrap.fill(title or "此刻", width=20)
    title_lines = wrapped_title.split("\n")
    total_h += len(title_lines) * 60 + 30

    wrapped_text = textwrap.fill(healing_text or "", width=28)
    text_lines = wrapped_text.split("\n")
    total_h += len(text_lines) * 44 + 40 + 60 + 30

    total_h += 80
    total_h = max(total_h, 800)

    poster = Image.new("RGB", (POSTER_W, total_h), BG_COLOR)
    draw = ImageDraw.Draw(poster)
    y = top_margin

    for stype, sdata in sections:
        if stype == "image":
            poster.paste(sdata, (0, y))
            y += sdata.height + 30

    badge_text = f" {emotion_emoji} {emotion} "
    badge_bbox = draw.textbbox((0, 0), badge_text, font=font_emoji)
    badge_w = badge_bbox[2] - badge_bbox[0] + 40
    badge_h = badge_bbox[3] - badge_bbox[1] + 20
    badge_x = CARD_PADDING
    r = badge_h // 2
    draw.rounded_rectangle(
        [badge_x, y, badge_x + badge_w, y + badge_h],
        radius=r,
        fill=(*emotion_color, 50) if len(emotion_color) == 3 else emotion_color,
        outline=emotion_color,
        width=2,
    )
    draw.text((badge_x + 20, y + 6), badge_text, fill=TEXT_COLOR, font=font_emoji)
    y += badge_h + 30

    for line in title_lines:
        draw.text((CARD_PADDING, y), line, fill=TEXT_COLOR, font=font_title)
        y += 60
    y += 20

    text_bg_x = CARD_PADDING - 10
    text_bg_w = POSTER_W - CARD_PADDING * 2 + 20
    text_bg_h = len(text_lines) * 44 + 40
    draw.rounded_rectangle(
        [text_bg_x, y, text_bg_x + text_bg_w, y + text_bg_h],
        radius=20,
        fill=(243, 237, 252),
    )
    ty = y + 20
    for line in text_lines:
        draw.text((CARD_PADDING + 10, ty), line, fill=MUTED_COLOR, font=font_body)
        ty += 44
    y += text_bg_h + 30

    draw.line([(CARD_PADDING, y), (POSTER_W - CARD_PADDING, y)], fill=(236, 228, 218), width=1)
    y += 20

    draw.text((CARD_PADDING, y), "🌸 EchoMie · 用 AI 治愈每一个瞬间", fill=MUTED_COLOR, font=font_brand)
    y += 50

    if output_path is None:
        from uuid import uuid4
        out_dir = Path(os.getenv("STORAGE_BASE_PATH", "/data/storage")) / "posters"
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(out_dir / f"{uuid4().hex}.jpg")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    poster.save(output_path, "JPEG", quality=92)
    logger.info("Poster saved: %s", output_path)
    return output_path
