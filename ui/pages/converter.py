import hashlib
import sys
import streamlit as st


def render_converter():
    st.markdown('<div class="eyebrow">FILE CONVERSION WORKSPACE</div>', unsafe_allow_html=True)
    st.title("Chuyển DOCX sang PDF")
    st.markdown('<div class="page-subtitle">Chuyển đổi tài liệu văn bản Microsoft Word (.docx) sang chuẩn file PDF chia sẻ và in ấn.</div>', unsafe_allow_html=True)

    if sys.platform != "win32":
        st.info("ℹ️ Tính năng chuyển đổi DOCX trực tiếp sang PDF sử dụng Microsoft Word Automation (COM API) và khả dụng khi chạy trên hệ điều hành Windows đã cài Microsoft Word.")

    with st.container(border=True):
        st.markdown("### Chọn tệp Word (.docx)")
        st.caption("Kéo thả hoặc duyệt tệp từ máy tính để bắt đầu chuyển đổi.")

        uploaded = st.file_uploader(
            "Chọn tài liệu Word (.docx)",
            type=["docx"],
            key="docx_to_pdf_upload",
            label_visibility="collapsed"
        )

        if uploaded:
            raw_docx = uploaded.getvalue()
            upload_hash = hashlib.sha256(raw_docx).hexdigest()
            if st.session_state.get("converter_input_hash") != upload_hash:
                st.session_state.pop("converted_pdf", None)
                st.session_state.pop("converted_pdf_name", None)
                st.session_state["converter_input_hash"] = upload_hash

            st.markdown(f"""
            <div class="meta-strip" style="margin-top: 10px;">
              <div class="meta-item"><span class="meta-item-strong">{uploaded.name}</span></div>
              <div class="meta-item">• <span>{uploaded.size / 1024:.1f} KB</span></div>
              <div class="meta-item"><span class="meta-badge-success">● Đã nạp</span></div>
            </div>
            """, unsafe_allow_html=True)

            btn_col1, _ = st.columns([1.5, 2.5])
            with btn_col1:
                convert_btn = st.button(
                    "Bắt đầu chuyển đổi sang PDF",
                    type="primary",
                    use_container_width=True,
                    disabled=(sys.platform != "win32")
                )

            if convert_btn:
                try:
                    from ui.services.documents import convert_docx_bytes_to_pdf_bytes
                    with st.spinner("Microsoft Word đang xử lý chuyển đổi bố cục tài liệu..."):
                        result = convert_docx_bytes_to_pdf_bytes(uploaded.getvalue())
                    st.session_state["converted_pdf"] = result
                    st.session_state["converted_pdf_name"] = uploaded.name.rsplit(".", 1)[0] + ".pdf"
                    st.success("Đã chuyển đổi tài liệu Word sang PDF thành công!")
                except Exception as exc:
                    st.error(f"Không thể chuyển đổi: {exc}")

        if st.session_state.get("converted_pdf") and st.session_state.get("converter_input_hash"):
            st.markdown("---")
            st.markdown("### Tệp PDF hoàn tất")
            st.download_button(
                "Tải xuống file PDF hoàn tất",
                data=st.session_state["converted_pdf"],
                file_name=st.session_state.get("converted_pdf_name", "converted.pdf"),
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
