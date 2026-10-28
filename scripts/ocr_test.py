"""
CLI script to run OCR on an image and export recognized text to Word (.docx).
Usage:
    python -m scripts.ocr_test --img path/to/image.png [--out path/to/doc.docx] [--lang en]
"""

import argparse
from pathlib import Path
from src.ocr_engine import extract_text_from_image, export_text_to_docx


def main():
    parser = argparse.ArgumentParser(description="Extract text from scanned image to editable Word DOCX")
    parser.add_argument("--img", required=True, help="Path to input image")
    parser.add_argument("--out", default=None, help="Output .docx file path (optional)")
    parser.add_argument("--lang", default="en", help="Language code (default: en)")
    args = parser.parse_args()

    img_path = Path(args.img)
    print(f"Running OCR on '{img_path}' (lang={args.lang})...")
    text = extract_text_from_image(img_path, lang=args.lang)

    print("\n--- Recognized Text ---")
    print(text if text else "(No text recognized)")
    print("------------------------\n")

    if args.out:
        out_docx = Path(args.out)
    else:
        out_docx = img_path.with_name(f"{img_path.stem}_ocr.docx")

    export_text_to_docx(text, out_docx, title=f"OCR Transcription: {img_path.name}")
    print(f"Editable Word document saved to: {out_docx}")


if __name__ == "__main__":
    main()
