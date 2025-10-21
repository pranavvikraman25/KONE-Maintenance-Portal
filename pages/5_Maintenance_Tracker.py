import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime
from docx import Document

st.set_page_config(page_title="Maintenance Tracker", layout="wide")
st.title("🧰 Maintenance Tracker — Technician Action Center")

st.markdown("""
Upload your **Actionable Report (Excel/CSV)** from Trend Analysis to mark maintenance actions.  
Each row represents a CKPI reading — mark:
- ✅ **Checked** if the task is complete or verified  
- ❌ **Wrong / Review** if the task needs attention  

Each action instantly changes color (green for ✅, red for ❌) and can be downloaded as a **Word (.docx)** report.
""")

# --- Session Setup ---
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "maint_df" not in st.session_state:
    st.session_state.maint_df = None

# --- Upload Section ---
uploaded = st.file_uploader("📂 Upload Actionable Report", type=["xlsx", "csv"])
if uploaded:
    try:
        df = pd.read_excel(uploaded) if uploaded.name.endswith('.xlsx') else pd.read_csv(uploaded)
        df["ckpi"] = df["ckpi"].astype(str).str.lower()
        st.session_state.maint_df = df
        st.session_state.uploaded_file = uploaded
        st.success("✅ File loaded successfully.")
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()
else:
    if st.session_state.maint_df is not None:
        df = st.session_state.maint_df
        st.info("Using previously uploaded file.")
    else:
        st.warning("Please upload a file to continue.")
        st.stop()

# --- KPI Filter Restriction ---
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
df["ckpi_statistics_date"] = pd.to_datetime(df["ckpi_statistics_date"], errors="coerce")
if df["ckpi_statistics_date"].isna().all():
    st.warning("Invalid or missing date values in your file.")
    st.stop()

min_d, max_d = df["ckpi_statistics_date"].min().date(), df["ckpi_statistics_date"].max().date()
sel_range = st.sidebar.date_input("Select Date Range", [min_d, max_d], min_value=min_d, max_value=max_d)
start_d, end_d = sel_range

# --- Apply Filters ---
df_filtered = df[
    (df["eq"].isin(sel_eqs)) &
    (df["ckpi"].isin(sel_ckpis)) &
    (df["ckpi_statistics_date"].dt.date >= start_d) &
    (df["ckpi_statistics_date"].dt.date <= end_d)
].copy()

if df_filtered.empty:
    st.warning("No data found for selected filters.")
    st.stop()

# --- Add Variability Index ---
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

# --- Checkbox Columns ---
if "✅ checked" not in df_filtered.columns:
    df_filtered["✅ checked"] = False
if "❌ wrong / review" not in df_filtered.columns:
    df_filtered["❌ wrong / review"] = False

# --- Persistent Checkbox State ---
if "checked_state" not in st.session_state:
    st.session_state.checked_state = df_filtered.copy()

# Sync the new filtered view with stored state
common_cols = list(set(df_filtered.columns) & set(st.session_state.checked_state.columns))
for col in common_cols:
    df_filtered[col] = st.session_state.checked_state[col].reindex(df_filtered.index, fill_value=False)

# --- Control Buttons ---
st.markdown("### 🧾 Maintenance Task Table")
col1, col2 = st.columns(2)
with col1:
    if st.button("☑️ Select All"):
        df_filtered["✅ checked"] = True
        df_filtered["❌ wrong / review"] = False
        st.session_state.checked_state.update(df_filtered)
        st.session_state.maint_df.update(df_filtered)
        st.rerun()

with col2:
    if st.button("🚫 Deselect All"):
        df_filtered["✅ checked"] = False
        df_filtered["❌ wrong / review"] = False
        st.session_state.checked_state.update(df_filtered)
        st.session_state.maint_df.update(df_filtered)
        st.rerun()

# --- Editable Table ---
edited_df = st.data_editor(df_filtered, use_container_width=True, num_rows="dynamic", key="maint_table")

# --- Enforce Mutual Exclusivity ---
for i in range(len(edited_df)):
    checked = bool(edited_df.at[i, "✅ checked"])
    wrong = bool(edited_df.at[i, "❌ wrong / review"])
    if checked and wrong:
        edited_df.at[i, "❌ wrong / review"] = False

# --- Save Back to Session ---
st.session_state.checked_state.update(edited_df)
st.session_state.maint_df.update(edited_df)

# --- Highlight instantly ---
def highlight_action(row):
    if row["✅ checked"]:
        return ["background-color: #b5e7a0"] * len(row)
    elif row["❌ wrong / review"]:
        return ["background-color: #f4a6a6"] * len(row)
    return [""] * len(row)

styled_df = edited_df.style.apply(highlight_action, axis=1)
st.dataframe(styled_df, use_container_width=True)

# --- Word Export ---
if st.button("✅ Submit and Generate Word Report"):
    final_df = st.session_state.checked_state.copy()

    checked_df = final_df[final_df["✅ checked"]]
    wrong_df = final_df[final_df["❌ wrong / review"]]

    if checked_df.empty and wrong_df.empty:
        st.warning("No maintenance actions marked.")
    else:
        doc = Document()
        doc.add_heading("Maintenance Review Report", level=1)
        doc.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.add_paragraph("")

        headers = ["eq", "ckpi", "ckpi_statistics_date", "floor", "ave", "variability_index", "Priority Flag", "Status"]
        table = doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"
        hdr_cells = table.rows[0].cells
        for i, h in enumerate(headers):
            hdr_cells[i].text = h

        # Merge & fill rows
        checked_df = checked_df.assign(Status="✅ Completed")
        wrong_df = wrong_df.assign(Status="❌ Review Needed")
        merged = pd.concat([checked_df, wrong_df], ignore_index=True)

        for _, row in merged.iterrows():
            row_cells = table.add_row().cells
            for i, h in enumerate(headers):
                val = row.get(h, "")
                row_cells[i].text = str(val)

            # color background (safe XML method)
                from docx.oxml import parse_xml
                from docx.oxml.ns import nsdecls
                
                if row["Status"].startswith("✅"):
                    shade_color = "C6EFCE"  # light green
                else:
                    shade_color = "FFC7CE"  # light red
                
                row_cells[i]._tc.get_or_add_tcPr().append(
                    parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), shade_color))
                )


        # export file
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        st.download_button(
            label="💾 Download Maintenance Report (Word)",
            data=buffer,
            file_name=f"Maintenance_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
