"""Document output services. Image processing algorithms remain in src/."""
import io
import tempfile
from pathlib import Path
import cv2
import numpy as np
from PIL import Image


def generate_pdf_bytes(img_input: np.ndarray, dpi: float = 150.0) -> bytes:
    try:
        from src.export import export_images_to_pdf
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            path = Path(tmp.name)
        try:
            export_images_to_pdf(img_input, str(path), dpi=dpi)
            return path.read_bytes()
        finally:
            path.unlink(missing_ok=True)
    except Exception:
        pil = Image.fromarray(img_input).convert("RGB") if img_input.ndim == 2 else Image.fromarray(cv2.cvtColor(img_input, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO(); pil.save(buf, format="PDF", resolution=dpi); return buf.getvalue()


def generate_docx_bytes(img_input: np.ndarray, title: str = "Tài liệu quét") -> bytes:
    import docx
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    doc = docx.Document()
    for section in doc.sections:
        section.page_width, section.page_height = Inches(8.27), Inches(11.69)
        section.top_margin = section.bottom_margin = Inches(.5)
        section.left_margin = section.right_margin = Inches(.5)
    if title:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(title); run.bold = True; run.font.size = Pt(15)
    ok, encoded = cv2.imencode(".png", img_input)
    if not ok: raise RuntimeError("Không thể mã hóa ảnh thành PNG")
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(io.BytesIO(encoded.tobytes()), width=Inches(7.27))
    buf = io.BytesIO(); doc.save(buf); return buf.getvalue()


def perform_ai_reconstruction(image, lang="vi", api_key="", model="gemini-2.5-flash"):
    from src.gemini_ocr import extract_structured_content, extract_text_with_gemini
    from src.ai_docx_builder import build_smart_docx, build_simple_docx
    key = api_key.strip() or None
    try:
        data = extract_structured_content(image, lang=lang, api_key=key, model=model)
        docx_bytes = build_smart_docx(data, lang=lang)
        lines = []
        if data.get("title"): lines.append("# " + data["title"])
        for block in data.get("blocks", []):
            kind = block.get("type", "paragraph")
            if kind == "table":
                lines.extend(["[BẢNG DỮ LIỆU]"] + [" | ".join(map(str, row)) for row in block.get("rows", [])])
            elif kind == "list": lines.extend("• " + str(x) for x in block.get("items", []))
            else:
                content = block.get("content", "")
                if content: lines.append(("## " if kind == "heading" else "") + content)
        return "\n".join(lines), docx_bytes, data
    except Exception as first_error:
        try:
            text = extract_text_with_gemini(image, lang=lang, api_key=key, model=model)
            return text, build_simple_docx(text, title="Tài liệu tái tạo"), {"title":"Tài liệu", "blocks":[{"type":"paragraph", "content":text}]}
        except Exception as second_error:
            raise RuntimeError(f"Gemini không thể xử lý tài liệu. Chi tiết: {first_error}; dự phòng: {second_error}") from second_error


def convert_docx_bytes_to_pdf_bytes(docx_bytes: bytes) -> bytes:
    """Convert through the existing Microsoft Word COM adapter (Windows only)."""
    import sys
    if sys.platform != "win32":
        raise OSError("Chuyển DOCX sang PDF bằng Word COM chỉ được hỗ trợ trên Windows.")
    from src.converter import convert_docx_to_pdf
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "source.docx"
        target = Path(directory) / "source.pdf"
        source.write_bytes(docx_bytes)
        convert_docx_to_pdf(source, target)
        return target.read_bytes()
