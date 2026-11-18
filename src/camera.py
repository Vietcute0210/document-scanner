"""
Camera Capture module for Document Scanner.
Allows capturing document photos directly from connected webcams or cameras.
Supports interactive preview window or single high-res frame capture.
"""

from typing import Optional
import sys
import cv2
import numpy as np


def open_camera_stream(camera_index: int = 0) -> cv2.VideoCapture:
    """Helper to open camera across Windows, Linux, and macOS reliably."""
    cap = None
    if sys.platform == "win32":
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(camera_index)
    elif hasattr(cv2, "CAP_V4L2"):
        cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
        if not cap.isOpened():
            cap = cv2.VideoCapture(camera_index)
    else:
        cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)

    return cap


def capture_single_frame(
    camera_index: int = 0,
    warmup_frames: int = 6,
    width: int = 1920,
    height: int = 1080
) -> Optional[np.ndarray]:
    """
    Directly captures a high-resolution frame from the local webcam without
    requiring a native GUI window. Ideal for desktop web apps.

    Returns:
        Captured BGR image as numpy array, or None if capture failed.
    """
    cap = open_camera_stream(camera_index)
    if not cap.isOpened():
        if camera_index == 0:
            cap = open_camera_stream(1)
        if not cap.isOpened():
            return None

    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Warmup a few frames so auto-exposure and white-balance stabilize
        for _ in range(warmup_frames):
            ret, _ = cap.read()
            if not ret:
                break

        ret, frame = cap.read()
        if ret and frame is not None and frame.size > 0:
            return frame
        return None
    finally:
        cap.release()


def capture_from_webcam(
    camera_index: int = 0,
    window_title: str = "Webcam Scanner (SPACE: Chup anh, Q/ESC: Huy)"
) -> Optional[np.ndarray]:
    """
    Opens the default webcam with a live interactive preview window.
    Press SPACE to capture the current frame.
    Press Q or ESC to cancel.

    Args:
        camera_index: Device index (default 0).
        window_title: Title of the OpenCV preview window.

    Returns:
        Captured BGR image as numpy array, or None if cancelled.
    """
    cap = open_camera_stream(camera_index)
    if not cap.isOpened() and camera_index == 0:
        cap = open_camera_stream(1)

    if not cap.isOpened():
        raise RuntimeError(f"Không thể kết nối đến thiết bị webcam (index {camera_index})")

    # Set high resolution if supported
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    captured_frame = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            # Overlay instructional banner on preview
            display_frame = frame.copy()
            h, w = display_frame.shape[:2]

            # Instruction overlay header
            cv2.rectangle(display_frame, (0, 0), (w, 48), (15, 23, 42), -1)
            cv2.putText(
                display_frame,
                "Nhan [SPACE] de chup tai lieu  |  [Q / ESC] de thoat",
                (20, 32),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.72,
                (74, 222, 128),
                2,
                cv2.LINE_AA,
            )

            # Document boundary guide box
            guide_h = int(h * 0.8)
            guide_w = int(guide_h / 1.414)
            gx1 = max(0, (w - guide_w) // 2)
            gy1 = max(0, (h - guide_h) // 2)
            gx2 = min(w, gx1 + guide_w)
            gy2 = min(h, gy1 + guide_h)
            cv2.rectangle(display_frame, (gx1, gy1), (gx2, gy2), (59, 130, 246), 2)

            cv2.imshow(window_title, display_frame)
            key = cv2.waitKey(1) & 0xFF

            if key == 32:  # SPACE
                captured_frame = frame.copy()
                break
            elif key == 27 or key == ord('q') or key == ord('Q'):  # ESC or Q
                break
    finally:
        cap.release()
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

    return captured_frame
