import streamlit as st
import os
from backend.translate_utils import auto_translate  # ✅ use Google Translate

# ------------------------------------------------------------------------------------------
# Page Config
st.set_page_config(page_title="KONE — Maintenance Dashboard", layout="wide")

# ------------------------------------------------------------------------------------------
# 🌐 Language Selector (Top-right corner)
col1, col2 = st.columns([6, 1])
with col2:
    target_lang = st.selectbox(
        "🌐 Language",
        ["en", "fi", "fr", "de", "it", "zh-cn"],
        format_func=lambda x: {
            "en": "English 🇬🇧",
            "fi": "Finnish 🇫🇮",
            "fr": "French 🇫🇷",
            "de": "German 🇩🇪",
            "it": "Italian 🇮🇹",
            "zh-cn": "Chinese 🇨🇳",
        }[x],
    )
    st.session_state["target_lang"] = target_lang

lang = st.session_state.get("target_lang", "en")

# ------------------------------------------------------------------------------------------
# Sidebar branding (KONE logo)
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=160)
    st.markdown(auto_translate("### KONE — Maintenance Dashboard", lang))
    st.markdown("---")

# ------------------------------------------------------------------------------------------
# Custom CSS — KONE Blue Theme
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
    letter-spacing: 0.5px;
}
.hero p {
    font-size: 1.1rem;
    opacity: 0.9;
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
    margin-bottom: 0.5rem;
}
.card p {
    color: #333;
    font-size: 0.95rem;
}
.footer {
    text-align: center;
    margin-top: 3rem;
    padding: 1rem 0;
    color: #888;
    font-size: 0.85rem;
    border-top: 1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------------------
# Hero Section
st.markdown(f"""
<div class="hero">
    <h1>{auto_translate("KONE Predictive Maintenance Portal", lang)}</h1>
    <p>{auto_translate("Welcome to KONE’s centralized AI-driven maintenance dashboard — designed to empower engineering analytics and field maintenance teams. Gain insights, analyze performance, and generate professional reports all in one unified platform.", lang)}</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------------------
# Available Modules
st.markdown(f"### >>> {auto_translate('Available Modules', lang)}")

cols = st.columns(3)
with cols[0]:
    st.markdown(f"""
    <div class="card">
        <h3>1️⃣ {auto_translate('Trend Analyzer', lang)}</h3>
        <p>{auto_translate('Visualize CKPI patterns, detect anomalies, and analyze elevator performance using thresholds and peaks.', lang)}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h3>2️⃣ {auto_translate('JSON ➜ Excel Converter', lang)}</h3>
        <p>{auto_translate('Convert raw KPI JSON files into structured Excel reports for technician-level readability.', lang)}</p>
    </div>
    """, unsafe_allow_html=True)

with cols[1]:
    st.markdown(f"""
    <div class="card">
        <h3>3️⃣ {auto_translate('Word Report Generator', lang)}</h3>
        <p>{auto_translate('Generate clean, formatted Word reports from live cloud data — perfect for inspection documentation.', lang)}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h3>4️⃣ {auto_translate('Maintenance Tracker', lang)}</h3>
        <p>{auto_translate('Track maintenance checks, technician comments, and issue resolutions directly from actionable reports.', lang)}</p>
    </div>
    """, unsafe_allow_html=True)

with cols[2]:
    st.markdown(f"""
    <div class="card">
        <h3>5️⃣ {auto_translate('Equipment Health Forecast', lang)}</h3>
        <p>{auto_translate('Forecast upcoming failures and evaluate unit health using time-series prediction models (Prophet, ARIMA).', lang)}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <h3>6️⃣ {auto_translate('Report Archive', lang)}</h3>
        <p>{auto_translate('Access and download previously generated reports — filtered by date, KPI, or equipment ID.', lang)}</p>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------------------
# How To Use Section
st.markdown(f"### 🧭 {auto_translate('How to Use', lang)}")
st.markdown(auto_translate("""
1. Use the sidebar to navigate between modules.  
2. Upload your relevant dataset or JSON/Excel file.  
3. Apply filters, graphs, and AI modules to analyze your data.  
4. Download results or reports for your maintenance workflow.
""", lang))

# ------------------------------------------------------------------------------------------
# Footer
st.markdown(f"""
<div class="footer">
    © 2025 {auto_translate('KONE Digital Maintenance', lang)} | {auto_translate('Developed with ❤️ by', lang)} 
    <a href="https://www.linkedin.com/in/pranav-vikraman-322020242/" target="_blank" style="color:#003087; text-decoration:none; font-weight:bold;">
        PRANAV VIKRAMAN S S
    </a>
</div>
""", unsafe_allow_html=True)
