"""
Document Converter module.
Converts Microsoft Word (.docx) files to PDF (.pdf) using Microsoft Word COM Automation.
"""

from pathlib import Path
from typing import Optional, Union
import sys


def convert_docx_to_pdf(
    docx_path: Union[str, Path],
    pdf_path: Optional[Union[str, Path]] = None
) -> str:
    """
    Converts a .docx file to a .pdf file using Microsoft Word via COM.

    Args:
        docx_path: Path to the input .docx file.
        pdf_path: Optional path to the output .pdf file.
                  If omitted, saves in the same directory with .pdf extension.

    Returns:
        The absolute path to the converted .pdf file.
    """
    docx_file = Path(docx_path).resolve()
    if not docx_file.exists():
        raise FileNotFoundError(f"Input DOCX file not found: {docx_file}")

    if pdf_path is None:
        pdf_file = docx_file.with_suffix(".pdf")
    else:
        pdf_file = Path(pdf_path).resolve()

    pdf_file.parent.mkdir(parents=True, exist_ok=True)

    if sys.platform != "win32":
        raise OSError("Word COM automation is only supported on Windows OS.")

    import pythoncom
    import win32com.client

    # Initialize COM in current thread (important for multithreaded / web environments)
    pythoncom.CoInitialize()
    word_app = None
    doc = None
    try:
        word_app = win32com.client.DispatchEx("Word.Application")
        word_app.Visible = False
        word_app.DisplayAlerts = False

        # Open docx document
        doc = word_app.Documents.Open(str(docx_file), ReadOnly=True)

        # wdFormatPDF = 17
        doc.SaveAs2(str(pdf_file), FileFormat=17)
        return str(pdf_file)
    finally:
        if doc is not None:
            try:
                doc.Close(SaveChanges=False)
            except Exception:
                pass
        if word_app is not None:
            try:
                word_app.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()
