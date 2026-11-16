"""Professional Dark Studio visual system: high contrast, neutral slate/charcoal, elegant typography."""
import streamlit as st


def apply_theme() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #FFFFFF;
        --ink-secondary: #E2E8F0;
        --muted: #94A3B8;
        --line: #262C3A;
        --line-subtle: #1E232E;
        --paper: #181B22;
        --canvas: #111318;
        --blue: #3B82F6;
        --blue-hover: #2563EB;
        --nav: #0D0F14;
    }

    /* Global Typography & Root */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        background-color: var(--canvas) !important;
        color: var(--ink-secondary) !important;
    }

    [data-testid="stHeader"] {
        background: rgba(17, 19, 24, 0.92) !important;
        backdrop-filter: blur(12px) !important;
        border-bottom: 1px solid var(--line-subtle) !important;
    }

    /* Headings: Crisp 100% Pure White */
    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        letter-spacing: -0.025em !important;
        font-weight: 700 !important;
    }
    h1 { font-size: 1.85rem !important; }
    h2 { font-size: 1.3rem !important; }
    h3 { font-size: 1.05rem !important; }

    p, span, label, [data-testid="stCaptionContainer"] {
        color: inherit;
    }

    /* Main Container Padding */
    [data-testid="stMainBlockContainer"] {
        max-width: 1560px;
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
    }

    /* Sidebar Dark Theme & Fix Invisible Inputs */
    [data-testid="stSidebar"] {
        background-color: var(--nav) !important;
        border-right: 1px solid var(--line-subtle) !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label {
        color: #CBD5E1 !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: #94A3B8 !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    /* FIX: Force Sidebar Dropdowns, Text Inputs, and Selectboxes to Dark Background with Pure White Text */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] div[data-baseweb="input"] > div,
    [data-testid="stSidebar"] input {
        background-color: #161922 !important;
        border: 1px solid #2D3548 !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] svg {
        fill: #94A3B8 !important;
    }
    /* Dropdown popover list */
    ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #181B22 !important;
        border: 1px solid var(--line) !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li {
        color: #E2E8F0 !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover {
        background-color: #262C3A !important;
        color: #FFFFFF !important;
    }

    /* Card Containers: Elegant Dark Slate */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--paper) !important;
        border: 1px solid var(--line) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
        padding: 16px 18px !important;
    }

    /* File Uploader */
    [data-testid="stFileUploader"] section {
        background: #141720 !important;
        border: 1.5px dashed #2D3548 !important;
        border-radius: 12px !important;
        color: #CBD5E1 !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: var(--blue) !important;
    }
    [data-testid="stFileUploader"] * {
        color: #CBD5E1 !important;
    }

    /* Action Buttons */
    .stButton > button, .stDownloadButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        min-height: 2.5rem !important;
        border: 1px solid #2D3548 !important;
        background: #1F2430 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-size: 0.88rem !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: #283040 !important;
        border-color: #475569 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Primary Button: Vibrant Blue with Pure White Text */
    .stButton > button[kind="primary"] {
        background: var(--blue) !important;
        border-color: var(--blue) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--blue-hover) !important;
        border-color: var(--blue-hover) !important;
    }
    .stButton > button[kind="primary"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Segmented Pill Control for stRadio */
    div[data-testid="stRadio"] > div {
        display: flex !important;
        flex-direction: row !important;
        background: #13161D !important;
        border: 1px solid var(--line) !important;
        border-radius: 8px !important;
        padding: 3px !important;
        gap: 3px !important;
    }
    div[data-testid="stRadio"] label {
        flex: 1 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: transparent !important;
        color: #94A3B8 !important;
        -webkit-text-fill-color: #94A3B8 !important;
        border-radius: 6px !important;
        padding: 6px 10px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stRadio"] label > div:first-child,
    div[data-testid="stRadio"] div[data-testid="stWidgetSelection"],
    div[data-testid="stRadio"] div[role="radio"] > div:first-child {
        display: none !important;
    }
    div[data-testid="stRadio"] label:hover {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    div[data-testid="stRadio"] label:has(input:checked),
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: #262C3A !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
        border: 1px solid #3B445A !important;
    }

    /* Slider: Modern Blue Accent */
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: var(--blue) !important;
        border: 2px solid #FFFFFF !important;
        box-shadow: 0 0 8px rgba(59, 130, 246, 0.5) !important;
        width: 16px !important;
        height: 16px !important;
    }
    div[data-baseweb="slider"] > div > div {
        background: #262C3A !important;
    }
    div[data-baseweb="slider"] > div > div > div {
        background: var(--blue) !important;
    }
    div[data-baseweb="slider"] [data-testid="stThumbValue"] {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
    }

    /* Image Display Frame */
    [data-testid="stImage"] img {
        border-radius: 8px !important;
        border: 1px solid var(--line) !important;
        background: #0D0F14 !important;
    }

    /* Textarea & Expanders */
    div[data-testid="stTextArea"] textarea {
        background-color: #13161D !important;
        color: #E2E8F0 !important;
        border: 1px solid var(--line) !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
    }

    /* Branding & Badges */
    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 6px 4px 18px;
    }
    .brand-mark {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
        display: grid;
        place-items: center;
        color: white;
        font-size: 18px;
        font-weight: 800;
        box-shadow: 0 2px 10px rgba(59, 130, 246, 0.35);
    }
    .brand-name {
        color: #FFFFFF !important;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .brand-caption {
        color: #94A3B8;
        font-size: 0.72rem;
        margin-top: 1px;
        letter-spacing: 0.04em;
    }

    .section-kicker {
        font-size: 0.75rem;
        font-weight: 700;
        color: #818CF8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 14px 0 6px;
    }

    .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #60A5FA;
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .page-subtitle {
        color: #94A3B8;
        margin-top: -0.3rem;
        margin-bottom: 1.2rem;
        font-size: 0.95rem;
    }

    /* Non-truncating Meta Strip */
    .meta-strip {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        padding: 8px 14px;
        background: #141720;
        border: 1px solid var(--line);
        border-radius: 8px;
        margin-bottom: 14px;
        font-size: 0.82rem;
    }
    .meta-item {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        color: #CBD5E1;
    }
    .meta-item-strong {
        color: #FFFFFF !important;
        font-weight: 600;
    }
    .meta-badge-success {
        background: #142E1F;
        color: #4ADE80 !important;
        border: 1px solid #1B4D2E;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .meta-badge-warn {
        background: #2E2514;
        color: #FBBF24 !important;
        border: 1px solid #4D3B1B;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    </style>
    """, unsafe_allow_html=True)
