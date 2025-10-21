import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Maintenance Tracker", layout="wide")
st.title("🧰 Maintenance Tracker — Technician Action Center")

st.markdown("""
Upload your **Actionable Report (Excel/CSV)** from Trend Analysis to mark maintenance actions.  
Each row represents a CKPI reading — mark:
- ✅ **Checked** if the task is complete or verified  
- ❌ **Wrong / Review** if the task needs attention  

Only one can be selected per row.  
This version filters only the **6 key CKPIs** and adds **precise date limits** based on your data.
""")

# -------------------------------------------------------------------------
# 🧠 Session Initialization
# -------------------------------------------------------------------------
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "df_cache" not in st.session_state:
    st.session_state.df_cache = None
if "sel_eqs" not in st.session_state:
    st.session_state.sel_eqs = []
if "sel_ckpis" not in st.session_state:
    st.session_state.sel_ckpis = []
if "sel_date_range" not in st.session_state:
    st.session_state.sel_date_range = None
if "last_edited_df" not in st.session_state:
    st.session_state.last_edited_df = None

# -------------------------------------------------------------------------
# 🧹 Reset Mechanism
# -------------------------------------------------------------------------
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset Session"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("✅ Session cleared. Ready for a new file.")
    st.experimental_rerun()

# -------------------------------------------------------------------------
# 📂 Upload / Reuse Logic
# -------------------------------------------------------------------------
uploaded = st.file_uploader("📂 Upload Actionable Report", type=["xlsx", "csv"], key="file_input")

if uploaded is None and st.session_state.df_cache is not None:
    choice = st.radio(
        "A previous file was found. What would you like to do?",
        ["📁 Reuse old file", "🆕 Upload a new one"],
        index=0
    )
    if choice == "📁 Reuse old file":
        df = st.session_state.df_cache
        st.info("Using previously uploaded file.")
    else:
        st.session_state.df_cache = None
        st.session_state.uploaded_file = None
        st.warning("Please upload a new file above to continue.")
        st.stop()
elif uploaded is not None:
    try:
        if uploaded.name.endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
        st.session_state.df_cache = df
        st.session_state.uploaded_file = uploaded
        st.success("✅ File successfully loaded and cached.")
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()
else:
    st.warning("📤 Please upload a file to begin tracking.")
    st.stop()

# -------------------------------------------------------------------------
# 🎯 Define 6 Key CKPIs
# -------------------------------------------------------------------------
KEY_CKPIS = [
    "doorfriction",
    "cumulativedoorspeederror",
    "lockhookclosingtime",
    "lockhooktime",
    "maximumforceduringcompress",
    "landingdoorlockrollerclearance"
]

# -------------------------------------------------------------------------
# 🧭 Sidebar Filters (Restricted to 6 CKPIs)
# -------------------------------------------------------------------------
st.sidebar.header("🔍 Filters")

# Ensure required columns
expected_cols = ["eq", "ckpi", "ckpi_statistics_date"]
missing_cols = [col for col in expected_cols if col not in df.columns]
if missing_cols:
    st.error(f"Missing required columns: {missing_cols}")
    st.stop()

# Clean CKPI names to lowercase for matching
df["ckpi"] = df["ckpi"].astype(str).str.lower()

# Equipment filter
eqs = sorted(df["eq"].dropna().unique())
if not st.session_state.sel_eqs:
    st.session_state.sel_eqs = eqs
sel_eqs = st.sidebar.multiselect("Select Equipment(s)", eqs, default=st.session_state.sel_eqs)
st.session_state.sel_eqs = sel_eqs

# KPI filter (only 6)
available_ckpis = [c for c in KEY_CKPIS if c in df["ckpi"].unique()]
if not available_ckpis:
    st.error("❌ None of the 6 main CKPIs found in your data.")
    st.stop()

if not st.session_state.sel_ckpis:
    st.session_state.sel_ckpis = available_ckpis
sel_ckpis = st.sidebar.multiselect("Select KPI(s)", available_ckpis, default=st.session_state.sel_ckpis)
st.session_state.sel_ckpis = sel_ckpis

# Date range
df["ckpi_statistics_date"] = pd.to_datetime(df["ckpi_statistics_date"], errors="coerce")
df = df.dropna(subset=["ckpi_statistics_date"])

# Auto-limit the calendar range
min_d, max_d = df["ckpi_statistics_date"].min().date(), df["ckpi_statistics_date"].max().date()
if st.session_state.sel_date_range is None:
    st.session_state.sel_date_range = [min_d, max_d]

st.sidebar.markdown("### 📅 Date Range (Available Only Within Data)")
sel_range = st.sidebar.date_input(
    "Select Date Range",
    value=st.session_state.sel_date_range,
    min_value=min_d,
    max_value=max_d
)
st.session_state.sel_date_range = sel_range
start_d, end_d = sel_range

# -------------------------------------------------------------------------
# 🔍 Apply Filters
# -------------------------------------------------------------------------
df_filt = df[
    (df["eq"].isin(sel_eqs))
    & (df["ckpi"].isin(sel_ckpis))
    & (df["ckpi_statistics_date"].dt.date >= start_d)
    & (df["ckpi_statistics_date"].dt.date <= end_d)
]

if df_filt.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# -------------------------------------------------------------------------
# 📈 Variability and Flags
# -------------------------------------------------------------------------
def calc_var(values):
    v = pd.to_numeric(values, errors="coerce").dropna()
    if len(v) < 4:
        return 0
    diffs = np.diff(v)
    return np.sum(np.diff(np.sign(diffs)) != 0) / len(v) * 100

if "ave" in df_filt.columns:
    var_df = (
        df_filt.groupby(["eq", "ckpi"])["ave"]
        .apply(calc_var)
        .reset_index()
        .rename(columns={"ave": "variability_index"})
    )
    df_filt = pd.merge(df_filt, var_df, on=["eq", "ckpi"], how="left")
    df_filt["Priority Flag"] = np.where(df_filt["variability_index"] > 30, "⚠️ High Variability", "")
else:
    st.warning("No 'ave' column found for variability analysis.")

# -------------------------------------------------------------------------
# 🧾 Editable Table (✅ / ❌)
# -------------------------------------------------------------------------
if st.session_state.last_edited_df is not None:
    df_filt = st.session_state.last_edited_df.copy()

if "✅ checked" not in df_filt.columns:
    df_filt["✅ checked"] = False
if "❌ wrong / review" not in df_filt.columns:
    df_filt["❌ wrong / review"] = False

st.markdown("### 🧾 Maintenance Task Review")

edited_df = st.data_editor(
    df_filt,
    use_container_width=True,
    num_rows="dynamic",
    key="maint_table"
)

# Ensure mutual exclusivity
for i in range(len(edited_df)):
    if edited_df.at[i, "✅ checked"] and edited_df.at[i, "❌ wrong / review"]:
        edited_df.at[i, "❌ wrong / review"] = False

st.session_state.last_edited_df = edited_df.copy()

# Highlight rows
def highlight_action(row):
    if row["✅ checked"]:
        return ["background-color: #b5e7a0"] * len(row)
    elif row["❌ wrong / review"]:
        return ["background-color: #f4a6a6"] * len(row)
    return [""] * len(row)

styled_df = edited_df.style.apply(highlight_action, axis=1)
st.markdown("### 📋 Reviewed Maintenance Records")
st.dataframe(styled_df, use_container_width=True)

# -------------------------------------------------------------------------
# 📤 Submit & Download
# -------------------------------------------------------------------------
st.markdown("---")
st.subheader("📤 Submit Maintenance Review")

if st.button("✅ Submit and Lock Progress"):
    st.success("✅ Submission recorded! Download your reviewed file below.")

    def to_excel(df_):
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df_.to_excel(writer, index=False, sheet_name="Maintenance_Review")
        out.seek(0)
        return out

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"Maintenance_Review_{ts}.xlsx"
    st.download_button(
        "💾 Download Maintenance Review File",
        data=to_excel(edited_df),
        file_name=fname
    )
else:
    st.info("Mark all tasks and then click Submit when done.")
