from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Optional, Tuple, Dict, Any, List

import cv2
import numpy as np

from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def imwrite(path: str | Path, img: np.ndarray) -> None:
    p = Path(path)
    ensure_dir(p.parent)
    ok = cv2.imwrite(str(p), img)
    if not ok:
        raise IOError(f"Failed to write image: {p}")


def resize_max_dim(img: np.ndarray, max_dim: int = 1200) -> Tuple[np.ndarray, float]:
    h, w = img.shape[:2]
    m = max(h, w)
    if m <= max_dim:
        return img.copy(), 1.0
    scale = float(max_dim) / float(m)
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale


@dataclass
class DetectionResult:
    corners: Optional[np.ndarray]  # (4, 2) float32 in original image coords: tl, tr, br, bl
    score: float
    method: str
    debug: Dict[str, Any]
    boundary_points: Optional[np.ndarray] = None  # (N, 2) float32: 4, 6, 8, or 12 points


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Orders 4 points in clockwise order: top-left, top-right, bottom-right, bottom-left.
    Uses angle from centroid to avoid diagonal ties on rotated rectangles.
    """
    pts = np.asarray(pts, dtype=np.float32).reshape(4, 2)
    center = pts.mean(axis=0)
    angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
    order = np.argsort(angles)
    sorted_pts = pts[order]

    s = sorted_pts.sum(axis=1)
    tl_idx = int(np.argmin(s))
    sorted_pts = np.roll(sorted_pts, -tl_idx, axis=0)
    return sorted_pts.astype(np.float32)


def quad_area(pts: np.ndarray) -> float:
    """Computes polygon area using the Shoelace formula."""
    x = pts[:, 0]
    y = pts[:, 1]
    return 0.5 * float(np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))))


def is_convex_quad(pts: np.ndarray) -> bool:
    """Checks if a 4-point polygon is strictly convex and non-self-intersecting."""
    pts = pts.reshape(4, 2)
    pts_ord = order_points(pts)
    cross_signs = []
    for i in range(4):
        p0 = pts_ord[i]
        p1 = pts_ord[(i + 1) % 4]
        p2 = pts_ord[(i + 2) % 4]
        v1 = p1 - p0
        v2 = p2 - p1
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        cross_signs.append(cross)
    cross_signs = np.array(cross_signs)
    return bool(np.all(cross_signs > 0) or np.all(cross_signs < 0))


def _estimate_paper_core_stats(lab_blur: np.ndarray) -> Tuple[float, float, float]:
    """
    Estimates the LAB color of the document paper by sampling the upper-bright
    half of the central 40% region of the image.
    """
    h, w = lab_blur.shape[:2]
    core = lab_blur[int(0.28 * h):int(0.72 * h), int(0.28 * w):int(0.72 * w)].reshape(-1, 3).astype(np.float32)
    l_med = np.median(core[:, 0])
    bright = core[core[:, 0] >= l_med]
    if len(bright) == 0:
        bright = core
    l_core = float(np.median(bright[:, 0]))
    a_core = float(np.median(bright[:, 1]))
    b_core = float(np.median(bright[:, 2]))
    return l_core, a_core, b_core


def _build_paper_probability_mask(lab_img: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """
    Builds a clean binary mask of the main document page by:
    1. Median-filtering the LAB image (ksize ~3% of min dimension) so thin ruled
       notebook lines and handwritten strokes inside the page completely vanish
       while region step-edges (page vs keyboard, page vs desk, page vs wall) remain sharp.
    2. Thresholding on paper chroma neutrality, luminance, and low step-gradient,
       plus directional step-edge barriers to prevent leaking across narrow bridges.
    3. Keeping the connected component overlapping the central document region.
    """
    h, w = lab_img.shape[:2]
    l_core, a_core, b_core = _estimate_paper_core_stats(lab_img)

    k_med = max(11, int(round(0.032 * min(h, w))) | 1)
    lab_med = cv2.medianBlur(lab_img, k_med)
    l_med = lab_med[:, :, 0].astype(np.float32)
    a_med = lab_med[:, :, 1].astype(np.float32)
    b_med = lab_med[:, :, 2].astype(np.float32)
    chroma = np.hypot(a_med - a_core, b_med - b_core)

    gx = np.abs(cv2.Sobel(l_med, cv2.CV_32F, 1, 0, ksize=3))
    gy = np.abs(cv2.Sobel(l_med, cv2.CV_32F, 0, 1, ksize=3))
    gmag = np.hypot(gx, gy)

    # Mask 1: Median-blurred low-gradient paper region (immune to ruled lines & text)
    l_min = max(92.0, l_core - 122.0)
    raw = ((l_med >= l_min) & (chroma <= 18.5) & (gmag <= 34.0)).astype(np.uint8) * 255

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(raw, connectivity=8)
    if num_labels <= 1:
        return raw

    center_box = labels[int(0.32 * h):int(0.68 * h), int(0.32 * w):int(0.68 * w)]
    valid_labels = center_box[center_box > 0]
    if len(valid_labels) == 0:
        best_label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    else:
        vals, counts = np.unique(valid_labels, return_counts=True)
        best_label = int(vals[int(np.argmax(counts))])

    core_mask = (labels == best_label).astype(np.uint8) * 255
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    core_mask = cv2.morphologyEx(core_mask, cv2.MORPH_CLOSE, k_close)
    return core_mask


def edge_support_score(quad: np.ndarray, edges: np.ndarray, num_samples: int = 24) -> float:
    """
    Measures how many sampled points along the 4 quadrilateral edges
    coincide with actual detected edge pixels in the image (within a 5x5 window).
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
        for t in np.linspace(0.08, 0.92, num_samples):
            pt = p1 + t * (p2 - p1)
            x, y = int(round(pt[0])), int(round(pt[1]))
            if 0 <= x < w and 0 <= y < h:
                total_pts += 1
                if x <= 2 or x >= w - 3 or y <= 2 or y >= h - 3:
                    hit_pts += 0.35
                    continue
                x0, x1 = max(0, x - 2), min(w, x + 3)
                y0, y1 = max(0, y - 2), min(h, y + 3)
                if np.any(edges[y0:y1, x0:x1] > 0):
                    hit_pts += 1.0
    return float(hit_pts / max(1, total_pts))


def interior_paper_purity_score(
    quad: np.ndarray,
    lab_blur: np.ndarray,
    num_samples: int = 24,
) -> float:
    """
    Verifies that the strips immediately INSIDE all 4 sides of the candidate
    quadrilateral actually consist of document paper (and NOT a dark laptop
    keyboard at the top or dark background triangles at the corners).
    """
    h, w = lab_blur.shape[:2]
    l_core, a_core, b_core = _estimate_paper_core_stats(lab_blur)
    l_min = max(96.0, l_core - 95.0)

    quad = order_points(quad).astype(np.float32)
    centroid = quad.mean(axis=0)

    side_purities = []
    for i in range(4):
        p1 = quad[i]
        p2 = quad[(i + 1) % 4]
        d = p2 - p1
        length = float(np.linalg.norm(d))
        if length < 1e-6:
            return 0.0

        # Sample at 2%, 5%, and 9% inward depths so even a thin keyboard strip near the edge is caught
        ts = np.linspace(0.05, 0.95, num_samples, dtype=np.float32)[:, None]
        edge_pts = p1[None, :] + ts * d[None, :]
        in1 = np.round(edge_pts + 0.025 * (centroid[None, :] - edge_pts)).astype(int)
        in2 = np.round(edge_pts + 0.060 * (centroid[None, :] - edge_pts)).astype(int)
        in3 = np.round(edge_pts + 0.100 * (centroid[None, :] - edge_pts)).astype(int)
        pts = np.vstack([in1, in2, in3])

        pts[:, 0] = np.clip(pts[:, 0], 0, w - 1)
        pts[:, 1] = np.clip(pts[:, 1], 0, h - 1)

        vals = lab_blur[pts[:, 1], pts[:, 0]].astype(np.float32)
        chroma = np.hypot(vals[:, 1] - a_core, vals[:, 2] - b_core)
        is_paper = (vals[:, 0] >= l_min) & (chroma <= 24.0)
        side_purities.append(float(np.mean(is_paper)))

    arr = np.array(side_purities, dtype=np.float32)
    return float(0.40 * arr.mean() + 0.60 * arr.min())


def boundary_contrast_score(
    quad: np.ndarray,
    lab_blur: np.ndarray,
    num_samples: int = 24,
) -> float:
    """
    Measures how strongly each side of the quadrilateral separates the bright
    document interior from a darker/different-colored exterior in LAB space.
    Penalizes sides that sit inside the page (where both inside and outside are paper).
    """
    h, w = lab_blur.shape[:2]
    l_core, a_core, b_core = _estimate_paper_core_stats(lab_blur)
    quad = order_points(quad).astype(np.float32)
    centroid = quad.mean(axis=0)
    offset = max(6.0, 0.016 * max(h, w))

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
            (inner[:, 0] >= 0) & (inner[:, 0] < w) &
            (inner[:, 1] >= 0) & (inner[:, 1] < h) &
            (outer[:, 0] >= 0) & (outer[:, 0] < w) &
            (outer[:, 1] >= 0) & (outer[:, 1] < h)
        )
        if np.sum(valid) < 0.5 * num_samples:
            in_clamped = np.clip(inner, [0, 0], [w - 1, h - 1])
            in_vals = lab_blur[in_clamped[:, 1], in_clamped[:, 0]].astype(np.float32)
            chroma_in = np.hypot(in_vals[:, 1] - a_core, in_vals[:, 2] - b_core)
            in_purity = float(np.mean((in_vals[:, 0] >= max(96.0, l_core - 95.0)) & (chroma_in <= 24.0)))
            side_scores.append(0.58 * in_purity)
            continue

        in_lab = lab_blur[inner[valid, 1], inner[valid, 0]].astype(np.float32)
        out_lab = lab_blur[outer[valid, 1], outer[valid, 0]].astype(np.float32)

        l_diff = in_lab[:, 0] - out_lab[:, 0]
        color_diff = np.linalg.norm(in_lab - out_lab, axis=1)

        s = np.clip((np.maximum(0.0, l_diff) * 0.65 + color_diff * 0.45) / 22.0, 0.0, 1.0)
        both_bright_same = (in_lab[:, 0] > 150) & (out_lab[:, 0] > 150) & (color_diff < 9.0)
        s[both_bright_same] *= 0.15

        side_scores.append(float(np.mean(s)))

    side_scores_arr = np.array(side_scores, dtype=np.float32)
    return float(0.65 * side_scores_arr.mean() + 0.35 * side_scores_arr.min())


def score_quad(
    quad: np.ndarray,
    img_shape: Tuple[int, int],
    edges: Optional[np.ndarray] = None,
    lab_blur: Optional[np.ndarray] = None,
) -> float:
    """
    Scores a candidate quadrilateral in [0, 1] based on:
    1. Area ratio (prefers full document over internal tables/blocks)
    2. Interior angle regularity (cosine similarity to 90 deg)
    3.Opposite side parallelism / length balance
    4. Boundary contrast (bright paper inside vs background outside)
    5. Interior paper purity (rejects quads that swallow dark keyboards or walls)
    6. Edge pixel support along the perimeter
    """
    h, w = img_shape[:2]
    img_area = float(h * w)
    area = quad_area(quad)

    area_ratio = area / max(1.0, img_area)
    if area_ratio < 0.06 or area_ratio > 0.992:
        return 0.0

    if not is_convex_quad(quad):
        return 0.0

    quad = order_points(quad)

    sides = []
    for i in range(4):
        p0 = quad[i]
        p1 = quad[(i + 1) % 4]
        sides.append(float(np.linalg.norm(p1 - p0)))
    if min(sides) < 0.08 * min(h, w):
        return 0.0

    cosines = []
    for i in range(4):
        p0 = quad[i]
        p_prev = quad[(i - 1) % 4]
        p_next = quad[(i + 1) % 4]
        v1 = p_prev - p0
        v2 = p_next - p0
        denom = (np.linalg.norm(v1) * np.linalg.norm(v2)) + 1e-6
        cos = float(np.abs(np.dot(v1, v2) / denom))
        cosines.append(cos)

    max_cos = max(cosines)
    mean_cos = float(np.mean(cosines))
    if max_cos > 0.72:
        return 0.0

    angle_score = float(np.clip(1.0 - (0.6 * mean_cos + 0.4 * max_cos) / 0.72, 0.0, 1.0))

    ratio_w = min(sides[0], sides[2]) / (max(sides[0], sides[2]) + 1e-6)
    ratio_h = min(sides[1], sides[3]) / (max(sides[1], sides[3]) + 1e-6)
    balance_score = 0.5 * (ratio_w + ratio_h)

    margin_x = 0.005 * w
    margin_y = 0.005 * h
    on_border = (
        (quad[:, 0] < margin_x) | (quad[:, 0] > (w - 1 - margin_x)) |
        (quad[:, 1] < margin_y) | (quad[:, 1] > (h - 1 - margin_y))
    )
    border_count = int(np.sum(on_border))
    border_penalty = 0.14 if (border_count == 4 and area_ratio > 0.96) else 0.0

    area_score = float(np.clip(area_ratio / 0.65, 0.0, 1.0) ** 0.55)

    if lab_blur is not None and edges is not None:
        c_score = boundary_contrast_score(quad, lab_blur)
        p_score = interior_paper_purity_score(quad, lab_blur)
        e_score = edge_support_score(quad, edges)
        composite = (
            0.22 * area_score
            + 0.24 * c_score
            + 0.26 * p_score
            + 0.14 * e_score
            + 0.08 * angle_score
            + 0.06 * balance_score
            - border_penalty
        )
    elif edges is not None:
        e_score = edge_support_score(quad, edges)
        composite = 0.40 * area_score + 0.30 * e_score + 0.20 * angle_score + 0.10 * balance_score - border_penalty
    else:
        composite = 0.60 * area_score + 0.40 * angle_score - border_penalty

    return float(max(0.0, min(1.0, composite)))


def _fit_quad_from_contour_midpoints(contour: np.ndarray, img_shape: Tuple[int, int]) -> Optional[np.ndarray]:
    """
    Fits 4 straight lines to the 4 sides (top, right, bottom, left) of a contour
    by dividing the middle 64% of each side (u in [0.18, 0.82]) into 24 bins,
    selecting the outermost contour point in each bin, and fitting an L1-robust
    line (cv2.DIST_L1). Completely immune to both rounded corners and corner spikes!
    """
    h, w = img_shape[:2]
    raw_pts = contour.reshape(-1, 2).astype(np.float32)
    if len(raw_pts) < 4:
        return None

    x, y, cw, ch = cv2.boundingRect(raw_pts)
    if cw < 0.15 * w or ch < 0.15 * h:
        return None

    # Densely resample the contour perimeter every ~2 pixels
    dense_pts = []
    n_v = len(raw_pts)
    for i in range(n_v):
        p1 = raw_pts[i]
        p2 = raw_pts[(i + 1) % n_v]
        dist = float(np.linalg.norm(p2 - p1))
        n_steps = max(1, int(round(dist / 2.0)))
        ts = np.linspace(0.0, 1.0, n_steps, endpoint=False, dtype=np.float32)[:, None]
        seg = p1[None, :] + ts * (p2 - p1)[None, :]
        dense_pts.append(seg)
    pts = np.vstack(dense_pts)
    if len(pts) < 20:
        return None

    rect_box = order_points(cv2.boxPoints(cv2.minAreaRect(raw_pts)))
    side_fitted_lines = []

    for i in range(4):
        b1 = rect_box[i]
        b2 = rect_box[(i + 1) % 4]
        d = b2 - b1
        side_len = float(np.linalg.norm(d))
        if side_len < 15.0:
            return None
        t_unit = d / side_len
        n_unit = np.array([-t_unit[1], t_unit[0]], dtype=np.float32)

        rel = pts - b1[None, :]
        u_proj = (rel @ t_unit) / side_len
        v_perp = np.abs(rel @ n_unit)

        # Sample 24 bins across the middle 64% of this side (u in [0.18, 0.82])
        # and take the outermost contour point (minimum v_perp) in each bin
        bins = np.linspace(0.18, 0.82, 25)
        bin_pts = []
        max_perp = 0.22 * min(cw, ch)
        for b_idx in range(24):
            in_bin = (u_proj >= bins[b_idx]) & (u_proj < bins[b_idx + 1]) & (v_perp <= max_perp)
            if np.any(in_bin):
                cand = pts[in_bin]
                cand_v = v_perp[in_bin]
                bin_pts.append(cand[int(np.argmin(cand_v))])

        if len(bin_pts) < 6:
            return None
        side_pts = np.array(bin_pts, dtype=np.float32)

        line = cv2.fitLine(side_pts, cv2.DIST_L1, 0, 0.01, 0.01).flatten()
        vx, vy, x0, y0 = float(line[0]), float(line[1]), float(line[2]), float(line[3])
        side_fitted_lines.append((x0, y0, x0 + vx * 100.0, y0 + vy * 100.0))

    def _intersect(l1, l2):
        x1, y1, x2, y2 = l1
        x3, y3, x4, y4 = l2
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-6:
            return None
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        px = x1 + t * (x2 - x1)
        py = y1 + t * (y2 - y1)
        return np.array([np.clip(px, 0, w - 1), np.clip(py, 0, h - 1)], dtype=np.float32)

    lt, lr, lb, ll = side_fitted_lines
    tl = _intersect(lt, ll)
    tr = _intersect(lt, lr)
    br = _intersect(lb, lr)
    bl = _intersect(lb, ll)
    if any(p is None for p in (tl, tr, br, bl)):
        return None

    quad = np.array([tl, tr, br, bl], dtype=np.float32)
    if is_convex_quad(quad):
        return quad
    return None


def extract_candidate_quads(contour: np.ndarray, img_shape: Tuple[int, int]) -> List[Tuple[np.ndarray, str, float]]:
    """
    Extracts multiple candidate quadrilaterals from a single contour using:
    1. Midpoint-fitted tangent intersection (immune to rounded corners & curved edges)
    2. Progressive approxPolyDP
    3. Convex Hull approximation
    4. Maximum inscribed quad area from convex hull
    5. Rotated bounding box (minAreaRect)
    """
    peri = cv2.arcLength(contour, True)
    if peri < 80:
        return []
    candidates = []

    # 1. Midpoint tangent fit on hull (solves rounded notebook corners and curved edges!)
    mid_q = _fit_quad_from_contour_midpoints(contour, img_shape)
    if mid_q is not None:
        candidates.append((mid_q, "midpoint_fit", 1.15))

    # 2. Direct approxPolyDP with progressive epsilon
    for eps in [0.015, 0.02, 0.025, 0.03, 0.04]:
        approx = cv2.approxPolyDP(contour, eps * peri, True)
        if len(approx) == 4 and is_convex_quad(approx):
            candidates.append((approx.reshape(4, 2).astype(np.float32), f"approx_{eps:.3f}", 1.12))
            break

    # 3. Convex Hull approximation
    hull = cv2.convexHull(contour)
    hull_peri = cv2.arcLength(hull, True)
    for eps in [0.015, 0.02, 0.025, 0.03, 0.04]:
        approx_h = cv2.approxPolyDP(hull, eps * hull_peri, True)
        if len(approx_h) == 4 and is_convex_quad(approx_h):
            candidates.append((approx_h.reshape(4, 2).astype(np.float32), f"hull_{eps:.3f}", 1.10))
            break

    # 4. 4-point maximum area convex subset from convex hull
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

    # 5. minAreaRect bounding box fallback
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect).astype(np.float32)
    candidates.append((box, "minAreaRect", 0.98))

    return candidates


def _trim_non_paper_borders(
    quad: np.ndarray,
    paper_mask: np.ndarray,
    lab_blur: np.ndarray,
    edges: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    1. If any side of the quadrilateral overshoots into a non-paper region (such as
       a laptop keyboard at the top), marches that side inward until its interior
       strip sits on actual paper.
    2. If a side lies on the image frame border (e.g. x=0 in fail1_curved where a
       narrow white wall strip touches the left border) and there is a strong internal
       parallel boundary edge within 12% of the span where the outer strip lacks
       perpendicular top/bottom contrast, snaps the side to that internal boundary edge.
    """
    h, w = paper_mask.shape[:2]
    l_core, a_core, b_core = _estimate_paper_core_stats(lab_blur)
    l_min = max(95.0, l_core - 95.0)

    quad = order_points(quad).copy()
    opp_pairs = [
        (0, 1, 3, 2),  # Top moves toward (BL, BR)
        (1, 2, 0, 3),  # Right moves toward (TL, BL)
        (2, 3, 1, 0),  # Bottom moves toward (TR, TL)
        (3, 0, 2, 1),  # Left moves toward (BR, TR)
    ]

    # Step 1: Trim non-paper borders (e.g. dark keyboard strip at top)
    for c1, c2, o1, o2 in opp_pairs:
        p1, p2 = quad[c1].copy(), quad[c2].copy()
        q1, q2 = quad[o1].copy(), quad[o2].copy()
        for alpha in np.linspace(0.0, 0.30, 31):
            cur1 = p1 + alpha * (q1 - p1)
            cur2 = p2 + alpha * (q2 - p2)
            in1 = cur1 + 0.015 * (q1 - cur1)
            in2 = cur2 + 0.015 * (q2 - cur2)
            ts = np.linspace(0.08, 0.92, 20, dtype=np.float32)[:, None]
            pts = np.round(in1[None, :] + ts * (in2 - in1)[None, :]).astype(int)
            pts[:, 0] = np.clip(pts[:, 0], 0, w - 1)
            pts[:, 1] = np.clip(pts[:, 1], 0, h - 1)

            vals = lab_blur[pts[:, 1], pts[:, 0]].astype(np.float32)
            chroma = np.hypot(vals[:, 1] - a_core, vals[:, 2] - b_core)
            pm = paper_mask[pts[:, 1], pts[:, 0]] > 0
            valid_paper = ((vals[:, 0] >= l_min) & (chroma <= 22.0)) | pm
            if np.mean(valid_paper) >= 0.80:
                quad[c1] = cur1
                quad[c2] = cur2
                break

    # Step 2: Check border-hugging sides for a true physical step-edge slightly inside (up to 13%)
    for c1, c2, o1, o2 in opp_pairs:
        p1, p2 = quad[c1].copy(), quad[c2].copy()
        q1, q2 = quad[o1].copy(), quad[o2].copy()
        on_b1 = (p1[0] <= 4) or (p1[0] >= w - 5) or (p1[1] <= 4) or (p1[1] >= h - 5)
        on_b2 = (p2[0] <= 4) or (p2[0] >= w - 5) or (p2[1] <= 4) or (p2[1] >= h - 5)
        if not (on_b1 and on_b2):
            continue

        # Check if the adjacent sides near p1 and p2 lack contrast (meaning the border strip is a background wall)
        mid_strip1 = p1 + 0.04 * (q1 - p1)
        d_adj1 = q1 - p1
        len_adj1 = float(np.linalg.norm(d_adj1))
        if len_adj1 < 20.0:
            continue
        n_adj1 = np.array([-d_adj1[1], d_adj1[0]], dtype=np.float32) / len_adj1
        pt_in = np.clip(np.round(mid_strip1 + 6.0 * n_adj1).astype(int), [0, 0], [w - 1, h - 1])
        pt_out = np.clip(np.round(mid_strip1 - 6.0 * n_adj1).astype(int), [0, 0], [w - 1, h - 1])
        diff_adj = float(np.linalg.norm(lab_blur[pt_in[1], pt_in[0]].astype(np.float32) - lab_blur[pt_out[1], pt_out[0]].astype(np.float32)))
        if diff_adj > 12.0:
            continue

        # Search alpha in [0.04, 0.13] for a genuine step-edge (|L_in - L_out| at +-5px)
        # Note: thin ruled lines have |L_in - L_out| ~ 0 at +-5px, so they are 100% ignored!
        best_alpha = 0.0
        best_step = 14.0
        for alpha in np.linspace(0.04, 0.13, 19):
            cur1 = p1 + alpha * (q1 - p1)
            cur2 = p2 + alpha * (q2 - p2)
            in_pts1 = p1 + (alpha + 0.018) * (q1 - p1)
            in_pts2 = p2 + (alpha + 0.018) * (q2 - p2)
            out_pts1 = p1 + (alpha - 0.018) * (q1 - p1)
            out_pts2 = p2 + (alpha - 0.018) * (q2 - p2)
            ts = np.linspace(0.10, 0.90, 20, dtype=np.float32)[:, None]
            p_in = np.clip(np.round(in_pts1[None, :] + ts * (in_pts2 - in_pts1)[None, :]).astype(int), [0, 0], [w - 1, h - 1])
            p_out = np.clip(np.round(out_pts1[None, :] + ts * (out_pts2 - out_pts1)[None, :]).astype(int), [0, 0], [w - 1, h - 1])
            l_in = lab_blur[p_in[:, 1], p_in[:, 0], 0].astype(np.float32)
            l_out = lab_blur[p_out[:, 1], p_out[:, 0], 0].astype(np.float32)
            step_val = float(np.mean(np.abs(l_in - l_out)))
            if step_val > best_step:
                best_step = step_val
                best_alpha = float(alpha)

        if best_alpha > 0.0:
            quad[c1] = p1 + best_alpha * (q1 - p1)
            quad[c2] = p2 + best_alpha * (q2 - p2)

    return quad


def extract_multipoint_boundary(
    quad: np.ndarray,
    paper_mask: np.ndarray,
    edges: np.ndarray,
    num_points: int = 8,
) -> np.ndarray:
    """
    Upgrades a 4-corner quadrilateral [TL, TR, BR, BL] into an N-point curved
    page boundary (N = 4, 6, 8, or 12) by casting normal rays at the edge
    midpoints / third-points to snap onto curved notebook edges.

    Point ordering (clockwise starting at TL):
    - 4 points:  [TL, TR, BR, BL]
    - 6 points:  [TL, TM, TR, BR, BM, BL] (midpoints on Top & Bottom)
    - 8 points:  [TL, TM, TR, RM, BR, BM, BL, LM] (4 corners + 4 midpoints)
    - 12 points: [TL, T1, T2, TR, R1, R2, BR, B1, B2, BL, L1, L2] (4 corners + 8 third-points)
    """
    quad = order_points(quad).astype(np.float32)
    if num_points <= 4:
        return quad

    h, w = paper_mask.shape[:2]
    centroid = quad.mean(axis=0)

    def _snap_edge_point(p1: np.ndarray, p2: np.ndarray, t: float) -> np.ndarray:
        """
        Casts a normal ray at fraction `t` along segment (p1 -> p2) from inside
        the page (-8% of side length) to outside (+8% of side length) and snaps
        to the true paper-mask boundary / edge transition.
        """
        base = p1 + t * (p2 - p1)
        d = p2 - p1
        length = float(np.linalg.norm(d))
        if length < 20.0:
            return base

        # If both endpoints lie on the same image border, keep the midpoint on the border
        if (
            (p1[0] <= 2 and p2[0] <= 2) or
            (p1[0] >= w - 3 and p2[0] >= w - 3) or
            (p1[1] <= 2 and p2[1] <= 2) or
            (p1[1] >= h - 3 and p2[1] >= h - 3)
        ):
            return base

        n_out = np.array([-d[1], d[0]], dtype=np.float32) / length
        if np.dot(base - centroid, n_out) < 0:
            n_out = -n_out

        max_shift = min(40.0, 0.08 * length)
        steps = np.linspace(-max_shift, max_shift, 41, dtype=np.float32)
        ray_pts = base[None, :] + steps[:, None] * n_out[None, :]
        xs = np.clip(np.round(ray_pts[:, 0]).astype(int), 0, w - 1)
        ys = np.clip(np.round(ray_pts[:, 1]).astype(int), 0, h - 1)

        pm = (paper_mask[ys, xs] > 0).astype(np.float32)
        best_s = 0.0
        best_weight = 0.0
        for idx in range(3, len(steps) - 3):
            in_val = float(np.mean(pm[max(0, idx - 3):idx + 1]))
            out_val = float(np.mean(pm[idx + 1:min(len(steps), idx + 4)]))
            trans = in_val - out_val
            has_edge = 1.0 if edges[ys[idx], xs[idx]] > 0 else 0.0
            prox = 1.0 - 0.35 * (abs(steps[idx]) / (max_shift + 1e-5))
            w_score = (trans + 0.35 * has_edge) * prox
            if trans >= 0.45 and w_score > best_weight:
                best_weight = w_score
                best_s = float(steps[idx])

        snapped = base + best_s * n_out
        snapped[0] = np.clip(snapped[0], 0, w - 1)
        snapped[1] = np.clip(snapped[1], 0, h - 1)
        return snapped

    tl, tr, br, bl = quad
    sides = [(tl, tr), (tr, br), (br, bl), (bl, tl)]

    if num_points == 6:
        tm = _snap_edge_point(tl, tr, 0.5)
        bm = _snap_edge_point(br, bl, 0.5)
        return np.array([tl, tm, tr, br, bm, bl], dtype=np.float32)
    elif num_points == 12:
        pts_12 = []
        for p1, p2 in sides:
            pts_12.append(p1)
            pts_12.append(_snap_edge_point(p1, p2, 1.0 / 3.0))
            pts_12.append(_snap_edge_point(p1, p2, 2.0 / 3.0))
        return np.array(pts_12, dtype=np.float32)
    else:
        pts_8 = []
        for p1, p2 in sides:
            pts_8.append(p1)
            pts_8.append(_snap_edge_point(p1, p2, 0.5))
        return np.array(pts_8, dtype=np.float32)


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
    """Otsu paper mask with progressive closing kernels."""
    _, otsu = cv2.threshold(gray_clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    otsu_mask = otsu if np.mean(otsu) < 160 else cv2.bitwise_not(otsu)

    return [
        cv2.morphologyEx(
            otsu_mask, cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11)),
        ),
        cv2.morphologyEx(
            otsu_mask, cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_RECT, (21, 21)),
        ),
    ]


def _channel_hsv_paper(img_bgr: np.ndarray) -> list[np.ndarray]:
    """Color-based paper segmentation via HSV (low saturation, high value)."""
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 17))
    k_open = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))

    strict = ((hsv[:, :, 1] < 45) & (hsv[:, :, 2] > 155)).astype(np.uint8) * 255
    strict_o = cv2.morphologyEx(cv2.morphologyEx(strict, cv2.MORPH_CLOSE, k_close), cv2.MORPH_OPEN, k_open)

    relaxed = ((hsv[:, :, 1] < 60) & (hsv[:, :, 2] > 125)).astype(np.uint8) * 255
    relaxed_o = cv2.morphologyEx(cv2.morphologyEx(relaxed, cv2.MORPH_CLOSE, k_close), cv2.MORPH_OPEN, k_open)

    return [strict_o, relaxed_o]


def _channel_lab_paper(img_bgr: np.ndarray) -> list[np.ndarray]:
    """LAB L-channel paper segmentation across multiple luminance thresholds."""
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l_ch = lab[:, :, 0]
    k_close = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 17))
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
    boundary_resized: Optional[np.ndarray] = None,
) -> dict:
    """Generates visual debug images showing both corner and midpoint anchors."""
    debug = {}
    debug["gray"] = intermediates.get("gray")
    debug["edges"] = intermediates.get("edges")
    debug["edges_closed"] = intermediates.get("edges_closed")

    overlay = img_bgr.copy()
    poly_to_draw = boundary_resized if boundary_resized is not None else quad_resized
    if poly_to_draw is not None:
        pts = poly_to_draw.reshape(-1, 1, 2).astype(np.int32)
        cv2.polylines(overlay, [pts], True, (0, 255, 0), max(2, int(img_bgr.shape[1] / 300)))

        r_mid = max(5, int(img_bgr.shape[1] / 180))
        for (x, y) in poly_to_draw:
            cv2.circle(overlay, (int(x), int(y)), r_mid, (0, 180, 255), -1)

    if quad_resized is not None:
        quad_ord = order_points(quad_resized)
        labels = ["TL", "TR", "BR", "BL"]
        r_corner = max(7, int(img_bgr.shape[1] / 140))
        for (x, y), lab in zip(quad_ord, labels):
            cv2.circle(overlay, (int(x), int(y)), r_corner, (0, 0, 255), -1)
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
    num_points: int = 8,
) -> DetectionResult:
    """
    Robust multi-strategy document boundary detector supporting 4, 6, 8, or 12 points.
    Combines:
    1. Median-blurred step-barrier paper segmentation (immune to ruled lines & text)
    2. Convex-hull midpoint tangent line intersections (handles rounded notebook corners)
    3. Inside/outside LAB boundary contrast + interior paper purity verification
    4. Normal ray-casting along the 4 sides to extract 6, 8, or 12 curved-edge anchor points
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

    lab_raw = cv2.cvtColor(img_resized, cv2.COLOR_BGR2LAB)
    lab_blur = cv2.GaussianBlur(lab_raw, (7, 7), 0)
    core_paper_mask = _build_paper_probability_mask(lab_raw, combined_edges)

    all_masks: list[tuple[np.ndarray, int]] = [(core_paper_mask, cv2.RETR_EXTERNAL)]
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

    all_contours = sorted(all_contours, key=cv2.contourArea, reverse=True)[:35]

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
        return DetectionResult(
            corners=corners_original,
            score=score,
            method=method_used,
            debug=dbg,
            boundary_points=None,
        )

    best_quad_trimmed = _trim_non_paper_borders(best_quad, core_paper_mask, lab_blur, combined_edges)
    best_quad_ord = order_points(best_quad_trimmed)

    boundary_resized = extract_multipoint_boundary(
        best_quad_ord, core_paper_mask, combined_edges, num_points=num_points
    )

    corners_original = (best_quad_ord / scale).astype(np.float32)
    boundary_original = (boundary_resized / scale).astype(np.float32)

    dbg = draw_debug(
        img_resized, inter, best_quad_ord, scale, best_method, best_score,
        boundary_resized=boundary_resized,
    )
    if debug_dir:
        save_debug_images(debug_dir, dbg)

    return DetectionResult(
        corners=corners_original,
        score=best_score,
        method=best_method,
        debug=dbg,
        boundary_points=boundary_original,
    )
