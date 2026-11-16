from pathlib import Path
import io
import sys
import streamlit as st
import cv2
import numpy as np

from src.detect_page import detect_page_corners, DetectionResult
from src.transform import warp_from_result, four_point_transform
from src.thresholding import thresh_document, magic_color_document, magic_gray_document
from src.quad_editor import render_quad_editor
from ui.state.session import set_image, clear_image
from ui.services.documents import generate_pdf_bytes, generate_docx_bytes, perform_ai_reconstruction

FILTERS = ["Màu thông minh", "Xám mịn", "Đen trắng", "Màu gốc"]


def _load_source(settings):
    source = settings.get("source", "Ảnh mẫu")
    if source == "Ảnh mẫu":
        path = settings.get("sample")
        if path:
            image = cv2.imread(str(path))
            if image is not None: set_image(image, path.stem)
    elif source == "Tải ảnh lên":
        uploaded = st.file_uploader("Kéo thả ảnh vào đây hoặc chọn từ thiết bị", type=["jpg", "jpeg", "png", "webp", "bmp"], key=f"scanner_upload_{st.session_state.get('scanner_source_epoch', 0)}")
        if uploaded:
            raw = np.frombuffer(uploaded.getvalue(), np.uint8)
            image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
            if image is None: st.error("Tệp ảnh không hợp lệ hoặc không thể đọc.")
            else: set_image(image, Path(uploaded.name).stem)
    else:
        photo = st.camera_input("Chụp tài liệu", key=f"scanner_camera_{st.session_state.get('scanner_source_epoch', 0)}")
        if photo:
            image = cv2.imdecode(np.frombuffer(photo.getvalue(), np.uint8), cv2.IMREAD_COLOR)
            if image is not None: set_image(image, "camera_capture")


def _detect_if_needed(image, settings):
    params = (settings.get("max_dim", 1200), settings.get("clahe", False), settings.get("num_points", 8))
    if st.session_state.get("detection") is None or st.session_state.get("last_detect_params") != params or st.session_state.get("needs_detection"):
        with st.spinner("Đang phân tích đường viền tài liệu..."):
            result = detect_page_corners(image, max_dim=params[0], use_clahe=params[1], num_points=params[2])
        st.session_state["detection"] = result
        st.session_state["last_detect_params"] = params
        st.session_state["needs_detection"] = False
        h, w = image.shape[:2]
        if result.corners is not None:
            st.session_state["active_corners"] = result.corners.copy()
        else:
            st.session_state["active_corners"] = np.array([[w*.05,h*.05],[w*.95,h*.05],[w*.95,h*.95],[w*.05,h*.95]], dtype=np.float32)
        st.session_state["is_manual_mode"] = False
    return st.session_state["detection"]


def _render_export(final_img, source_name, settings):
    st.markdown("## Xuất tài liệu")
    st.caption("Tải bản scan giữ nguyên hình ảnh hoặc dùng AI tái tạo văn bản có thể chỉnh sửa.")
    pdf_col, docx_col, ai_col = st.columns(3, gap="medium")
    with pdf_col:
        with st.container(border=True):
            st.markdown("### PDF · A4")
            st.caption("Phù hợp lưu trữ và chia sẻ.")
            if st.button("Tạo PDF", key="make_pdf", use_container_width=True):
                try:
                    with st.spinner("Đang tạo PDF..."):
                        st.session_state["pdf_output"] = generate_pdf_bytes(final_img)
                except Exception as exc: st.error(f"Không thể tạo PDF: {exc}")
            if st.session_state.get("pdf_output"):
                st.download_button("Tải PDF", st.session_state["pdf_output"], f"{source_name}_scanned.pdf", "application/pdf", use_container_width=True)
    with docx_col:
        with st.container(border=True):
            st.markdown("### Word · Scan")
            st.caption("Đưa trang scan vào tài liệu Word.")
            if st.button("Tạo Word", key="make_docx", use_container_width=True):
                try:
                    with st.spinner("Đang tạo Word..."):
                        st.session_state["docx_output"] = generate_docx_bytes(final_img, f"Tài liệu - {source_name}")
                except Exception as exc: st.error(f"Không thể tạo Word: {exc}")
            if st.session_state.get("docx_output"):
                st.download_button("Tải Word", st.session_state["docx_output"], f"{source_name}_scanned.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    with ai_col:
        with st.container(border=True):
            st.markdown("### AI · Editable Word")
            st.caption("Tái tạo đoạn văn, tiêu đề, bảng và danh sách.")
            if st.button("Tái tạo bằng AI", type="primary", key="make_ai", use_container_width=True):
                try:
                    with st.spinner(f"Gemini đang phân tích bằng {settings.get('model', 'gemini-2.5-flash')}..."):
                        text, data, structured = perform_ai_reconstruction(final_img, settings.get("lang", "vi"), settings.get("api_key", ""), settings.get("model", "gemini-2.5-flash"))
                    st.session_state["ai_text"], st.session_state["ai_docx"], st.session_state["ai_data"] = text, data, structured
                    st.session_state["ai_result_hash"] = st.session_state.get("final_image_hash")
                    st.success("Đã tái tạo tài liệu.")
                except Exception as exc: st.error(str(exc))
            if st.session_state.get("ai_docx") and st.session_state.get("ai_result_hash") == st.session_state.get("final_image_hash"):
                st.download_button("Tải Word có thể chỉnh sửa", st.session_state["ai_docx"], f"{source_name}_ai_reconstructed.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    if st.session_state.get("ai_result_hash") == st.session_state.get("final_image_hash") and st.session_state.get("ai_text"):
        with st.expander("Xem nội dung AI nhận diện"):
            blocks = st.session_state.get("ai_data", {}).get("blocks", [])
            counts = {kind:sum(1 for b in blocks if b.get("type")==kind) for kind in ("heading","paragraph","table","list")}
            st.caption(f"{counts['heading']} tiêu đề · {counts['paragraph']} đoạn · {counts['table']} bảng · {counts['list']} danh sách")
            st.text_area("Nội dung", st.session_state["ai_text"], height=240, label_visibility="collapsed")


def render_scanner(settings):
    source = settings.get("source", "Ảnh mẫu")
    previous_source = st.session_state.get("scanner_last_source")
    if previous_source is not None and previous_source != source:
        clear_image()
        st.session_state["scanner_source_epoch"] = st.session_state.get("scanner_source_epoch", 0) + 1
    st.session_state.setdefault("scanner_source_epoch", 0)
    st.session_state["scanner_last_source"] = source
    st.markdown('<div class="eyebrow">DOCUMENT WORKSPACE</div>', unsafe_allow_html=True)
    st.title("Quét tài liệu")
    st.markdown('<div class="page-subtitle">Số hóa giấy tờ, căn chỉnh đường viền và xuất bản scan trong một luồng làm việc.</div>', unsafe_allow_html=True)
    _load_source(settings)
    image = st.session_state.get("raw_cv_img")
    if image is None:
        with st.container(border=True):
            st.markdown("### Bắt đầu với một tài liệu")
            st.write("Chọn **Ảnh mẫu**, **Tải ảnh lên** hoặc **Camera** ở thanh điều hướng bên trái.")
            st.info("Mẹo: đặt giấy trên nền tương phản, tránh bóng đổ mạnh và đảm bảo đủ sáng để nhận diện đường viền tốt hơn.")
        return

    result: DetectionResult = _detect_if_needed(image, settings)
    corners = st.session_state.get("active_corners")
    manual = st.session_state.get("is_manual_mode", False)
    h, w = image.shape[:2]
    detected = result.corners is not None
    meta1, meta2, meta3, meta4 = st.columns([2,1,1,1])
    meta1.markdown(f"**{st.session_state.get('source_name','document')}**")
    meta2.metric("Kích thước", f"{w} × {h}")
    meta3.metric("Nhận diện", "Thành công" if detected else "Cần chỉnh tay")
    meta4.metric("Chế độ", "Thủ công" if manual else "Tự động")

    if not detected:
        st.warning("Chưa tìm thấy đường viền đáng tin cậy. Hãy kéo 4 góc để chọn vùng tài liệu thủ công.")
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("### 01 · Ảnh gốc & căn chỉnh")
            st.caption("Kéo các điểm góc để xác định vùng giấy. Với giấy cong, điều chỉnh thêm các điểm neo trung gian.")
            updated, updated_manual = render_quad_editor(image_bgr=image, corners=corners, auto_corners=result.corners if detected else corners, is_manual=manual, key=f"quad_editor_{st.session_state['current_img_hash'][:12]}", display_max_dim=1050)
            if updated_manual != manual or not np.allclose(updated, corners, atol=.5):
                st.session_state["active_corners"] = updated
                st.session_state["is_manual_mode"] = updated_manual
                st.session_state.pop("ai_docx", None); st.session_state.pop("ai_text", None); st.session_state.pop("ai_data", None); st.session_state.pop("ai_result_hash", None)
                corners, manual = updated, updated_manual
            if st.button("Khôi phục đường viền tự động", use_container_width=True, disabled=not detected):
                st.session_state["active_corners"] = result.corners.copy(); st.session_state["is_manual_mode"] = False; st.rerun()
    with right:
        with st.container(border=True):
            st.markdown("### 02 · Bản scan")
            st.caption("Xem trước kết quả sau khi nắn phối cảnh và tăng cường chất lượng ảnh.")
            filter_mode = st.radio("Chế độ hình ảnh", FILTERS, horizontal=True, key="filter_mode", label_visibility="collapsed")
            contrast = st.slider("Độ đậm nét chữ", 1.0, 4.0, 2.2, .2, key="contrast_boost", help="Tăng cường độ đậm của nét chữ.")
            if manual or not detected:
                warped = four_point_transform(image, corners)
            else:
                warped = warp_from_result(image, result)
                if warped is None: warped = four_point_transform(image, corners)
            boost = contrast if filter_mode != "Màu gốc" else 1.0
            if filter_mode == "Màu thông minh": final_img = magic_color_document(warped, contrast_boost=boost); display = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)
            elif filter_mode == "Xám mịn": final_img = magic_gray_document(warped, contrast_boost=boost); display = cv2.cvtColor(final_img, cv2.COLOR_GRAY2RGB)
            elif filter_mode == "Đen trắng": final_img = thresh_document(warped, contrast_boost=boost); display = cv2.cvtColor(final_img, cv2.COLOR_GRAY2RGB)
            else: final_img = warped; display = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)
            st.image(display, use_container_width=True)
            fh, fw = final_img.shape[:2]
            st.caption(f"{fw} × {fh} px · {'Phối cảnh 4 góc' if manual else 'Coons Patch / tự động'}")
    from ui.state.session import image_digest
    final_hash = image_digest(final_img)
    if st.session_state.get("final_image_hash") != final_hash:
        for key in ("pdf_output", "docx_output", "ai_text", "ai_docx", "ai_data", "ai_result_hash"):
            st.session_state.pop(key, None)
        st.session_state["final_image_hash"] = final_hash
    st.session_state["final_img"] = final_img
    st.markdown("---")
    _render_export(final_img, st.session_state.get("source_name", "document"), settings)
