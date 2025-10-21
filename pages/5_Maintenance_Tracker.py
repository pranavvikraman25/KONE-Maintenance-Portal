import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from docx import Document

st.title("🧰 Maintenance Tracker — Technician Action Center")

st.markdown("""
Upload your **Actionable Report (Excel/CSV)** from Trend Analysis to mark maintenance actions.  
Each row represents a CKPI reading — mark as:

✅ **Checked** if the task is complete or verified  
❌ **Wrong / Review** if the task needs attention  
""")

# --- File Upload ---
uploaded = st.file_uploader("Upload Actionable Report (Excel/CSV)", type=["xlsx", "csv"])

if not uploaded:
    st.info("Upload a file to start tracking maintenance progress.")
    st.stop()

# --- Read file ---
if uploaded.name.endswith(".csv"):
    df = pd.read_csv(uploaded)
else:
    df = pd.read_excel(uploaded)

# --- Ensure expected columns exist ---
if not {"eq", "ckpi", "ckpi_statistics_date"}.issubset(df.columns):
    st.error("Uploaded file missing required columns: 'eq', 'ckpi', 'ckpi_statistics_date'")
    st.stop()

# --- Prepare data ---
df["ckpi_statistics_date"] = pd.to_datetime(df["ckpi_statistics_date"], errors="coerce")
df = df.sort_values("ckpi_statistics_date")

# Initialize session storage
if "maint_table" not in st.session_state:
    df["✅ checked"] = False
    df["❌ wrong / review"] = False
    st.session_state["maint_table"] = df.copy()

# --- Load from session ---
edited_df = st.session_state["maint_table"].copy()

#-----------side filter---------------------------------------------

with st.sidebar:
    st.subheader("⚙️ Filters")

    # --- Safe handling: if columns not found yet ---
    if "eq" in edited_df.columns:
        eqs = sorted(edited_df["eq"].dropna().unique())
    else:
        eqs = []
    selected_eq = st.multiselect("Select Equipment(s)", eqs, default=eqs)

    kpis = [
        "doorfriction",
        "cumulativedoorspeederror",
        "lockhookclosingtime",
        "lockhooktime",
        "maximumforceduringcompress",
        "landingdoorlockrollerclearance",
    ]
    selected_kpi = st.multiselect("Select KPI(s)", kpis, default=kpis)

    # --- Date range filter ---
    if "ckpi_statistics_date" in edited_df.columns and not edited_df["ckpi_statistics_date"].isna().all():
        min_date = edited_df["ckpi_statistics_date"].min()
        max_date = edited_df["ckpi_statistics_date"].max()
        start_date, end_date = st.date_input(
            "Select Date Range (Available Only Within Data)",
            [min_date.date(), max_date.date()],
            min_value=min_date.date(),
            max_value=max_date.date()
        )
    else:
        start_date = end_date = datetime.today().date()
        st.info("Upload a valid file to activate date filters.")


# --- Apply filters ---
df_filtered = edited_df[
    (edited_df["eq"].isin(selected_eq)) &
    (edited_df["ckpi"].str.lower().isin([k.lower() for k in selected_kpi])) &
    (edited_df["ckpi_statistics_date"].dt.date >= start_date) &
    (edited_df["ckpi_statistics_date"].dt.date <= end_date)
].copy()

# --- Select All / Deselect All ---
col1, col2 = st.columns(2)
with col1:
    if st.button("✅ Select All (Checked)"):
        df_filtered["✅ checked"] = True
        df_filtered["❌ wrong / review"] = False
        st.session_state["maint_table"].update(df_filtered)
        st.rerun()
with col2:
    if st.button("❌ Deselect All"):
        df_filtered["✅ checked"] = False
        df_filtered["❌ wrong / review"] = False
        st.session_state["maint_table"].update(df_filtered)
        st.rerun()

# --- Editable Table ---
edited_filtered_df = st.data_editor(
    df_filtered,
    use_container_width=True,
    num_rows="dynamic",
    key="maint_table_edit"
)

# --- Enforce mutual exclusivity ---
for i in range(len(edited_filtered_df)):
    checked = bool(edited_filtered_df.at[i, "✅ checked"])
    wrong = bool(edited_filtered_df.at[i, "❌ wrong / review"])
    if checked and wrong:
        edited_filtered_df.at[i, "❌ wrong / review"] = False

# Update only edited rows back into session table
st.session_state["maint_table"].update(edited_filtered_df)

# --- Highlight instantly ---
def highlight_action(row):
    if row["✅ checked"]:
        return ["background-color: #b5e7a0"] * len(row)
    elif row["❌ wrong / review"]:
        return ["background-color: #f4a6a6"] * len(row)
    return [""] * len(row)

styled_df = edited_filtered_df.style.apply(highlight_action, axis=1)
st.dataframe(styled_df, use_container_width=True)

# --- Word Report Export ---
if st.button("💾 Submit and Generate Word Report"):
    final_df = st.session_state["maint_table"]

    checked_df = final_df[final_df["✅ checked"]]
    wrong_df = final_df[final_df["❌ wrong / review"]]

    if checked_df.empty and wrong_df.empty:
        st.warning("No maintenance actions marked. Please select before generating report.")
    else:
        doc = Document()
        doc.add_heading("Maintenance Review Report", level=1)
        doc.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.add_paragraph("")

        # Table headers
        headers = ["eq", "ckpi", "ckpi_statistics_date", "floor", "ave", "variability_index", "Priority Flag", "Status"]
        table = doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"
        hdr_cells = table.rows[0].cells
        for i, h in enumerate(headers):
            hdr_cells[i].text = h

        # Add rows
        merged = pd.concat([
            checked_df.assign(Status="✅ Completed"),
            wrong_df.assign(Status="❌ Review Needed")
        ], ignore_index=True)

        for _, row in merged.iterrows():
            row_cells = table.add_row().cells
            for i, h in enumerate(headers):
                val = row.get(h, "")
                row_cells[i].text = str(val)
                shading = row_cells[i]._tc.get_or_add_tcPr().add_new_shd()
                shading.val = "clear"
                shading.color = "auto"
                shading.fill = "C6EFCE" if row["Status"] == "✅ Completed" else "FFC7CE"

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        st.download_button(
            label="⬇️ Download Word Report",
            data=buffer,
            file_name=f"Maintenance_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
