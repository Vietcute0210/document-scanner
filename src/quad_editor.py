from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np
import streamlit.components.v1 as components

from .geometry import is_convex_quad, clamp_quad


_COMPONENT_DIR = Path(__file__).parent / "components" / "quad_editor"
_quad_editor_raw = components.declare_component("quad_editor", path=str(_COMPONENT_DIR))


def render_quad_editor(
    image_bgr: np.ndarray,
    corners: np.ndarray,
    auto_corners: Optional[np.ndarray] = None,
    is_manual: bool = False,
    key: str = "quad_editor_widget",
    display_max_dim: int = 1000,
) -> Tuple[np.ndarray, bool]:
    """
    Renders an interactive HTML5 Canvas quad editor inside Streamlit.
    Allows users to drag individual corner handles (red dots) or drag full straight
    edges (orange midpoints) with live magnification and convexity enforcement.

    Parameters:
      image_bgr: Source OpenCV image in BGR format.
      corners: (4, 2) array of [TL, TR, BR, BL] coordinates currently active.
      auto_corners: (4, 2) array of original auto-detected corners for reset action.
      is_manual: Whether current quad was manually positioned by user.
      key: Streamlit widget key.
      display_max_dim: Maximum dimension for base64 display compression.

    Returns:
      (active_corners, is_manual) where active_corners is (4, 2) float32 in original image coordinates.
    """
    orig_h, orig_w = image_bgr.shape[:2]
    pts = np.asarray(corners, dtype=np.float32).reshape(4, 2)
    auto_pts = np.asarray(auto_corners if auto_corners is not None else pts, dtype=np.float32).reshape(4, 2)

    # 1. Prepare display thumbnail for high-speed base64 streaming
    scale = 1.0
    if max(orig_w, orig_h) > display_max_dim:
        scale = float(display_max_dim) / float(max(orig_w, orig_h))
        disp_w = int(round(orig_w * scale))
        disp_h = int(round(orig_h * scale))
        disp_img = cv2.resize(image_bgr, (disp_w, disp_h), interpolation=cv2.INTER_AREA)
    else:
        disp_img = image_bgr

    # JPEG encode with balanced compression
    success, buffer = cv2.imencode(".jpg", disp_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not success:
        b64_str = ""
    else:
        b64_str = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

    # Generate a lightweight unique hash for this image instance
    img_sample = image_bgr[::max(1, orig_h // 30), ::max(1, orig_w // 30)]
    edit_id = hashlib.md5(img_sample.tobytes()).hexdigest()[:12]

    # 2. Invoke component
    res = _quad_editor_raw(
        image=b64_str,
        orig_width=orig_w,
        orig_height=orig_h,
        corners=pts.tolist(),
        auto_corners=auto_pts.tolist(),
        is_manual=is_manual,
        edit_id=edit_id,
        key=key,
        default=None,
    )

    # 3. Process return value
    if res is not None and isinstance(res, dict) and "corners" in res:
        returned_pts = np.asarray(res["corners"], dtype=np.float32).reshape(4, 2)
        # Validate returned points
        returned_pts = clamp_quad(returned_pts, float(orig_w), float(orig_h))
        if is_convex_quad(returned_pts, min_area=0.01 * orig_w * orig_h):
            return returned_pts, bool(res.get("is_manual", True))

    return pts, is_manual
