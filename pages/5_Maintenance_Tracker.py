import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.shared import Inches
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

st.set_page_config(page_title="Maintenance Tracker", layout="wide")
st.title("🧰 Maintenance Tracker — Technician Action Center")

st.markdown("""
Upload your **Actionable Report (Excel/CSV)** from Trend Analysis to mark maintenance actions.  
Each row represents a CKPI reading — mark:
- ✅ **Checked** if the task is complete or verified  
- ❌ **Wrong / Review** if the task needs attention  

Each action instantly changes color (green for ✅, red for ❌) and can be downloaded as a **Word (.docx)** report.
""")

# --- Session State Setup ---
for key in ["uploaded_file", "maint_df", "maint_table_state"]:
    if key not in st.session_state:
        st.session_state[key] = None

# --- File Upload ---
uploaded = st.file_uploader("📂 Upload Actionable Report", type=["xlsx", "csv"])
if uploaded:
    try:
        df = pd.read_excel(uploaded) if uploaded.name.endswith(".xlsx") else pd.read_csv(uploaded)
        df["ckpi"] = df["ckpi"].astype(str).str.lower()
        st.session_state.maint_df = df.copy()
        st.session_state.maint_table_state = df.copy()
        st.success("✅ File loaded successfully.")
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()
else:
    if st.session_state.maint_df is not None:
        df = st.session_state.maint_df.copy()
        st.info("Using previously uploaded file.")
    else:
        st.warning("Please upload a file to continue.")
        st.stop()

# --- Define KPI Filter ---
KEY_CKPIS = [
    "doorfriction",
    "cumulativedoorspeederror",
    "lockhookclosingtime",
    "lockhooktime",
    "maximumforceduringcompress",
    "landingdoorlockrollerclearance"
]

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")
eqs = sorted(df["eq"].dropna().unique()) if "eq" in df.columns else []
sel_eqs = st.sidebar.multiselect("Select Equipment(s)", eqs, default=eqs)

available_ckpis = [k for k in KEY_CKPIS if k in df["ckpi"].unique()]
sel_ckpis = st.sidebar.multiselect("Select KPI(s)", available_ckpis, default=available_ckpis)

# --- Date Range Filter ---
if "ckpi_statistics_date" in df.columns:
    df["ckpi_statistics_date"] = pd.to_datetime(df["ckpi_statistics_date"], errors="coerce")
    if df["ckpi_statistics_date"].isna().all():
        st.warning("⚠️ No valid dates found in your file.")
        st.stop()
else:
    st.warning("⚠️ Missing 'ckpi_statistics_date' column.")
    st.stop()

min_d, max_d = df["ckpi_statistics_date"].min().date(), df["ckpi_statistics_date"].max().date()
sel_range = st.sidebar.date_input("Select Date Range", [min_d, max_d], min_value=min_d, max_value=max_d)
start_d, end_d = sel_range

# --- Filtered Data ---
df_filtered = df[
    (df["eq"].isin(sel_eqs)) &
    (df["ckpi"].isin(sel_ckpis)) &
    (df["ckpi_statistics_date"].dt.date >= start_d) &
    (df["ckpi_statistics_date"].dt.date <= end_d)
].copy()

if df_filtered.empty:
    st.warning("No data found for selected filters.")
    st.stop()

# --- Add Missing Columns Safely ---
for col in ["✅ checked", "❌ wrong / review"]:
    if col not in df_filtered.columns:
        df_filtered[col] = False

# --- Variability Index ---
def calc_var(values):
    v = pd.to_numeric(values, errors="coerce").dropna()
    if len(v) < 4:
        return 0
    diffs = np.diff(v)
    return np.sum(np.diff(np.sign(diffs)) != 0) / len(v) * 100

if "ave" in df_filtered.columns:
    var_df = (
        df_filtered.groupby(["eq", "ckpi"])["ave"]
        .apply(calc_var)
        .reset_index()
        .rename(columns={"ave": "variability_index"})
    )
    df_filtered = pd.merge(df_filtered, var_df, on=["eq", "ckpi"], how="left")
    df_filtered["Priority Flag"] = np.where(df_filtered["variability_index"] > 30, "⚠️ High Variability", "")

# --- Control Buttons ---
st.markdown("### 🧾 Maintenance Task Table")
col1, col2 = st.columns(2)
with col1:
    if st.button("☑️ Select All"):
        df_filtered["✅ checked"] = True
        df_filtered["❌ wrong / review"] = False
        st.session_state.maint_table_state = df_filtered.copy()
        st.rerun()
with col2:
    if st.button("🚫 Deselect All"):
        df_filtered["✅ checked"] = False
        df_filtered["❌ wrong / review"] = False
        st.session_state.maint_table_state = df_filtered.copy()
        st.rerun()

# --- Optimized Editable Table ---
df_display = st.session_state.maint_table_state.copy() if st.session_state.maint_table_state is not None else df_filtered.copy()

# Guarantee columns exist before display
for col in ["✅ checked", "❌ wrong / review"]:
    if col not in df_display.columns:
        df_display[col] = False

edited_df = st.data_editor(
    df_display,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    key="maint_table",
    column_config={
        "✅ checked": st.column_config.CheckboxColumn("✅ Checked", help="Mark as completed"),
        "❌ wrong / review": st.column_config.CheckboxColumn("❌ Review", help="Mark for recheck"),
    },
)

# --- Enforce Mutual Exclusivity ---
for i in range(len(edited_df)):
    if "✅ checked" in edited_df.columns and "❌ wrong / review" in edited_df.columns:
        if bool(edited_df.at[i, "✅ checked"]) and bool(edited_df.at[i, "❌ wrong / review"]):
            edited_df.at[i, "❌ wrong / review"] = False

st.session_state.maint_table_state = edited_df.copy()

# --- Row Highlighting ---
def highlight_action(row):
    if row["✅ checked"]:
        return ["background-color: #b5e7a0"] * len(row)
    elif row["❌ wrong / review"]:
        return ["background-color: #f4a6a6"] * len(row)
    return [""] * len(row)

st.dataframe(edited_df.style.apply(highlight_action, axis=1), use_container_width=True)

# --- Export as Word (Landscape) ---
if st.button("✅ Submit and Generate Word Report"):
    final_df = st.session_state.maint_table_state.copy()
    checked_df = final_df[final_df["✅ checked"]]
    wrong_df = final_df[final_df["❌ wrong / review"]]

    if checked_df.empty and wrong_df.empty:
        st.warning("⚠️ No tasks selected for export.")
    else:
        doc = Document()

        # Landscape layout
        section = doc.sections[-1]
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width = Inches(11.69)
        section.page_height = Inches(8.27)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)

        doc.add_heading("Maintenance Review Report", level=1)
        doc.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.add_paragraph("")

        headers = list(final_df.columns)
        table = doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"

        hdr_cells = table.rows[0].cells
        for i, h in enumerate(headers):
            hdr_cells[i].text = str(h)

        for _, row in final_df.iterrows():
            row_cells = table.add_row().cells
            for i, h in enumerate(headers):
                val = row.get(h, "")
                row_cells[i].text = str(val)
                color = "C6EFCE" if row.get("✅ checked") else "FFC7CE" if row.get("❌ wrong / review") else "FFFFFF"
                row_cells[i]._tc.get_or_add_tcPr().append(
                    parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls("w"), color))
                )

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        st.download_button(
            "💾 Download Maintenance Report (Word)",
            data=buffer,
            file_name=f"Maintenance_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
