# app.py
import streamlit as st

# --- Page Setup ---
st.set_page_config(
    page_title="KONE Maintenance Portal",
    layout="wide",
    page_icon="🧭"
)

# --- Load CSS ---
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("assets/style.css")

# --- Sidebar Branding ---
with st.sidebar:
    st.image("assets/logo.png", width=160)
    st.markdown("### 🏢 KONE Maintenance Portal")
    st.markdown("---")
    st.write("Use the left sidebar to navigate across different modules of the portal.")
    st.markdown("---")
    st.markdown("#### 💡 About")
    st.caption("This internal portal is designed to analyze KPI trends, detect anomalies, "
               "and generate actionable insights for predictive maintenance.")

# --- Main Page ---
st.title("KONE Predictive Maintenance Portal")
st.markdown("""
Welcome to **KONE’s Centralized Maintenance Dashboard**,  
a unified portal designed to support the **Engineering Analytics** and **Field Maintenance** teams.

This application combines all your KPI tools, analysis modules, and AI insights into one seamless platform.
""")

st.markdown("### 🔧 Available Modules")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **1️⃣ Trend Analyzer**  
    Visualize CKPI patterns and detect anomalies across elevators.  
    Tracks performance using thresholds and trend graphs.
    """)

    st.markdown("""
    **2️⃣ JSON → Excel Converter**  
    Converts raw KPI JSON into human-readable Excel files.  
    Great for field engineers reviewing daily reports.
    """)

    st.markdown("""
    **3️⃣ Live Cloud Data → Word Report Generator**  
    Generates readable Word reports from cloud telemetry for documentation.
    """)

with col2:
    st.markdown("""
    **4️⃣ AI Chatbot (Anomaly Q&A)**  
    Interact with your KPI dataset using **Llama 3 (via Ollama)**.  
    Ask questions like “Which EQ had most peaks last week?”
    """)

    st.markdown("""
    **5️⃣ Maintenance Tracker**  
    Technicians can mark “Checked” / “Resolved” on issues from the Actionable Report.
    """)

    st.markdown("""
    **6️⃣ Equipment Health Forecast**  
    Compute weighted KPI health per EQ — identify which units need inspection first and Forecast upcoming failures using time-series AI models - Prophet
    """)

st.markdown("""

**7️⃣ Report Archive**  
Browse and download generated reports by date or equipment ID.
""")

st.markdown("---")
st.markdown("### 📘 How to Use")
st.markdown("""
1. Navigate using the left sidebar (each module opens in a new view).  
2. Upload the relevant dataset or report in each page.  
3. Use **filters, graphs, and AI insights** to analyze the results.  
4. Download results or actionable reports for technician use.
""")

st.markdown("---")
st.caption("© 2025 KONE Digital Maintenance | Developed by PRANAV VIKRAMAN S S")




