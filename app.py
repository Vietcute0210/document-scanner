"""Document Studio — Professional Document Scanner & Converter Studio."""
import streamlit as st

from ui.theme import apply_theme
from ui.state.session import init_session
from ui.components.sidebar import render_sidebar
from ui.pages.scanner import render_scanner
from ui.pages.converter import render_converter

st.set_page_config(
    page_title="Document Studio — Pro Document Scanner",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session()
apply_theme()
page, settings = render_sidebar()

if page == "Quét tài liệu":
    render_scanner(settings)
else:
    render_converter()

with st.sidebar:
    st.markdown("---")
    st.caption("Document Studio · Pro Document Scanner v2.5")
    st.caption("Image processing powered by OpenCV & Gemini AI")
