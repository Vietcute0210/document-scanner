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
from src.camera import capture_from_webcam, capture_single_frame
from ui.state.session import set_image, clear_image, image_digest
from ui.services.documents import generate_pdf_bytes, generate_docx_bytes, perform_ai_reconstruction

FILTERS = ["Màu thông minh", "Xám mịn", "Đen trắng", "Màu gốc"]


def _render_camera_viewfinder(epoch: int):
    """Dedicated interactive camera viewfinder and capture options."""
    with st.container(border=True):
        st.markdown("""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
          <div>
            <h3 style="margin: 0; font-size: 1.15rem;">Ống kính Camera · Sẵn sàng quét</h3>
            <p style="margin: 2px 0 0 0; color: #64748B; font-size: 0.85rem;">Chọn chụp trực tiếp qua Webcam phần cứng máy tính hoặc sử dụng Camera trình duyệt.</p>
          </div>
          <span class="meta-badge-success">● Camera Online</span>
        </div>
        """, unsafe_allow_html=True)

        col_hw, col_web = st.columns([1, 1.15], gap="large")

        with col_hw:
            st.markdown("#### 💻 Webcam máy tính (OpenCV)")
            st.caption("Chụp từ webcam phần cứng với độ phân giải cao và tốc độ phản hồi tức thì.")

            if st.button("📸 Chụp ngay 1 ảnh từ Webcam (1-Click)", type="primary", use_container_width=True, key=f"hw_snap_btn_{epoch}"):
                with st.spinner("Đang kết nối camera và bắt khung hình nét nhất..."):
                    frame = capture_single_frame(0)
                    if frame is None:
                        frame = capture_single_frame(1)

                if frame is not None:
                    set_image(frame, "camera_capture")
                    st.success("Đã chụp ảnh tài liệu thành công!")
                    st.rerun()
                else:
                    st.error("Không thể mở thiết bị camera phần cứng. Vui lòng kiểm tra quyền truy cập webcam hoặc chuyển sang Camera Trình duyệt bên cạnh.")

            st.write("")
            if st.button("🎥 Mở xem trước trực tiếp (Phím SPACE)", use_container_width=True, key=f"hw_preview_btn_{epoch}"):
                try:
                    with st.spinner("Đang mở cửa sổ xem trước camera (Nhấn SPACE để chụp, ESC để hủy)..."):
                        frame = capture_from_webcam(0)
                    if frame is not None:
                        set_image(frame, "camera_capture")
                        st.success("Đã chụp ảnh thành công từ cửa sổ xem trước!")
                        st.rerun()
                    else:
                        st.info("Đã hủy chụp từ camera.")
                except Exception as exc:
                    st.error(f"Lỗi khởi động cửa sổ webcam: {exc}")

        with col_web:
            st.markdown("#### 🌐 Camera Trình duyệt")
            st.caption("Cấp quyền camera cho trình duyệt để căn chỉnh và bấm chụp trực tiếp trên trang.")
            photo = st.camera_input("Chụp ảnh tài liệu qua trình duyệt", key=f"browser_cam_{epoch}", label_visibility="collapsed")
            if photo is not None:
                raw_bytes = photo.getvalue()
                image = cv2.imdecode(np.frombuffer(raw_bytes, np.uint8), cv2.IMREAD_COLOR)
                if image is not None and image.size > 0:
                    set_image(image, "camera_capture")
                    st.session_state["webcam_photo_bytes"] = raw_bytes
                    st.rerun()
                else:
                    st.error("Không thể giải mã dữ liệu ảnh từ camera trình duyệt.")

        st.markdown("""
        <div class="tip-box">
          💡 <strong>Mẹo chụp tài liệu chuẩn nét:</strong>
          Đưa toàn bộ 4 mép giấy vào trong khung hình, đặt trên mặt bàn có màu tương phản (ví dụ giấy trắng trên mặt bàn gỗ tối) và đảm bảo đủ ánh sáng để hệ thống tự động nhận diện viền chuẩn xác nhất.
        </div>
        """, unsafe_allow_html=True)


def _render_uploader_view(epoch: int):
    """Dedicated file upload screen when no image is loaded yet."""
    with st.container(border=True):
        st.markdown("""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
          <div>
            <h3 style="margin: 0; font-size: 1.15rem;">Tải ảnh tài liệu từ thiết bị</h3>
            <p style="margin: 2px 0 0 0; color: #64748B; font-size: 0.85rem;">Hỗ trợ các định dạng ảnh phổ biến: JPG, PNG, WEBP, BMP.</p>
          </div>
          <span class="meta-badge-info">Chờ tệp tải lên</span>
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Kéo thả ảnh tài liệu vào đây hoặc duyệt từ thiết bị:",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
            key=f"scanner_upload_{epoch}",
            label_visibility="collapsed"
        )
        if uploaded:
            raw = np.frombuffer(uploaded.getvalue(), np.uint8)
            image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
            if image is None:
                st.error("Tệp ảnh không hợp lệ hoặc bị lỗi định dạng.")
            else:
                set_image(image, Path(uploaded.name).stem)
                st.rerun()

        st.markdown("""
        <div class="tip-box">
          💡 <strong>Lưu ý:</strong> Để có kết quả quét tốt nhất, hãy chọn ảnh có độ phân giải từ 1000px trở lên, chữ in hoặc viết tay rõ nét.
        </div>
        """, unsafe_allow_html=True)


def _load_source(settings):
    source = settings.get("source", "Ảnh mẫu")
    if source == "Ảnh mẫu":
        path = settings.get("sample")
        if path:
            image = cv2.imread(str(path))
            if image is not None:
                set_image(image, path.stem)


def _detect_if_needed(image, settings):
    params = (settings.get("max_dim", 1200), settings.get("clahe", False), settings.get("num_points", 8))
    if st.session_state.get("detection") is None or st.session_state.get("last_detect_params") != params or st.session_state.get("needs_detection"):
        with st.spinner("Đang tự động phân tích và dò đường viền tài liệu..."):
            result = detect_page_corners(image, max_dim=params[0], use_clahe=params[1], num_points=params[2])
        st.session_state["detection"] = result
        st.session_state["last_detect_params"] = params
        st.session_state["needs_detection"] = False
        h, w = image.shape[:2]
        if result.corners is not None:
            st.session_state["active_corners"] = result.corners.copy()
        else:
            st.session_state["active_corners"] = np.array([
                [w * 0.05, h * 0.05],
                [w * 0.95, h * 0.05],
                [w * 0.95, h * 0.95],
                [w * 0.05, h * 0.95]
            ], dtype=np.float32)
        st.session_state["is_manual_mode"] = False
    return st.session_state["detection"]


def _render_export(final_img, source_name, settings):
    st.markdown("## Xuất tài liệu")
    st.caption("Lưu trữ bản scan chuẩn in ấn hoặc sử dụng trí tuệ nhân tạo AI để tái tạo văn bản có thể chỉnh sửa.")
    pdf_col, docx_col, ai_col = st.columns(3, gap="medium")

    with pdf_col:
        with st.container(border=True):
            st.markdown("### PDF · A4")
            st.caption("Xuất file PDF kích thước A4 chuẩn in ấn và chia sẻ.")
            pdf_bytes = generate_pdf_bytes(final_img)
            st.download_button(
                "Tải file PDF (.pdf)",
                data=pdf_bytes,
                file_name=f"{source_name}_scanned.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    with docx_col:
        with st.container(border=True):
            st.markdown("### Word · Scan")
            st.caption("Nhúng trang scan vào bố cục trang tài liệu Word tiêu chuẩn.")
            docx_bytes = generate_docx_bytes(final_img, f"Tài liệu - {source_name}")
            st.download_button(
                "Tải file Word (.docx)",
                data=docx_bytes,
                file_name=f"{source_name}_scanned.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

    with ai_col:
        with st.container(border=True):
            st.markdown("### AI · Editable Word")
            st.caption("Tái tạo đoạn văn, tiêu đề, bảng và danh sách có thể chỉnh sửa.")
            if st.button("Tái tạo bằng AI", type="primary", key="make_ai", use_container_width=True):
                try:
                    with st.spinner(f"Gemini đang phân tích nội dung bằng mô hình {settings.get('model', 'gemini-2.5-flash')}..."):
                        text, data, structured = perform_ai_reconstruction(
                            final_img,
                            settings.get("lang", "vi"),
                            settings.get("api_key", ""),
                            settings.get("model", "gemini-2.5-flash")
                        )
                    st.session_state["ai_text"] = text
                    st.session_state["ai_docx"] = data
                    st.session_state["ai_data"] = structured
                    st.session_state["ai_result_hash"] = st.session_state.get("final_image_hash")
                    st.success("Đã tái tạo tài liệu thành công!")
                except Exception as exc:
                    st.error(str(exc))

            if st.session_state.get("ai_docx") and st.session_state.get("ai_result_hash") == st.session_state.get("final_image_hash"):
                st.download_button(
                    "Tải Word đã tái tạo (.docx)",
                    data=st.session_state["ai_docx"],
                    file_name=f"{source_name}_ai_reconstructed.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

    if st.session_state.get("ai_result_hash") == st.session_state.get("final_image_hash") and st.session_state.get("ai_text"):
        with st.expander("Xem chi tiết nội dung văn bản tái tạo"):
            blocks = st.session_state.get("ai_data", {}).get("blocks", [])
            counts = {kind: sum(1 for b in blocks if b.get("type") == kind) for kind in ("heading", "paragraph", "table", "list")}
            st.caption(f"{counts['heading']} tiêu đề · {counts['paragraph']} đoạn · {counts['table']} bảng · {counts['list']} danh sách")
            st.text_area("Nội dung", st.session_state["ai_text"], height=200, label_visibility="collapsed")


def render_scanner(settings):
    source = settings.get("source", "Ảnh mẫu")
    previous_source = st.session_state.get("scanner_last_source")
    if previous_source is not None and previous_source != source:
        clear_image()
        st.session_state["scanner_source_epoch"] = st.session_state.get("scanner_source_epoch", 0) + 1
    st.session_state.setdefault("scanner_source_epoch", 0)
    st.session_state["scanner_last_source"] = source
    epoch = st.session_state["scanner_source_epoch"]

    st.markdown('<div class="eyebrow">DOCUMENT STUDIO WORKSPACE</div>', unsafe_allow_html=True)
    st.title("Quét tài liệu")
    st.markdown('<div class="page-subtitle">Số hóa giấy tờ, nắn phẳng phối cảnh góc nghiêng và xuất bản scan chuyên nghiệp.</div>', unsafe_allow_html=True)

    # 1. If sample source, load immediately
    if source == "Ảnh mẫu":
        _load_source(settings)

    image = st.session_state.get("raw_cv_img")

    # 2. If no image loaded yet in Camera or Upload mode, render dedicated screens
    if image is None:
        if source == "Camera":
            _render_camera_viewfinder(epoch)
        elif source == "Tải ảnh lên":
            _render_uploader_view(epoch)
        else:
            with st.container(border=True):
                st.markdown("### Bắt đầu với một tài liệu")
                st.write("Chọn **Ảnh mẫu**, **Tải ảnh lên** hoặc **Camera** ở thanh điều hướng bên trái.")
        return

    # 3. An image is active — render the full workspace
    result: DetectionResult = _detect_if_needed(image, settings)
    corners = st.session_state.get("active_corners")
    manual = st.session_state.get("is_manual_mode", False)
    h, w = image.shape[:2]
    detected = result.corners is not None

    badge_class = "meta-badge-success" if detected else "meta-badge-warn"
    b_count = len(result.boundary_points) if result.boundary_points is not None else 4
    detect_text = f"Tự động ({b_count} điểm)" if detected else "Cần chỉnh tay"
    mode_text = "Phối cảnh thủ công 4 góc" if manual else "Khử cong Coons Patch"
    source_name = st.session_state.get("source_name", "document")

    # Clean Top Info Strip with Action Button
    meta_left, meta_right = st.columns([3.8, 1.2], gap="medium")
    with meta_left:
        st.markdown(f"""
        <div class="meta-strip">
          <div class="meta-item"><span class="meta-item-strong">{source_name}</span></div>
          <div class="meta-item">• <span>{w} × {h} px</span></div>
          <div class="meta-item"><span class="{badge_class}">● {detect_text}</span></div>
          <div class="meta-item">• <span>{mode_text}</span></div>
        </div>
        """, unsafe_allow_html=True)

    with meta_right:
        if source == "Camera":
            if st.button("📸 Chụp lại ảnh khác", use_container_width=True, type="secondary"):
                clear_image()
                st.session_state["scanner_source_epoch"] = epoch + 1
                st.rerun()
        elif source == "Tải ảnh lên":
            if st.button("📁 Đổi ảnh khác", use_container_width=True, type="secondary"):
                clear_image()
                st.session_state["scanner_source_epoch"] = epoch + 1
                st.rerun()

    if not detected:
        st.warning("⚠️ Chưa tự động nhận diện được 4 góc rõ ràng. Bạn hãy kéo 4 điểm neo màu đỏ ở khung bên trái để định vị vùng giấy thủ công.")

    # Symmetrical Dual-Pane Workspace
    left, right = st.columns([1.05, 1], gap="large")

    with left:
        with st.container(border=True):
            st.markdown("### 01 · Ảnh gốc & căn chỉnh")
            st.caption("Kéo 4 góc đỏ để nắn phối cảnh. Với trang cong hoặc mép uốn, điều chỉnh thêm các điểm neo màu cam.")
            updated, updated_manual = render_quad_editor(
                image_bgr=image,
                corners=corners,
                auto_corners=result.corners if detected else corners,
                is_manual=manual,
                key=f"quad_editor_{st.session_state['current_img_hash'][:12]}",
                display_max_dim=1050
            )
            if updated_manual != manual or not np.allclose(updated, corners, atol=0.5):
                st.session_state["active_corners"] = updated
                st.session_state["is_manual_mode"] = updated_manual
                for k in ("ai_docx", "ai_text", "ai_data", "ai_result_hash"):
                    st.session_state.pop(k, None)
                corners, manual = updated, updated_manual

            if st.button("Khôi phục đường viền tự động", use_container_width=True, disabled=not detected):
                st.session_state["active_corners"] = result.corners.copy()
                st.session_state["is_manual_mode"] = False
                st.rerun()

    with right:
        with st.container(border=True):
            st.markdown("### 02 · Bản scan")
            st.caption("Xem trước kết quả nắn phẳng phối cảnh và tăng cường chất lượng nét chữ.")
            filter_mode = st.radio("Chế độ hình ảnh", FILTERS, horizontal=True, key="filter_mode", label_visibility="collapsed")
            contrast = st.slider("Độ đậm nét chữ", 1.0, 4.0, 2.2, 0.2, key="contrast_boost", help="Tăng cường độ đậm của nét mực văn bản.")

            if manual or not detected:
                warped = four_point_transform(image, corners)
            else:
                warped = warp_from_result(image, result)
                if warped is None:
                    warped = four_point_transform(image, corners)

            boost = contrast if filter_mode != "Màu gốc" else 1.0
            if filter_mode == "Màu thông minh":
                final_img = magic_color_document(warped, contrast_boost=boost)
                display = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)
            elif filter_mode == "Xám mịn":
                final_img = magic_gray_document(warped, contrast_boost=boost)
                display = cv2.cvtColor(final_img, cv2.COLOR_GRAY2RGB)
            elif filter_mode == "Đen trắng":
                final_img = thresh_document(warped, contrast_boost=boost)
                display = cv2.cvtColor(final_img, cv2.COLOR_GRAY2RGB)
            else:
                final_img = warped
                display = cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB)

            st.image(display, use_container_width=True)
            fh, fw = final_img.shape[:2]
            st.caption(f"{fw} × {fh} px · {'Phối cảnh 4 góc' if manual else 'Coons Patch / tự động'}")

    final_hash = image_digest(final_img)
    if st.session_state.get("final_image_hash") != final_hash:
        for key in ("pdf_output", "docx_output", "ai_text", "ai_docx", "ai_data", "ai_result_hash"):
            st.session_state.pop(key, None)
        st.session_state["final_image_hash"] = final_hash
    st.session_state["final_img"] = final_img

    st.markdown("---")
    _render_export(final_img, source_name, settings)
