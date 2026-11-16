"""Hybrid visual system: dark navigation, light document workspace."""
import streamlit as st


def apply_theme() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    :root { --ink:#172033; --muted:#687386; --line:#e5e9f0; --paper:#ffffff; --canvas:#f4f6fa; --blue:#2563eb; --blue-soft:#eff6ff; --nav:#111827; }
    html, body, [class*="css"], .stApp { font-family:Inter,ui-sans-serif,system-ui,sans-serif; }
    .stApp { background:var(--canvas); color:var(--ink); }
    [data-testid="stHeader"] { background:rgba(244,246,250,.92); }
    [data-testid="stSidebar"] { background:var(--nav); border-right:1px solid #263244; }
    [data-testid="stSidebar"] * { color:#e5e7eb; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#aeb9ca; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { color:#e5e7eb!important; }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color:#9caec5!important; font-size:.78rem; font-weight:600; }
    [data-testid="stMainBlockContainer"] { max-width:1600px; padding-top:2rem; padding-bottom:3rem; }
    h1,h2,h3 { color:var(--ink); letter-spacing:-.035em; }
    h1 { font-size:2rem!important; font-weight:800!important; }
    h2 { font-size:1.35rem!important; font-weight:750!important; }
    h3 { font-size:1.05rem!important; font-weight:700!important; }
    p, label, [data-testid="stCaptionContainer"] { color:var(--muted); }
    [data-testid="stVerticalBlockBorderWrapper"] { background:var(--paper); border:1px solid var(--line); border-radius:16px; box-shadow:0 3px 14px rgba(15,23,42,.035); }
    [data-testid="stFileUploader"] section { background:#f8fbff; border:1.5px dashed #b9c9e2; border-radius:14px; }
    [data-testid="stFileUploader"] section:hover { border-color:var(--blue); }
    .stButton>button,.stDownloadButton>button { border-radius:10px; font-weight:650; min-height:2.55rem; border:1px solid #d8dfeb; }
    .stButton>button[kind="primary"] { background:var(--blue); border-color:var(--blue); color:white; }
    .stButton>button[kind="primary"]:hover { background:#1d4ed8; border-color:#1d4ed8; }
    .stDownloadButton>button { background:white; color:#1e293b; }
    [data-testid="stImage"] img { border-radius:10px; }
    [data-baseweb="tab-list"] { gap:8px; }
    [data-baseweb="tab"] { background:white; border:1px solid var(--line); border-radius:10px 10px 0 0; padding:8px 16px; }
    [data-testid="stMetric"] { background:#f8fafc; padding:12px 14px; border:1px solid var(--line); border-radius:12px; }
    .eyebrow { text-transform:uppercase; letter-spacing:.12em; color:#64748b; font-size:.72rem; font-weight:800; }
    .page-subtitle { color:#64748b; margin-top:-.6rem; margin-bottom:1.4rem; }
    .brand-lockup { display:flex; align-items:center; gap:11px; padding:8px 4px 22px; }
    .brand-mark { width:38px;height:38px;border-radius:12px;background:#2563eb;display:grid;place-items:center;color:white;font-size:20px;font-weight:800; }
    .brand-name { color:white;font-size:1rem;font-weight:800;letter-spacing:-.02em; }
    .brand-caption { color:#94a3b8;font-size:.72rem;margin-top:2px; }
    .section-kicker { font-size:.78rem;font-weight:750;color:#64748b;text-transform:uppercase;letter-spacing:.08em;margin:8px 0; }
    .status-chip { display:inline-block;padding:5px 10px;border-radius:999px;background:#ecfdf5;color:#047857;font-size:.75rem;font-weight:700; }
    .hint { color:#64748b;font-size:.83rem;line-height:1.5; }
    @media(max-width:900px){ [data-testid="stMainBlockContainer"]{padding:1rem;} h1{font-size:1.6rem!important;} }
    </style>
    """, unsafe_allow_html=True)
