from __future__ import annotations

from typing import Optional, Tuple
import numpy as np


def line_intersection(
    p1: np.ndarray | tuple[float, float],
    p2: np.ndarray | tuple[float, float],
    p3: np.ndarray | tuple[float, float],
    p4: np.ndarray | tuple[float, float],
    eps: float = 1e-6,
) -> Optional[np.ndarray]:
    """
    Computes the intersection of line (p1 -> p2) and line (p3 -> p4).
    Returns (x, y) as float32 np.ndarray, or None if lines are parallel.
    """
    x1, y1 = float(p1[0]), float(p1[1])
    x2, y2 = float(p2[0]), float(p2[1])
    x3, y3 = float(p3[0]), float(p3[1])
    x4, y4 = float(p4[0]), float(p4[1])

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < eps:
        return None

    term1 = x1 * y2 - y1 * x2
    term2 = x3 * y4 - y3 * x4

    px = (term1 * (x3 - x4) - (x1 - x2) * term2) / denom
    py = (term1 * (y3 - y4) - (y1 - y2) * term2) / denom
    return np.array([px, py], dtype=np.float32)


def is_convex_quad(pts: np.ndarray, min_area: float = 100.0) -> bool:
    """
    Checks if 4 points form a strictly convex quadrilateral with sufficient area
    and no self-intersections. Expected order: [TL, TR, BR, BL] clockwise.
    """
    pts = np.asarray(pts, dtype=np.float32).reshape(4, 2)

    # 1. Check Shoelace area
    x = pts[:, 0]
    y = pts[:, 1]
    shoelace = 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    if abs(shoelace) < min_area:
        return False

    # 2. Check cross products for convexity (all 4 must have the same sign)
    signs = []
    for i in range(4):
        p0 = pts[i]
        p1 = pts[(i + 1) % 4]
        p2 = pts[(i + 2) % 4]

        v1 = p1 - p0
        v2 = p2 - p1
        cross = float(v1[0] * v2[1] - v1[1] * v2[0])
        if abs(cross) < 1e-4:
            return False  # Collinear points are invalid
        signs.append(cross > 0)

    # All must match (either all clockwise or all counter-clockwise)
    return len(set(signs)) == 1


def clamp_quad(pts: np.ndarray, width: float, height: float, margin: float = 0.0) -> np.ndarray:
    """
    Clamps all quad vertices within the bounding box [margin, width - margin].
    """
    clamped = np.asarray(pts, dtype=np.float32).copy().reshape(4, 2)
    clamped[:, 0] = np.clip(clamped[:, 0], margin, max(margin, width - margin))
    clamped[:, 1] = np.clip(clamped[:, 1], margin, max(margin, height - margin))
    return clamped


def move_edge(
    quad: np.ndarray,
    edge_idx: int,
    delta: Tuple[float, float],
    img_shape: Optional[Tuple[int, int]] = None,
) -> np.ndarray:
    """
    Translates an edge of the quad by (delta_x, delta_y).
    Maintains straight adjacent lines: the two new endpoints of the edge are
    computed as the intersections of the translated edge line with the two
    adjacent edge lines (like Adobe Scan / MS Lens).

    edge_idx:
      0: Top edge (TL -> TR, vertex 0 to vertex 1)
      1: Right edge (TR -> BR, vertex 1 to vertex 2)
      2: Bottom edge (BR -> BL, vertex 2 to vertex 3)
      3: Left edge (BL -> TL, vertex 3 to vertex 0)

    Returns a new (4, 2) quad. If the result is degenerate or non-convex,
    the original quad is preserved.
    """
    pts = np.asarray(quad, dtype=np.float32).copy().reshape(4, 2)
    dx, dy = float(delta[0]), float(delta[1])
    if abs(dx) < 1e-5 and abs(dy) < 1e-5:
        return pts

    i_start = edge_idx % 4
    i_end = (edge_idx + 1) % 4
    i_prev = (edge_idx - 1) % 4
    i_next = (edge_idx + 2) % 4

    p_prev = pts[i_prev]
    p_start = pts[i_start]
    p_end = pts[i_end]
    p_next = pts[i_next]

    d_vec = np.array([dx, dy], dtype=np.float32)
    # Translated edge line points
    p_start_trans = p_start + d_vec
    p_end_trans = p_end + d_vec

    # Intersect translated edge line with prev adjacent line (p_prev -> p_start)
    new_start = line_intersection(p_start_trans, p_end_trans, p_prev, p_start)
    # Intersect translated edge line with next adjacent line (p_end -> p_next)
    new_end = line_intersection(p_start_trans, p_end_trans, p_end, p_next)

    # Check bounds or fallback if parallel / near infinite intersection
    diag_limit = 5.0
    if img_shape is not None:
        h, w = img_shape[:2]
        diag_limit = 2.0 * float(np.hypot(w, h))

    valid = True
    if new_start is None or new_end is None:
        valid = False
    else:
        # Distance checks from original to prevent astronomical jumps
        if (
            np.linalg.norm(new_start - p_start) > diag_limit
            or np.linalg.norm(new_end - p_end) > diag_limit
        ):
            valid = False

    candidate = pts.copy()
    if valid and new_start is not None and new_end is not None:
        candidate[i_start] = new_start
        candidate[i_end] = new_end
    else:
        # Fallback: rigid translation of both endpoints
        candidate[i_start] = p_start + d_vec
        candidate[i_end] = p_end + d_vec

    if img_shape is not None:
        h, w = img_shape[:2]
        candidate = clamp_quad(candidate, float(w), float(h))

    # Verify convexity and minimum size
    min_area = 200.0
    if img_shape is not None:
        min_area = 0.01 * float(img_shape[0] * img_shape[1])

    if is_convex_quad(candidate, min_area=min_area):
        return candidate

    return pts  # Reject invalid deformation
