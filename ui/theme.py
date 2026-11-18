"""
Document Studio Modern Clean & Bright visual system:
Minimalist Swiss design, crisp typography, clean surfaces, high contrast.
"""
import streamlit as st


def apply_theme() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

    :root {
        --canvas: #F8FAFC;
        --paper: #FFFFFF;
        --card-border: #E2E8F0;
        --card-border-hover: #CBD5E1;
        --card-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 2px 8px -2px rgba(0, 0, 0, 0.05);
        --card-shadow-hover: 0 4px 14px -2px rgba(0, 0, 0, 0.07);

        --ink: #0F172A;
        --ink-secondary: #334155;
        --muted: #64748B;
        --muted-light: #94A3B8;

        --line: #E2E8F0;
        --line-subtle: #F1F5F9;

        --blue: #2563EB;
        --blue-hover: #1D4ED8;
        --blue-active: #1E40AF;
        --blue-light: #EFF6FF;
        --blue-border: #BFDBFE;

        --emerald: #059669;
        --emerald-light: #ECFDF5;
        --emerald-border: #A7F3D0;

        --amber: #D97706;
        --amber-light: #FFFBEB;
        --amber-border: #FDE68A;

        --nav: #FFFFFF;
        --nav-border: #E2E8F0;
    }

    /* Global Typography & Root */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        background-color: var(--canvas) !important;
        color: var(--ink-secondary) !important;
    }

    /* Header styling */
    [data-testid="stHeader"] {
        background: rgba(248, 250, 252, 0.88) !important;
        backdrop-filter: blur(14px) !important;
        border-bottom: 1px solid var(--line) !important;
    }

    /* Headings: Crisp Slate 900 */
    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
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
        padding-bottom: 3rem;
    }

    /* Sidebar Modern White Theme */
    [data-testid="stSidebar"] {
        background-color: var(--nav) !important;
        border-right: 1px solid var(--nav-border) !important;
        box-shadow: 1px 0 3px rgba(0, 0, 0, 0.02) !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label {
        color: var(--ink-secondary) !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: var(--muted) !important;
        font-size: 0.76rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }

    /* Sidebar Inputs, Selectboxes & Textfields */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] div[data-baseweb="input"] > div,
    [data-testid="stSidebar"] input {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        font-size: 0.875rem !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"]:hover > div,
    [data-testid="stSidebar"] div[data-baseweb="input"]:hover > div {
        border-color: #94A3B8 !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] svg {
        fill: var(--muted) !important;
    }

    /* Dropdown popover list */
    ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #FFFFFF !important;
        border: 1px solid var(--line) !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05) !important;
        border-radius: 8px !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li {
        color: var(--ink-secondary) !important;
        font-size: 0.875rem !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover {
        background-color: var(--blue-light) !important;
        color: var(--blue) !important;
    }

    /* Card Containers: Crisp White with Soft Shadow */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--paper) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 14px !important;
        box-shadow: var(--card-shadow) !important;
        padding: 18px 20px !important;
        transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: var(--card-border-hover) !important;
    }

    /* File Uploader */
    [data-testid="stFileUploader"] section {
        background: #F8FAFC !important;
        border: 1.5px dashed #CBD5E1 !important;
        border-radius: 12px !important;
        color: var(--ink-secondary) !important;
        transition: all 0.2s ease !important;
        padding: 18px 12px !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: var(--blue) !important;
        background: #EFF6FF !important;
    }
    [data-testid="stFileUploader"] * {
        color: var(--ink-secondary) !important;
    }

    /* Buttons: Clean, Modern Flat & Elevated */
    .stButton > button, .stDownloadButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        min-height: 2.5rem !important;
        border: 1px solid #CBD5E1 !important;
        background: #FFFFFF !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        font-size: 0.875rem !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: #F8FAFC !important;
        border-color: #94A3B8 !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.07) !important;
    }
    .stButton > button:active, .stDownloadButton > button:active {
        transform: translateY(1px) !important;
    }

    /* Primary Button: Vivid Blue with Soft Glow */
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
        background: var(--blue) !important;
        border-color: var(--blue) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25) !important;
    }
    .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
        background: var(--blue-hover) !important;
        border-color: var(--blue-hover) !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
    }
    .stButton > button[kind="primary"] *, .stDownloadButton > button[kind="primary"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Segmented Pill Control for stRadio */
    div[data-testid="stRadio"] > div {
        display: flex !important;
        flex-direction: row !important;
        background: #F1F5F9 !important;
        border: 1px solid var(--line) !important;
        border-radius: 9px !important;
        padding: 3px !important;
        gap: 3px !important;
    }
    div[data-testid="stRadio"] label {
        flex: 1 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: transparent !important;
        color: var(--muted) !important;
        -webkit-text-fill-color: var(--muted) !important;
        border-radius: 7px !important;
        padding: 6px 12px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        border: 1px solid transparent !important;
    }
    div[data-testid="stRadio"] label > div:first-child,
    div[data-testid="stRadio"] div[data-testid="stWidgetSelection"],
    div[data-testid="stRadio"] div[role="radio"] > div:first-child {
        display: none !important;
    }
    div[data-testid="stRadio"] label:hover {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        background: rgba(255, 255, 255, 0.6) !important;
    }
    div[data-testid="stRadio"] label:has(input:checked),
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: #FFFFFF !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        font-weight: 600 !important;
        border: 1px solid #CBD5E1 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }

    /* Slider: Modern Accent */
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: var(--blue) !important;
        border: 2px solid #FFFFFF !important;
        box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4) !important;
        width: 17px !important;
        height: 17px !important;
    }
    div[data-baseweb="slider"] > div > div {
        background: #E2E8F0 !important;
    }
    div[data-baseweb="slider"] > div > div > div {
        background: var(--blue) !important;
    }
    div[data-baseweb="slider"] [data-testid="stThumbValue"] {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
    }

    /* Image Display Frame */
    [data-testid="stImage"] img {
        border-radius: 10px !important;
        border: 1px solid var(--line) !important;
        background: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    }

    /* Camera Input Widget: Clean Modern Frame */
    [data-testid="stCameraInput"] {
        background: #FFFFFF !important;
        border: 1px solid var(--line) !important;
        border-radius: 14px !important;
        padding: 12px !important;
        box-shadow: var(--card-shadow) !important;
    }
    [data-testid="stCameraInput"] video {
        border-radius: 10px !important;
    }

    /* Textarea & Expanders */
    div[data-testid="stTextArea"] textarea {
        background-color: #FFFFFF !important;
        color: var(--ink) !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        font-size: 0.875rem !important;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border-color: var(--blue) !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15) !important;
    }

    .streamlit-expanderHeader {
        background: #F8FAFC !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: var(--ink) !important;
        border: 1px solid var(--line) !important;
    }

    /* Branding & Badges */
    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 4px 18px;
        border-bottom: 1px solid var(--line-subtle);
        margin-bottom: 12px;
    }
    .brand-mark {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        display: grid;
        place-items: center;
        color: white;
        font-size: 19px;
        font-weight: 800;
        box-shadow: 0 2px 10px rgba(37, 99, 235, 0.28);
    }
    .brand-name {
        color: var(--ink) !important;
        font-size: 1.08rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .brand-caption {
        color: var(--muted);
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-top: 1px;
    }

    .section-kicker {
        font-size: 0.73rem;
        font-weight: 700;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 14px 0 6px;
    }

    .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--blue);
        font-size: 0.74rem;
        font-weight: 700;
        margin-bottom: 4px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .page-subtitle {
        color: var(--muted);
        margin-top: -0.3rem;
        margin-bottom: 1.4rem;
        font-size: 0.95rem;
    }

    /* Clean Crisp Meta Strip */
    .meta-strip {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        padding: 9px 16px;
        background: #FFFFFF;
        border: 1px solid var(--card-border);
        border-radius: 10px;
        margin-bottom: 16px;
        font-size: 0.84rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .meta-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: var(--ink-secondary);
    }
    .meta-item-strong {
        color: var(--ink) !important;
        font-weight: 700;
    }
    .meta-badge-success {
        background: var(--emerald-light);
        color: var(--emerald) !important;
        border: 1px solid var(--emerald-border);
        padding: 3px 9px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.76rem;
    }
    .meta-badge-warn {
        background: var(--amber-light);
        color: var(--amber) !important;
        border: 1px solid var(--amber-border);
        padding: 3px 9px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.76rem;
    }
    .meta-badge-info {
        background: var(--blue-light);
        color: var(--blue) !important;
        border: 1px solid var(--blue-border);
        padding: 3px 9px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.76rem;
    }

    /* Camera Viewfinder & Helpful Box */
    .viewfinder-card {
        background: #FFFFFF;
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 24px;
        box-shadow: var(--card-shadow);
        text-align: center;
        margin-bottom: 16px;
    }
    .viewfinder-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: var(--blue-light);
        color: var(--blue);
        border: 1px solid var(--blue-border);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 12px;
    }
    .tip-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 0.84rem;
        color: var(--ink-secondary);
        line-height: 1.5;
        margin-top: 12px;
        text-align: left;
    }
    .tip-box strong {
        color: var(--ink);
    }
    </style>
    """, unsafe_allow_html=True)
