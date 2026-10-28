from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from .detect_page import order_points, DetectionResult


def four_point_transform(image: np.ndarray, pts: np.ndarray, min_width: int = 1600) -> np.ndarray:
    """
    Applies a 4-point perspective transform to deskew a document quadrilateral.
    Uses Lanczos-4 interpolation and upscales to at least `min_width` pixels
    (default 1600px) so fine handwritten strokes remain sharp and high-resolution.
    """
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = int(max(heightA, heightB))

    target_w = max(maxWidth, min_width)
    target_h = int(round(target_w * float(maxHeight) / float(max(1, maxWidth))))

    dst = np.array([
        [0,            0           ],
        [target_w - 1, 0           ],
        [target_w - 1, target_h - 1],
        [0,            target_h - 1],
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (target_w, target_h), flags=cv2.INTER_LANCZOS4)
    return warped


def _edge_chord_deviation(side_pts: np.ndarray, t: np.ndarray) -> np.ndarray:
    """
    Computes the smooth Lagrange polynomial deviation Delta(t) from the straight
    chord (P_start -> P_end) for parameter array `t` in [0, 1].
    - If `side_pts` has 3 points [P0, P_mid, P1]: quadratic Lagrange deviation.
    - If `side_pts` has 4 points [P0, P_1/3, P_2/3, P1]: cubic Lagrange deviation.
    Returns shape (len(t), 2).
    """
    t = np.asarray(t, dtype=np.float32)[:, None]
    p0 = side_pts[0][None, :]
    p1 = side_pts[-1][None, :]

    if len(side_pts) == 3:
        pmid = side_pts[1][None, :]
        d_mid = pmid - 0.5 * (p0 + p1)
        return 4.0 * t * (1.0 - t) * d_mid
    elif len(side_pts) == 4:
        p_a = side_pts[1][None, :]
        p_b = side_pts[2][None, :]
        d_a = p_a - ((2.0 / 3.0) * p0 + (1.0 / 3.0) * p1)
        d_b = p_b - ((1.0 / 3.0) * p0 + (2.0 / 3.0) * p1)
        l1 = 13.5 * t * (1.0 - t) * ((2.0 / 3.0) - t)
        l2 = 13.5 * t * (1.0 - t) * (t - (1.0 / 3.0))
        return l1 * d_a + l2 * d_b
    else:
        return np.zeros((len(t), 2), dtype=np.float32)


def _unpack_sides(boundary_pts: np.ndarray) -> tuple[np.ndarray, list[np.ndarray]]:
    """
    Unpacks 4, 6, 8, or 12 clockwise boundary points into:
      - corners: (4, 2) [TL, TR, BR, BL]
      - sides: [top_pts, right_pts, bottom_pts, left_pts] in clockwise order
        (TL->TR, TR->BR, BR->BL, BL->TL)
    """
    pts = np.asarray(boundary_pts, dtype=np.float32).reshape(-1, 2)
    n = len(pts)
    if n == 6:
        # [TL, TM, TR, BR, BM, BL]
        tl, tm, tr, br, bm, bl = pts
        rm = 0.5 * (tr + br)
        lm = 0.5 * (bl + tl)
        corners = np.array([tl, tr, br, bl], dtype=np.float32)
        sides = [
            np.array([tl, tm, tr], dtype=np.float32),
            np.array([tr, rm, br], dtype=np.float32),
            np.array([br, bm, bl], dtype=np.float32),
            np.array([bl, lm, tl], dtype=np.float32),
        ]
        return corners, sides
    elif n == 8:
        # [TL, TM, TR, RM, BR, BM, BL, LM]
        tl, tm, tr, rm, br, bm, bl, lm = pts
        corners = np.array([tl, tr, br, bl], dtype=np.float32)
        sides = [
            np.array([tl, tm, tr], dtype=np.float32),
            np.array([tr, rm, br], dtype=np.float32),
            np.array([br, bm, bl], dtype=np.float32),
            np.array([bl, lm, tl], dtype=np.float32),
        ]
        return corners, sides
    elif n == 12:
        # [TL, T1, T2, TR, R1, R2, BR, B1, B2, BL, L1, L2]
        tl, t1, t2, tr, r1, r2, br, b1, b2, bl, l1, l2 = pts
        corners = np.array([tl, tr, br, bl], dtype=np.float32)
        sides = [
            np.array([tl, t1, t2, tr], dtype=np.float32),
            np.array([tr, r1, r2, br], dtype=np.float32),
            np.array([br, b1, b2, bl], dtype=np.float32),
            np.array([bl, l1, l2, tl], dtype=np.float32),
        ]
        return corners, sides
    else:
        corners = order_points(pts[:4])
        tl, tr, br, bl = corners
        sides = [
            np.array([tl, tr], dtype=np.float32),
            np.array([tr, br], dtype=np.float32),
            np.array([br, bl], dtype=np.float32),
            np.array([bl, tl], dtype=np.float32),
        ]
        return corners, sides


def sample_curved_boundary(boundary_pts: np.ndarray, samples_per_side: int = 24) -> np.ndarray:
    """
    Samples a smooth closed contour along the 4 curved Coons-patch sides for
    rendering on UI overlays. Returns shape (4 * samples_per_side, 2).
    """
    _, sides = _unpack_sides(boundary_pts)
    t = np.linspace(0.0, 1.0, samples_per_side, endpoint=False, dtype=np.float32)
    curve_pts = []
    for side in sides:
        p0 = side[0][None, :]
        p1 = side[-1][None, :]
        chord = (1.0 - t[:, None]) * p0 + t[:, None] * p1
        dev = _edge_chord_deviation(side, t)
        curve_pts.append(chord + dev)
    return np.vstack(curve_pts).astype(np.float32)


def multi_point_warp(
    image: np.ndarray,
    boundary_pts: np.ndarray,
    min_width: int = 1600,
    grid_size: int = 65,
) -> np.ndarray:
    """
    Perspective-Corrected Coons-Patch Mesh Warp for 4, 6, 8, or 12 boundary points.
    Combines exact 4-corner projective homography with smooth transfinite Coons
    interpolation of curved page boundaries, eliminating page-curl distortion
    while keeping text lines straight and sharp via Lanczos-4 remapping.
    """
    pts = np.asarray(boundary_pts, dtype=np.float32).reshape(-1, 2)
    if len(pts) <= 4:
        return four_point_transform(image, pts, min_width=min_width)

    corners, sides = _unpack_sides(pts)
    tl, tr, br, bl = corners

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = int(max(widthA, widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = int(max(heightA, heightB))

    target_w = max(maxWidth, min_width)
    target_h = int(round(target_w * float(maxHeight) / float(max(1, maxWidth))))

    # 1. Base 4-corner projective homography on a coarse (grid_size x grid_size) mesh
    u = np.linspace(0.0, 1.0, grid_size, dtype=np.float32)
    v = np.linspace(0.0, 1.0, grid_size, dtype=np.float32)
    uu, vv = np.meshgrid(u, v)

    unit_sq = np.array([
        [0.0, 0.0],
        [1.0, 0.0],
        [1.0, 1.0],
        [0.0, 1.0],
    ], dtype=np.float32)
    H = cv2.getPerspectiveTransform(unit_sq, corners)
    uv_pts = np.stack([uu.ravel(), vv.ravel()], axis=-1).reshape(-1, 1, 2)
    base_mesh = cv2.perspectiveTransform(uv_pts, H).reshape(grid_size, grid_size, 2)

    # 2. Boundary chord deviations along Top (u), Right (v), Bottom (1-u), Left (1-v)
    top_side, right_side, bottom_side, left_side = sides
    dev_top = _edge_chord_deviation(top_side, u)          # (G, 2), left-to-right (u)
    dev_right = _edge_chord_deviation(right_side, v)      # (G, 2), top-to-bottom (v)
    dev_bottom = _edge_chord_deviation(bottom_side, 1.0 - u)  # (G, 2), left-to-right (u)
    dev_left = _edge_chord_deviation(left_side, 1.0 - v)      # (G, 2), top-to-bottom (v)

    # 3. Transfinite Coons patch blending of boundary deviations
    # (grid_size, grid_size, 2)
    vv_3 = vv[:, :, None]
    uu_3 = uu[:, :, None]
    coons_offset = (
        (1.0 - vv_3) * dev_top[None, :, :]
        + vv_3 * dev_bottom[None, :, :]
        + (1.0 - uu_3) * dev_left[:, None, :]
        + uu_3 * dev_right[:, None, :]
    )

    coarse_map = (base_map := base_mesh + coons_offset).astype(np.float32)

    # 4. Upsample smooth displacement field to full resolution (target_w x target_h)
    map_x = cv2.resize(coarse_map[:, :, 0], (target_w, target_h), interpolation=cv2.INTER_CUBIC)
    map_y = cv2.resize(coarse_map[:, :, 1], (target_w, target_h), interpolation=cv2.INTER_CUBIC)

    warped = cv2.remap(
        image,
        map_x,
        map_y,
        interpolation=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return warped


def warp_from_result(
    img_bgr: np.ndarray,
    result: DetectionResult,
    min_width: int = 1600,
) -> Optional[np.ndarray]:
    """
    Deskewed & un-curved document image from DetectionResult, or None if no corners were detected.
    Uses multi-point Coons-patch mesh warping when boundary_points (>4) are present.
    """
    if result.corners is None:
        return None
    if result.boundary_points is not None and len(result.boundary_points) > 4:
        return multi_point_warp(img_bgr, result.boundary_points, min_width=min_width)
    return four_point_transform(img_bgr, result.corners, min_width=min_width)
