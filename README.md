# Document Scanner & Converter Studio

A document scanner and converter built with computer vision methods in Python, OpenCV, and Streamlit.

This project takes a photo of a document (via camera capture or image upload), detects the page boundary, corrects perspective distortion, produces high-contrast scanned results, and exports directly to **PDF (.pdf)** and **Microsoft Word (.docx)**. It also includes an integrated **1-click Word-to-PDF converter** and **OCR text recognition**.

---

## Key Features

- **Document Boundary Detection**: Contour analysis scoring candidate quadrilaterals based on area, convexity, aspect ratio, and angles.
- **Perspective Rectification**: 4-point perspective warp to deskew angled captures.
- **Scanned Enhancement**: Adaptive thresholding and optional CLAHE contrast balance.
- **Direct Camera Capture**: Live webcam photo capture via Streamlit (`st.camera_input`) or OpenCV preview (`scripts/capture_scan.py`).
- **Dual Export Formats**:
  - **PDF (.pdf)**: High-resolution standardized A4 layout ready for printing.
  - **Word (.docx) - Scan Layout**: Embeds scanned documents formatted into standard margins.
  - **Word (.docx) - OCR Editable Text**: Optical character recognition extracts text into an editable Word document.
- **1-Click DOCX to PDF Converter**: Converts any Word `.docx` file to `.pdf` using native Microsoft Word automation on Windows.
- **Interactive Web UI**: Built with Streamlit for drag-and-drop file processing, real-time parameter tuning, and one-click downloads.

---

## Installation

Ensure Python 3.11+ is installed, then install dependencies:
```bash
pip install -r requirements.txt
```

---

## Quick Start (Web UI)

### Option 1: Double-click (Windows)
Double-click `run_app.bat` to launch the application and open your default browser.

### Option 2: Command Line
```bash
streamlit run app.py
```

---

## Command Line Usage (CLI)

### 1. Single Image Scan & Export:
```bash
# Scan and export to image, PDF, and Word:
python -m scripts.single_img_test --img documents/raw/base.jpg --outdir outputs/my_scan --pdf --docx
```

### 2. Live Webcam Capture & Scan:
```bash
# Press SPACE to capture, Q/ESC to quit:
python -m scripts.capture_scan --outdir outputs/camera_scans
```

### 3. OCR Text Extraction to Word:
```bash
python -m scripts.ocr_test --img documents/raw/base.jpg --out outputs/my_scan/extracted.docx --lang en
```

### 4. Convert DOCX to PDF:
```bash
python -m scripts.convert_docx_to_pdf --docx outputs/my_scan/scanned_doc.docx --out outputs/my_scan/final.pdf
```

### 5. Batch Image Processing:
```bash
python -m scripts.multi_img_test --input documents/raw --outdir outputs/batch_eval --pdf --docx
```

---

## Branch Architecture

Features are developed on dedicated branches for code review:
1. `feature/export-documents`: PDF and Word DOCX export modules.
2. `feature/docx-to-pdf`: Microsoft Word COM automation converter.
3. `feature/ocr-text`: OCR text extraction engine to editable DOCX.
4. `feature/camera-capture`: Webcam live preview and frame capture.
5. `feature/web-ui`: Streamlit graphical user interface.
6. `feature/docs-and-scripts`: Batch launcher and updated documentation.

---

## Dataset

This project uses the **GNHK (GoodNotes Handwriting Kollection)** dataset for evaluation and benchmarking of document boundary detection and perspective correction:
> Lee, A. W. C., Chung, J., & Lee, M. (2021). *GNHK: A Dataset for English Handwriting in the Wild*. ICDAR 2021.
- Official page: https://www.goodnotes.com/gnhk/
- GitHub repository: https://github.com/GoodNotes/GNHK-dataset
