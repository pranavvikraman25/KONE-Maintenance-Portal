import streamlit as st
import os
from backend.report_utils import list_all_reports

st.title("📁 Report Archive")

st.markdown("""
All reports saved by modules (Trend_Analyzer, JSON_to_Excel, Report_Generator, etc.)  
Each section lists the latest reports for that module.
""")

reports = list_all_reports()

if not reports:
    st.info("No reports found yet.")
else:
    grouped = {}
    for path in reports:
        module = os.path.basename(os.path.dirname(path))
        grouped.setdefault(module, []).append(path)

    # Search box
    query = st.text_input("🔍 Search reports (by name or module):", value="").strip().lower()

    for module, files in grouped.items():
        # Apply search filter
        visible_files = [f for f in files if query in os.path.basename(f).lower() or query in module.lower()]
        if not visible_files:
            continue

        st.markdown(f"## 🧩 {module}")
        latest_files = sorted(visible_files, reverse=True)[:5]  # show latest 5 per module

        for report_path in latest_files:
            file_name = os.path.basename(report_path)
            ext = os.path.splitext(file_name)[1].lower()
            icon = "📊" if ext == ".xlsx" else "📄" if ext in [".docx", ".doc"] else "🧾"

            with open(report_path, "rb") as f:
                data = f.read()

            st.download_button(
                label=f"{icon} {file_name}",
                data=data,
                file_name=file_name,
                mime="application/octet-stream",
                key=file_name
            )
        st.markdown("---")

    st.success(f"✅ Total saved reports: {len(reports)}")
def delete_report(file_path):
    """Delete a report file safely."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting {file_path}: {e}")
        return False
