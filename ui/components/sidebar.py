from pathlib import Path
import streamlit as st
from ui.state.session import clear_image


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="brand-lockup">
          <div class="brand-mark">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="width: 20px; height: 20px;">
              <path d="M4 7V4h3M20 7V4h-3M4 17v3h3M20 17v3h-3M9 12h6M9 16h6M9 8h6"/>
            </svg>
          </div>
          <div>
            <div class="brand-name">Document Studio</div>
            <div class="brand-caption">DOCUMENT WORKSPACE</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-kicker">Chế độ làm việc</div>', unsafe_allow_html=True)
        page = st.radio(
            "Workspace",
            ["Quét tài liệu", "Chuyển DOCX sang PDF"],
            label_visibility="collapsed"
        )
        st.markdown("---")

        settings = {}
        if page == "Quét tài liệu":
            st.markdown('<div class="section-kicker">Nguồn tài liệu</div>', unsafe_allow_html=True)
            settings["source"] = st.radio(
                "Nguồn ảnh",
                ["Ảnh mẫu", "Tải ảnh lên", "Camera"],
                horizontal=False,
                label_visibility="collapsed"
            )

            current_src = st.session_state.get("source_name", "")
            has_active_img = st.session_state.get("raw_cv_img") is not None

            if settings["source"] == "Ảnh mẫu":
                folder = Path("documents/sample")
                files = sorted([*folder.glob("*.jpg"), *folder.glob("*.png"), *folder.glob("*.jpeg")])
                labels = {
                    "sample1.jpg": "Mẫu 01 - Tài liệu phẳng",
                    "sample2.jpg": "Mẫu 02 - Góc nghiêng 45°",
                    "sample3.jpg": "Mẫu 03 - Mép mờ sát nền",
                    "sample4.jpg": "Mẫu 04 - Trang giấy cong",
                    "sample5.jpg": "Mẫu 05 - Ánh sáng phức tạp"
                }
                if files:
                    settings["sample"] = st.selectbox(
                        "Chọn ảnh mẫu",
                        files,
                        format_func=lambda p: labels.get(p.name, p.name)
                    )

            elif settings["source"] == "Camera":
                if has_active_img and current_src == "camera_capture":
                    st.caption("Đã nạp ảnh camera vào bàn làm việc.")
                    if st.button("Chụp lại ảnh khác", use_container_width=True, type="secondary"):
                        clear_image()
                        st.session_state["scanner_source_epoch"] = st.session_state.get("scanner_source_epoch", 0) + 1
                        st.rerun()

            elif settings["source"] == "Tải ảnh lên":
                if has_active_img and current_src not in ("sample1", "sample2", "sample3", "sample4", "sample5", "camera_capture"):
                    if st.button("Đổi sang ảnh khác", use_container_width=True, type="secondary"):
                        clear_image()
                        st.session_state["scanner_source_epoch"] = st.session_state.get("scanner_source_epoch", 0) + 1
                        st.rerun()

            st.markdown("---")
            st.markdown('<div class="section-kicker">Cấu hình AI Vision</div>', unsafe_allow_html=True)
            settings["model"] = st.selectbox(
                "Mô hình Gemini",
                ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
            )
            settings["api_key"] = st.text_input(
                "Google AI Studio API Key",
                value=st.session_state.get("gemini_api_key_input", ""),
                type="password",
                help="Để trống nếu API key đã được cấu hình trong file .env hoặc biến môi trường."
            )
            st.session_state["gemini_api_key_input"] = settings["api_key"]
            settings["lang"] = st.selectbox(
                "Ngôn ngữ tài liệu",
                ["vi", "en"],
                format_func=lambda x: "Tiếng Việt (vi)" if x == "vi" else "English (en)"
            )

            with st.expander("Tham số dò biên nâng cao"):
                labels = {
                    "8 điểm - 4 góc + 4 trung điểm Coons Patch": 8,
                    "12 điểm - Bám sát độ uốn cong cao": 12,
                    "6 điểm - 4 góc + 2 trung điểm": 6,
                    "4 điểm - Tứ giác cơ bản": 4
                }
                selected = st.selectbox("Số điểm neo", list(labels))
                settings["num_points"] = labels[selected]
                settings["clahe"] = st.checkbox(
                    "Cân bằng sáng CLAHE",
                    value=False,
                    help="Tăng cường tương phản cục bộ cho tài liệu bị sấp bóng hoặc ánh sáng yếu."
                )
                settings["max_dim"] = st.slider("Độ phân giải dò biên (px)", 600, 2000, 1200, 100)

            st.markdown("---")
            st.caption("Document Studio · v2.5")
            st.caption("Engine: OpenCV & Gemini Vision")

        return page, settings
