"""
Streamlit Web UI for Document Scanner & Converter Studio.
Minimalist, high-contrast dark workspace: balanced 2-column layout,
stable dimensions, and professional document digitizing pipeline.
"""

import hashlib
import io
from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np
from PIL import Image
import streamlit as st

# Core CV imports from src
from src.detect_page import detect_page_corners, DetectionResult
from src.transform import warp_from_result, four_point_transform
from src.thresholding import thresh_document, magic_color_document, magic_gray_document
from src.ocr_engine import extract_text_from_image
from src.quad_editor import render_quad_editor


# --- HELPER EXPORT FUNCTIONS ---

def generate_pdf_bytes(img_input: np.ndarray, dpi: float = 150.0) -> bytes:
    """Generates PDF file bytes from a numpy image."""
    try:
        from src.export import export_images_to_pdf
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        export_images_to_pdf(img_input, tmp_path, dpi=dpi)
        with open(tmp_path, "rb") as f:
            data = f.read()
        Path(tmp_path).unlink(missing_ok=True)
        return data
    except Exception:
        if img_input.ndim == 2:
            pil_img = Image.fromarray(img_input).convert("RGB")
        else:
            pil_img = Image.fromarray(cv2.cvtColor(img_input, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        pil_img.save(buf, format="PDF", resolution=dpi)
        return buf.getvalue()


def generate_docx_bytes(img_input: np.ndarray, title: str = "Tài Liệu Quét") -> bytes:
    """Generates Word DOCX file bytes embedding the scanned document image in A4 layout."""
    import docx
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = docx.Document()
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)

    if title:
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p_title.add_run(title)
        run.bold = True
        run.font.size = Pt(15)

    success, encoded = cv2.imencode(".png", img_input)
    if not success:
        raise RuntimeError("Lỗi mã hóa ảnh sang định dạng PNG")
    img_buf = io.BytesIO(encoded.tobytes())

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(img_buf, width=Inches(7.27))

    out_buf = io.BytesIO()
    doc.save(out_buf)
    return out_buf.getvalue()


def perform_ai_ocr_and_export_docx(
    img_input: np.ndarray,
    lang: str = "vi",
    api_key: str = "",
    model: str = "gemini-2.5-flash",
) -> Tuple[str, bytes, dict]:
    """
    Uses Gemini AI Vision to analyze the scanned image and generate
    an editable Word document that recreates the document content
    (text, tables, lists, headings) — NOT just inserting the image.
    """
    from src.gemini_ocr import extract_structured_content, extract_text_with_gemini
    from src.ai_docx_builder import build_smart_docx, build_simple_docx

    key = api_key.strip() if api_key and api_key.strip() else None

    try:
        structured = extract_structured_content(img_input, lang=lang, api_key=key, model=model)
        docx_bytes = build_smart_docx(structured, lang=lang)

        blocks = structured.get("blocks", [])
        text_parts = []
        if structured.get("title"):
            text_parts.append(f"# {structured['title']}\n")

        for b in blocks:
            b_type = b.get("type", "paragraph")
            if b_type == "heading":
                level = b.get("level", 1)
                text_parts.append(f"{'#' * (level + 1)} {b.get('content', '')}")
            elif b_type == "table":
                text_parts.append("\n[BẢNG DỮ LIỆU]")
                for row in b.get("rows", []):
                    text_parts.append(" | ".join(str(c) for c in row))
                text_parts.append("")
            elif b_type == "list":
                for item in b.get("items", []):
                    text_parts.append(f"• {item}")
            elif b_type == "image_description":
                text_parts.append(f"\n[HÌNH ẢNH / SƠ ĐỒ]: {b.get('content', '')}\n")
            else:
                content = b.get("content", "")
                if content:
                    text_parts.append(content)

        extracted_text = "\n".join(text_parts)
        return extracted_text, docx_bytes, structured

    except Exception as e:
        try:
            plain_text = extract_text_with_gemini(img_input, lang=lang, api_key=key, model=model)
            docx_bytes = build_simple_docx(plain_text, title="Tài Liệu Tái Tạo")
            return plain_text, docx_bytes, {"title": "Tài Liệu", "blocks": [{"type": "paragraph", "content": plain_text}]}
        except Exception as e2:
            err_msg = f"Lỗi Gemini Vision ({model}): {e} (Dự phòng: {e2})"
            err_docx = build_simple_docx(err_msg, title="Lỗi Xử Lý")
            return err_msg, err_docx, {}


def convert_docx_bytes_to_pdf_bytes(docx_bytes: bytes) -> bytes:
    """Converts DOCX bytes to PDF bytes using Microsoft Word COM on Windows."""
    import tempfile
    import pythoncom
    import win32com.client

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
        tmp_docx.write(docx_bytes)
        docx_path = tmp_docx.name

    pdf_path = str(Path(docx_path).with_suffix(".pdf"))

    pythoncom.CoInitialize()
    word_app = None
    doc = None
    try:
        word_app = win32com.client.DispatchEx("Word.Application")
        word_app.Visible = False
        word_app.DisplayAlerts = False

        doc = word_app.Documents.Open(str(Path(docx_path).resolve()), ReadOnly=True)
        doc.SaveAs2(str(Path(pdf_path).resolve()), FileFormat=17)
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

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    Path(docx_path).unlink(missing_ok=True)
    Path(pdf_path).unlink(missing_ok=True)
    return pdf_bytes


# --- STREAMLIT PAGE CONFIG & MINIMALIST DARK THEME ---

st.set_page_config(
    page_title="Document Studio",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global Root & Typography */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        background-color: #121212 !important;
        color: #F3F5F7 !important;
    }

    /* Enforce pure bright white headings everywhere - never dark */
    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        margin: 0 !important;
    }

    p, span, label, div {
        color: inherit;
    }

    /* Clean Streamlit Header */
    [data-testid="stHeader"] {
        background-color: rgba(18, 18, 18, 0.95) !important;
        backdrop-filter: blur(12px) !important;
        border-bottom: 1px solid #222222 !important;
    }

    /* Sidebar Dark Styling */
    [data-testid="stSidebar"] {
        background-color: #161616 !important;
        border-right: 1px solid #262626 !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label {
        color: #D1D5DB !important;
        font-size: 0.85rem !important;
    }
    .sidebar-section-title {
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        color: #888888 !important;
        -webkit-text-fill-color: #888888 !important;
        margin: 14px 0 6px 0 !important;
    }

    /* Top Studio Bar */
    .top-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 16px;
        background: #181818;
        border: 1px solid #282828;
        border-radius: 8px;
        margin-bottom: 14px;
    }
    .top-bar-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        letter-spacing: -0.02em;
        display: inline-flex;
        align-items: center;
        gap: 10px;
    }
    .top-bar-title svg {
        width: 22px;
        height: 22px;
        stroke: #FFFFFF;
    }
    .top-bar-meta {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #222222;
        border: 1px solid #333333;
        border-radius: 6px;
        padding: 5px 12px;
        font-size: 0.82rem;
    }
    .meta-name {
        font-weight: 600;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    .meta-dim {
        color: #999999 !important;
        -webkit-text-fill-color: #999999 !important;
    }
    .meta-badge {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 7px;
        border-radius: 4px;
        background: #1B2B1B;
        color: #4ADE80 !important;
        -webkit-text-fill-color: #4ADE80 !important;
        border: 1px solid #234E23;
    }

    /* Symmetrical Panel Headers */
    .panel-header {
        font-size: 0.9rem;
        font-weight: 600;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        background: #181818;
        border: 1px solid #282828;
        border-radius: 8px 8px 0 0;
        padding: 9px 14px;
        margin-bottom: 0px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .panel-title-group {
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    .panel-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #3B82F6;
        display: inline-block;
    }
    .panel-dot-green {
        background: #10B981;
    }
    .panel-badge {
        font-size: 0.74rem;
        font-weight: 500;
        color: #A0A0A0 !important;
        -webkit-text-fill-color: #A0A0A0 !important;
        background: #222222;
        border: 1px solid #303030;
        padding: 2px 8px;
        border-radius: 4px;
    }

    /* Panel Footer Note */
    .panel-footer {
        font-size: 0.78rem;
        color: #888888 !important;
        -webkit-text-fill-color: #888888 !important;
        background: #181818;
        border: 1px solid #282828;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 7px 12px;
        line-height: 1.4;
    }

    /* Status Notes */
    .status-note {
        font-size: 0.8rem;
        padding: 8px 12px;
        border-radius: 0 0 8px 8px;
        margin-top: 0px;
        border: 1px solid #282828;
        border-top: none;
        line-height: 1.4;
    }
    .note-auto {
        background: #131813 !important;
        color: #4ADE80 !important;
        -webkit-text-fill-color: #4ADE80 !important;
    }
    .note-manual {
        background: #1A1813 !important;
        color: #FBBF24 !important;
        -webkit-text-fill-color: #FBBF24 !important;
    }
    .note-warn {
        background: #1F1414 !important;
        color: #F87171 !important;
        -webkit-text-fill-color: #F87171 !important;
    }

    /* Modern Segmented Pill Control (Hides Radio Circles) */
    div[data-testid="stRadio"] > div {
        display: flex !important;
        flex-direction: row !important;
        background: #161616 !important;
        border: 1px solid #282828 !important;
        border-radius: 8px !important;
        padding: 3px !important;
        gap: 3px !important;
    }
    div[data-testid="stRadio"] label {
        flex: 1 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: transparent !important;
        color: #888888 !important;
        -webkit-text-fill-color: #888888 !important;
        border-radius: 6px !important;
        padding: 6px 10px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stRadio"] label > div:first-child,
    div[data-testid="stRadio"] div[data-testid="stWidgetSelection"],
    div[data-testid="stRadio"] div[class*="StyledRadio"],
    div[data-testid="stRadio"] div[role="radio"] > div:first-child {
        display: none !important;
    }
    div[data-testid="stRadio"] label:hover {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"],
    div[data-testid="stRadio"] label:has(input:checked),
    div[data-testid="stRadio"] div[aria-checked="true"] {
        background: #2A2A2A !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
        border: 1px solid #3E3E3E !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4) !important;
    }

    /* Monochrome Slider - No Coral Red */
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: #FFFFFF !important;
        border: 2px solid #FFFFFF !important;
        box-shadow: 0 0 6px rgba(255, 255, 255, 0.4) !important;
        width: 15px !important;
        height: 15px !important;
    }
    div[data-baseweb="slider"] > div > div {
        background: #2A2A2A !important;
    }
    div[data-baseweb="slider"] > div > div > div {
        background: #FFFFFF !important;
    }
    div[data-baseweb="slider"] [data-testid="stThumbValue"] {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
    }

    /* Standard Buttons */
    div.stButton > button {
        background: #222222 !important;
        color: #F3F5F7 !important;
        -webkit-text-fill-color: #F3F5F7 !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
        transition: all 0.15s ease !important;
    }
    div.stButton > button:hover {
        background: #2E2E2E !important;
        border-color: #555555 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    div.stButton > button[kind="primary"] {
        background: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border: 1px solid #FFFFFF !important;
        font-weight: 600 !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #E5E5E5 !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* Download Buttons */
    div.stDownloadButton > button {
        background: #1C1C1C !important;
        color: #F3F5F7 !important;
        -webkit-text-fill-color: #F3F5F7 !important;
        border: 1px solid #303030 !important;
        border-radius: 8px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
        transition: all 0.15s ease !important;
    }
    div.stDownloadButton > button:hover {
        background: #282828 !important;
        border-color: #555555 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Image Display Frame */
    [data-testid="stImage"] img {
        border-radius: 0 0 8px 8px !important;
        border: 1px solid #282828 !important;
        border-top: none !important;
        background: #0E0E0E !important;
    }

    /* Action Dock */
    .export-dock {
        background: #181818;
        border: 1px solid #282828;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 14px;
    }
    .export-dock-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        margin-bottom: 10px;
    }

    /* AI Card */
    .ai-box {
        background: #181818;
        border: 1px solid #282828;
        border-radius: 8px;
        padding: 12px 16px;
        margin-top: 12px;
    }
    .ai-box-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .ai-badge {
        font-size: 0.78rem;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        background: #262626;
        border: 1px solid #363636;
        padding: 2px 8px;
        border-radius: 6px;
    }

    div[data-testid="stTextArea"] textarea {
        background-color: #141414 !important;
        color: #F3F5F7 !important;
        -webkit-text-fill-color: #F3F5F7 !important;
        border: 1px solid #282828 !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
    }
</style>
""", unsafe_allow_html=True)


# --- SIDEBAR NAVIGATION & IMAGE SOURCE ---

st.sidebar.markdown("<h3 style='color: #FFFFFF; margin-bottom: 6px;'>Document Studio</h3>", unsafe_allow_html=True)

app_mode = st.sidebar.radio(
    "Chế độ làm việc",
    ["Quét tài liệu", "Chuyển đổi DOCX sang PDF"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

new_img_detected = None
new_source_name = None

if app_mode == "Quét tài liệu":
    st.sidebar.markdown("<h4 style='color: #FFFFFF; font-size: 0.9rem; margin-bottom: 6px;'>Nguồn tài liệu</h4>", unsafe_allow_html=True)
    input_source = st.sidebar.radio(
        "Nguồn ảnh:",
        ["Ảnh mẫu", "Tải ảnh lên", "Webcam"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if input_source == "Ảnh mẫu":
        sample_dir = Path("documents/sample")
        sample_files = sorted(list(sample_dir.glob("*.jpg")) + list(sample_dir.glob("*.png")))
        if sample_files:
            sample_labels = {
                "sample1.jpg": "Mẫu 1 - Chuẩn in (phẳng)",
                "sample2.jpg": "Mẫu 2 - Góc nghiêng 45°",
                "sample3.jpg": "Mẫu 3 - Mép mờ sát nền",
                "sample4.jpg": "Mẫu 4 - Vở ô ly cong (GNHK)",
                "sample5.jpg": "Mẫu 5 - Bóng tối phức tạp",
            }
            sample_names = [f.name for f in sample_files]
            selected_sample = st.sidebar.selectbox(
                "Chọn ảnh mẫu:",
                sample_names,
                format_func=lambda x: sample_labels.get(x, x),
                label_visibility="collapsed"
            )
            sample_path = sample_dir / selected_sample
            new_img_detected = cv2.imread(str(sample_path))
            new_source_name = Path(selected_sample).stem

    elif input_source == "Tải ảnh lên":
        uploaded_file = st.sidebar.file_uploader(
            "Chọn tập tin ảnh tài liệu:",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
            label_visibility="collapsed"
        )
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            new_img_detected = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            new_source_name = Path(uploaded_file.name).stem

    elif input_source == "Webcam":
        camera_photo = st.sidebar.camera_input("Chụp ảnh webcam", label_visibility="collapsed")
        if camera_photo is not None:
            bytes_data = camera_photo.getvalue()
            new_img_detected = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            new_source_name = "camera_capture"

    st.sidebar.markdown("---")
    st.sidebar.markdown("<h4 style='color: #FFFFFF; font-size: 0.9rem; margin-bottom: 6px;'>Cấu hình AI Vision</h4>", unsafe_allow_html=True)
    ai_model = st.sidebar.selectbox(
        "Mô hình Gemini:",
        ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
        index=0,
        help="Gemini 2.5 Flash phân tích cấu trúc tài liệu và trích xuất bảng biểu tốc độ cao."
    )
    api_key_input = st.sidebar.text_input(
        "Google AI Studio API Key:",
        value=st.session_state.get("gemini_api_key_input", ""),
        type="password",
        help="Nhập API Key hoặc để trống để tự động nạp từ .env"
    )
    if api_key_input:
        st.session_state["gemini_api_key_input"] = api_key_input

    ocr_lang = st.sidebar.selectbox(
        "Ngôn ngữ tài liệu:",
        ["vi", "en"],
        format_func=lambda x: "Tiếng Việt (vi)" if x == "vi" else "English (en)"
    )

    with st.sidebar.expander("Tham số thuật toán nâng cao", expanded=False):
        boundary_mode_label = st.selectbox(
            "Số điểm neo nhận diện viền:",
            [
                "8 điểm (4 Góc + 4 Trung điểm)",
                "12 điểm (Bám sát độ uốn cong)",
                "6 điểm (4 Góc + 2 Trung điểm)",
                "4 điểm (Tứ giác cơ bản)",
            ],
            index=0,
            help="Sử dụng 8 hoặc 12 điểm neo giúp bám sát mép giấy bị uốn cong qua Coons Patch."
        )
        num_points_map = {
            "8 điểm (4 Góc + 4 Trung điểm)": 8,
            "12 điểm (Bám sát độ uốn cong)": 12,
            "6 điểm (4 Góc + 2 Trung điểm)": 6,
            "4 điểm (Tứ giác cơ bản)": 4,
        }
        num_points = num_points_map[boundary_mode_label]
        use_clahe = st.checkbox("Cân bằng sáng CLAHE", value=False, help="Hỗ trợ tài liệu bị sấp bóng hoặc ánh sáng không đều")
        max_dim = st.slider("Độ phân giải dò biên (px):", min_value=600, max_value=2000, value=1200, step=100)
else:
    num_points = 8
    use_clahe = False
    max_dim = 1200
    ocr_lang = "vi"
    ai_model = "gemini-2.5-flash"


# --- MAIN WORKSPACE ---

if app_mode == "Quét tài liệu":
    # Cache loaded image
    if new_img_detected is not None:
        new_hash = hashlib.md5(new_img_detected.tobytes()).hexdigest()
        old_hash = st.session_state.get("current_img_hash")
        if new_hash != old_hash:
            st.session_state["raw_cv_img"] = new_img_detected
            st.session_state["source_name"] = new_source_name or "document"
            st.session_state["current_img_hash"] = new_hash
            st.session_state["needs_detection"] = True

    # Fallback to sample1 on fresh launch
    if "raw_cv_img" not in st.session_state or st.session_state["raw_cv_img"] is None:
        sample_path = Path("documents/sample/sample1.jpg")
        if sample_path.exists():
            st.session_state["raw_cv_img"] = cv2.imread(str(sample_path))
            st.session_state["source_name"] = "sample1"
            st.session_state["current_img_hash"] = hashlib.md5(st.session_state["raw_cv_img"].tobytes()).hexdigest()
            st.session_state["needs_detection"] = True

    raw_cv_img = st.session_state.get("raw_cv_img")
    source_name = st.session_state.get("source_name", "document")

    if raw_cv_img is not None:
        img_h, img_w = raw_cv_img.shape[:2]

        current_detect_params = (max_dim, use_clahe, num_points)
        cached_params = st.session_state.get("last_detect_params")
        needs_detection = st.session_state.get("needs_detection", False) or (current_detect_params != cached_params)

        if needs_detection or "detection" not in st.session_state:
            with st.spinner("Đang phân tích biên dạng tài liệu..."):
                detection = detect_page_corners(
                    raw_cv_img,
                    max_dim=max_dim,
                    use_clahe=use_clahe,
                    num_points=num_points,
                )
            st.session_state["detection"] = detection
            st.session_state["last_detect_params"] = current_detect_params
            st.session_state["needs_detection"] = False

            if detection.corners is not None:
                st.session_state["active_corners"] = detection.corners.copy()
            else:
                margin_x = float(img_w * 0.05)
                margin_y = float(img_h * 0.05)
                st.session_state["active_corners"] = np.array([
                    [margin_x, margin_y],
                    [img_w - margin_x, margin_y],
                    [img_w - margin_x, img_h - margin_y],
                    [margin_x, img_h - margin_y]
                ], dtype=np.float32)

            st.session_state["is_manual_mode"] = False

        detection: DetectionResult = st.session_state["detection"]
        active_corners: np.ndarray = st.session_state.get("active_corners")
        is_manual_mode: bool = st.session_state.get("is_manual_mode", False)

        mode_desc = "Chỉnh tay (4 góc)" if is_manual_mode else f"Tự động ({len(detection.boundary_points) if detection.boundary_points is not None else 4} điểm neo)"

        # Top Bar (Clean, fixed height, high contrast, pure white branding)
        st.markdown(f"""
        <div class="top-bar">
          <div class="top-bar-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 7V4h3M20 7V4h-3M4 17v3h3M20 17v3h-3M9 12h6M9 16h6M9 8h6"/></svg>
            <span>Document Studio</span>
          </div>
          <div class="top-bar-meta">
            <span class="meta-name">{source_name}</span>
            <span class="meta-dim">• {img_w} × {img_h} px</span>
            <span class="meta-badge">{mode_desc}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Equal, Symmetrical Dual-Pane Workspace
        col1, col2 = st.columns(2, gap="medium")

        # --- COLUMN 1: BOUNDARY EDITOR ---
        with col1:
            st.markdown(f"""
            <div class="panel-header">
              <div class="panel-title-group">
                <span class="panel-dot"></span>
                <span>Ảnh gốc & Căn chỉnh viền</span>
              </div>
              <span class="panel-badge">{mode_desc}</span>
            </div>
            """, unsafe_allow_html=True)

            updated_corners, updated_is_manual = render_quad_editor(
                image_bgr=raw_cv_img,
                corners=active_corners,
                auto_corners=detection.corners if detection.corners is not None else active_corners,
                is_manual=is_manual_mode,
                key=f"quad_editor_{st.session_state['current_img_hash'][:10]}",
                display_max_dim=1050,
            )

            if (updated_is_manual != is_manual_mode) or not np.allclose(updated_corners, active_corners, atol=0.5):
                st.session_state["active_corners"] = updated_corners
                st.session_state["is_manual_mode"] = updated_is_manual
                active_corners = updated_corners
                is_manual_mode = updated_is_manual

            st.markdown(
                '<div class="panel-footer">💡 Kéo 4 góc đỏ để nắn phối cảnh • Kéo điểm vàng để uốn theo nếp cong</div>',
                unsafe_allow_html=True
            )

        # --- COLUMN 2: ENHANCED RESULT ---
        with col2:
            st.markdown("""
            <div class="panel-header">
              <div class="panel-title-group">
                <span class="panel-dot panel-dot-green"></span>
                <span>Bản scan hoàn thiện</span>
              </div>
              <span class="panel-badge">Xử lý tự động</span>
            </div>
            """, unsafe_allow_html=True)

            # Compact single-row control strip: Filter pills + Ink boost slider
            ctrl_col1, ctrl_col2 = st.columns([1.4, 1.0], gap="small")
            with ctrl_col1:
                filter_mode = st.radio(
                    "Bộ lọc ảnh",
                    ["Màu thông minh", "Xám mịn", "Đen trắng", "Màu gốc"],
                    index=0,
                    horizontal=True,
                    label_visibility="collapsed"
                )
            with ctrl_col2:
                contrast_boost = st.slider(
                    "Độ đậm nét chữ (Ink Boost)",
                    min_value=1.0,
                    max_value=4.0,
                    value=2.2,
                    step=0.2,
                    label_visibility="collapsed",
                    help="Độ đậm nét chữ (Ink Boost): 1.0 - 4.0"
                )

            # Warp processing
            if is_manual_mode:
                warped = four_point_transform(raw_cv_img, active_corners)
            else:
                if detection.corners is not None:
                    warped = warp_from_result(raw_cv_img, detection)
                else:
                    warped = four_point_transform(raw_cv_img, active_corners)

            if warped is not None:
                boost_to_apply = contrast_boost if filter_mode != "Màu gốc" else 1.0

                if filter_mode == "Màu thông minh":
                    final_img = magic_color_document(warped, contrast_boost=boost_to_apply)
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)
                elif filter_mode == "Xám mịn":
                    final_img = magic_gray_document(warped, contrast_boost=boost_to_apply)
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_GRAY2RGB)
                elif filter_mode == "Đen trắng":
                    final_img = thresh_document(warped, contrast_boost=boost_to_apply)
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_GRAY2RGB)
                else:
                    final_img = warped
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)

                st.image(display_rgb, use_container_width=True)
                final_h, final_w = final_img.shape[:2]
                transform_label = "Phối cảnh 4 góc" if is_manual_mode else "Lưới Coons Patch khử uốn cong"
                st.markdown(
                    f'<div class="panel-footer" style="text-align: center;">{final_w} × {final_h} px • {transform_label}</div>',
                    unsafe_allow_html=True
                )

        # --- EXPORT & AI ACTION DOCK ---
        st.markdown('<div class="export-dock"><div class="export-dock-title">XUẤT BẢN TÀI LIỆU</div></div>', unsafe_allow_html=True)

        exp_col1, exp_col2, exp_col3 = st.columns(3, gap="small")

        # 1. Download PDF
        with exp_col1:
            pdf_bytes = generate_pdf_bytes(final_img)
            st.download_button(
                label="Xuất file PDF (A4)",
                data=pdf_bytes,
                file_name=f"{source_name}_scanned.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        # 2. Download DOCX Layout
        with exp_col2:
            docx_layout_bytes = generate_docx_bytes(final_img, title=f"Tài Liệu - {source_name}")
            st.download_button(
                label="Xuất file Word (.docx)",
                data=docx_layout_bytes,
                file_name=f"{source_name}_scanned.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

        # 3. AI Smart Reconstruction
        with exp_col3:
            ai_key_to_use = st.session_state.get("gemini_api_key_input", "")
            if st.button("Tái tạo văn bản bằng AI", type="primary", use_container_width=True, help="Tái tạo lại văn bản, bảng biểu, danh sách thành file Word thật sự qua Gemini"):
                with st.spinner(f"Đang phân tích cấu trúc qua {ai_model}..."):
                    ai_text, ai_docx, ai_data = perform_ai_ocr_and_export_docx(
                        final_img,
                        lang=ocr_lang,
                        api_key=ai_key_to_use,
                        model=ai_model
                    )
                st.session_state["ai_text"] = ai_text
                st.session_state["ai_docx"] = ai_docx
                st.session_state["ai_data"] = ai_data

        # AI Result Summary (Clean, fixed scroll container)
        if "ai_docx" in st.session_state and st.session_state["ai_docx"]:
            ai_data = st.session_state.get("ai_data", {})
            blocks = ai_data.get("blocks", [])

            p_count = sum(1 for b in blocks if b.get("type") == "paragraph")
            h_count = sum(1 for b in blocks if b.get("type") == "heading")
            t_count = sum(1 for b in blocks if b.get("type") == "table")
            l_count = sum(1 for b in blocks if b.get("type") == "list")

            structure_desc = f"{h_count} tiêu đề • {p_count} đoạn văn • {t_count} bảng dữ liệu • {l_count} danh sách"

            st.markdown(f"""
            <div class="ai-box">
              <div class="ai-box-header">
                <span style="font-weight: 600; color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important;">Cấu trúc tài liệu tái tạo bởi AI</span>
                <span class="ai-badge">{structure_desc}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            ai_dl1, ai_dl2 = st.columns([1, 2], gap="small")
            with ai_dl1:
                st.download_button(
                    label="Tải file Word (.docx) đã tái tạo",
                    data=st.session_state["ai_docx"],
                    file_name=f"{source_name}_ai_reconstructed.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            with ai_dl2:
                with st.expander("Xem chi tiết văn bản", expanded=False):
                    st.text_area("Nội dung tài liệu:", value=st.session_state.get("ai_text", ""), height=150, label_visibility="collapsed")


elif app_mode == "Chuyển đổi DOCX sang PDF":
    # Mode 2: Clean DOCX to PDF Converter
    st.markdown("""
    <div class="top-bar">
      <div class="top-bar-title">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2.2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
        Chuyển Đổi DOCX sang PDF
      </div>
    </div>
    """, unsafe_allow_html=True)

    upload_word = st.file_uploader(
        "Kéo thả hoặc duyệt tập tin Word (.docx):",
        type=["docx"]
    )

    if upload_word is not None:
        file_size_kb = upload_word.size / 1024
        st.markdown(f"""
        <div class="top-bar-meta" style="margin-bottom: 12px;">
          <span class="meta-name">{upload_word.name}</span>
          <span class="meta-dim">({file_size_kb:.1f} KB) • Sẵn sàng chuyển đổi</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Bắt đầu chuyển đổi sang PDF", type="primary"):
            with st.spinner("Microsoft Word đang xử lý chuyển đổi tài liệu..."):
                try:
                    docx_raw_bytes = upload_word.getvalue()
                    pdf_result_bytes = convert_docx_bytes_to_pdf_bytes(docx_raw_bytes)

                    st.success("Chuyển đổi tài liệu thành công.")
                    out_pdf_name = f"{Path(upload_word.name).stem}.pdf"

                    st.download_button(
                        label=f"Tải File PDF ({out_pdf_name})",
                        data=pdf_result_bytes,
                        file_name=out_pdf_name,
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Lỗi khi chuyển đổi tài liệu: {e}")
