"""
Document Studio Modern Rich & Bright Design System:
Minimalist Swiss structure elevated with modern Bento Grid, glassmorphic accents,
vibrant brand gradients, crisp typography, and micro-interactions.
"""
import streamlit as st


def apply_theme() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

    :root {
        /* Primitive Tokens */
        --blue-50: #EFF6FF;
        --blue-100: #DBEAFE;
        --blue-500: #3B82F6;
        --blue-600: #2563EB;
        --blue-700: #1D4ED8;
        --indigo-50: #EEF2FF;
        --indigo-600: #4F46E5;
        --purple-50: #FAF5FF;
        --purple-600: #7C3AED;
        --purple-700: #6D28D9;
        --emerald-50: #ECFDF5;
        --emerald-600: #059669;
        --amber-50: #FFFBEB;
        --amber-600: #D97706;
        --rose-50: #FFF1F2;
        --rose-600: #E11D48;
        --slate-50: #F8FAFC;
        --slate-100: #F1F5F9;
        --slate-200: #E2E8F0;
        --slate-300: #CBD5E1;
        --slate-400: #94A3B8;
        --slate-500: #64748B;
        --slate-600: #475569;
        --slate-700: #334155;
        --slate-800: #1E293B;
        --slate-900: #0F172A;

        /* Semantic Tokens */
        --canvas: #F8FAFC;
        --paper: #FFFFFF;
        --card-border: #E2E8F0;
        --card-border-hover: #CBD5E1;
        --card-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 4px 16px -2px rgba(37, 99, 235, 0.04), 0 10px 24px -4px rgba(15, 23, 42, 0.03);
        --card-shadow-hover: 0 4px 20px -2px rgba(37, 99, 235, 0.12), 0 12px 28px -5px rgba(15, 23, 42, 0.08);

        --ink: #0F172A;
        --ink-secondary: #334155;
        --muted: #64748B;
        --muted-light: #94A3B8;
        --line: #E2E8F0;
        --line-subtle: #F1F5F9;

        /* Brand Gradients & Accents */
        --brand-gradient: linear-gradient(135deg, #2563EB 0%, #4F46E5 50%, #7C3AED 100%);
        --brand-gradient-hover: linear-gradient(135deg, #1D4ED8 0%, #4338CA 50%, #6D28D9 100%);
        --brand-glow: 0 4px 18px rgba(79, 70, 229, 0.28);
        --brand-blue: #2563EB;
        --nav: #FFFFFF;
        --nav-border: #E2E8F0;
    }

    /* Global Typography & Body */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        background-color: var(--canvas) !important;
        color: var(--ink-secondary) !important;
    }

    /* Subtle Top Accent Gradient Line on App */
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

    /* Streamlit Glass Header */
    [data-testid="stHeader"] {
        background: rgba(248, 250, 252, 0.85) !important;
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
    h1 { font-size: 1.85rem !important; }
    h2 { font-size: 1.28rem !important; }
    h3 { font-size: 1.05rem !important; }

    p, span, label, [data-testid="stCaptionContainer"] {
        color: inherit;
    }

    /* Main Container Padding */
    [data-testid="stMainBlockContainer"] {
        max-width: 1560px;
        padding-top: 1.25rem;
        padding-bottom: 3rem;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: var(--nav) !important;
        border-right: 1px solid var(--nav-border) !important;
        box-shadow: 2px 0 10px rgba(0, 0, 0, 0.02) !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label {
        color: var(--ink-secondary) !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: var(--muted) !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
    }

    /* Sidebar Dropdowns, Inputs, and Fields */
    [data-testid="stSidebar"] div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] div[data-baseweb="input"] > div,
    [data-testid="stSidebar"] input {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 9px !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        font-size: 0.875rem !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
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

    /* Popover dropdown menu */
    ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #FFFFFF !important;
        border: 1px solid var(--line) !important;
        box-shadow: 0 12px 30px -5px rgba(0, 0, 0, 0.12), 0 8px 10px -6px rgba(0, 0, 0, 0.04) !important;
        border-radius: 10px !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li {
        color: var(--ink-secondary) !important;
        font-size: 0.875rem !important;
        padding: 8px 12px !important;
    }
    ul[data-testid="stSelectboxVirtualDropdown"] li:hover {
        background-color: #EFF6FF !important;
        color: var(--blue-600) !important;
        font-weight: 600 !important;
    }

    /* Card Containers: Modern Bento Box Styling */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--paper) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 16px !important;
        box-shadow: var(--card-shadow) !important;
        padding: 20px 22px !important;
        position: relative !important;
        transition: box-shadow 0.25s ease, border-color 0.25s ease, transform 0.25s ease !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #CBD5E1 !important;
        box-shadow: var(--card-shadow-hover) !important;
    }

    /* File Uploader Section */
    [data-testid="stFileUploader"] section {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%) !important;
        border: 1.5px dashed #CBD5E1 !important;
        border-radius: 14px !important;
        color: var(--ink-secondary) !important;
        transition: all 0.2s ease !important;
        padding: 24px 16px !important;
        text-align: center !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: var(--blue-600) !important;
        background: #EFF6FF !important;
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.08) !important;
    }
    [data-testid="stFileUploader"] * {
        color: var(--ink-secondary) !important;
    }

    /* Buttons: Secondary and Standard */
    .stButton > button, .stDownloadButton > button {
        border-radius: 9px !important;
        font-weight: 600 !important;
        min-height: 2.6rem !important;
        border: 1px solid #CBD5E1 !important;
        background: #FFFFFF !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        font-size: 0.88rem !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: #F8FAFC !important;
        border-color: #94A3B8 !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active, .stDownloadButton > button:active {
        transform: translateY(0px) !important;
    }

    /* Primary Button: Vibrant Gradient with Rich Glow */
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
        background: var(--brand-gradient) !important;
        border: none !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        box-shadow: var(--brand-glow) !important;
    }
    .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
        background: var(--brand-gradient-hover) !important;
        box-shadow: 0 6px 22px rgba(79, 70, 229, 0.4) !important;
        transform: translateY(-1.5px) !important;
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
        border-radius: 11px !important;
        padding: 4px !important;
        gap: 4px !important;
    }
    div[data-testid="stRadio"] label {
        flex: 1 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: transparent !important;
        color: var(--muted) !important;
        -webkit-text-fill-color: var(--muted) !important;
        border-radius: 8px !important;
        padding: 7px 12px !important;
        font-size: 0.83rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.16s ease !important;
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
        background: rgba(255, 255, 255, 0.7) !important;
    }
    div[data-testid="stRadio"] label:has(input:checked),
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: #FFFFFF !important;
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        font-weight: 700 !important;
        border: 1px solid #CBD5E1 !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08) !important;
    }

    /* Slider: Modern Accent with Value Pill */
    div[data-baseweb="slider"] div[role="slider"] {
        background-color: var(--blue-600) !important;
        border: 2.5px solid #FFFFFF !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.45) !important;
        width: 18px !important;
        height: 18px !important;
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
        font-weight: 700 !important;
        font-size: 0.83rem !important;
    }

    /* Images */
    [data-testid="stImage"] img {
        border-radius: 12px !important;
        border: 1px solid var(--line) !important;
        background: #FFFFFF !important;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.05) !important;
    }

    /* Camera Input Widget */
    [data-testid="stCameraInput"] {
        background: #FFFFFF !important;
        border: 1px solid var(--line) !important;
        border-radius: 14px !important;
        padding: 14px !important;
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
        border-radius: 9px !important;
        font-size: 0.88rem !important;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border-color: var(--blue-600) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: #F8FAFC !important;
        border-radius: 9px !important;
        font-weight: 600 !important;
        color: var(--ink) !important;
        border: 1px solid var(--line) !important;
    }

    /* Branding Lockup in Sidebar */
    .brand-lockup {
        display: flex;
        align-items: center;
        gap: 13px;
        padding: 8px 4px 18px;
        border-bottom: 1px solid var(--line);
        margin-bottom: 14px;
    }
    .brand-mark {
        width: 40px;
        height: 40px;
        border-radius: 11px;
        background: var(--brand-gradient);
        display: grid;
        place-items: center;
        color: white;
        font-size: 20px;
        font-weight: 800;
        box-shadow: var(--brand-glow);
    }
    .brand-name {
        color: var(--ink) !important;
        font-size: 1.12rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .brand-caption {
        color: var(--muted);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        margin-top: 1px;
    }

    .section-kicker {
        font-size: 0.74rem;
        font-weight: 700;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 16px 0 6px;
    }

    /* Hero Banner Component */
    .hero-banner {
        background: linear-gradient(135deg, #F0F7FF 0%, #F5F3FF 50%, #FAF5FF 100%);
        border: 1px solid rgba(199, 210, 254, 0.6);
        border-radius: 16px;
        padding: 22px 26px;
        margin-bottom: 22px;
        box-shadow: 0 4px 20px -3px rgba(99, 102, 241, 0.08);
        position: relative;
        overflow: hidden;
    }
    .hero-banner::after {
        content: "";
        position: absolute;
        top: -40px;
        right: -40px;
        width: 140px;
        height: 140px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, rgba(255, 255, 255, 0) 70%);
        pointer-events: none;
    }
    .hero-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #FFFFFF;
        border: 1px solid #C7D2FE;
        color: #4338CA;
        font-size: 0.74rem;
        font-weight: 700;
        padding: 4px 11px;
        border-radius: 20px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        box-shadow: 0 1px 3px rgba(99, 102, 241, 0.08);
        margin-bottom: 10px;
    }
    .hero-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.7rem;
        font-weight: 800;
        color: var(--ink);
        letter-spacing: -0.03em;
        margin: 0 0 6px 0;
        line-height: 1.25;
    }
    .hero-subtitle {
        color: #475569;
        font-size: 0.94rem;
        margin: 0 0 14px 0;
        max-width: 820px;
        line-height: 1.5;
    }
    .hero-stepper {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        padding-top: 10px;
        border-top: 1px solid rgba(199, 210, 254, 0.5);
    }
    .step-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #334155;
        background: rgba(255, 255, 255, 0.8);
        padding: 4px 10px;
        border-radius: 7px;
        border: 1px solid rgba(224, 231, 255, 0.8);
    }
    .step-num {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: var(--blue-600);
        color: white;
        display: grid;
        place-items: center;
        font-size: 0.68rem;
        font-weight: 800;
    }
    .step-arrow {
        color: #94A3B8;
        font-size: 0.8rem;
    }

    /* Meta Strip */
    .meta-strip {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        padding: 10px 16px;
        background: #FFFFFF;
        border: 1px solid var(--card-border);
        border-radius: 12px;
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
        background: #ECFDF5;
        color: #059669 !important;
        border: 1px solid #A7F3D0;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.76rem;
    }
    .meta-badge-warn {
        background: #FFFBEB;
        color: #D97706 !important;
        border: 1px solid #FDE68A;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.76rem;
    }
    .meta-badge-info {
        background: #EFF6FF;
        color: #2563EB !important;
        border: 1px solid #BFDBFE;
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.76rem;
    }

    /* Section Card Header */
    .panel-header-rich {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--line-subtle);
    }
    .panel-title-group {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .panel-icon-badge {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        display: grid;
        place-items: center;
        color: white;
        font-weight: 800;
        font-size: 14px;
    }
    .icon-badge-blue { background: linear-gradient(135deg, #3B82F6, #2563EB); }
    .icon-badge-purple { background: linear-gradient(135deg, #8B5CF6, #6366F1); }
    .icon-badge-emerald { background: linear-gradient(135deg, #10B981, #059669); }
    .icon-badge-rose { background: linear-gradient(135deg, #F43F5E, #E11D48); }

    .panel-title-text {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--ink);
        margin: 0;
    }
    .panel-badge {
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 5px;
        background: #F1F5F9;
        color: #475569;
        border: 1px solid #E2E8F0;
    }

    /* Feature Card in Viewfinder */
    .feat-card {
        background: #FFFFFF;
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        height: 100%;
        transition: all 0.2s ease;
    }
    .feat-card:hover {
        border-color: #CBD5E1;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.08);
        transform: translateY(-1.5px);
    }
    .feat-icon {
        font-size: 22px;
        margin-bottom: 8px;
    }
    .feat-title {
        font-size: 0.92rem;
        font-weight: 700;
        color: var(--ink);
        margin-bottom: 4px;
    }
    .feat-desc {
        font-size: 0.8rem;
        color: var(--muted);
        line-height: 1.45;
    }

    /* Sidebar Footer Info Card */
    .sidebar-info-card {
        background: #F8FAFC;
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 12px;
        margin-top: 16px;
        font-size: 0.78rem;
        color: #475569;
    }
    .sidebar-info-card strong {
        color: var(--ink);
    }

    /* Tip Box */
    .tip-box {
        background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 14px 18px;
        font-size: 0.84rem;
        color: var(--ink-secondary);
        line-height: 1.55;
        margin-top: 14px;
    }
    .tip-box strong {
        color: var(--ink);
    }
    </style>
    """, unsafe_allow_html=True)
