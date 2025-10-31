import streamlit as st
import os
from backend.report_utils import list_all_reports, delete_report

st.title("📁 Report Archive")

st.markdown("""
All reports saved by modules (Trend_Analyzer, JSON_to_Excel, Report_Generator, etc.).  
You can download or delete reports directly from here.
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

    deleted_any = False  # track refresh trigger

    for module, files in grouped.items():
        # Filter by search
        visible_files = [f for f in files if query in os.path.basename(f).lower() or query in module.lower()]
        if not visible_files:
            continue

        st.markdown(f"## 🧩 {module}")
        latest_files = sorted(visible_files, reverse=True)[:10]  # show latest 10 files

        for report_path in latest_files:
            file_name = os.path.basename(report_path)
            ext = os.path.splitext(file_name)[1].lower()
            icon = "📊" if ext == ".xlsx" else "📄" if ext in [".docx", ".doc"] else "🧾"

            col1, col2 = st.columns([6, 1])
            with col1:
                with open(report_path, "rb") as f:
                    data = f.read()
                st.download_button(
                    label=f"{icon} {file_name}",
                    data=data,
                    file_name=file_name,
                    mime="application/octet-stream",
                    key=file_name
                )
            with col2:
                if st.button("🗑", key=f"delete_{file_name}", help="Delete this report"):
                    ok = delete_report(report_path)
                    if ok:
                        st.success(f"Deleted: {file_name}")
                        deleted_any = True
                    else:
                        st.error(f"Failed to delete {file_name}")

        st.markdown("---")

    # If any file was deleted, rerun to refresh the list
    if deleted_any:
        st.experimental_rerun()

    st.success(f"✅ Total saved reports: {len(reports)}")

# Optional: add a "Clear All" button
st.markdown("---")
if st.button("🧹 Clear All Reports"):
    import shutil
    from backend.report_utils import REPORTS_DIR
    try:
        shutil.rmtree(REPORTS_DIR)
        os.makedirs(REPORTS_DIR, exist_ok=True)
        st.success("All reports deleted successfully.")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Failed to clear reports: {e}")
