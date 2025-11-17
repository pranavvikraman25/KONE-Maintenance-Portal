import streamlit as st
import os
from backend.translate_utils import auto_translate  # your translate backend

# ------------------------------------------------------------------------------------------
# PAGE CONFIG
st.set_page_config(page_title="KONE — Maintenance Dashboard", layout="wide")

# ------------------------------------------------------------------------------------------
# GLOBAL LANGUAGE STATE
if "global_lang" not in st.session_state:
    st.session_state["global_lang"] = "en"

# Shortcut function
def tr(text: str):
    """Universal translation wrapper for the entire app."""
    return auto_translate(text, st.session_state["global_lang"])

# ------------------------------------------------------------------------------------------
# LANGUAGE SELECTOR
col1, col2 = st.columns([6, 1])
with col2:
    supported_langs = ["en", "fi", "fr", "de", "it", "sv", "zh-CN"]
    lang_labels = {
        "en": "English 🇬🇧",
        "fi": "Finnish 🇫🇮",
        "fr": "French 🇫🇷",
        "de": "German 🇩🇪",
        "it": "Italian 🇮🇹",
        "sv": "Swedish 🇸🇪",
        "zh-CN": "Chinese 🇨🇳",
    }

    selected_lang = st.selectbox(
        "🌍 Language",
        supported_langs,
        format_func=lambda x: lang_labels[x],
        index=supported_langs.index(st.session_state["global_lang"])
    )

    st.session_state["global_lang"] = selected_lang

# ------------------------------------------------------------------------------------------
# SIDEBAR
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=160)
    st.markdown(f"### {tr('KONE — Maintenance Dashboard')}")
    st.write("---")

# ------------------------------------------------------------------------------------------
# CSS — DO NOT MODIFY
st.markdown("""
<style>
body {
    background-color: #f8f9fc;
    font-family: "Segoe UI", Roboto, sans-serif;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #003087 0%, #0048AA 100%);
    color: white !important;
}
[data-testid="stSidebar"] * {
    color: white !important;
    font-weight: 500;
}
[data-testid="stSidebar"] img {
    margin: 20px auto;
    display: block;
}
.hero {
    background: linear-gradient(90deg, #003087, #0048AA);
    color: white;
    padding: 2rem 2.5rem;
    border-radius: 12px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.15);
}
.hero h1 {
    font-size: 2rem;
    font-weight: 700;
}
.hero p {
    font-size: 1.1rem;
}
.card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
}
.card h3 {
    color: #003087;
}
.footer {
    text-align: center;
    margin-top: 3rem;
    padding: 1rem;
    color: #888;
    font-size: 0.85rem;
    border-top: 1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------------------
# HERO SECTION
st.markdown(f"""
<div class="hero">
    <h1>{tr("KONE Predictive Maintenance Portal")}</h1>
    <p>{tr("Welcome to KONE’s centralized maintenance dashboard — designed to empower engineering analytics and field maintenance teams. Gain insights, analyze performance, and generate professional reports all in one unified platform.")}</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------------------
# AVAILABLE MODULES
st.markdown(f"### >>> {tr('Available Modules')}")

cols = st.columns(3)

with cols[0]:
    st.markdown(f"""
    <div class="card">
        <h3>1️⃣ {tr('Trend Analyzer')}</h3>
        <p>{tr('Visualize CKPI patterns, detect anomalies, and analyze elevator performance using thresholds and peaks.')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h3>2️⃣ {tr('JSON ➜ Excel Converter')}</h3>
        <p>{tr('Convert raw KPI JSON files into structured Excel reports for technician-level readability.')}</p>
    </div>
    """, unsafe_allow_html=True)

with cols[1]:
    st.markdown(f"""
    <div class="card">
        <h3>3️⃣ {tr('Word Report Generator')}</h3>
        <p>{tr('Generate clean, formatted Word reports from live cloud data — perfect for inspection documentation.')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h3>4️⃣ {tr('Maintenance Tracker')}</h3>
        <p>{tr('Track maintenance checks, technician comments, and issue resolutions directly from actionable reports.')}</p>
    </div>
    """, unsafe_allow_html=True)

with cols[2]:
    st.markdown(f"""
    <div class="card">
        <h3>5️⃣ {tr('Equipment Health Forecast')}</h3>
        <p>{tr('Forecast upcoming failures and evaluate unit health using time-series prediction models (Prophet, ARIMA).')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h3>6️⃣ {tr('Report Archive')}</h3>
        <p>{tr('Access and download previously generated reports — filtered by date, KPI, or equipment ID.')}</p>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------------------
# HOW TO USE
st.markdown(f"### 📌 {tr('How to Use')}")
st.markdown(tr("""
1. Use the sidebar to navigate between modules.  
2. Upload your relevant dataset or JSON/Excel file.  
3. Apply filters, graphs, and AI modules to analyze your data.  
4. Download results or reports for your maintenance workflow.
"""))

# ------------------------------------------------------------------------------------------
# FOOTER
st.markdown(f"""
<div class="footer">
    © 2025 {tr('KONE Digital Maintenance')} | {tr('Developed with ❤️ by')} 
    <a href="https://www.linkedin.com/in/pranav-vikraman-322020242/" target="_blank" 
    style="color:#003087; text-decoration:none; font-weight:bold;">
        PRANAV VIKRAMAN S S
    </a>
</div>
""", unsafe_allow_html=True)
