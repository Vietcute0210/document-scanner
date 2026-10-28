from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations
from typing import Optional, List, Tuple

import cv2
import numpy as np

from .preprocess import resize_max_dim, preprocess_for_edges
from .io_handling import imwrite, ensure_dir


@dataclass
class DetectionResult:
    corners: Optional[np.ndarray]
    score: float
    method: str
    debug: dict


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Orders 4 points in clockwise order: [Top-Left, Top-Right, Bottom-Right, Bottom-Left].
    Uses coordinate sum/difference with fallback to x-coordinate sorting.
    """
    pts = pts.astype(np.float32)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]

    rect = np.array([tl, tr, br, bl], dtype=np.float32)
    if cv2.isContourConvex(rect.reshape(-1, 1, 2)):
        return rect

    # Fallback x-sort
    sorted_by_x = pts[np.argsort(pts[:, 0])]
    left = sorted_by_x[:2]
    right = sorted_by_x[2:]
    tl, bl = left[np.argsort(left[:, 1])]
    tr, br = right[np.argsort(right[:, 1])]
    return np.stack([tl, tr, br, bl], axis=0).astype(np.float32)


def quad_area(quad: np.ndarray) -> float:
    """Computes polygon area via cv2.contourArea."""
    return float(cv2.contourArea(quad.reshape(-1, 1, 2).astype(np.float32)))


def is_convex_quad(quad: np.ndarray) -> bool:
    """Checks whether the quadrilateral is strictly convex."""
    return bool(cv2.isContourConvex(quad.reshape(-1, 1, 2).astype(np.float32)))


def angle_degrees(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Calculates angle ABC in degrees."""
    ba = a - b
    bc = c - b
    denom = (np.linalg.norm(ba) * np.linalg.norm(bc)) + 1e-9
    cosang = float(np.dot(ba, bc) / denom)
    cosang = max(-1.0, min(1.0, cosang))
    return math.degrees(math.acos(cosang))


def edge_support_score(quad: np.ndarray, edges: np.ndarray, num_samples: int = 24) -> float:
    """
    Measures how many sampled points along the 4 quadrilateral edges
    coincide with actual detected edge pixels in the image (within a 5x5 window),
    giving credit to edges that lie directly on the image frame boundary when a
    close-up document is partially clipped by the camera frame.
    """
    if edges is None:
        return 0.0
    total_pts = 0
    hit_pts = 0.0
    h, w = edges.shape[:2]
    quad = quad.astype(np.float32)
    for i in range(4):
        p1 = quad[i]
        p2 = quad[(i + 1) % 4]
        for t in np.linspace(0.05, 0.95, num_samples):
            pt = p1 + t * (p2 - p1)
            x, y = int(round(pt[0])), int(round(pt[1]))
            if 0 <= x < w and 0 <= y < h:
                total_pts += 1
                # If the side runs along the camera frame boundary (close-up photo), give partial credit
                if x <= 3 or x >= w - 4 or y <= 3 or y >= h - 4:
                    hit_pts += 0.65
                    continue
                x0, x1 = max(0, x - 2), min(w, x + 3)
                y0, y1 = max(0, y - 2), min(h, y + 3)
                if np.any(edges[y0:y1, x0:x1] > 0):
                    hit_pts += 1.0
    return float(hit_pts / max(1, total_pts))


def boundary_contrast_score(
    quad: np.ndarray,
    lab_blur: np.ndarray,
    num_samples: int = 24,
) -> float:
    """
    Measures how strongly each side of the quadrilateral separates the bright
    document interior from a darker/different-colored exterior in LAB space.

    Crucially, if a side lies inside the document (such as a notebook's inner
    margin line, header line, or a shadow line across the page), both the
    inside and outside samples sit on bright paper -> low LAB difference ->
    heavily penalized so the detector expands to the true outer edges of the page.
    """
    h, w = lab_blur.shape[:2]
    quad = order_points(quad).astype(np.float32)
    centroid = quad.mean(axis=0)
    offset = max(6.0, 0.016 * max(h, w))
    neutral = 0.62

    side_scores = []
    for i in range(4):
        p1 = quad[i]
        p2 = quad[(i + 1) % 4]
        d = p2 - p1
        length = float(np.linalg.norm(d))
        if length < 1e-6:
            return 0.0
        n = np.array([-d[1], d[0]], dtype=np.float32) / length
        mid = (p1 + p2) / 2.0
        if np.dot(centroid - mid, n) < 0:
            n = -n  # inward unit normal

        ts = np.linspace(0.08, 0.92, num_samples, dtype=np.float32)[:, None]
        pts = p1[None, :] + ts * d[None, :]
        inner = np.round(pts + n * offset).astype(int)
        outer = np.round(pts - n * offset).astype(int)

        valid = (
            (outer[:, 0] >= 0) & (outer[:, 0] < w) & (outer[:, 1] >= 0) & (outer[:, 1] < h)
            & (inner[:, 0] >= 0) & (inner[:, 0] < w) & (inner[:, 1] >= 0) & (inner[:, 1] < h)
        )
        if valid.sum() < 0.5 * num_samples:
            # Side lies on the camera frame border (close-up capture)
            side_scores.append(neutral)
            continue

        vin = lab_blur[inner[valid, 1], inner[valid, 0]].astype(np.float32)
        vout = lab_blur[outer[valid, 1], outer[valid, 0]].astype(np.float32)
        dist = float(np.median(np.linalg.norm(vin - vout, axis=1)))

        # Check if the exterior is ALSO bright neutral paper (meaning this side is inside the page!)
        l_in = float(np.median(vin[:, 0]))
        l_out = float(np.median(vout[:, 0]))
        chroma_out = float(np.median(np.hypot(vout[:, 1] - 128.0, vout[:, 2] - 128.0)))

        if dist < 14.0 and l_in > 145.0 and l_out > 145.0 and chroma_out < 18.0:
            # Both sides of this edge are bright white/gray paper -> inner notebook line!
            side_scores.append(0.05)
        else:
            side_scores.append(float(min(1.0, dist / 30.0)))

    side_scores_arr = np.array(side_scores, dtype=np.float32)
    return float(0.55 * side_scores_arr.mean() + 0.45 * side_scores_arr.min())


def score_quad(
    quad: np.ndarray,
    img_shape: tuple[int, int, ...],
    edges: Optional[np.ndarray] = None,
    lab_blur: Optional[np.ndarray] = None,
) -> float:
    """
    Scores a candidate quadrilateral based on convexity, area coverage,
    aspect ratio, internal angles, edge alignment, and inside/outside boundary contrast.
    """
    h, w = img_shape[:2]
    img_area = float(h * w)

    quad = order_points(quad)
    if not is_convex_quad(quad):
        return 0.0

    area = quad_area(quad)
    area_ratio = area / (img_area + 1e-9)
    if area_ratio < 0.06 or area_ratio > 0.995:
        return 0.0

    tl, tr, br, bl = quad
    sides = [
        np.linalg.norm(tr - tl),
        np.linalg.norm(br - tr),
        np.linalg.norm(bl - br),
        np.linalg.norm(tl - bl),
    ]
    min_side, max_side = min(sides), max(sides)
    if min_side < 0.05 * min(h, w) or max_side / (min_side + 1e-9) > 8.0:
        return 0.0

    angles = [
        angle_degrees(bl, tl, tr),
        angle_degrees(tl, tr, br),
        angle_degrees(tr, br, bl),
        angle_degrees(br, bl, tl),
    ]
    if any(a < 40.0 or a > 145.0 for a in angles):
        return 0.0

    # Larger valid page quads are preferred over inner notebook boxes
    area_score = max(0.0, min(1.0, area_ratio / 0.88))

    # Angle score: penalty for deviation from 90 degrees
    angle_err = sum(abs(a - 90.0) for a in angles) / 4.0
    angle_score = max(0.0, 1.0 - angle_err / 45.0)

    # Only penalize when all 4 corners hug the full camera sensor boundary
    border_pts = sum(1 for (x, y) in quad if x <= 2 or x >= w - 3 or y <= 2 or y >= h - 3)
    if border_pts == 4 and area_ratio > 0.96:
        border_penalty = 0.30
    else:
        border_penalty = 0.02 * (border_pts / 4.0)

    edge_score = edge_support_score(quad, edges) if edges is not None else 0.0

    if edges is not None and lab_blur is not None:
        contrast_score = boundary_contrast_score(quad, lab_blur)
        composite = (
            0.28 * area_score
            + 0.20 * angle_score
            + 0.17 * edge_score
            + 0.35 * contrast_score
            - border_penalty
        )
    elif edges is not None:
        composite = 0.40 * area_score + 0.35 * angle_score + 0.25 * edge_score - border_penalty
    else:
        composite = 0.60 * area_score + 0.40 * angle_score - border_penalty

    return float(max(0.0, min(1.0, composite)))


def extract_candidate_quads(contour: np.ndarray, img_shape: tuple[int, int]) -> List[Tuple[np.ndarray, str, float]]:
    """
    Extracts multiple candidate quadrilaterals from a single contour using:
    1. Progressive approxPolyDP
    2. Convex Hull approximation
    3. Maximum inscribed quad area from convex hull (handles rounded corners and spirals)
    4. Rotated bounding box (minAreaRect)
    """
    peri = cv2.arcLength(contour, True)
    if peri < 80:
        return []
    candidates = []

    # 1. Direct approxPolyDP with progressive epsilon
    for eps in [0.015, 0.02, 0.025, 0.03, 0.04]:
        approx = cv2.approxPolyDP(contour, eps * peri, True)
        if len(approx) == 4 and is_convex_quad(approx):
            candidates.append((approx.reshape(4, 2).astype(np.float32), f"approx_{eps:.3f}", 1.12))
            break

    # 2. Convex Hull approximation
    hull = cv2.convexHull(contour)
    hull_peri = cv2.arcLength(hull, True)
    for eps in [0.015, 0.02, 0.025, 0.03, 0.04]:
        approx_h = cv2.approxPolyDP(hull, eps * hull_peri, True)
        if len(approx_h) == 4 and is_convex_quad(approx_h):
            candidates.append((approx_h.reshape(4, 2).astype(np.float32), f"hull_{eps:.3f}", 1.10))
            break

    # 3. 4-point maximum area convex subset from convex hull
    pts = hull.reshape(-1, 2).astype(np.float32)
    if len(pts) > 12:
        approx_pre = cv2.approxPolyDP(pts, 0.015 * hull_peri, True)
        pts = approx_pre.reshape(-1, 2).astype(np.float32)
    if 4 <= len(pts) <= 12:
        best_q = None
        max_a = 0.0
        for comb in combinations(pts, 4):
            q = np.array(comb, dtype=np.float32)
            if is_convex_quad(q):
                a = quad_area(q)
                if a > max_a:
                    max_a = a
                    best_q = q
        if best_q is not None:
            candidates.append((best_q, "hull_max_quad", 1.06))

    # 4. minAreaRect bounding box fallback
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect).astype(np.float32)
    candidates.append((box, "minAreaRect", 0.98))

    return candidates


def _channel_adaptive_canny(gray: np.ndarray, gray_clahe: np.ndarray) -> list[np.ndarray]:
    """Median-based adaptive Canny + CLAHE Canny – returns two closed edge maps."""
    v = np.median(gray)
    c_lo = int(max(15, 0.5 * v))
    c_hi = int(min(220, 1.3 * v))
    blurred1 = cv2.GaussianBlur(gray, (5, 5), 0)
    edges1 = cv2.Canny(blurred1, c_lo, c_hi)
    edges1_closed = cv2.morphologyEx(
        edges1, cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)),
    )

    blurred2 = cv2.GaussianBlur(gray_clahe, (5, 5), 0)
    edges2 = cv2.Canny(blurred2, 40, 140)
    edges2_closed = cv2.morphologyEx(
        edges2, cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)),
    )
    return [edges1_closed, edges2_closed]


def _channel_otsu(gray_clahe: np.ndarray) -> list[np.ndarray]:
    """Otsu paper mask with progressive closing kernels to bridge shadow gaps."""
    _, otsu = cv2.threshold(gray_clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    otsu_mask = otsu if np.mean(otsu) < 160 else cv2.bitwise_not(otsu)

    return [
        cv2.morphologyEx(
            otsu_mask, cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11)),
        ),
        cv2.morphologyEx(
            otsu_mask, cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25)),
        ),
    ]


def _channel_hsv_paper(img_bgr: np.ndarray) -> list[np.ndarray]:
    """
    Color-based paper segmentation via HSV (low saturation, high value).
    Separates white/gray notebook paper from colored or dark desk/clothing backgrounds.
    """
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    k_open = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))

    strict = ((hsv[:, :, 1] < 45) & (hsv[:, :, 2] > 155)).astype(np.uint8) * 255
    strict_o = cv2.morphologyEx(cv2.morphologyEx(strict, cv2.MORPH_CLOSE, k_close), cv2.MORPH_OPEN, k_open)

    relaxed = ((hsv[:, :, 1] < 60) & (hsv[:, :, 2] > 120)).astype(np.uint8) * 255
    k_close_big = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 31))
    relaxed_o = cv2.morphologyEx(cv2.morphologyEx(relaxed, cv2.MORPH_CLOSE, k_close_big), cv2.MORPH_OPEN, k_open)

    return [strict_o, relaxed_o]


def _channel_lab_paper(img_bgr: np.ndarray) -> list[np.ndarray]:
    """LAB L-channel paper segmentation across multiple luminance thresholds."""
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l_ch = lab[:, :, 0]
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21))
    k_open = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))

    masks = []
    for thresh in [160, 138]:
        mask = (l_ch > thresh).astype(np.uint8) * 255
        mo = cv2.morphologyEx(cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k_close), cv2.MORPH_OPEN, k_open)
        masks.append(mo)
    return masks


def draw_debug(
    img_bgr: np.ndarray,
    intermediates: dict,
    quad_resized: Optional[np.ndarray],
    scale: float,
    method: str,
    score: float,
) -> dict:
    """Generates visual debug images."""
    debug = {}
    debug["gray"] = intermediates.get("gray")
    debug["edges"] = intermediates.get("edges")
    debug["edges_closed"] = intermediates.get("edges_closed")

    overlay = img_bgr.copy()
    if quad_resized is not None:
        quad_ord = order_points(quad_resized)
        pts = quad_ord.reshape(-1, 1, 2).astype(np.int32)
        cv2.polylines(overlay, [pts], True, (0, 255, 0), max(2, int(img_bgr.shape[1] / 300)))

        labels = ["TL", "TR", "BR", "BL"]
        for (x, y), lab in zip(quad_ord, labels):
            cv2.circle(overlay, (int(x), int(y)), max(6, int(img_bgr.shape[1] / 150)), (0, 0, 255), -1)
            cv2.putText(
                overlay,
                lab,
                (int(x) + 8, int(y) - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )

    cv2.putText(
        overlay,
        f"method={method} score={score:.2f} scale={scale:.3f}",
        (12, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 0, 0),
        2,
        cv2.LINE_AA,
    )
    debug["overlay_resized"] = overlay
    return debug


def save_debug_images(debug_dir: str, debug: dict) -> None:
    """Saves generated debug images to directory."""
    ensure_dir(debug_dir)
    for name, img in debug.items():
        if img is not None:
            path = f"{debug_dir}/{name}.png"
            imwrite(path, img)


def detect_page_corners(
    img_bgr_original: np.ndarray,
    debug_dir: Optional[str] = None,
    max_dim: int = 1200,
    use_clahe: bool = False,
) -> DetectionResult:
    """
    Robust multi-strategy document corner detector.
    Combines adaptive Canny edges, CLAHE Canny, Otsu binarization, HSV/LAB paper
    masks, and inside/outside LAB boundary-contrast verification so inner notebook
    grids/margins are never mistaken for the outer page boundary.
    """
    img_resized, scale = resize_max_dim(img_bgr_original, max_dim=max_dim)
    h, w = img_resized.shape[:2]

    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
    clahe_obj = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_clahe = clahe_obj.apply(gray)

    v = np.median(gray)
    c_lo = int(max(15, 0.5 * v))
    c_hi = int(min(220, 1.3 * v))
    blurred1 = cv2.GaussianBlur(gray, (5, 5), 0)
    edges1 = cv2.Canny(blurred1, c_lo, c_hi)

    blurred2 = cv2.GaussianBlur(gray_clahe, (5, 5), 0)
    edges2 = cv2.Canny(blurred2, 40, 140)
    combined_edges = cv2.bitwise_or(edges1, edges2)

    lab_blur = cv2.GaussianBlur(cv2.cvtColor(img_resized, cv2.COLOR_BGR2LAB), (7, 7), 0)

    all_masks: list[tuple[np.ndarray, int]] = []
    canny_channels = _channel_adaptive_canny(gray, gray_clahe)
    for emap in canny_channels:
        all_masks.append((emap, cv2.RETR_LIST))
    for omask in _channel_otsu(gray_clahe):
        all_masks.append((omask, cv2.RETR_EXTERNAL))
    for hmask in _channel_hsv_paper(img_resized):
        all_masks.append((hmask, cv2.RETR_EXTERNAL))
    for lmask in _channel_lab_paper(img_resized):
        all_masks.append((lmask, cv2.RETR_EXTERNAL))

    all_contours = []
    min_cnt_area = 0.04 * (w * h)
    for mask, mode in all_masks:
        cnts, _ = cv2.findContours(mask, mode, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            if cv2.contourArea(c) >= min_cnt_area:
                all_contours.append(c)

    all_contours = sorted(all_contours, key=cv2.contourArea, reverse=True)[:30]

    best_quad = None
    best_score = 0.0
    best_method = "none"

    for c in all_contours:
        for q, method_name, multiplier in extract_candidate_quads(c, (h, w)):
            s = score_quad(q, (h, w), combined_edges, lab_blur) * multiplier
            if s > best_score:
                best_score = s
                best_quad = q
                best_method = method_name

    inter = {
        "gray": gray,
        "gray_eq": gray_clahe,
        "blurred": blurred1,
        "edges": combined_edges,
        "edges_closed": canny_channels[0],
    }

    if best_quad is None or best_score < 0.15:
        score = 0.0
        corners_original = None
        method_used = "none_rejected" if best_quad is not None else "none"
        dbg = draw_debug(img_resized, inter, None, scale, method_used, score)
        if debug_dir:
            save_debug_images(debug_dir, dbg)
        return DetectionResult(corners=corners_original, score=score, method=method_used, debug=dbg)

    best_quad_ord = order_points(best_quad)
    corners_original = (best_quad_ord / scale).astype(np.float32)

    dbg = draw_debug(img_resized, inter, best_quad_ord, scale, best_method, best_score)
    if debug_dir:
        save_debug_images(debug_dir, dbg)

    return DetectionResult(corners=corners_original, score=best_score, method=best_method, debug=dbg)
