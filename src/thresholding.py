import cv2
import numpy as np


def unsharp_mask(img: np.ndarray, sigma: float = 1.2, strength: float = 0.85) -> np.ndarray:
    """
    Applies halo-clamped unsharp masking to recover fine edge sharpness from
    blurry or soft-focus camera captures without creating bright overshoot halos.
    """
    blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=sigma, sigmaY=sigma)
    sharpened = cv2.addWeighted(img, 1.0 + strength, blurred, -strength, 0)
    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    lo = cv2.erode(img, se)
    hi = cv2.dilate(img, se)
    return np.clip(sharpened, lo, hi).astype(np.uint8)


def _estimate_macro_illumination(ch: np.ndarray) -> np.ndarray:
    """
    Estimates the smooth macro-scale paper illumination surface (~14% of page width)
    using an 8x-downsampled two-stage median (75th-percentile) filter followed by
    Gaussian smoothing.

    Unlike a small-kernel Gaussian blur (which gets pulled down on words and hollows
    out thin handwriting strokes) or morphological dilation (which latches onto bright
    JPEG noise spikes), the 75th-percentile macro estimator is 100% immune to dark
    ink strokes AND bright JPEG ringing.
    """
    h, w = ch.shape[:2]
    scale = 8
    sw, sh = max(16, w // scale), max(16, h // scale)
    small = cv2.resize(ch, (sw, sh), interpolation=cv2.INTER_AREA)

    win = max(15, int(sw * 0.14)) | 1
    med = cv2.medianBlur(small, win)
    upper = np.maximum(small, med)
    p75 = cv2.medianBlur(upper, win)

    bg_small = cv2.GaussianBlur(p75.astype(np.float32), (0, 0), sigmaX=10, sigmaY=10)
    return cv2.resize(bg_small, (w, h), interpolation=cv2.INTER_CUBIC)


def magic_color_document(
    img: np.ndarray,
    contrast_boost: float = 2.2,
    sharpen: bool = True,
) -> np.ndarray:
    """
    Pro-grade 'Magic Color' document enhancement:
    1. Macro-scale 75th-percentile illumination normalization flattens uneven shadows
       without ever dipping on dense words or erasing thin strokes.
    2. Retinal lateral-inhibition local contrast (Difference-of-Gaussians at stroke
       scale sigma=4.2px and edge scale sigma=1.2px) recovers faint thin pen strokes
       even when phone-ISP sharpening halos lift them above the open-paper level.
    3. Smooth rational Reinhard tone curve produces spotless 255 snow-white paper
       while keeping character interiors open, anti-aliased, and bold.
    """
    if img.ndim == 2:
        return magic_gray_document(img, contrast_boost=contrast_boost, sharpen=sharpen)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    bg_gray = _estimate_macro_illumination(img[:, :, 1])

    # Activity gate: 1.0 within ~7px of any ink stroke, 0.0 on empty open paper
    # Prevents any JPEG mosquito noise on open paper from being amplified.
    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    local_darkest = cv2.erode(gray, se)
    near_text = np.clip(
        (bg_gray - 13.0 - cv2.GaussianBlur(local_darkest, (0, 0), sigmaX=4.0)) / 18.0,
        0.0,
        1.0,
    )

    b = max(1.0, float(contrast_boost))
    out = np.empty_like(img)

    for c in range(3):
        ch = img[:, :, c].astype(np.float32)
        bg = _estimate_macro_illumination(img[:, :, c])

        # 1. Macro ink deficit (4.5-level dead-zone keeps flat paper strictly at 0 -> pure white 255)
        d_macro = np.maximum(0.0, bg - 4.5 - ch) / (bg + 1e-5)

        if sharpen:
            # 2. Local surround contrast at stroke scale (sigma=4.2) & fine edge scale (sigma=1.25)
            g_surround = cv2.GaussianBlur(ch, (0, 0), sigmaX=4.2, sigmaY=4.2)
            g_fine = cv2.GaussianBlur(ch, (0, 0), sigmaX=1.25, sigmaY=1.25)

            d_local = near_text * np.maximum(0.0, g_surround - 1.5 - ch) / (g_surround + 1e-5)
            d_edge = near_text * (g_fine - ch) / (g_surround + 1e-5)
            d_total = np.clip(d_macro + 0.85 * d_local + 0.55 * d_edge, 0.0, 1.0)
        else:
            d_total = np.clip(d_macro, 0.0, 1.0)

        # 3. Rational tone curve: full gain on faint strokes, smooth roll-off on dark ink
        ink = (b * 1.30 * d_total) / (1.0 + (b * 0.75) * d_total)
        out[:, :, c] = np.clip((1.0 - ink) * 255.0, 0.0, 255.0).astype(np.uint8)

    return out


def magic_gray_document(
    img: np.ndarray,
    contrast_boost: float = 2.2,
    sharpen: bool = True,
) -> np.ndarray:
    """
    Smooth anti-aliased grayscale document scan using macro-illumination leveling
    and retinal lateral-inhibition stroke recovery.
    """
    gray_u8 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img.copy()
    ch = gray_u8.astype(np.float32)
    bg = _estimate_macro_illumination(gray_u8)

    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    local_darkest = cv2.erode(ch, se)
    near_text = np.clip(
        (bg - 13.0 - cv2.GaussianBlur(local_darkest, (0, 0), sigmaX=4.0)) / 18.0,
        0.0,
        1.0,
    )

    d_macro = np.maximum(0.0, bg - 4.5 - ch) / (bg + 1e-5)
    if sharpen:
        g_surround = cv2.GaussianBlur(ch, (0, 0), sigmaX=4.2, sigmaY=4.2)
        g_fine = cv2.GaussianBlur(ch, (0, 0), sigmaX=1.25, sigmaY=1.25)
        d_local = near_text * np.maximum(0.0, g_surround - 1.5 - ch) / (g_surround + 1e-5)
        d_edge = near_text * (g_fine - ch) / (g_surround + 1e-5)
        d_total = np.clip(d_macro + 0.85 * d_local + 0.55 * d_edge, 0.0, 1.0)
    else:
        d_total = np.clip(d_macro, 0.0, 1.0)

    b = max(1.0, float(contrast_boost))
    ink = (b * 1.30 * d_total) / (1.0 + (b * 0.75) * d_total)
    return np.clip((1.0 - ink) * 255.0, 0.0, 255.0).astype(np.uint8)


def thresh_document(
    img: np.ndarray,
    contrast_boost: float = 2.2,
    sharpen: bool = True,
) -> np.ndarray:
    """
    Produces a crisp, high-contrast black-and-white scanned document appearance
    using Sauvola-inspired local adaptive thresholding on the enhanced grayscale scan.
    """
    mg = magic_gray_document(img, contrast_boost=contrast_boost, sharpen=sharpen)
    h, w = mg.shape[:2]

    b_size = max(21, int(w * 0.025)) | 1
    thresh_img = cv2.adaptiveThreshold(
        mg, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, b_size, 10
    )
    return cv2.medianBlur(thresh_img, 3)


def enhance_document(
    img: np.ndarray,
    style: str = "magic_color",
    contrast_boost: float = 2.2,
    sharpen: bool = True,
) -> np.ndarray:
    """
    Convenience router to enhance document images by style:
    - 'magic_color': CamScanner-style clean white paper with vivid ink colors
    - 'magic_gray': Smooth anti-aliased grayscale
    - 'bw': Crisp high-contrast black and white
    """
    if style == "magic_color":
        return magic_color_document(img, contrast_boost=contrast_boost, sharpen=sharpen)
    elif style == "magic_gray":
        return magic_gray_document(img, contrast_boost=contrast_boost, sharpen=sharpen)
    elif style == "bw":
        return thresh_document(img, contrast_boost=contrast_boost, sharpen=sharpen)
    return img
