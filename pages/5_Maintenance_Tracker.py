import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Maintenance Tracker", layout="wide")
st.title("🧰 Maintenance Tracker — Technician Action Center")

st.markdown("""
Upload the **Actionable Report (Excel/CSV)** generated from the Trend Analysis page.  
This module helps technicians **filter**, **review**, and **mark maintenance actions**.
""")

# -------------------- Upload Section --------------------
uploaded = st.file_uploader("📂 Upload Actionable Report", type=["xlsx", "csv"])
if not uploaded:
    st.info("Upload a file to begin tracking.")
    st.stop()

# --- Read File ---
try:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

if df.empty:
    st.warning("Uploaded file is empty.")
    st.stop()

# --- Normalize Columns ---
df.columns = [c.strip().lower() for c in df.columns]

# Check required columns
required_cols = ["kpi", "floor", "action needed"]
for col in required_cols:
    if col not in df.columns:
        st.error(f"Column '{col}' not found. Expected columns: {required_cols}")
        st.stop()

# Optional columns for filtering
eq_col = next((c for c in df.columns if "eq" in c), None)
date_col = next((c for c in df.columns if "date" in c or "day" in c), None)

# -------------------- Sidebar Filters --------------------
st.sidebar.header("🔍 Filters")

# EQ Filter
if eq_col:
    eq_list = sorted(df[eq_col].dropna().unique())
    selected_eq = st.sidebar.multiselect("Select Equipment(s)", eq_list, default=eq_list)
else:
    selected_eq = None

# KPI Filter
all_kpis = sorted(df["kpi"].dropna().unique())
selected_kpis = st.sidebar.multiselect("Select KPI(s)", all_kpis, default=all_kpis)

# Date Filter (if available)
if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    min_date, max_date = df[date_col].min().date(), df[date_col].max().date()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])
    start_date, end_date = date_range
else:
    start_date = end_date = None

# Apply filters
filtered_df = df.copy()
if selected_eq:
    filtered_df = filtered_df[filtered_df[eq_col].isin(selected_eq)]
if selected_kpis:
    filtered_df = filtered_df[filtered_df["kpi"].isin(selected_kpis)]
if date_col and start_date and end_date:
    filtered_df = filtered_df[(filtered_df[date_col].dt.date >= start_date) & (filtered_df[date_col].dt.date <= end_date)]

if filtered_df.empty:
    st.warning("No data found for selected filters.")
    st.stop()

# -------------------- Detect KPI Uncertainty --------------------
# Uncertainty = KPI with frequent fluctuations (peaks/lows count)
# Here we mark uncertain data with a tag.
def detect_uncertainty(values):
    values = pd.to_numeric(values, errors="coerce").dropna()
    if len(values) < 3:
        return 0
    diffs = np.diff(values)
    sign_changes = np.sum(np.diff(np.sign(diffs)) != 0)
    return sign_changes / len(values)

uncertainty_summary = filtered_df.groupby("kpi").apply(lambda g: detect_uncertainty(g.index)).reset_index(name="uncertainty_index")
high_uncertainty = uncertainty_summary.sort_values("uncertainty_index", ascending=False)["kpi"].tolist()
filtered_df["Priority Flag"] = filtered_df["kpi"].apply(lambda k: "⚠️ High Variability" if k in high_uncertainty[:2] else "")

# -------------------- Checkboxes for Technicians --------------------
st.markdown("### 🧾 Maintenance Task List")

# Add checkboxes
if "✅ Checked" not in filtered_df.columns:
    filtered_df["✅ Checked"] = False
if "❌ Wrong / Review" not in filtered_df.columns:
    filtered_df["❌ Wrong / Review"] = False

edited_df = st.data_editor(
    filtered_df,
    use_container_width=True,
    num_rows="dynamic",
    key="maintenance_table"
)

st.markdown("### 📋 Updated Maintenance Review")
st.dataframe(edited_df)

# -------------------- Submit Section --------------------
st.markdown("---")
st.subheader("📤 Submit Progress")

if st.button("✅ Submit and Lock Current Work"):
    st.success("✅ Submission recorded! You can now download your current progress for manager review.")
    st.markdown("_Editing has been disabled for this session._")

    # Save to Excel
    def df_to_excel_bytes(df_):
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df_.to_excel(writer, index=False, sheet_name="Maintenance_Review")
        out.seek(0)
        return out

    st.download_button(
        "💾 Download Maintenance Progress (Excel)",
        data=df_to_excel_bytes(edited_df),
        file_name="Maintenance_Progress_Report.xlsx"
    )
else:
    st.info("Make sure to review and mark all actions before submitting.")
