"""
EchoMie — cartoon / stylization effects using OpenCV + Pillow.
Strengthened effects for clearly visible cartoon transformations.
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
    data = img.reshape((-1, 3)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    centers = np.uint8(centers)
    return centers[labels.flatten()].reshape(img.shape)


def _warm_shift(img: np.ndarray, strength: float = 0.15) -> np.ndarray:
    overlay = np.full_like(img, (140, 180, 255))
    return cv2.addWeighted(img, 1 - strength, overlay, strength, 0)


def _cool_shift(img: np.ndarray, strength: float = 0.10) -> np.ndarray:
    overlay = np.full_like(img, (255, 210, 190))
    return cv2.addWeighted(img, 1 - strength, overlay, strength, 0)


def _pink_shift(img: np.ndarray, strength: float = 0.12) -> np.ndarray:
    overlay = np.full_like(img, (200, 180, 255))
    return cv2.addWeighted(img, 1 - strength, overlay, strength, 0)


def _green_shift(img: np.ndarray, strength: float = 0.10) -> np.ndarray:
    overlay = np.full_like(img, (180, 240, 180))
    return cv2.addWeighted(img, 1 - strength, overlay, strength, 0)


def _add_soft_glow(img: np.ndarray, radius: int = 25, alpha: float = 0.3) -> np.ndarray:
    blurred = cv2.GaussianBlur(img, (radius | 1, radius | 1), 0)
    return cv2.addWeighted(img, 1 - alpha, blurred, alpha, 0)


def _get_edges(img: np.ndarray, blur_k: int = 7, block_size: int = 9, c: int = 3) -> np.ndarray:
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


def _bilateral_smooth(img: np.ndarray, passes: int = 5, d: int = 9,
                       sigma_color: int = 90, sigma_space: int = 90) -> np.ndarray:
    result = img.copy()
    for _ in range(passes):
        result = cv2.bilateralFilter(result, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)
    return result


# ──────────────────────────────────────────────
# Style implementations (strengthened)
# ──────────────────────────────────────────────

def effect_warm_cartoon(img: np.ndarray) -> np.ndarray:
    """Warm cartoon: heavy smoothing + bold edges + warm palette + color reduction."""
    smooth = _bilateral_smooth(img, passes=6, sigma_color=100, sigma_space=100)
    smooth = _color_quantize(smooth, k=8)

    edges = _get_edges(img, blur_k=7, block_size=9, c=2)
    cartoon = cv2.bitwise_and(smooth, edges)

    cartoon = _warm_shift(cartoon, 0.20)
    cartoon = _brighten(cartoon, 15)
    cartoon = _saturate(cartoon, 1.3)
    return cartoon


def effect_soft_anime(img: np.ndarray) -> np.ndarray:
    """Soft anime: very smooth skin, pastel glow, dreamy feel."""
    smooth = _bilateral_smooth(img, passes=7, sigma_color=120, sigma_space=120)

    smooth = _brighten(smooth, 30)
    smooth = _saturate(smooth, 0.75)

    smooth = _add_soft_glow(smooth, radius=45, alpha=0.45)

    edges = _get_edges(img, blur_k=9, block_size=13, c=4)
    result = cv2.bitwise_and(smooth, edges)

    result = _pink_shift(result, 0.15)
    return result


def effect_watercolor(img: np.ndarray) -> np.ndarray:
    """Watercolor: strong stylization + saturation boost + soft bleeding."""
    styled = cv2.stylization(img, sigma_s=100, sigma_r=0.55)
    styled = _saturate(styled, 1.5)
    styled = _add_soft_glow(styled, radius=31, alpha=0.3)
    styled = _warm_shift(styled, 0.06)
    return styled


def effect_dreamy(img: np.ndarray) -> np.ndarray:
    """Dreamy: heavy bloom + high saturation + vignette."""
    bloom = cv2.GaussianBlur(img, (0, 0), sigmaX=25)
    dreamy = cv2.addWeighted(img, 0.45, bloom, 0.55, 15)
    dreamy = _saturate(dreamy, 1.5)
    dreamy = _warm_shift(dreamy, 0.15)
    dreamy = _brighten(dreamy, 10)

    h, w = dreamy.shape[:2]
    x = np.linspace(-1, 1, w)
    y = np.linspace(-1, 1, h)
    X, Y = np.meshgrid(x, y)
    vignette = 1 - 0.45 * (X ** 2 + Y ** 2)
    vignette = np.clip(vignette, 0.2, 1.0).astype(np.float32)
    dreamy = (dreamy.astype(np.float32) * vignette[:, :, np.newaxis]).astype(np.uint8)
    return dreamy


def effect_ghibli(img: np.ndarray) -> np.ndarray:
    """Ghibli-inspired: strong edge-preserving + vivid greens + warm contrast."""
    filtered = cv2.edgePreservingFilter(img, flags=1, sigma_s=100, sigma_r=0.5)
    filtered = _saturate(filtered, 1.5)
    filtered = _green_shift(filtered, 0.18)

    filtered = cv2.convertScaleAbs(filtered, alpha=1.1, beta=10)

    edges = _get_edges(img, blur_k=7, block_size=11, c=4)
    result = cv2.bitwise_and(filtered, edges)
    return result


def effect_chibi(img: np.ndarray) -> np.ndarray:
    """Chibi/cute: extreme smoothing + very few colors + thick edges + vivid."""
    smooth = _bilateral_smooth(img, passes=8, sigma_color=150, sigma_space=150)
    smooth = _color_quantize(smooth, k=6)

    edges = _get_edges(img, blur_k=5, block_size=7, c=2)
    # Make edges thicker
    kernel = np.ones((2, 2), np.uint8)
    edges_inv = cv2.bitwise_not(edges)
    edges_inv = cv2.dilate(edges_inv, kernel, iterations=1)
    edges = cv2.bitwise_not(edges_inv)

    cartoon = cv2.bitwise_and(smooth, edges)
    cartoon = _brighten(cartoon, 35)
    cartoon = _saturate(cartoon, 1.6)
    cartoon = _pink_shift(cartoon, 0.10)
    return cartoon


def effect_pixel_art(img: np.ndarray) -> np.ndarray:
    """Pixel art: aggressive downscale + very few colors."""
    h, w = img.shape[:2]
    pixel_size = max(6, min(w, h) // 48)

    small = cv2.resize(img, (w // pixel_size, h // pixel_size), interpolation=cv2.INTER_LINEAR)
    small = _color_quantize(small, k=12)
    small = _saturate(small, 1.4)
    pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    return pixelated


def effect_sketch(img: np.ndarray) -> np.ndarray:
    """Pencil sketch: strong pencil lines + faint color wash."""
    gray, colour = cv2.pencilSketch(img, sigma_s=80, sigma_r=0.05, shade_factor=0.03)

    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    # Strong sketch lines with subtle color
    result = cv2.addWeighted(colour, 0.3, gray_bgr, 0.7, 0)
    result = _warm_shift(result, 0.05)
    return result


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
