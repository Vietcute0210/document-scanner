"""
CLI script to capture an image directly from webcam and run document scanning pipeline.
Usage:
    python -m scripts.capture_scan [--outdir outputs/camera_scans] [--clahe]
"""

import argparse
from pathlib import Path
import cv2

from src.io_handling import ensure_dir
from src.camera import capture_from_webcam
from src.detect_page import detect_page_corners
from src.transform import warp_from_result
from src.thresholding import thresh_document


def main():
    parser = argparse.ArgumentParser(description="Capture document from webcam and scan")
    parser.add_argument("--outdir", default="outputs/camera_scans", help="Output directory")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0)")
    parser.add_argument("--clahe", action="store_true", help="Apply CLAHE lighting correction")
    args = parser.parse_args()

    ensure_dir(args.outdir)
    print("Opening webcam preview... Press SPACE to capture, Q/ESC to quit.")
    frame = capture_from_webcam(camera_index=args.camera)

    if frame is None:
        print("Capture cancelled by user.")
        return

    out_raw = Path(args.outdir) / "captured_raw.jpg"
    cv2.imwrite(str(out_raw), frame)
    print(f"Captured image saved to: {out_raw}")

    # Process scanned document
    result = detect_page_corners(frame, debug_dir=args.outdir, use_clahe=args.clahe)
    if result.corners is None:
        print("Warning: Could not detect page boundary in captured image.")
        return

    warped = warp_from_result(frame, result)
    if warped is not None:
        cv2.imwrite(str(Path(args.outdir) / "cutout.png"), warped)

    thresh = thresh_document(warped)
    out_scan = Path(args.outdir) / "scanned_doc.png"
    cv2.imwrite(str(out_scan), thresh)
    print(f"Scanned document saved to: {out_scan}")


if __name__ == "__main__":
    main()
