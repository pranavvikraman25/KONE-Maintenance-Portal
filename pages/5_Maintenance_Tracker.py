import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Maintenance Tracker", layout="wide")
st.title("🧰 Maintenance Tracker — Technician Action Center")

st.markdown("""
Upload the **Actionable Report (Excel/CSV)** generated from your Trend Analysis.  
You can filter by Equipment, KPI, and Date, then mark each record as:
- ✅ **Checked** → Verified and resolved  
- ❌ **Wrong / Review** → Needs further inspection  
""")

# -------------------- Upload --------------------
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

# --- Normalize column names ---
df.columns = [c.strip().lower() for c in df.columns]

# --- Expected core columns ---
expected_cols = ["eq", "ckpi", "ckpi_statistics_date", "floor"]
for col in expected_cols:
    if col not in df.columns:
        st.error(f"Required column '{col}' not found in uploaded file.")
        st.stop()

# -------------------- Sidebar Filters --------------------
st.sidebar.header("🔍 Filters")

# Equipment Filter
eq_list = sorted(df["eq"].dropna().unique())
selected_eq = st.sidebar.multiselect("Select Equipment(s)", eq_list, default=eq_list)

# KPI Filter
ckpi_list = sorted(df["ckpi"].dropna().unique())
selected_ckpis = st.sidebar.multiselect("Select KPI(s)", ckpi_list, default=ckpi_list)

# Date Filter
df["ckpi_statistics_date"] = pd.to_datetime(df["ckpi_statistics_date"], errors="coerce")
df = df.dropna(subset=["ckpi_statistics_date"])

min_date = df["ckpi_statistics_date"].min().date()
max_date = df["ckpi_statistics_date"].max().date()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])
start_date, end_date = date_range

# Apply Filters
filtered_df = df[
    (df["eq"].isin(selected_eq)) &
    (df["ckpi"].isin(selected_ckpis)) &
    (df["ckpi_statistics_date"].dt.date >= start_date) &
    (df["ckpi_statistics_date"].dt.date <= end_date)
]

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# -------------------- Variability Detection --------------------
# Identify CKPIs with high up/down fluctuations (uncertainty)
def calc_variability(values):
    values = pd.to_numeric(values, errors="coerce").dropna()
    if len(values) < 4:
        return 0
    diffs = np.diff(values)
    sign_changes = np.sum(np.diff(np.sign(diffs)) != 0)
    return round((sign_changes / len(values)) * 100, 1)

variability = (
    filtered_df.groupby(["eq", "ckpi"])["ave"]
    .apply(calc_variability)
    .reset_index()
    .rename(columns={"ave": "variability_index"})
)

filtered_df = pd.merge(filtered_df, variability, on=["eq", "ckpi"], how="left")
filtered_df["Priority Flag"] = np.where(filtered_df["variability_index"] > 30, "⚠️ High Variability", "")

# -------------------- Technician Action Table --------------------
st.markdown("### 🧾 Maintenance Task Review")

# Add action columns if not present
if "✅ checked" not in filtered_df.columns:
    filtered_df["✅ checked"] = False
if "❌ wrong / review" not in filtered_df.columns:
    filtered_df["❌ wrong / review"] = False

# Sort: show high variability first
filtered_df = filtered_df.sort_values(by="variability_index", ascending=False)

# Editable table
edited_df = st.data_editor(
    filtered_df,
    use_container_width=True,
    num_rows="dynamic",
    key="maint_table"
)

st.markdown("### 📋 Reviewed Maintenance Records")
st.dataframe(edited_df)

# -------------------- Submit Section --------------------
st.markdown("---")
st.subheader("📤 Submit Your Review")

if st.button("✅ Submit and Lock Progress"):
    st.success("✅ Submission recorded! Download your progress file below.")

    # Save reviewed data to Excel
    def df_to_excel_bytes(df_):
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df_.to_excel(writer, index=False, sheet_name="Maintenance_Review")
        out.seek(0)
        return out

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Maintenance_Progress_{current_time}.xlsx"

    st.download_button(
        "💾 Download Maintenance Progress",
        data=df_to_excel_bytes(edited_df),
        file_name=filename
    )

    st.info("Editing disabled after submission for audit integrity.")
else:
    st.warning("Make sure you review and mark before submitting.")
