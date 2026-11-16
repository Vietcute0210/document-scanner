from pathlib import Path
import streamlit as st


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
        page = st.radio("Workspace", ["Quét tài liệu", "Chuyển DOCX → PDF"], label_visibility="collapsed")
        st.markdown("---")

        settings = {}
        if page == "Quét tài liệu":
            st.markdown('<div class="section-kicker">Nguồn tài liệu</div>', unsafe_allow_html=True)
            settings["source"] = st.radio("Nguồn ảnh", ["Ảnh mẫu", "Tải ảnh lên", "Camera"], horizontal=False, label_visibility="collapsed")

            if settings["source"] == "Ảnh mẫu":
                folder = Path("documents/sample")
                files = sorted([*folder.glob("*.jpg"), *folder.glob("*.png"), *folder.glob("*.jpeg")])
                labels = {
                    "sample1.jpg": "Mẫu 01 · Tài liệu phẳng",
                    "sample2.jpg": "Mẫu 02 · Góc nghiêng 45°",
                    "sample3.jpg": "Mẫu 03 · Mép mờ sát nền",
                    "sample4.jpg": "Mẫu 04 · Trang giấy cong",
                    "sample5.jpg": "Mẫu 05 · Ánh sáng phức tạp"
                }
                if files:
                    settings["sample"] = st.selectbox("Chọn ảnh mẫu", files, format_func=lambda p: labels.get(p.name, p.name))

            st.markdown("---")
            st.markdown('<div class="section-kicker">Cấu hình AI Vision</div>', unsafe_allow_html=True)
            settings["model"] = st.selectbox("Mô hình Gemini", ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"])
            settings["api_key"] = st.text_input(
                "Google AI Studio API Key",
                value=st.session_state.get("gemini_api_key_input", ""),
                type="password",
                help="Để trống nếu API key đã được cấu hình trong môi trường .env"
            )
            st.session_state["gemini_api_key_input"] = settings["api_key"]
            settings["lang"] = st.selectbox("Ngôn ngữ tài liệu", ["vi", "en"], format_func=lambda x: "Tiếng Việt (vi)" if x == "vi" else "English (en)")

            with st.expander("Tham số dò biên nâng cao"):
                labels = {
                    "8 điểm · 4 góc + 4 trung điểm": 8,
                    "12 điểm · Bám sát độ uốn cong": 12,
                    "6 điểm · 4 góc + 2 trung điểm": 6,
                    "4 điểm · Tứ giác cơ bản": 4
                }
                selected = st.selectbox("Số điểm neo", list(labels))
                settings["num_points"] = labels[selected]
                settings["clahe"] = st.checkbox("Cân bằng sáng CLAHE", value=False, help="Hỗ trợ tài liệu bị sấp bóng hoặc ánh sáng không đều")
                settings["max_dim"] = st.slider("Độ phân giải dò biên (px)", 600, 2000, 1200, 100)

        return page, settings
