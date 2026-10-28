"""
Camera Capture module for Document Scanner.
Allows capturing document photos directly from connected webcams or cameras.
"""

from typing import Optional
import cv2
import numpy as np


def capture_from_webcam(
    camera_index: int = 0,
    window_title: str = "Webcam Scanner (SPACE: Capture, Q/ESC: Cancel)"
) -> Optional[np.ndarray]:
    """
    Opens the default webcam with a live preview window.
    Press SPACE to capture the current frame.
    Press Q or ESC to cancel.

    Args:
        camera_index: Device index (default 0).
        window_title: Title of the OpenCV preview window.

    Returns:
        Captured BGR image as numpy array, or None if cancelled.
    """
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open webcam with index {camera_index}")

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

            # Instruction overlay
            cv2.rectangle(display_frame, (0, 0), (w, 40), (0, 0, 0), -1)
            cv2.putText(
                display_frame,
                "Press [SPACE] to capture document | [Q / ESC] to exit",
                (20, 26),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.imshow(window_title, display_frame)
            key = cv2.waitKey(1) & 0xFF

            if key == 32:  # SPACE
                captured_frame = frame.copy()
                break
            elif key == 27 or key == ord('q'):  # ESC or Q
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    return captured_frame
