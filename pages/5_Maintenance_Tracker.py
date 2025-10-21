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
This version filters only the **6 key CKPIs** and applies filters correctly to both result tables.
""")

# --- Session Setup ---
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "df_cache" not in st.session_state:
    st.session_state.df_cache = None
if "last_edited_df" not in st.session_state:
    st.session_state.last_edited_df = None

# --- Reset Mechanism ---
if st.sidebar.button("🔄 Reset Session"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("✅ Session cleared. Upload a new file.")
    st.experimental_rerun()

# --- Upload Section ---
uploaded = st.file_uploader("📂 Upload Actionable Report", type=["xlsx", "csv"])
if uploaded:
    try:
        df = pd.read_excel(uploaded) if uploaded.name.endswith('.xlsx') else pd.read_csv(uploaded)
        st.session_state.df_cache = df
        st.session_state.uploaded_file = uploaded
        st.success("✅ File loaded successfully.")
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()
else:
    if st.session_state.df_cache is not None:
        df = st.session_state.df_cache
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

df["ckpi"] = df["ckpi"].astype(str).str.lower()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")
eqs = sorted(df["eq"].dropna().unique())
sel_eqs = st.sidebar.multiselect("Select Equipment(s)", eqs, default=eqs[:1] if eqs else [])

available_ckpis = [k for k in KEY_CKPIS if k in df["ckpi"].unique()]
sel_ckpis = st.sidebar.multiselect("Select KPI(s)", available_ckpis, default=available_ckpis)

# --- Date Range Filter ---
df["ckpi_statistics_date"] = pd.to_datetime(df["ckpi_statistics_date"], errors="coerce")
min_d, max_d = df["ckpi_statistics_date"].min().date(), df["ckpi_statistics_date"].max().date()
sel_range = st.sidebar.date_input(
    "Select Date Range", [min_d, max_d], min_value=min_d, max_value=max_d
)
start_d, end_d = sel_range

# --- Apply Filters ---
df_filtered = df[
    (df["eq"].isin(sel_eqs)) &
    (df["ckpi"].isin(sel_ckpis)) &
    (df["ckpi_statistics_date"].dt.date >= start_d) &
    (df["ckpi_statistics_date"].dt.date <= end_d)
]

if df_filtered.empty:
    st.warning("No data found for selected filters.")
    st.stop()

# --- Variability Calculation ---
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

# --- Editable Table ---
if "✅ checked" not in df_filtered.columns:
    df_filtered["✅ checked"] = False
if "❌ wrong / review" not in df_filtered.columns:
    df_filtered["❌ wrong / review"] = False

if st.session_state.last_edited_df is not None:
    df_filtered = st.session_state.last_edited_df

st.markdown("### 🧾 Maintenance Task Review")
edited_df = st.data_editor(df_filtered, use_container_width=True, num_rows="dynamic", key="maint_table")

# --- Enforce Single Selection Logic ---
for i in range(len(edited_df)):
    if edited_df.at[i, "✅ checked"] and edited_df.at[i, "❌ wrong / review"]:
        # keep only one active, last one clicked wins
        if st.session_state.get("last_click") == "✅":
            edited_df.at[i, "❌ wrong / review"] = False
        else:
            edited_df.at[i, "✅ checked"] = False

st.session_state.last_edited_df = edited_df

# --- Highlighted Table ---
def highlight_action(row):
    if row["✅ checked"]:
        return ["background-color: #b5e7a0"] * len(row)
    elif row["❌ wrong / review"]:
        return ["background-color: #f4a6a6"] * len(row)
    return [""] * len(row)

styled_df = edited_df.style.apply(highlight_action, axis=1)

st.markdown("### 📋 Reviewed Maintenance Records")
st.dataframe(styled_df, use_container_width=True)

# --- Download Updated File ---
if st.button("✅ Submit and Lock Progress"):
    st.success("✅ Submission recorded! Download below.")
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        edited_df.to_excel(writer, index=False, sheet_name="Maintenance_Review")
    out.seek(0)
    st.download_button(
        "💾 Download Reviewed File",
        data=out,
        file_name=f"Maintenance_Review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
