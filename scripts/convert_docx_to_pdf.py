"""
CLI script to convert a Word (.docx) document to PDF (.pdf).
Usage:
    python -m scripts.convert_docx_to_pdf --docx path/to/document.docx [--out path/to/output.pdf]
"""

import argparse
from pathlib import Path
from src.converter import convert_docx_to_pdf


def main():
    parser = argparse.ArgumentParser(description="Convert DOCX to PDF using Word COM automation")
    parser.add_argument("--docx", required=True, help="Path to input .docx file")
    parser.add_argument("--out", default=None, help="Path to output .pdf file (optional)")
    args = parser.parse_args()

    input_docx = Path(args.docx)
    print(f"Converting '{input_docx}' to PDF...")
    output_pdf = convert_docx_to_pdf(input_docx, args.out)
    print(f"Successfully converted! PDF saved to: {output_pdf}")


if __name__ == "__main__":
    main()
