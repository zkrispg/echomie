"""
EchoMie — real cartoon / stylization effects using OpenCV + Pillow.

Each public function takes an input image path and output image path,
applies the effect, and writes the result.  For videos the caller
should use `apply_video_effect` which processes frame-by-frame.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Callable, Dict

from .logging_config import get_logger

logger = get_logger("app.effects")


# ──────────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────────

def _read_img(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return img


def _write_img(path: str, img: np.ndarray):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(path, img)


def _color_quantize(img: np.ndarray, k: int = 8) -> np.ndarray:
    """Reduce to k colours via k-means for a flat cartoon look."""
    data = img.reshape((-1, 3)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    centers = np.uint8(centers)
    return centers[labels.flatten()].reshape(img.shape)


def _warm_shift(img: np.ndarray, strength: float = 0.15) -> np.ndarray:
    """Add a warm (orange-pink) tint."""
    overlay = np.full_like(img, (180, 200, 255))  # BGR: light warm
    return cv2.addWeighted(img, 1 - strength, overlay, strength, 0)


def _cool_shift(img: np.ndarray, strength: float = 0.10) -> np.ndarray:
    overlay = np.full_like(img, (255, 220, 200))  # BGR: light cool
    return cv2.addWeighted(img, 1 - strength, overlay, strength, 0)


def _green_shift(img: np.ndarray, strength: float = 0.10) -> np.ndarray:
    overlay = np.full_like(img, (200, 240, 200))  # BGR: gentle green
    return cv2.addWeighted(img, 1 - strength, overlay, strength, 0)


def _add_soft_glow(img: np.ndarray, radius: int = 25, alpha: float = 0.3) -> np.ndarray:
    blurred = cv2.GaussianBlur(img, (radius | 1, radius | 1), 0)
    return cv2.addWeighted(img, 1 - alpha, blurred, alpha, 0)


def _get_edges(img: np.ndarray, blur_k: int = 5, block_size: int = 9, c: int = 2) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, blur_k)
    edges = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, block_size, c
    )
    return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)


def _saturate(img: np.ndarray, factor: float = 1.3) -> np.ndarray:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def _brighten(img: np.ndarray, beta: int = 15) -> np.ndarray:
    return cv2.convertScaleAbs(img, alpha=1.0, beta=beta)


# ──────────────────────────────────────────────
# Style implementations
# ──────────────────────────────────────────────

def effect_warm_cartoon(img: np.ndarray) -> np.ndarray:
    """Classic warm cartoon: smooth + edges + warm palette."""
    # Heavy bilateral smoothing (3 passes)
    smooth = img.copy()
    for _ in range(3):
        smooth = cv2.bilateralFilter(smooth, d=9, sigmaColor=75, sigmaSpace=75)

    # Colour quantisation
    smooth = _color_quantize(smooth, k=12)

    # Edge overlay
    edges = _get_edges(img)
    cartoon = cv2.bitwise_and(smooth, edges)

    # Warm tint + brightness
    cartoon = _warm_shift(cartoon, 0.12)
    cartoon = _brighten(cartoon, 10)
    return cartoon


def effect_soft_anime(img: np.ndarray) -> np.ndarray:
    """Soft anime: heavy smoothing, pastel glow, subtle edges."""
    smooth = img.copy()
    for _ in range(4):
        smooth = cv2.bilateralFilter(smooth, d=9, sigmaColor=90, sigmaSpace=90)

    # Lighten and desaturate slightly
    smooth = _brighten(smooth, 20)
    smooth = _saturate(smooth, 0.85)

    # Soft glow
    smooth = _add_soft_glow(smooth, radius=35, alpha=0.35)

    # Subtle edge overlay
    edges = _get_edges(img, blur_k=7, block_size=11, c=3)
    result = cv2.bitwise_and(smooth, edges)

    # Cool pastel tint
    result = _cool_shift(result, 0.08)
    return result


def effect_watercolor(img: np.ndarray) -> np.ndarray:
    """OpenCV stylization for a watercolour feel."""
    styled = cv2.stylization(img, sigma_s=60, sigma_r=0.45)
    styled = _saturate(styled, 1.2)
    styled = _add_soft_glow(styled, radius=21, alpha=0.2)
    return styled


def effect_dreamy(img: np.ndarray) -> np.ndarray:
    """Dreamy/ethereal: bloom + saturation + vignette."""
    bloom = cv2.GaussianBlur(img, (0, 0), sigmaX=15)
    dreamy = cv2.addWeighted(img, 0.6, bloom, 0.4, 10)
    dreamy = _saturate(dreamy, 1.3)
    dreamy = _warm_shift(dreamy, 0.10)

    # Soft vignette
    h, w = dreamy.shape[:2]
    x = np.linspace(-1, 1, w)
    y = np.linspace(-1, 1, h)
    X, Y = np.meshgrid(x, y)
    vignette = 1 - 0.35 * (X ** 2 + Y ** 2)
    vignette = np.clip(vignette, 0.3, 1.0).astype(np.float32)
    dreamy = (dreamy.astype(np.float32) * vignette[:, :, np.newaxis]).astype(np.uint8)
    return dreamy


def effect_ghibli(img: np.ndarray) -> np.ndarray:
    """Ghibli-inspired: edge-preserving filter + green nature tint."""
    filtered = cv2.edgePreservingFilter(img, flags=1, sigma_s=60, sigma_r=0.4)
    filtered = _saturate(filtered, 1.25)
    filtered = _green_shift(filtered, 0.12)

    # Subtle warm contrast
    filtered = cv2.convertScaleAbs(filtered, alpha=1.05, beta=5)
    return filtered


def effect_chibi(img: np.ndarray) -> np.ndarray:
    """Chibi/cute: extreme smoothing + strong edges + bright colours."""
    smooth = img.copy()
    for _ in range(5):
        smooth = cv2.bilateralFilter(smooth, d=9, sigmaColor=100, sigmaSpace=100)

    smooth = _color_quantize(smooth, k=10)

    # Strong edges
    edges = _get_edges(img, blur_k=5, block_size=9, c=2)
    cartoon = cv2.bitwise_and(smooth, edges)

    cartoon = _brighten(cartoon, 25)
    cartoon = _saturate(cartoon, 1.4)
    cartoon = _warm_shift(cartoon, 0.08)
    return cartoon


def effect_pixel_art(img: np.ndarray) -> np.ndarray:
    """Pixel art: quantise then downscale/upscale."""
    h, w = img.shape[:2]
    pixel_size = max(4, min(w, h) // 80)

    small = cv2.resize(img, (w // pixel_size, h // pixel_size), interpolation=cv2.INTER_LINEAR)
    small = _color_quantize(small, k=16)
    pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    return pixelated


def effect_sketch(img: np.ndarray) -> np.ndarray:
    """Pencil sketch effect."""
    gray, colour = cv2.pencilSketch(img, sigma_s=60, sigma_r=0.07, shade_factor=0.05)
    # Blend sketch with faint colour
    colour_faint = cv2.addWeighted(colour, 0.4, cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), 0.6, 0)
    return colour_faint


# ──────────────────────────────────────────────
# Style registry
# ──────────────────────────────────────────────

STYLE_MAP: Dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "warm_cartoon": effect_warm_cartoon,
    "soft_anime":   effect_soft_anime,
    "watercolor":   effect_watercolor,
    "dreamy":       effect_dreamy,
    "ghibli":       effect_ghibli,
    "chibi":        effect_chibi,
    "pixel_art":    effect_pixel_art,
    "sketch":       effect_sketch,
}


def get_effect_fn(style: str) -> Callable[[np.ndarray], np.ndarray]:
    fn = STYLE_MAP.get(style)
    if fn is None:
        logger.warning("Unknown style '%s', falling back to warm_cartoon", style)
        fn = STYLE_MAP["warm_cartoon"]
    return fn


# ──────────────────────────────────────────────
# Public API for tasks.py
# ──────────────────────────────────────────────

def apply_image_effect(input_path: str, output_path: str, style: str = "warm_cartoon"):
    """Read image → apply style → write result."""
    logger.info("Applying '%s' to image: %s", style, input_path)
    img = _read_img(input_path)
    fn = get_effect_fn(style)
    result = fn(img)
    _write_img(output_path, result)
    logger.info("Saved stylised image: %s", output_path)


def apply_video_effect(
    input_path: str,
    output_path: str,
    style: str = "warm_cartoon",
    progress_cb: Callable[[int], None] | None = None,
):
    """Process video frame-by-frame. progress_cb receives 0-100."""
    logger.info("Applying '%s' to video: %s", style, input_path)
    fn = get_effect_fn(style)

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    frame_idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            styled = fn(frame)
            out.write(styled)
            frame_idx += 1
            if progress_cb and frame_idx % max(1, total_frames // 20) == 0:
                pct = min(95, int(frame_idx / total_frames * 100))
                progress_cb(pct)
    finally:
        cap.release()
        out.release()

    logger.info("Saved stylised video (%d frames): %s", frame_idx, output_path)
