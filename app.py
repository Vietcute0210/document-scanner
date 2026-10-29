"""
Streamlit Web UI for Document Scanner & Converter Studio.
Supports:
1. Image capture directly via webcam/camera (st.camera_input), file upload, or sample document selection.
2. Automatic page corner & curved boundary detection.
3. Interactive Quad Manual Editor: drag corner points (red dots) or drag straight edges (orange midpoints)
   with real-time magnification and convexity constraints (guaranteed strictly straight lines / no curves).
4. Perspective transformation & intelligent document enhancement (Magic Color / Crisp B&W).
5. Export to PDF (.pdf) and Word (.docx) with standard A4 layout.
6. Optical Character Recognition (OCR) to extract editable text into Word.
7. 1-click DOCX to PDF converter using Microsoft Word COM automation.
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
from src.transform import warp_from_result, four_point_transform, sample_curved_boundary
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
        # Fallback using PIL
        if img_input.ndim == 2:
            pil_img = Image.fromarray(img_input).convert("RGB")
        else:
            pil_img = Image.fromarray(cv2.cvtColor(img_input, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        pil_img.save(buf, format="PDF", resolution=dpi)
        return buf.getvalue()


def generate_docx_bytes(img_input: np.ndarray, title: str = "Tài Liệu Đã Quét") -> bytes:
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
        run.font.size = Pt(16)

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


def perform_ocr_and_export_docx(img_input: np.ndarray, lang: str = "en") -> Tuple[str, bytes]:
    """Runs OCR and generates an editable Word DOCX file."""
    text = ""
    try:
        text = extract_text_from_image(img_input, lang=lang)
    except Exception as e:
        text = f"(Không thể kích hoạt OCR tự động: {e})"

    import docx
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("Văn Bản Trích Xuất (OCR Editable Text)")
    r_title.bold = True
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(16)

    for line in text.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        p = doc.add_paragraph()
        r = p.add_run(line_clean)
        r.font.name = "Calibri"
        r.font.size = Pt(12)

    buf = io.BytesIO()
    doc.save(buf)
    return text, buf.getvalue()


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


# --- STREAMLIT PAGE CONFIG & STYLES ---

st.set_page_config(
    page_title="Document Scanner & Converter Studio",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# --- SIDEBAR SETTINGS ---

st.sidebar.title("⚙️ Cấu Hình Máy Quét")

app_mode = st.sidebar.radio(
    "Chọn Chức Năng:",
    ["📄 Quét & Xuất Tài Liệu", "🔄 Chuyển Đổi DOCX sang PDF"]
)

st.sidebar.markdown("---")

if app_mode == "📄 Quét & Xuất Tài Liệu":
    st.sidebar.subheader("Bộ Lọc & Xử Lý Ảnh")
    boundary_mode_label = st.sidebar.selectbox(
        "Số điểm neo nhận diện viền:",
        [
            "8 điểm (4 Góc + 4 Trung điểm - Khuyên dùng)",
            "12 điểm (Bám sát giấy uốn cong)",
            "6 điểm (4 Góc + 2 Trung điểm Trên/Dưới)",
            "4 điểm (Tứ giác cơ bản)",
        ],
        index=0,
        help="Sử dụng 8 hoặc 12 điểm neo giúp bám sát mép vở bị cong/bo góc và nắn phẳng bằng lưới Coons Patch.",
    )
    num_points_map = {
        "8 điểm (4 Góc + 4 Trung điểm - Khuyên dùng)": 8,
        "12 điểm (Bám sát giấy uốn cong)": 12,
        "6 điểm (4 Góc + 2 Trung điểm Trên/Dưới)": 6,
        "4 điểm (Tứ giác cơ bản)": 4,
    }
    num_points = num_points_map[boundary_mode_label]
    use_clahe = st.sidebar.checkbox("Khử bóng & Cân bằng sáng (CLAHE)", value=False, help="Hữu ích khi chụp tài liệu bị sấp bóng hoặc ánh sáng không đều")
    max_dim = st.sidebar.slider("Độ phân giải phát hiện viền (max dim)", min_value=600, max_value=2000, value=1200, step=100)
    output_style = st.sidebar.selectbox(
        "Kiểu ảnh xuất:",
        [
            "✨ Scan thông minh (Magic Color - Nền trắng, chữ rõ nét)",
            "🖋️ Scan xám mịn (Magic Gray - Chống răng cưa, nét tự nhiên)",
            "📄 Scan đen trắng (B&W High-Contrast)",
            "🖼️ Ảnh màu nắn phẳng (Color Deskewed)",
        ]
    )
    contrast_boost = st.sidebar.slider(
        "Độ đậm nét chữ (Ink Boost):",
        min_value=1.0,
        max_value=4.0,
        value=2.2,
        step=0.2,
        help="Tăng giá trị nếu ảnh chụp bị mờ, nét bút nhạt hoặc ánh sáng phòng bị chói",
    )
    ocr_lang = st.sidebar.selectbox(
        "Ngôn ngữ OCR (Trích xuất chữ):",
        ["en", "vi"],
        format_func=lambda x: "Tiếng Anh (en)" if x == "en" else "Tiếng Việt (vi)"
    )


# --- MAIN APP ROUTING ---

if app_mode == "📄 Quét & Xuất Tài Liệu":
    st.markdown('<div class="main-header">📄 Document Scanner Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Tự động nhận diện 4 góc, cho phép chỉnh tay kéo góc & cạnh (đường thẳng), nắn phẳng và xuất PDF / Word chuẩn A4</div>', unsafe_allow_html=True)

    # Input method tabs
    tab_cam, tab_upload, tab_sample = st.tabs([
        "📷 Chụp Trực Tiếp Từ Camera",
        "📁 Tải Ảnh Lên Từ Máy Tính",
        "🖼️ Dùng Ảnh Mẫu Có Sẵn"
    ])

    new_img_detected = None
    new_source_name = None

    with tab_cam:
        st.write("Bật camera/webcam và hướng về phía tài liệu:")
        camera_photo = st.camera_input("Chụp ảnh tài liệu")
        if camera_photo is not None:
            bytes_data = camera_photo.getvalue()
            new_img_detected = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            new_source_name = "camera_capture"

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Chọn file ảnh chụp tài liệu (JPG, PNG, WEBP):",
            type=["jpg", "jpeg", "png", "webp", "bmp"]
        )
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            new_img_detected = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            new_source_name = Path(uploaded_file.name).stem

    with tab_sample:
        sample_dir = Path("documents/raw")
        sample_files = list(sample_dir.glob("*.jpg")) + list(sample_dir.glob("*.png"))
        if sample_files:
            sample_names = [f.name for f in sample_files]
            selected_sample = st.selectbox("Chọn một ảnh mẫu từ tập dữ liệu thử nghiệm:", sample_names)
            btn_load_sample = st.button("Tải và Quét Ảnh Mẫu Này")

            if btn_load_sample:
                sample_path = sample_dir / selected_sample
                new_img_detected = cv2.imread(str(sample_path))
                new_source_name = Path(selected_sample).stem
            elif "raw_cv_img" not in st.session_state:
                # Load first sample by default on initial app launch
                sample_path = sample_dir / sample_names[0]
                new_img_detected = cv2.imread(str(sample_path))
                new_source_name = Path(sample_names[0]).stem
        else:
            st.info("Chưa tìm thấy ảnh trong thư mục documents/raw")

    # Persist uploaded/selected image across Streamlit rerun cycles
    if new_img_detected is not None:
        new_hash = hashlib.md5(new_img_detected.tobytes()).hexdigest()
        old_hash = st.session_state.get("current_img_hash")
        if new_hash != old_hash:
            st.session_state["raw_cv_img"] = new_img_detected
            st.session_state["source_name"] = new_source_name or "document"
            st.session_state["current_img_hash"] = new_hash
            # Force auto redetection for new image
            st.session_state["needs_detection"] = True

    raw_cv_img = st.session_state.get("raw_cv_img")
    source_name = st.session_state.get("source_name", "document")

    # --- PROCESSING PIPELINE ---
    if raw_cv_img is not None:
        st.markdown("---")
        img_h, img_w = raw_cv_img.shape[:2]
        current_detect_params = (max_dim, use_clahe, num_points)
        cached_params = st.session_state.get("last_detect_params")
        needs_detection = st.session_state.get("needs_detection", False) or (current_detect_params != cached_params)

        if needs_detection or "detection" not in st.session_state:
            with st.spinner("Đang nhận diện viền tài liệu tự động..."):
                detection = detect_page_corners(
                    raw_cv_img,
                    max_dim=max_dim,
                    use_clahe=use_clahe,
                    num_points=num_points,
                )
            st.session_state["detection"] = detection
            st.session_state["last_detect_params"] = current_detect_params
            st.session_state["needs_detection"] = False

            # Initialize corners from detection or default quad
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

        col1, col2 = st.columns(2)

        # --- COLUMN 1: INTERACTIVE QUAD EDITOR ---
        with col1:
            st.subheader("1. Căn Chỉnh Viền & Điểm Neo")

            # Render interactive component
            updated_corners, updated_is_manual = render_quad_editor(
                image_bgr=raw_cv_img,
                corners=active_corners,
                auto_corners=detection.corners if detection.corners is not None else active_corners,
                is_manual=is_manual_mode,
                key=f"quad_editor_{st.session_state['current_img_hash'][:10]}",
                display_max_dim=1050,
            )

            # Check if user updated quad
            if (updated_is_manual != is_manual_mode) or not np.allclose(updated_corners, active_corners, atol=0.5):
                st.session_state["active_corners"] = updated_corners
                st.session_state["is_manual_mode"] = updated_is_manual
                active_corners = updated_corners
                is_manual_mode = updated_is_manual

            if is_manual_mode:
                st.info(
                    "✏️ **Chế độ chỉnh tay (Đường thẳng):** Bạn có thể kéo tự do 4 chấm đỏ (góc) hoặc 4 chấm cam (cả cạnh). Viền luôn giữ thẳng tuyệt đối. Nhấn **↺ Về Tự Động** nếu muốn khôi phục."
                )
            elif detection.corners is not None:
                b_count = len(detection.boundary_points) if detection.boundary_points is not None else 4
                st.success(
                    f"🟢 **Tự động nhận diện:** Thuật toán **{detection.method}** ({b_count} điểm neo) | Độ tin cậy: **{detection.score:.2f}**. (Kéo bất kỳ điểm đỏ/cam nào nếu muốn căn chỉnh lại bằng tay)."
                )
            else:
                st.warning("⚠️ Chưa tự động nhận diện được 4 góc rõ ràng. Bạn hãy kéo các chấm đỏ để căn chuẩn tài liệu.")

        # --- COLUMN 2: RESULT & ENHANCEMENT ---
        with col2:
            st.subheader("2. Kết Quả Scan Hoàn Thiện")

            if is_manual_mode:
                # Manual mode: strictly straight-line 4-point homography warp (no curves)
                warped = four_point_transform(raw_cv_img, active_corners)
            else:
                # Auto mode: use multi-point Coons patch curved warp if available, else 4-point
                if detection.corners is not None:
                    warped = warp_from_result(raw_cv_img, detection)
                else:
                    warped = four_point_transform(raw_cv_img, active_corners)

            if warped is not None:
                # Apply document enhancement
                if "Magic Color" in output_style:
                    final_img = magic_color_document(warped, contrast_boost=contrast_boost)
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)
                elif "Magic Gray" in output_style:
                    final_img = magic_gray_document(warped, contrast_boost=contrast_boost)
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_GRAY2RGB)
                elif "B&W" in output_style:
                    final_img = thresh_document(warped, contrast_boost=contrast_boost)
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_GRAY2RGB)
                else:
                    final_img = warped
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)

                st.image(display_rgb, use_container_width=True)
                final_h, final_w = final_img.shape[:2]
                st.caption(f"Kích thước tài liệu sau khi nắn: {final_w} x {final_h} px | Chế độ: {'Tứ giác thẳng (Chỉnh tay)' if is_manual_mode else 'Tự động'}")

        # --- EXPORT & DOWNLOAD SECTION ---
        st.markdown("---")
        st.subheader("📥 Xuất Tài Liệu & Tải Về")

        btn_col1, btn_col2, btn_col3 = st.columns(3)

        # 1. Download PDF Button
        with btn_col1:
            pdf_bytes = generate_pdf_bytes(final_img)
            st.download_button(
                label="📄 Tải File PDF (.pdf)",
                data=pdf_bytes,
                file_name=f"{source_name}_scanned.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.caption("Khổ A4 chuẩn nét, tương thích mọi máy in")

        # 2. Download DOCX Image Layout Button
        with btn_col2:
            docx_layout_bytes = generate_docx_bytes(final_img, title=f"Tài Liệu Quét - {source_name}")
            st.download_button(
                label="📝 Tải File Word (.docx) - Bản Scan",
                data=docx_layout_bytes,
                file_name=f"{source_name}_scanned.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
            st.caption("Nhúng trang scan chuẩn lề trang A4")

        # 3. OCR Text Extraction Button
        with btn_col3:
            if st.button("🔍 Trích Xuất Chữ (OCR) Ra Word", use_container_width=True):
                with st.spinner("Đang chạy OCR nhận diện văn bản..."):
                    extracted_text, ocr_docx_bytes = perform_ocr_and_export_docx(warped, lang=ocr_lang)

                st.session_state["ocr_text"] = extracted_text
                st.session_state["ocr_docx_bytes"] = ocr_docx_bytes

            if "ocr_docx_bytes" in st.session_state:
                st.download_button(
                    label="💾 Tải Word Văn Bản OCR (.docx)",
                    data=st.session_state["ocr_docx_bytes"],
                    file_name=f"{source_name}_ocr_text.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

        if "ocr_text" in st.session_state and st.session_state["ocr_text"]:
            with st.expander("📖 Xem trước nội dung văn bản nhận dạng được (OCR Text Preview)", expanded=True):
                st.text_area("Nội dung trích xuất:", value=st.session_state["ocr_text"], height=160)


elif app_mode == "🔄 Chuyển Đổi DOCX sang PDF":
    st.markdown('<div class="main-header">🔄 Chuyển Đổi Word (.docx) sang PDF (.pdf)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Sử dụng Microsoft Word Engine để chuyển đổi tài liệu giữ nguyên 100% định dạng, font chữ và căn lề</div>', unsafe_allow_html=True)

    upload_word = st.file_uploader(
        "Kéo thả hoặc tải lên tập tin Word (.docx):",
        type=["docx"]
    )

    if upload_word is not None:
        st.write(f"Đã chọn: **{upload_word.name}** ({upload_word.size / 1024:.1f} KB)")

        if st.button("🚀 Bắt Đầu Chuyển Đổi Sang PDF", type="primary"):
            with st.spinner("Microsoft Word đang xử lý chuyển đổi tài liệu..."):
                try:
                    docx_raw_bytes = upload_word.getvalue()
                    pdf_result_bytes = convert_docx_bytes_to_pdf_bytes(docx_raw_bytes)

                    st.success("🎉 Chuyển đổi thành công 100%!")
                    out_pdf_name = f"{Path(upload_word.name).stem}.pdf"

                    st.download_button(
                        label=f"📥 Tải Về File PDF Hoàn Tất ({out_pdf_name})",
                        data=pdf_result_bytes,
                        file_name=out_pdf_name,
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Lỗi khi chuyển đổi tài liệu: {e}")
