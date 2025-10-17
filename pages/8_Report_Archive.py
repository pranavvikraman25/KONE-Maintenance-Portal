import streamlit as st
import os
import pandas as pd

UPLOAD_DIR = "backend/uploads"
files = os.listdir(UPLOAD_DIR)

st.title("📂 Report Archive")
if not files:
    st.info("No reports or uploads yet.")
else:
    for f in files:
        st.download_button(label=f"Download {f}", data=open(os.path.join(UPLOAD_DIR, f), "rb"), file_name=f)

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
