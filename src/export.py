"""
Export module for Document Scanner.
Supports exporting scanned images to PDF (.pdf) and Microsoft Word (.docx).
"""

from pathlib import Path
from typing import Union, List, Sequence
import io
import cv2
import numpy as np
from PIL import Image
import docx
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


def _to_pil_image(img: Union[np.ndarray, str, Path, Image.Image]) -> Image.Image:
    """Helper to convert various image input formats to PIL Image in RGB format."""
    if isinstance(img, (str, Path)):
        return Image.open(str(img)).convert("RGB")
    elif isinstance(img, Image.Image):
        return img.convert("RGB")
    elif isinstance(img, np.ndarray):
        if img.ndim == 2:
            return Image.fromarray(img).convert("RGB")
        elif img.ndim == 3:
            if img.shape[2] == 4:
                rgb = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            else:
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb)
        else:
            raise ValueError(f"Unsupported numpy array shape: {img.shape}")
    else:
        raise TypeError(f"Unsupported image type: {type(img)}")


def _to_image_bytes(img: Union[np.ndarray, str, Path, Image.Image], format: str = ".png") -> io.BytesIO:
    """Helper to convert image input to in-memory BytesIO for docx insertion."""
    if isinstance(img, (str, Path)):
        with open(img, "rb") as f:
            return io.BytesIO(f.read())
    elif isinstance(img, Image.Image):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    elif isinstance(img, np.ndarray):
        success, encoded = cv2.imencode(format, img)
        if not success:
            raise RuntimeError("Failed to encode image to buffer")
        return io.BytesIO(encoded.tobytes())
    else:
        raise TypeError(f"Unsupported image type: {type(img)}")


def export_images_to_pdf(
    images: Union[np.ndarray, str, Path, Sequence[Union[np.ndarray, str, Path, Image.Image]]],
    output_path: Union[str, Path],
    dpi: float = 150.0,
) -> str:
    """
    Exports a single image or a list of images to a PDF file.

    Args:
        images: A single image or list/tuple of images (numpy array, filepath, or PIL Image).
        output_path: Output .pdf file path.
        dpi: Target DPI for resolution metadata.

    Returns:
        The absolute path to the generated PDF.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not isinstance(images, (list, tuple)):
        images = [images]

    if not images:
        raise ValueError("No images provided for PDF export")

    pil_images = [_to_pil_image(im) for im in images]
    first_page = pil_images[0]
    other_pages = pil_images[1:] if len(pil_images) > 1 else []

    first_page.save(
        str(output_path),
        "PDF",
        resolution=dpi,
        save_all=True,
        append_images=other_pages,
    )
    return str(output_path.resolve())


def export_images_to_docx(
    images: Union[np.ndarray, str, Path, Sequence[Union[np.ndarray, str, Path, Image.Image]]],
    output_path: Union[str, Path],
    title: str = None,
    page_width_in: float = 8.27,   # A4 width
    page_height_in: float = 11.69,  # A4 height
    margin_in: float = 0.5,
) -> str:
    """
    Exports scanned document images into a Microsoft Word (.docx) file
    with standard A4 page layout and fitted margins.

    Args:
        images: A single image or list of images.
        output_path: Output .docx file path.
        title: Optional document title placed before the pages.
        page_width_in: Page width in inches (defaults to A4).
        page_height_in: Page height in inches (defaults to A4).
        margin_in: Margin in inches.

    Returns:
        The absolute path to the generated DOCX.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not isinstance(images, (list, tuple)):
        images = [images]

    if not images:
        raise ValueError("No images provided for DOCX export")

    doc = docx.Document()

    # Configure margins for all sections
    usable_width = page_width_in - (2 * margin_in)
    usable_height = page_height_in - (2 * margin_in)

    for section in doc.sections:
        section.page_width = Inches(page_width_in)
        section.page_height = Inches(page_height_in)
        section.top_margin = Inches(margin_in)
        section.bottom_margin = Inches(margin_in)
        section.left_margin = Inches(margin_in)
        section.right_margin = Inches(margin_in)

    if title:
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p_title.add_run(title)
        run.bold = True
        run.font.size = Pt(16)

    for i, im in enumerate(images):
        if i > 0:
            doc.add_page_break()

        img_bytes = _to_image_bytes(im)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Add image fitted to usable page width
        p.add_run().add_picture(img_bytes, width=Inches(usable_width))

    doc.save(str(output_path))
    return str(output_path.resolve())
