import streamlit as st
import os
import pandas as pd

st.title("📂 Report Archive")

st.markdown("""
This section lists all available reports from the `/reports` folder  
and lets you download them directly.
""")

REPORT_PATH = "reports"
if not os.path.exists(REPORT_PATH):
    os.makedirs(REPORT_PATH)

files = [f for f in os.listdir(REPORT_PATH) if f.endswith((".xlsx",".csv",".docx",".pdf"))]
if not files:
    st.info("No reports found yet.")
    st.stop()

for f in files:
    path = os.path.join(REPORT_PATH, f)
    st.download_button(
        label=f"📄 Download {f}",
        data=open(path, "rb").read(),
        file_name=f
    )
