"""
EchoMie — cartoon / stylization effects using OpenCV.
Balanced: clearly different from original, but aesthetically pleasing.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Callable, Dict

from .logging_config import get_logger

logger = get_logger("app.effects")


def _read_img(path: str) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return img


def _write_img(path: str, img: np.ndarray):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(path, img)


def _flatten(img: np.ndarray, sp: int = 20, sr: int = 40) -> np.ndarray:
    return cv2.pyrMeanShiftFiltering(img, sp=sp, sr=sr)


def _quantize(img: np.ndarray, k: int = 8) -> np.ndarray:
    h, w = img.shape[:2]
    max_dim = 300
    scale = min(1.0, max_dim / max(h, w))
    small = cv2.resize(img, None, fx=scale, fy=scale) if scale < 1 else img
    data = small.reshape((-1, 3)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, _, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    centers = np.uint8(centers)
    full_data = img.reshape((-1, 3)).astype(np.float32)
    dists = np.linalg.norm(full_data[:, None] - centers[None, :], axis=2)
    labels = np.argmin(dists, axis=1)
    return centers[labels].reshape(img.shape)


def _edges(img: np.ndarray, blur_k: int = 7, block: int = 9,
           c: int = 3, thick: int = 0) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, blur_k)
    e = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY, block, c)
    if thick > 0:
        inv = cv2.bitwise_not(e)
        inv = cv2.dilate(inv, np.ones((thick, thick), np.uint8), iterations=1)
        e = cv2.bitwise_not(inv)
    return cv2.cvtColor(e, cv2.COLOR_GRAY2BGR)


def _tint(img: np.ndarray, bgr: tuple, strength: float) -> np.ndarray:
    overlay = np.full_like(img, bgr)
    return cv2.addWeighted(img, 1 - strength, overlay, strength, 0)


def _saturate(img: np.ndarray, factor: float) -> np.ndarray:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * factor, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def _glow(img: np.ndarray, r: int = 31, a: float = 0.3) -> np.ndarray:
    blurred = cv2.GaussianBlur(img, (r | 1, r | 1), 0)
    return cv2.addWeighted(img, 1 - a, blurred, a, 0)


# ──────────────────────────────────────────────

def effect_warm_cartoon(img: np.ndarray) -> np.ndarray:
    """Warm cartoon: smooth + limited palette + outlines + warm tint."""
    flat = _flatten(img, sp=20, sr=45)
    q = _quantize(flat, k=8)
    e = _edges(img, blur_k=7, block=9, c=2, thick=2)
    result = cv2.bitwise_and(q, e)
    result = _tint(result, (120, 170, 255), 0.15)
    result = _saturate(result, 1.3)
    return cv2.convertScaleAbs(result, alpha=1.05, beta=10)


def effect_soft_anime(img: np.ndarray) -> np.ndarray:
    """Soft anime: smooth, pastel, glow, thin lines."""
    flat = _flatten(img, sp=25, sr=50)
    flat = cv2.convertScaleAbs(flat, alpha=1.0, beta=25)
    flat = _saturate(flat, 0.7)
    flat = _glow(flat, r=45, a=0.4)
    e = _edges(img, blur_k=9, block=13, c=5, thick=1)
    result = cv2.bitwise_and(flat, e)
    result = _tint(result, (210, 180, 255), 0.12)
    return result


def effect_watercolor(img: np.ndarray) -> np.ndarray:
    """Watercolor: stylization + saturation + glow."""
    s = cv2.stylization(img, sigma_s=150, sigma_r=0.6)
    s = _saturate(s, 1.5)
    s = _glow(s, r=35, a=0.25)
    return s


def effect_dreamy(img: np.ndarray) -> np.ndarray:
    """Dreamy: bloom + warm + vignette."""
    bloom = cv2.GaussianBlur(img, (0, 0), sigmaX=30)
    d = cv2.addWeighted(img, 0.4, bloom, 0.6, 15)
    d = _saturate(d, 1.5)
    d = _tint(d, (130, 170, 255), 0.15)
    h, w = d.shape[:2]
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    dist = ((X - cx) ** 2 + (Y - cy) ** 2) / (cx ** 2 + cy ** 2)
    vig = np.clip(1.0 - 0.5 * dist, 0.2, 1.0)
    d = (d.astype(np.float32) * vig[:, :, None]).astype(np.uint8)
    return d


def effect_ghibli(img: np.ndarray) -> np.ndarray:
    """Ghibli: edge-preserving + vivid greens + outlines."""
    flat = cv2.edgePreservingFilter(img, flags=1, sigma_s=120, sigma_r=0.55)
    flat = _saturate(flat, 1.5)
    flat = _tint(flat, (150, 235, 150), 0.12)
    flat = cv2.convertScaleAbs(flat, alpha=1.1, beta=10)
    e = _edges(img, blur_k=7, block=11, c=4, thick=1)
    return cv2.bitwise_and(flat, e)


def effect_chibi(img: np.ndarray) -> np.ndarray:
    """Chibi: very smooth, few colors, thick outlines, vivid."""
    flat = _flatten(img, sp=35, sr=60)
    q = _quantize(flat, k=6)
    e = _edges(img, blur_k=5, block=7, c=2, thick=3)
    result = cv2.bitwise_and(q, e)
    result = cv2.convertScaleAbs(result, alpha=1.05, beta=25)
    result = _saturate(result, 1.6)
    result = _tint(result, (200, 170, 255), 0.08)
    return result


def effect_pixel_art(img: np.ndarray) -> np.ndarray:
    """Pixel art: chunky pixels, limited palette."""
    h, w = img.shape[:2]
    ps = max(8, min(w, h) // 36)
    small = cv2.resize(img, (w // ps, h // ps), interpolation=cv2.INTER_LINEAR)
    small = _quantize(small, k=10)
    small = _saturate(small, 1.4)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)


def effect_sketch(img: np.ndarray) -> np.ndarray:
    """Pencil sketch: pencil lines + faint color wash."""
    gray, colour = cv2.pencilSketch(img, sigma_s=100, sigma_r=0.04, shade_factor=0.03)
    g3 = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    result = cv2.addWeighted(g3, 0.6, colour, 0.4, 0)
    result = _tint(result, (200, 210, 230), 0.05)
    return result


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
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(fn(frame))
            idx += 1
            if progress_cb and idx % max(1, total // 20) == 0:
                progress_cb(min(95, int(idx / total * 100)))
    finally:
        cap.release()
        out.release()
    logger.info("Saved stylised video (%d frames): %s", idx, output_path)
