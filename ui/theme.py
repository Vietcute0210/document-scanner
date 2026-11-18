"""
Document Studio Professional Atlantic Slate Theme:
Clean, spacious engineering aesthetic with deep ocean slate gradients.
Zero purple AI clichés, spacious vertical rhythm, zero icon clutter.
"""
import streamlit as st


def apply_theme() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

    :root {
        /* Atlantic Ocean & Slate Palette (Non-AI Cliché) */
        --brand-start: #0F2942;
        --brand-mid: #0E4B6E;
        --brand-end: #0369A1;
        --brand-gradient: linear-gradient(135deg, #0F2942 0%, #0369A1 100%);
        --brand-gradient-hover: linear-gradient(135deg, #0A1C2E 0%, #0284C7 100%);
        --brand-accent: #0284C7;
        --brand-accent-hover: #0369A1;
        --brand-tint: #F0F9FF;
        --brand-tint-border: #BAE6FD;

        --canvas: #F8FAFC;
        --paper: #FFFFFF;
        --card-border: #E2E8F0;
        --card-border-hover: #CBD5E1;
        --card-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.03), 0 4px 12px -2px rgba(15, 41, 66, 0.04);
        --card-shadow-hover: 0 4px 16px -2px rgba(15, 41, 66, 0.08), 0 8px 24px -4px rgba(15, 41, 66, 0.04);

        --ink: #0F172A;
        --ink-secondary: #334155;
        --muted: #64748B;
        --muted-light: #94A3B8;
        --line: #E2E8F0;
        --line-subtle: #F1F5F9;

        --nav: #FFFFFF;
        --nav-border: #E2E8F0;
    }

    /* Global Typography & Root */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        background-color: var(--canvas) !important;
        color: var(--ink-secondary) !important;
    }

    /* Top Accent Line */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--brand-gradient);
        z-index: 999999;
    }

    /* Header styling */
    [data-testid="stHeader"] {
        background: rgba(248, 250, 252, 0.88) !important;
        backdrop-filter: blur(14px) !important;
        border-bottom: 1px solid var(--line) !important;
    }

    /* Headings */
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
    h1 { font-size: 1.75rem !important; margin-bottom: 0.35rem !important; }
    h2 { font-size: 1.25rem !important; margin-bottom: 0.3rem !important; }
    h3 { font-size: 1.02rem !important; margin-bottom: 0.25rem !important; }

    p, span, label, [data-testid="stCaptionContainer"] {
        color: inherit;
    }

    /* Main Container Padding */
    [data-testid="stMainBlockContainer"] {
        max-width: 1540px;
        padding-top: 1.8rem;
        padding-bottom: 4rem;
    }

    /* Sidebar Base */
    [data-testid="stSidebar"] {
        background-color: var(--nav) !important;
        border-right: 1px solid var(--nav-border) !important;
        box-shadow: 1px 0 6px rgba(0, 0, 0, 0.02) !important;
        padding-top: 1rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label {
        color: var(--ink-secondary) !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: var(--muted) !important;
        font-size: 0.74rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        margin-bottom: 6px !important;
    }

    /* CRITICAL FIX: ABSOLUTELY HIDE ALL COLLAPSED WIDGET LABELS */
    [data-testid="stRadio"] label[data-testid="stWidgetLabel"],
    [data-testid="stRadio"] > label,
    div[data-testid="stRadio"] > label {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        visibility: hidden !important;
    }

    /* SIDEBAR RADIOS: MUST BE STACKED VERTICALLY IN ROLE="RADIOGROUP" */
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {
        display: flex !important;
        flex-direction: column !important;
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        gap: 8px !important;
        width: 100% !important;
        margin-top: 4px !important;
        margin-bottom: 14px !important;
    }
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: 100% !important;
        background: #FFFFFF !important;
        color: #334155 !important;
        -webkit-text-fill-color: #334155 !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        padding: 9px 14px !important;
        font-size: 0.86rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
    }
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background: #F8FAFC !important;
        border-color: #CBD5E1 !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
    }
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked),
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] {
        background: var(--brand-tint) !important;
        color: #0369A1 !important;
        -webkit-text-fill-color: #0369A1 !important;
        border: 1.5px solid var(--brand-accent) !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(2, 132, 199, 0.12) !important;
    }
    /* Proper radio dot spacing inside sidebar label */
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label div[data-testid="stWidgetSelection"],
    [data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
        margin-right: 10px !important;
    }

    /* MAIN CONTENT RADIOS (Filter mode): Clean, spacious wrap without radio circle */
    [data-testid="stMainBlockContainer"] div[data-testid="stRadio"] div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        background: #F1F5F9 !important;
        border: 1px solid var(--line) !important;
        border-radius: 9px !important;
        padding: 4px !important;
        gap: 6px !important;
        margin-bottom: 14px !important;
    }
    [data-testid="stMainBlockContainer"] div[data-testid="stRadio"] div[role="radiogroup"] > label {
        flex: 1 1 auto !important;
        min-width: 90px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: transparent !important;
        color: var(--muted) !important;
        -webkit-text-fill-color: var(--muted) !important;
        border-radius: 7px !important;
        padding: 7px 12px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        border: 1px solid transparent !important;
    }
    [data-testid="stMainBlockContainer"] div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        background: rgba(255, 255, 255, 0.7) !important;
    }
    [data-testid="stMainBlockContainer"] div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked),
    [data-testid="stMainBlockContainer"] div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] {
        background: #FFFFFF !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        font-weight: 600 !important;
        border: 1px solid #CBD5E1 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }
    /* Hide circular radio dot on main segmented pills */
    [data-testid="stMainBlockContainer"] div[data-testid="stRadio"] div[role="radiogroup"] > label div[data-testid="stWidgetSelection"],
    [data-testid="stMainBlockContainer"] div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* Sidebar Inputs, Selectboxes */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] div[data-baseweb="input"] > div,
    [data-testid="stSidebar"] input {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        font-size: 0.86rem !important;
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

    /* Card Containers: Crisp, Spacious with Generous Padding */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--paper) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 14px !important;
        box-shadow: var(--card-shadow) !important;
        padding: 22px 24px !important;
        margin-bottom: 18px !important;
        transition: box-shadow 0.2s ease, border-color 0.2s ease !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: var(--card-border-hover) !important;
        box-shadow: var(--card-shadow-hover) !important;
    }

    /* File Uploader Section */
    [data-testid="stFileUploader"] section {
        background: #F8FAFC !important;
        border: 1.5px dashed #CBD5E1 !important;
        border-radius: 12px !important;
        color: var(--ink-secondary) !important;
        transition: all 0.2s ease !important;
        padding: 24px 16px !important;
        text-align: center !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: var(--brand-accent) !important;
        background: var(--brand-tint) !important;
    }

    /* Buttons: Secondary / Normal */
    .stButton > button, .stDownloadButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        min-height: 2.6rem !important;
        border: 1px solid #CBD5E1 !important;
        background: #FFFFFF !important;
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
        font-size: 0.875rem !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: #F8FAFC !important;
        border-color: #94A3B8 !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.06) !important;
    }
    .stButton > button:active, .stDownloadButton > button:active {
        transform: translateY(1px) !important;
    }

    /* Primary Button: Deep Atlantic Slate Gradient */
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
        background: var(--brand-gradient) !important;
        border: none !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(15, 41, 66, 0.22) !important;
    }
    .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
        background: var(--brand-gradient-hover) !important;
        box-shadow: 0 4px 14px rgba(15, 41, 66, 0.32) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="primary"] *, .stDownloadButton > button[kind="primary"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Slider: Atlantic Navy Accent */
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: var(--brand-accent) !important;
        border: 2px solid #FFFFFF !important;
        box-shadow: 0 1px 4px rgba(2, 132, 199, 0.4) !important;
        width: 17px !important;
        height: 17px !important;
    }
    div[data-baseweb="slider"] > div > div {
        background: #E2E8F0 !important;
        height: 6px !important;
        border-radius: 3px !important;
    }
    div[data-baseweb="slider"] > div > div > div {
        background: var(--brand-gradient) !important;
        border-radius: 3px !important;
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

    /* Camera Input Widget */
    [data-testid="stCameraInput"] {
        background: #FFFFFF !important;
        border: 1px solid var(--line) !important;
        border-radius: 12px !important;
        padding: 12px !important;
        box-shadow: var(--card-shadow) !important;
    }
    [data-testid="stCameraInput"] video {
        border-radius: 8px !important;
    }

    /* Clean Studio Header */
    .studio-header {
        margin-bottom: 22px;
        padding-bottom: 14px;
        border-bottom: 1px solid var(--line-subtle);
    }
    .studio-badge {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #0369A1;
        background: var(--brand-tint);
        border: 1px solid var(--brand-tint-border);
        padding: 3px 10px;
        border-radius: 5px;
        margin-bottom: 6px;
    }
    .studio-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.65rem;
        font-weight: 800;
        color: var(--ink);
        letter-spacing: -0.025em;
        margin: 0 0 4px 0;
    }
    .studio-desc {
        color: var(--muted);
        font-size: 0.92rem;
        margin: 0;
        line-height: 1.5;
    }

    /* Clean Meta Strip with Generous Margin */
    .meta-strip {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        padding: 11px 18px;
        background: #FFFFFF;
        border: 1px solid var(--card-border);
        border-radius: 10px;
        margin-bottom: 22px;
        font-size: 0.85rem;
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
        background: #F0FDF4;
        color: #15803D !important;
        border: 1px solid #BBF7D0;
        padding: 3px 9px;
        border-radius: 5px;
        font-weight: 600;
        font-size: 0.76rem;
    }
    .meta-badge-warn {
        background: #FFFBEB;
        color: #B45309 !important;
        border: 1px solid #FDE68A;
        padding: 3px 9px;
        border-radius: 5px;
        font-weight: 600;
        font-size: 0.76rem;
    }

    /* Section Card Header (Clean & Un-cluttered) */
    .card-header-clean {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 14px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--line-subtle);
    }
    .card-title-text {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.02rem;
        font-weight: 700;
        color: var(--ink);
        margin: 0;
    }
    .card-badge-pill {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        background: #F1F5F9;
        color: #475569;
        border: 1px solid #E2E8F0;
    }

    /* Brand Lockup in Sidebar */
    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 6px 4px 16px;
        border-bottom: 1px solid var(--line);
        margin-bottom: 14px;
    }
    .brand-mark {
        width: 38px;
        height: 38px;
        border-radius: 9px;
        background: var(--brand-gradient);
        display: grid;
        place-items: center;
        color: white;
        box-shadow: 0 2px 8px rgba(15, 41, 66, 0.2);
    }
    .brand-name {
        color: var(--ink) !important;
        font-size: 1.05rem;
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
        letter-spacing: 0.06em;
        margin: 16px 0 8px;
    }

    /* Helper Callout Box */
    .helper-callout {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 9px;
        padding: 12px 16px;
        font-size: 0.83rem;
        color: var(--ink-secondary);
        line-height: 1.5;
        margin-top: 14px;
    }
    .helper-callout strong {
        color: var(--ink);
    }
    </style>
    """, unsafe_allow_html=True)
