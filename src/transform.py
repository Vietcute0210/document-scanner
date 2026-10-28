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


def warp_from_result(
    img_bgr: np.ndarray,
    result: DetectionResult,
    min_width: int = 1600,
) -> Optional[np.ndarray]:
    """
    Deskewed document image from DetectionResult, or None if no corners were detected.
    """
    if result.corners is None:
        return None
    return four_point_transform(img_bgr, result.corners, min_width=min_width)
