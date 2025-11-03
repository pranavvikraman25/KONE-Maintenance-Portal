import streamlit as st

import streamlit as st
import os

st.set_page_config(page_title="KONE — Maintenance Dashboard", layout="wide")

# Sidebar branding (shown only on Home page)
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=160)
    st.markdown("### KONE — Maintenance Dashboard")
    st.markdown("---")

# Main content
st.title("Welcome to KONE Maintenance Dashboard")
st.markdown("""
This internal dashboard helps monitor and analyze key elevator KPIs.  
Choose a module from the sidebar to get started:
- **Trend Analyzer** — Visualize KPI trends and anomalies  
- **JSON to Excel** — Convert raw data into readable KPI sheets  
- **Report Generator** — Create maintenance reports  
- **Maintenance Tracker** — Manage inspection and service logs  
- **Equipment Health Score** — Evaluate performance and reliability  
- **Report Archive** — Access all generated reports  
""")

st.info("Use the sidebar to navigate between modules.")





st.set_page_config(page_title="KONE Predictive Maintenance Portal", layout="wide")

# ---------- Custom CSS ----------
st.markdown("""
<style>
/* Global Styles */
body {
    background-color: #f8f9fc;
    font-family: "Segoe UI", Roboto, sans-serif;
}

/* Sidebar Styling */
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

/* Hero Header */
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

/* Card Container */
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

/* Footer */
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

# ---------- Hero Section ----------
st.markdown("""
<div class="hero">
    <h1> KONE Predictive Maintenance Portal</h1>
    <p>Welcome to KONE’s centralized AI-driven maintenance dashboard — designed to empower engineering analytics and field maintenance teams.<br>
    Gain insights, analyze performance, and generate professional reports all in one unified platform.</p>
</div>
""", unsafe_allow_html=True)

# ---------- Available Modules Section ----------
st.markdown("### >>> Available Modules")

cols = st.columns(3)
with cols[0]:
    st.markdown("""
    <div class="card">
        <h3>1️⃣ Trend Analyzer</h3>
        <p>Visualize CKPI patterns, detect anomalies, and analyze elevator performance using thresholds and peaks.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>2️⃣ JSON ➜ Excel Converter</h3>
        <p>Convert raw KPI JSON files into structured Excel reports for technician-level readability.</p>
    </div>
    """, unsafe_allow_html=True)

with cols[1]:
    st.markdown("""
    <div class="card">
        <h3>3️⃣ Word Report Generator</h3>
        <p>Generate clean, formatted Word reports from live cloud data — perfect for inspection documentation.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>4️⃣ Maintenance Tracker</h3>
        <p>Track maintenance checks, technician comments, and issue resolutions directly from actionable reports.</p>
    </div>
    """, unsafe_allow_html=True)

with cols[2]:
    st.markdown("""
    <div class="card">
        <h3>5️⃣ Equipment Health Forecast</h3>
        <p>Forecast upcoming failures and evaluate unit health using time-series prediction models (Prophet, ARIMA).</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <h3>6️⃣ Report Archive</h3>
        <p>Access and download previously generated reports — filtered by date, KPI, or equipment ID.</p>
    </div>
    """, unsafe_allow_html=True)

# ---------- How To Use ----------
st.markdown("### 🧭 How to Use")
st.markdown("""
1. Use the sidebar to navigate between modules.  
2. Upload your relevant dataset or JSON/Excel file.  
3. Apply **filters, graphs, and AI modules** to analyze your data.  
4. Download results or reports for your maintenance workflow.
""")

# ---------- Footer ----------
st.markdown("""
<div class="footer">
    © 2025 KONE Digital Maintenance | Developed with ❤️ by 
    <a href="https://www.linkedin.com/in/pranav-vikraman-322020242/" target="_blank" style="color:#003087; text-decoration:none; font-weight:bold;">
        PRANAV VIKRAMAN S S
    </a>
</div>
""", unsafe_allow_html=True)



