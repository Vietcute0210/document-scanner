"""
AI-Powered DOCX Builder.
Takes structured content extracted by Gemini AI from scanned document images
and generates a well-formatted, editable Microsoft Word (.docx) file.

The key difference from traditional OCR export:
- Recognizes headings, paragraphs, lists, tables, and image descriptions
- Applies proper Word formatting (fonts, sizes, styles)
- Recreates the document structure, not just dumps raw text
"""

import io
from typing import Optional, Union

import numpy as np
import docx
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn


def _set_cell_shading(cell, color_hex: str):
    """Set background shading for a table cell."""
    shading = docx.oxml.OxmlElement("w:shd")
    shading.set(qn("w:fill"), color_hex)
    shading.set(qn("w:val"), "clear")
    cell._tc.get_or_add_tcPr().append(shading)


def build_smart_docx(
    structured_content: dict,
    title_override: Optional[str] = None,
    font_name: str = "Calibri",
    lang: str = "vi",
) -> bytes:
    """
    Build a well-formatted Word document from structured content.

    Args:
        structured_content: Dict with 'title' and 'blocks' from Gemini extraction.
            Each block has 'type' (heading/paragraph/list/table/image_description)
            and corresponding content fields.
        title_override: Override the document title (uses extracted title if None).
        font_name: Default font for the document.
        lang: Language hint for formatting.

    Returns:
        DOCX file as bytes.
    """
    doc = docx.Document()

    # --- Page Setup: A4 with standard margins ---
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    # --- Default font style ---
    style = doc.styles["Normal"]
    style.font.name = font_name
    style.font.size = Pt(12)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.15

    # --- Document Title ---
    title = title_override or structured_content.get("title")
    if title:
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_title.paragraph_format.space_after = Pt(18)
        run = p_title.add_run(title)
        run.bold = True
        run.font.name = font_name
        run.font.size = Pt(18)
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)  # Dark blue

    # --- Process each content block ---
    blocks = structured_content.get("blocks", [])
    for block in blocks:
        block_type = block.get("type", "paragraph")

        if block_type == "heading":
            _add_heading_block(doc, block, font_name)

        elif block_type == "paragraph":
            _add_paragraph_block(doc, block, font_name)

        elif block_type == "list":
            _add_list_block(doc, block, font_name)

        elif block_type == "table":
            _add_table_block(doc, block, font_name)

        elif block_type == "image_description":
            _add_image_description_block(doc, block, font_name)

        else:
            # Unknown type → treat as paragraph
            content = block.get("content", "")
            if content:
                p = doc.add_paragraph()
                run = p.add_run(str(content))
                run.font.name = font_name
                run.font.size = Pt(12)

    # --- Footer ---
    p_footer = doc.add_paragraph()
    p_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_footer.paragraph_format.space_before = Pt(24)
    run_footer = p_footer.add_run("— Tài liệu được tái tạo bởi AI (Gemini Vision) —")
    run_footer.font.name = font_name
    run_footer.font.size = Pt(8)
    run_footer.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
    run_footer.italic = True

    # --- Save to bytes ---
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _add_heading_block(doc, block: dict, font_name: str):
    """Add a heading block to the document."""
    level = block.get("level", 1)
    content = block.get("content", "")
    if not content:
        return

    # Map level to Word heading sizes
    size_map = {1: 16, 2: 14, 3: 13}
    font_size = size_map.get(level, 12)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)

    run = p.add_run(content)
    run.bold = True
    run.font.name = font_name
    run.font.size = Pt(font_size)

    if level == 1:
        run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
    elif level == 2:
        run.font.color.rgb = RGBColor(0x2D, 0x2D, 0x44)


def _add_paragraph_block(doc, block: dict, font_name: str):
    """Add a paragraph block to the document."""
    content = block.get("content", "")
    if not content:
        return

    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(1.27)  # Standard first-line indent

    run = p.add_run(content)
    run.font.name = font_name
    run.font.size = Pt(12)


def _add_list_block(doc, block: dict, font_name: str):
    """Add a list block to the document."""
    items = block.get("items", [])
    if not items:
        content = block.get("content", "")
        if content:
            items = [line.strip().lstrip("-•·") .strip()
                     for line in content.split("\n") if line.strip()]

    for item in items:
        if not item:
            continue
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1.27)
        p.paragraph_format.first_line_indent = Cm(-0.63)
        p.paragraph_format.space_after = Pt(3)

        run = p.add_run(f"• {item}")
        run.font.name = font_name
        run.font.size = Pt(12)


def _add_table_block(doc, block: dict, font_name: str):
    """Add a table block to the document."""
    rows_data = block.get("rows", [])
    if not rows_data:
        content = block.get("content", "")
        if content:
            p = doc.add_paragraph()
            run = p.add_run(content)
            run.font.name = font_name
            run.font.size = Pt(12)
        return

    # Determine table dimensions
    num_cols = max(len(row) for row in rows_data) if rows_data else 1
    num_rows = len(rows_data)

    table = doc.add_table(rows=num_rows, cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    for i, row_data in enumerate(rows_data):
        row = table.rows[i]
        for j, cell_text in enumerate(row_data):
            if j < num_cols:
                cell = row.cells[j]
                cell.text = ""
                p = cell.paragraphs[0]
                run = p.add_run(str(cell_text))
                run.font.name = font_name
                run.font.size = Pt(11)

                # Style header row
                if i == 0:
                    run.bold = True
                    _set_cell_shading(cell, "E8EAF6")

    # Add spacing after table
    doc.add_paragraph()


def _add_image_description_block(doc, block: dict, font_name: str):
    """Add an image description block (for diagrams/charts found in the document)."""
    content = block.get("content", "")
    if not content:
        return

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(12)

    # Add a visual indicator that this was an image/diagram in the original
    run_icon = p.add_run("📊 ")
    run_icon.font.size = Pt(14)

    run_label = p.add_run("[Hình/Biểu đồ] ")
    run_label.bold = True
    run_label.italic = True
    run_label.font.name = font_name
    run_label.font.size = Pt(11)
    run_label.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    run_desc = p.add_run(content)
    run_desc.italic = True
    run_desc.font.name = font_name
    run_desc.font.size = Pt(11)
    run_desc.font.color.rgb = RGBColor(0x66, 0x66, 0x66)


# ---------------------------------------------------------------------------
# Simple fallback builder (from plain text)
# ---------------------------------------------------------------------------

def build_simple_docx(
    text: str,
    title: Optional[str] = None,
    font_name: str = "Calibri",
) -> bytes:
    """
    Build a simple Word document from plain extracted text.
    Used as fallback when structured extraction is not available.

    Args:
        text: Plain text content.
        title: Optional document title.
        font_name: Font to use.

    Returns:
        DOCX file as bytes.
    """
    doc = docx.Document()

    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)

    style = doc.styles["Normal"]
    style.font.name = font_name
    style.font.size = Pt(12)

    if title:
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p_title.add_run(title)
        run.bold = True
        run.font.name = font_name
        run.font.size = Pt(16)
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

    for line in text.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue

        p = doc.add_paragraph()

        # Simple heuristic formatting
        if line_clean.startswith("## "):
            run = p.add_run(line_clean[3:])
            run.bold = True
            run.font.size = Pt(14)
        elif line_clean.startswith("# "):
            run = p.add_run(line_clean[2:])
            run.bold = True
            run.font.size = Pt(16)
        elif line_clean.startswith("- ") or line_clean.startswith("• "):
            p.paragraph_format.left_indent = Cm(1.27)
            run = p.add_run(f"• {line_clean[2:]}")
        else:
            run = p.add_run(line_clean)

        run.font.name = font_name
        if not run.font.size:
            run.font.size = Pt(12)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
