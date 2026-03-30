"""
EchoMie — cartoon / stylization effects using OpenCV + Pillow.
Dramatically visible effects — every style should look obviously different from the original.
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
    h, w = img.shape[:2]
    small = cv2.resize(img, (min(w, 400), min(h, 400)))
    data = small.reshape((-1, 3)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels_s, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    centers = np.uint8(centers)
    data_full = img.reshape((-1, 3)).astype(np.float32)
    dists = np.linalg.norm(data_full[:, None] - centers[None, :], axis=2)
    labels_full = np.argmin(dists, axis=1)
    return centers[labels_full].reshape(img.shape)


def _warm_shift(img: np.ndarray, strength: float = 0.15) -> np.ndarray:
    overlay = np.full_like(img, (120, 170, 255))
    return cv2.addWeighted(img, 1 - strength, overlay, strength, 0)


def _cool_shift(img: np.ndarray, strength: float = 0.10) -> np.ndarray:
    overlay = np.full_like(img, (255, 200, 180))
    return cv2.addWeighted(img, 1 - strength, overlay, strength, 0)


def _pink_shift(img: np.ndarray, strength: float = 0.12) -> np.ndarray:
    overlay = np.full_like(img, (200, 160, 255))
    return cv2.addWeighted(img, 1 - strength, overlay, strength, 0)


def _green_shift(img: np.ndarray, strength: float = 0.10) -> np.ndarray:
    overlay = np.full_like(img, (160, 240, 160))
    return cv2.addWeighted(img, 1 - strength, overlay, strength, 0)


def _add_soft_glow(img: np.ndarray, radius: int = 25, alpha: float = 0.3) -> np.ndarray:
    blurred = cv2.GaussianBlur(img, (radius | 1, radius | 1), 0)
    return cv2.addWeighted(img, 1 - alpha, blurred, alpha, 0)


def _get_edges(img: np.ndarray, blur_k: int = 7, block_size: int = 9,
               c: int = 3, thickness: int = 0) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, blur_k)
    edges = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, block_size, c
    )
    if thickness > 0:
        inv = cv2.bitwise_not(edges)
        kernel = np.ones((thickness, thickness), np.uint8)
        inv = cv2.dilate(inv, kernel, iterations=1)
        edges = cv2.bitwise_not(inv)
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
# Style implementations — each must produce a DRAMATICALLY visible change
# ──────────────────────────────────────────────

def effect_warm_cartoon(img: np.ndarray) -> np.ndarray:
    """Heavy flat cartoon: very smooth, few colors, bold black outlines, warm tint."""
    smooth = _bilateral_smooth(img, passes=10, d=9, sigma_color=150, sigma_space=150)
    smooth = _color_quantize(smooth, k=6)

    edges = _get_edges(img, blur_k=7, block_size=9, c=2, thickness=3)
    cartoon = cv2.bitwise_and(smooth, edges)

    cartoon = _warm_shift(cartoon, 0.25)
    cartoon = _brighten(cartoon, 20)
    cartoon = _saturate(cartoon, 1.5)
    return cartoon


def effect_soft_anime(img: np.ndarray) -> np.ndarray:
    """Anime: ultra-smooth, pastel, dreamy glow, thin edge lines, pink tint."""
    smooth = _bilateral_smooth(img, passes=12, d=9, sigma_color=200, sigma_space=200)
    smooth = _brighten(smooth, 40)
    smooth = _saturate(smooth, 0.65)
    smooth = _add_soft_glow(smooth, radius=55, alpha=0.55)

    edges = _get_edges(img, blur_k=9, block_size=13, c=5, thickness=2)
    result = cv2.bitwise_and(smooth, edges)
    result = _pink_shift(result, 0.22)
    return result


def effect_watercolor(img: np.ndarray) -> np.ndarray:
    """Watercolor: heavy stylization, color bleeding, paper texture feel."""
    styled = cv2.stylization(img, sigma_s=150, sigma_r=0.65)
    styled = _saturate(styled, 1.7)
    styled = _add_soft_glow(styled, radius=41, alpha=0.35)
    styled = _warm_shift(styled, 0.10)
    return styled


def effect_dreamy(img: np.ndarray) -> np.ndarray:
    """Dreamy: massive bloom, oversaturated, heavy vignette, ethereal glow."""
    bloom = cv2.GaussianBlur(img, (0, 0), sigmaX=35)
    dreamy = cv2.addWeighted(img, 0.35, bloom, 0.65, 20)
    dreamy = _saturate(dreamy, 1.7)
    dreamy = _warm_shift(dreamy, 0.22)
    dreamy = _brighten(dreamy, 15)

    h, w = dreamy.shape[:2]
    x = np.linspace(-1, 1, w)
    y = np.linspace(-1, 1, h)
    X, Y = np.meshgrid(x, y)
    vignette = 1 - 0.55 * (X ** 2 + Y ** 2)
    vignette = np.clip(vignette, 0.15, 1.0).astype(np.float32)
    dreamy = (dreamy.astype(np.float32) * vignette[:, :, np.newaxis]).astype(np.uint8)
    return dreamy


def effect_ghibli(img: np.ndarray) -> np.ndarray:
    """Ghibli: edge-preserving + vivid greens + warm sunlight + visible outlines."""
    filtered = cv2.edgePreservingFilter(img, flags=1, sigma_s=150, sigma_r=0.6)
    filtered = _saturate(filtered, 1.7)
    filtered = _green_shift(filtered, 0.22)
    filtered = cv2.convertScaleAbs(filtered, alpha=1.15, beta=15)

    edges = _get_edges(img, blur_k=7, block_size=11, c=4, thickness=2)
    result = cv2.bitwise_and(filtered, edges)
    result = _warm_shift(result, 0.08)
    return result


def effect_chibi(img: np.ndarray) -> np.ndarray:
    """Chibi: extreme smoothing, only 4 colors, very thick black outlines, vivid pink."""
    smooth = _bilateral_smooth(img, passes=15, d=9, sigma_color=250, sigma_space=250)
    smooth = _color_quantize(smooth, k=4)

    edges = _get_edges(img, blur_k=5, block_size=7, c=2, thickness=4)
    cartoon = cv2.bitwise_and(smooth, edges)

    cartoon = _brighten(cartoon, 45)
    cartoon = _saturate(cartoon, 1.8)
    cartoon = _pink_shift(cartoon, 0.18)
    return cartoon


def effect_pixel_art(img: np.ndarray) -> np.ndarray:
    """Pixel art: very chunky pixels, limited palette, retro."""
    h, w = img.shape[:2]
    pixel_size = max(8, min(w, h) // 32)

    small = cv2.resize(img, (w // pixel_size, h // pixel_size), interpolation=cv2.INTER_LINEAR)
    small = _color_quantize(small, k=8)
    small = _saturate(small, 1.6)
    small = _brighten(small, 10)
    pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    return pixelated


def effect_sketch(img: np.ndarray) -> np.ndarray:
    """Pencil sketch: heavy dark pencil lines, very faint washed-out color."""
    gray, colour = cv2.pencilSketch(img, sigma_s=100, sigma_r=0.04, shade_factor=0.02)
    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    result = cv2.addWeighted(colour, 0.2, gray_bgr, 0.8, 0)
    result = _warm_shift(result, 0.06)
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
