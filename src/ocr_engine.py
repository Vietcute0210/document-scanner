"""
Optical Character Recognition (OCR) Engine module.
Extracts editable text from scanned documents and exports to Microsoft Word (.docx).
"""

from pathlib import Path
from typing import Optional, Union, Sequence
import cv2
import numpy as np
import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


def extract_text_from_image(
    image: Union[np.ndarray, str, Path],
    lang: str = "en"
) -> str:
    """
    Extracts text from an image using Windows native OCR (winocr)
    with fallbacks if needed.

    Args:
        image: Image as numpy array (BGR or grayscale) or path to image.
        lang: Language tag (e.g., 'en', 'vi').

    Returns:
        Recognized text string.
    """
    if isinstance(image, (str, Path)):
        img_path = str(Path(image).resolve())
        cv_img = cv2.imread(img_path)
        if cv_img is None:
            raise FileNotFoundError(f"Could not read image file: {img_path}")
    elif isinstance(image, np.ndarray):
        cv_img = image.copy()
        if cv_img.ndim == 2:
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2BGR)
    else:
        raise TypeError(f"Unsupported image type: {type(image)}")

    # Try Gemini AI Vision OCR first (highest priority)
    try:
        from src.gemini_ocr import extract_text_with_gemini
        text = extract_text_with_gemini(cv_img, lang=lang)
        if text and text.strip():
            return text
    except Exception:
        pass  # Fall through to traditional OCR engines

    # Try Windows native OCR
    try:
        import winocr
        target_lang = lang
        try:
            avail_langs = [l.language_tag for l in winocr.OcrEngine.available_recognizer_languages]
            if target_lang in avail_langs:
                win_lang = target_lang
            else:
                matched = [l for l in avail_langs if l.lower().startswith(target_lang.lower())]
                win_lang = matched[0] if matched else (avail_langs[0] if avail_langs else target_lang)
        except Exception:
            win_lang = target_lang

        res = winocr.recognize_cv2_sync(cv_img, lang=win_lang)
        text = res.get("text", "").strip()
        return text
    except Exception as e:
        # Fallback to easyocr if available
        try:
            import easyocr
            reader = easyocr.Reader([lang], gpu=False)
            results = reader.readtext(cv_img, detail=0)
            return "\n".join(results)
        except Exception:
            pass

        # Fallback to pytesseract if available
        try:
            import pytesseract
            return pytesseract.image_to_string(cv_img, lang=lang).strip()
        except Exception:
            pass

        raise RuntimeError(f"OCR recognition failed: {e}")


def export_text_to_docx(
    text: str,
    output_path: Union[str, Path],
    title: Optional[str] = None,
    font_name: str = "Calibri",
    font_size_pt: int = 12
) -> str:
    """
    Exports plain/extracted text into an editable Microsoft Word document (.docx).

    Args:
        text: Extracted text content.
        output_path: Destination .docx path.
        title: Optional document heading.
        font_name: Default font name.
        font_size_pt: Default font size in points.

    Returns:
        Absolute path to the created .docx file.
    """
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    doc = docx.Document()

    # Standard 1-inch margins for readable text documents
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    if title:
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p_title.add_run(title)
        run.bold = True
        run.font.name = font_name
        run.font.size = Pt(font_size_pt + 4)

    lines = text.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        p = doc.add_paragraph()
        run = p.add_run(stripped)
        run.font.name = font_name
        run.font.size = Pt(font_size_pt)

    doc.save(str(out_file))
    return str(out_file)
