# pages/8_Report_Archive.py
import streamlit as st
import os
from backend.report_utils import list_all_reports

st.title("📁 Report Archive")
st.markdown("All reports saved by modules (Trend_Analyzer, JSON_to_Excel, etc.).")

reports = list_all_reports()

if not reports:
    st.info("No reports found yet.")
else:
    # group by module folder
    grouped = {}
    for path in reports:
        module = os.path.basename(os.path.dirname(path))
        grouped.setdefault(module, []).append(path)

    # optional search/filter input
    query = st.text_input("Search reports (filename, module, filter label)", value="")
    for module, files in grouped.items():
        st.markdown(f"### 🧩 {module}")
        for report_path in files:
            file_name = os.path.basename(report_path)
            if query and query.lower() not in file_name.lower() and query.lower() not in module.lower():
                continue
            ext = os.path.splitext(file_name)[1].lower()
            icon = "📊" if ext == ".xlsx" else "📄" if ext in [".docx", ".doc"] else "🧾"
            with open(report_path, "rb") as f:
                data = f.read()
            st.download_button(label=f"{icon} {file_name}", data=data, file_name=file_name, key=report_path)
        st.markdown("---")
    st.success(f"Total reports: {len(reports)}")
