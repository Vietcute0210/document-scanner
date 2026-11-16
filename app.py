"""
Streamlit Web UI for Document Scanner & Converter Studio.
Professional, minimalist document digitizer, boundary editor,
enhancement engine, and AI-powered document reconstruction studio.
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


# --- STREAMLIT PAGE CONFIG & DESIGN SYSTEM ---

st.set_page_config(
    page_title="Document Studio",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Document Studio Modern Minimalist Design System */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Studio Header */
    .studio-header {
        margin-bottom: 1.1rem;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid #e2e8f0;
    }
    .studio-title-row {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .studio-logo {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.025em;
    }
    .studio-badge {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 8px;
        background: #f1f5f9;
        color: #475569;
        border-radius: 9999px;
        border: 1px solid #e2e8f0;
    }
    .studio-subtitle {
        font-size: 0.9rem;
        color: #64748b;
        margin-top: 3px;
        margin-bottom: 0;
    }

    /* Document Status Bar */
    .doc-status-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 9px 14px;
        margin-bottom: 1rem;
        font-size: 0.85rem;
    }
    .doc-name {
        font-weight: 600;
        color: #0f172a;
    }
    .doc-meta {
        color: #64748b;
        font-size: 0.8rem;
    }

    /* Pane Titles */
    .pane-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.6rem;
    }

    /* Status Notes */
    .status-note {
        font-size: 0.82rem;
        padding: 8px 12px;
        border-radius: 6px;
        margin-top: 8px;
        line-height: 1.4;
    }
    .note-auto {
        background: #f0fdf4;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    .note-manual {
        background: #fffbeb;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    .note-warn {
        background: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }

    /* Dimension caption */
    .doc-dim-caption {
        font-size: 0.78rem;
        color: #64748b;
        text-align: center;
        margin-top: 6px;
    }

    /* AI Summary Card */
    .ai-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 14px;
        margin-top: 1rem;
    }
    .ai-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .ai-card-title {
        font-weight: 600;
        font-size: 0.92rem;
        color: #0f172a;
    }
    .ai-badge-tag {
        font-size: 0.78rem;
        color: #475569;
        background: #f1f5f9;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
    }

    /* Action bar */
    .export-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        margin-top: 0.5rem;
    }

    /* Streamlit controls refinement */
    div[data-testid="stRadio"] > label {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #334155 !important;
    }
    div.stButton > button, div.stDownloadButton > button {
        border-radius: 6px;
        font-size: 0.88rem;
        font-weight: 500;
        transition: all 0.15s ease;
    }
</style>
""", unsafe_allow_html=True)


# --- SIDEBAR NAVIGATION & SETTINGS ---

st.sidebar.markdown("### Document Studio")
app_mode = st.sidebar.radio(
    "Chế độ làm việc",
    ["Quét tài liệu", "Chuyển đổi DOCX sang PDF"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

if app_mode == "Quét tài liệu":
    st.sidebar.markdown("#### Cấu hình AI Vision")
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
    # Mode DOCX to PDF: clean sidebar
    num_points = 8
    use_clahe = False
    max_dim = 1200
    ocr_lang = "vi"
    ai_model = "gemini-2.5-flash"


# --- MAIN APP ROUTING ---

if app_mode == "Quét tài liệu":
    # Studio Header
    st.markdown("""
    <div class="studio-header">
      <div class="studio-title-row">
        <span class="studio-logo">Document Studio</span>
        <span class="studio-badge">Studio</span>
      </div>
      <p class="studio-subtitle">Số hóa, căn chỉnh phối cảnh và tái tạo tài liệu chuẩn in ấn</p>
    </div>
    """, unsafe_allow_html=True)

    new_img_detected = None
    new_source_name = None

    # Compact Input Section
    has_active_image = "raw_cv_img" in st.session_state and st.session_state["raw_cv_img"] is not None

    with st.expander("Nguồn ảnh đầu vào", expanded=(not has_active_image)):
        tab_upload, tab_cam, tab_sample = st.tabs([
            "Tải ảnh lên",
            "Chụp từ Camera",
            "Ảnh mẫu thử nghiệm"
        ])

        with tab_upload:
            uploaded_file = st.file_uploader(
                "Chọn tập tin ảnh tài liệu:",
                type=["jpg", "jpeg", "png", "webp", "bmp"],
                help="Hỗ trợ các định dạng ảnh phổ biến"
            )
            if uploaded_file is not None:
                bytes_data = uploaded_file.getvalue()
                new_img_detected = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                new_source_name = Path(uploaded_file.name).stem

        with tab_cam:
            camera_photo = st.camera_input("Chụp ảnh tài liệu qua webcam")
            if camera_photo is not None:
                bytes_data = camera_photo.getvalue()
                new_img_detected = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                new_source_name = "camera_capture"

        with tab_sample:
            sample_dir = Path("documents/sample")
            sample_files = sorted(list(sample_dir.glob("*.jpg")) + list(sample_dir.glob("*.png")))
            if sample_files:
                sample_labels = {
                    "sample1.jpg": "Mẫu 1: Tài liệu in tiêu chuẩn (phẳng)",
                    "sample2.jpg": "Mẫu 2: Chụp nghiêng góc 45°",
                    "sample3.jpg": "Mẫu 3: Mép viền mờ sát nền",
                    "sample4.jpg": "Mẫu 4: Vở kẻ ô cong mép (GNHK)",
                    "sample5.jpg": "Mẫu 5: Ánh sáng phức tạp & bóng râm",
                }
                sample_names = [f.name for f in sample_files]
                selected_sample = st.selectbox(
                    "Chọn tài liệu mẫu:",
                    sample_names,
                    format_func=lambda x: sample_labels.get(x, x)
                )
                if st.button("Tải mẫu này"):
                    sample_path = sample_dir / selected_sample
                    new_img_detected = cv2.imread(str(sample_path))
                    new_source_name = Path(selected_sample).stem
                elif not has_active_image:
                    sample_path = sample_dir / sample_names[0]
                    new_img_detected = cv2.imread(str(sample_path))
                    new_source_name = Path(sample_names[0]).stem

    # Cache loaded image
    if new_img_detected is not None:
        new_hash = hashlib.md5(new_img_detected.tobytes()).hexdigest()
        old_hash = st.session_state.get("current_img_hash")
        if new_hash != old_hash:
            st.session_state["raw_cv_img"] = new_img_detected
            st.session_state["source_name"] = new_source_name or "document"
            st.session_state["current_img_hash"] = new_hash
            st.session_state["needs_detection"] = True

    raw_cv_img = st.session_state.get("raw_cv_img")
    source_name = st.session_state.get("source_name", "document")

    # --- WORKSPACE PIPELINE ---
    if raw_cv_img is not None:
        img_h, img_w = raw_cv_img.shape[:2]

        # Top Document Status Bar
        st.markdown(f"""
        <div class="doc-status-bar">
          <div>
            <span class="doc-name">{source_name}</span>
            <span class="doc-meta" style="margin-left: 8px;">({img_w} × {img_h} px)</span>
          </div>
          <span class="doc-meta">Đang xử lý</span>
        </div>
        """, unsafe_allow_html=True)

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

        col1, col2 = st.columns([1, 1], gap="medium")

        # --- COLUMN 1: INTERACTIVE QUAD EDITOR ---
        with col1:
            st.markdown('<div class="pane-title">Căn chỉnh viền tài liệu</div>', unsafe_allow_html=True)

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

            if is_manual_mode:
                st.markdown(
                    '<div class="status-note note-manual">Chế độ chỉnh tay: Áp dụng phép biến đổi phối cảnh 4 điểm thẳng.</div>',
                    unsafe_allow_html=True
                )
            elif detection.corners is not None:
                b_count = len(detection.boundary_points) if detection.boundary_points is not None else 4
                st.markdown(
                    f'<div class="status-note note-auto">Tự động phát hiện ({detection.method}, {b_count} điểm neo, độ tin cậy {detection.score:.2f}). Kéo góc để tinh chỉnh.</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    '<div class="status-note note-warn">Chưa xác định được viền rõ ràng. Vui lòng kéo 4 điểm góc để định vị văn bản.</div>',
                    unsafe_allow_html=True
                )

        # --- COLUMN 2: ENHANCED RESULT ---
        with col2:
            st.markdown('<div class="pane-title">Bản quét hoàn thiện</div>', unsafe_allow_html=True)

            # Filter preset bar (clean segmented style)
            filter_options = [
                "Màu thông minh",
                "Xám mịn",
                "Đen trắng",
                "Màu gốc"
            ]
            filter_mode = st.radio(
                "Bộ lọc ảnh",
                filter_options,
                index=0,
                horizontal=True,
                label_visibility="collapsed"
            )

            # Compact ink contrast boost slider
            contrast_boost = 2.2
            if filter_mode != "Màu gốc":
                contrast_boost = st.slider(
                    "Độ đậm nét chữ (Ink Boost):",
                    min_value=1.0,
                    max_value=4.0,
                    value=2.2,
                    step=0.2,
                    help="Tăng nếu nét chữ bị nhạt hoặc phòng quá sáng"
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
                if filter_mode == "Màu thông minh":
                    final_img = magic_color_document(warped, contrast_boost=contrast_boost)
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)
                elif filter_mode == "Xám mịn":
                    final_img = magic_gray_document(warped, contrast_boost=contrast_boost)
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_GRAY2RGB)
                elif filter_mode == "Đen trắng":
                    final_img = thresh_document(warped, contrast_boost=contrast_boost)
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_GRAY2RGB)
                else:
                    final_img = warped
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)

                st.image(display_rgb, use_container_width=True)
                final_h, final_w = final_img.shape[:2]
                st.markdown(
                    f'<div class="doc-dim-caption">{final_w} × {final_h} px • {"Phối cảnh 4 góc" if is_manual_mode else "Lưới Coons Patch khử uốn cong"}</div>',
                    unsafe_allow_html=True
                )

        # --- EXPORT & RECONSTRUCTION DOCK ---
        st.markdown("---")
        st.markdown('<div class="pane-title">Xuất bản tài liệu</div>', unsafe_allow_html=True)

        exp_col1, exp_col2, exp_col3 = st.columns(3)

        # 1. Download PDF
        with exp_col1:
            pdf_bytes = generate_pdf_bytes(final_img)
            st.download_button(
                label="Tải File PDF (.pdf)",
                data=pdf_bytes,
                file_name=f"{source_name}_scanned.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.caption("Khổ A4 chuẩn in ấn")

        # 2. Download DOCX Image Layout
        with exp_col2:
            docx_layout_bytes = generate_docx_bytes(final_img, title=f"Tài Liệu - {source_name}")
            st.download_button(
                label="Tải File Word (.docx)",
                data=docx_layout_bytes,
                file_name=f"{source_name}_scanned.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
            st.caption("Nhúng trang scan vào Word")

        # 3. AI Smart Reconstruction
        with exp_col3:
            ai_key_to_use = st.session_state.get("gemini_api_key_input", "")
            if st.button("Tái tạo văn bản bằng AI", type="primary", use_container_width=True, help="Tái tạo lại văn bản, bảng biểu, danh sách thành file Word thật sự"):
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

            if "ai_docx" in st.session_state and st.session_state["ai_docx"]:
                st.download_button(
                    label="Tải Word Tái Tạo Bởi AI",
                    data=st.session_state["ai_docx"],
                    file_name=f"{source_name}_reconstructed.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            st.caption(f"Tái tạo cấu trúc qua {ai_model}")

        # AI Result Summary (Clean, elegant, no tacky metric counters)
        if "ai_text" in st.session_state and st.session_state["ai_text"]:
            ai_data = st.session_state.get("ai_data", {})
            blocks = ai_data.get("blocks", [])

            p_count = sum(1 for b in blocks if b.get("type") == "paragraph")
            h_count = sum(1 for b in blocks if b.get("type") == "heading")
            t_count = sum(1 for b in blocks if b.get("type") == "table")
            l_count = sum(1 for b in blocks if b.get("type") == "list")

            structure_desc = f"{h_count} tiêu đề • {p_count} đoạn văn • {t_count} bảng dữ liệu • {l_count} danh sách"

            st.markdown(f"""
            <div class="ai-card">
              <div class="ai-card-header">
                <span class="ai-card-title">Cấu trúc tài liệu tái tạo</span>
                <span class="ai-badge-tag">{structure_desc}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("Xem nội dung chi tiết bản thảo", expanded=True):
                st.text_area("Nội dung tài liệu:", value=st.session_state["ai_text"], height=220, label_visibility="collapsed")


elif app_mode == "Chuyển đổi DOCX sang PDF":
    # Mode 2: Clean DOCX to PDF Converter
    st.markdown("""
    <div class="studio-header">
      <div class="studio-title-row">
        <span class="studio-logo">Chuyển Đổi DOCX sang PDF</span>
        <span class="studio-badge">Engine Word</span>
      </div>
      <p class="studio-subtitle">Chuyển đổi tài liệu Word sang PDF chuẩn in ấn, bảo toàn 100% font chữ, lề và định dạng bảng</p>
    </div>
    """, unsafe_allow_html=True)

    upload_word = st.file_uploader(
        "Kéo thả hoặc duyệt tập tin Word (.docx):",
        type=["docx"]
    )

    if upload_word is not None:
        file_size_kb = upload_word.size / 1024
        st.markdown(f"""
        <div class="doc-status-bar">
          <div>
            <span class="doc-name">{upload_word.name}</span>
            <span class="doc-meta" style="margin-left: 8px;">({file_size_kb:.1f} KB)</span>
          </div>
          <span class="doc-meta">Sẵn sàng chuyển đổi</span>
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
