"""
Streamlit Web UI for Document Scanner & Converter.
Supports:
1. Image capture directly via webcam/camera (st.camera_input) or file upload.
2. Perspective transformation & adaptive thresholding (scanned look).
3. Export to PDF (.pdf) and Word (.docx) with standard A4 layout.
4. Optical Character Recognition (OCR) to extract editable text into Word.
5. 1-click DOCX to PDF converter using Microsoft Word COM automation.
"""

import io
from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np
from PIL import Image
import streamlit as st

# Core CV imports from src
from src.detect_page import detect_page_corners
from src.transform import warp_from_result
from src.thresholding import thresh_document


# --- HELPER EXPORT FUNCTIONS (Self-contained & compatible with src.export / src.converter / src.ocr_engine) ---

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
    # Try using winocr
    try:
        import winocr
        if img_input.ndim == 2:
            bgr = cv2.cvtColor(img_input, cv2.COLOR_GRAY2BGR)
        else:
            bgr = img_input
        res = winocr.recognize_cv2_sync(bgr, lang=lang)
        text = res.get("text", "").strip()
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
    use_clahe = st.sidebar.checkbox("Khử bóng & Cân bằng sáng (CLAHE)", value=False, help="Hữu ích khi chụp tài liệu bị sấp bóng hoặc ánh sáng không đều")
    max_dim = st.sidebar.slider("Độ phân giải phát hiện viền (max dim)", min_value=600, max_value=2000, value=1200, step=100)
    output_style = st.sidebar.selectbox(
        "Kiểu ảnh xuất:",
        ["Ảnh scan trắng đen (B&W High-Contrast)", "Ảnh màu nắn phẳng (Color Deskewed)"]
    )
    ocr_lang = st.sidebar.selectbox(
        "Ngôn ngữ OCR (Trích xuất chữ):",
        ["en", "vi"],
        format_func=lambda x: "Tiếng Anh (en)" if x == "en" else "Tiếng Việt (vi)"
    )


# --- MAIN APP ROUTING ---

if app_mode == "📄 Quét & Xuất Tài Liệu":
    st.markdown('<div class="main-header">📄 Document Scanner Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Tự động nhận diện 4 góc, nắn thẳng góc phối cảnh và xuất tài liệu PDF / Word chuẩn A4</div>', unsafe_allow_html=True)

    # Input method tabs
    tab_cam, tab_upload, tab_sample = st.tabs([
        "📷 Chụp Trực Tiếp Từ Camera",
        "📁 Tải Ảnh Lên Từ Máy Tính",
        "🖼️ Dùng Ảnh Mẫu Có Sẵn"
    ])

    raw_cv_img = None
    source_name = "document"

    with tab_cam:
        st.write("Bật camera/webcam và hướng về phía tài liệu:")
        camera_photo = st.camera_input("Chụp ảnh tài liệu")
        if camera_photo is not None:
            bytes_data = camera_photo.getvalue()
            raw_cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            source_name = "camera_capture"

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Chọn file ảnh chụp tài liệu (JPG, PNG, WEBP):",
            type=["jpg", "jpeg", "png", "webp", "bmp"]
        )
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            raw_cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            source_name = Path(uploaded_file.name).stem

    with tab_sample:
        sample_dir = Path("documents/raw")
        sample_files = list(sample_dir.glob("*.jpg")) + list(sample_dir.glob("*.png"))
        if sample_files:
            sample_names = [f.name for f in sample_files]
            selected_sample = st.selectbox("Chọn một ảnh mẫu từ tập dữ liệu thử nghiệm:", sample_names)
            if st.button("Tải và Quét Ảnh Mẫu Này"):
                sample_path = sample_dir / selected_sample
                raw_cv_img = cv2.imread(str(sample_path))
                source_name = Path(selected_sample).stem
        else:
            st.info("Chưa tìm thấy ảnh trong thư mục documents/raw")

    # --- PROCESSING PIPELINE ---
    if raw_cv_img is not None:
        st.markdown("---")
        with st.spinner("Đang nhận diện viền tài liệu và xử lý nắn thẳng..."):
            detection = detect_page_corners(raw_cv_img, max_dim=max_dim, use_clahe=use_clahe)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("1. Ảnh Gốc & Đường Bao Nhận Diện")
            overlay = raw_cv_img.copy()
            if detection.corners is not None:
                pts = detection.corners.reshape(-1, 1, 2).astype("int32")
                cv2.polylines(overlay, [pts], True, (0, 255, 0), max(3, int(overlay.shape[1] / 300)))
                for (x, y) in detection.corners:
                    cv2.circle(overlay, (int(x), int(y)), max(8, int(overlay.shape[1] / 150)), (0, 0, 255), -1)
                st.image(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB), use_container_width=True)
                st.success(f"Thuật toán: **{detection.method}** | Điểm tin cậy: **{detection.score:.2f}**")
            else:
                st.image(cv2.cvtColor(raw_cv_img, cv2.COLOR_BGR2RGB), use_container_width=True)
                st.warning("Không nhận diện được rõ 4 góc viền tài liệu. Sẽ giữ nguyên toàn bộ ảnh.")

        with col2:
            st.subheader("2. Kết Quả Scan Hoàn Thiện")
            if detection.corners is not None:
                warped = warp_from_result(raw_cv_img, detection)
            else:
                warped = raw_cv_img.copy()

            if warped is not None:
                thresh_scan = thresh_document(warped)
                
                # Determine display image based on sidebar selection
                if "B&W" in output_style:
                    final_img = thresh_scan
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_GRAY2RGB)
                else:
                    final_img = warped
                    display_rgb = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)

                st.image(display_rgb, use_container_width=True)
                h, w = final_img.shape[:2]
                st.caption(f"Kích thước tài liệu sau khi nắn: {w} x {h} px")

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
