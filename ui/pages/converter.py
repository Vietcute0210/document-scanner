import hashlib
import sys
import streamlit as st


def render_converter():
    st.markdown('<div class="eyebrow">FILE CONVERSION</div>', unsafe_allow_html=True)
    st.title("Chuyển DOCX sang PDF")
    st.markdown('<div class="page-subtitle">Chuyển tài liệu Word thành PDF để chia sẻ và lưu trữ.</div>', unsafe_allow_html=True)
    if sys.platform != "win32":
        st.warning("Tính năng hiện tại sử dụng Microsoft Word COM và chỉ chạy trên Windows có cài Microsoft Word.")
    with st.container(border=True):
        uploaded = st.file_uploader("Chọn tài liệu Word (.docx)", type=["docx"], key="docx_to_pdf_upload")
        if uploaded:
            raw_docx = uploaded.getvalue()
            upload_hash = hashlib.sha256(raw_docx).hexdigest()
            if st.session_state.get("converter_input_hash") != upload_hash:
                st.session_state.pop("converted_pdf", None)
                st.session_state.pop("converted_pdf_name", None)
                st.session_state["converter_input_hash"] = upload_hash
            st.success(f"Đã chọn: **{uploaded.name}** · {uploaded.size/1024:.1f} KB")
            if st.button("Chuyển đổi sang PDF", type="primary", disabled=sys.platform != "win32"):
                try:
                    from ui.services.documents import convert_docx_bytes_to_pdf_bytes
                    with st.spinner("Microsoft Word đang chuyển đổi..."):
                        result = convert_docx_bytes_to_pdf_bytes(uploaded.getvalue())
                    st.session_state["converted_pdf"] = result
                    st.session_state["converted_pdf_name"] = uploaded.name.rsplit(".",1)[0] + ".pdf"
                    st.success("Chuyển đổi thành công.")
                except Exception as exc: st.error(f"Không thể chuyển đổi: {exc}")
        if st.session_state.get("converted_pdf") and st.session_state.get("converter_input_hash"):
            st.download_button("Tải file PDF", st.session_state["converted_pdf"], st.session_state.get("converted_pdf_name", "converted.pdf"), "application/pdf", use_container_width=True)
