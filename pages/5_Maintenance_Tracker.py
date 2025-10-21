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
This page now **remembers your data** even if you switch modules or come back later.
""")

# -------------------------------------------------------------------------
# 📂 Step 1 — Persistent Upload
# -------------------------------------------------------------------------
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.df_cache = None

uploaded = st.file_uploader("📂 Upload Actionable Report", type=["xlsx", "csv"], key="file_input")

if uploaded is not None:
    # Only reload if new file uploaded
    if st.session_state.uploaded_file != uploaded:
        st.session_state.uploaded_file = uploaded
        try:
            if uploaded.name.endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)
            st.session_state.df_cache = df
            st.success("✅ File loaded and saved in session.")
        except Exception as e:
            st.error(f"Error reading file: {e}")
else:
    if st.session_state.df_cache is not None:
        st.info("📂 Reusing previously uploaded file.")
        df = st.session_state.df_cache
    else:
        st.warning("Upload a file to begin tracking.")
        st.stop()

# -------------------------------------------------------------------------
# 🧭 Step 2 — Persistent Filters
# -------------------------------------------------------------------------
st.sidebar.header("🔍 Filters")

eqs = sorted(df["eq"].dropna().unique())
if "sel_eqs" not in st.session_state:
    st.session_state.sel_eqs = eqs
sel_eqs = st.sidebar.multiselect("Select Equipment(s)", eqs, default=st.session_state.sel_eqs)
st.session_state.sel_eqs = sel_eqs

ckpis = sorted(df["ckpi"].dropna().unique())
if "sel_ckpis" not in st.session_state:
    st.session_state.sel_ckpis = ckpis
sel_ckpis = st.sidebar.multiselect("Select KPI(s)", ckpis, default=st.session_state.sel_ckpis)
st.session_state.sel_ckpis = sel_ckpis

df["ckpi_statistics_date"] = pd.to_datetime(df["ckpi_statistics_date"], errors="coerce")
df = df.dropna(subset=["ckpi_statistics_date"])

min_d, max_d = df["ckpi_statistics_date"].min().date(), df["ckpi_statistics_date"].max().date()
if "sel_date_range" not in st.session_state:
    st.session_state.sel_date_range = [min_d, max_d]
sel_range = st.sidebar.date_input("Select Date Range", st.session_state.sel_date_range)
st.session_state.sel_date_range = sel_range
start_d, end_d = sel_range

# Reset button
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset Session"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# -------------------------------------------------------------------------
# 🔎 Step 3 — Apply Filters
# -------------------------------------------------------------------------
df_filt = df[
    (df["eq"].isin(sel_eqs)) &
    (df["ckpi"].isin(sel_ckpis)) &
    (df["ckpi_statistics_date"].dt.date >= start_d) &
    (df["ckpi_statistics_date"].dt.date <= end_d)
]

if df_filt.empty:
    st.warning("No records for selected filters.")
    st.stop()

# -------------------------------------------------------------------------
# 📈 Step 4 — Variability Index & Priority Flags
# -------------------------------------------------------------------------
def calc_var(values):
    v = pd.to_numeric(values, errors="coerce").dropna()
    if len(v) < 4:
        return 0
    diffs = np.diff(v)
    return np.sum(np.diff(np.sign(diffs)) != 0) / len(v) * 100

var_df = (
    df_filt.groupby(["eq", "ckpi"])["ave"]
    .apply(calc_var)
    .reset_index()
    .rename(columns={"ave": "variability_index"})
)
df_filt = pd.merge(df_filt, var_df, on=["eq", "ckpi"], how="left")
df_filt["Priority Flag"] = np.where(df_filt["variability_index"] > 30, "⚠️ High Variability", "")

# -------------------------------------------------------------------------
# 🧾 Step 5 — Editable Table with Persistence & Exclusivity
# -------------------------------------------------------------------------
if "last_edited_df" in st.session_state and st.session_state.last_edited_df is not None:
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

# Mutual exclusivity between ✅ and ❌
for i in range(len(edited_df)):
    if edited_df.at[i, "✅ checked"] and edited_df.at[i, "❌ wrong / review"]:
        # Keep only the latest clicked
        prev = st.session_state.last_edited_df if "last_edited_df" in st.session_state else df_filt
        prev_check = prev.at[i, "✅ checked"] if "✅ checked" in prev.columns else False
        prev_wrong = prev.at[i, "❌ wrong / review"] if "❌ wrong / review" in prev.columns else False
        if prev_check != edited_df.at[i, "✅ checked"]:
            edited_df.at[i, "❌ wrong / review"] = False
        else:
            edited_df.at[i, "✅ checked"] = False

# Save progress
st.session_state.last_edited_df = edited_df.copy()

# Color rows
def highlight_action(row):
    if row["✅ checked"]:
        return ["background-color: #b5e7a0"] * len(row)  # green
    elif row["❌ wrong / review"]:
        return ["background-color: #f4a6a6"] * len(row)  # red
    return [""] * len(row)

styled_df = edited_df.style.apply(highlight_action, axis=1)

st.markdown("### 📋 Reviewed Maintenance Records")
st.dataframe(styled_df, use_container_width=True)

# -------------------------------------------------------------------------
# 📤 Step 6 — Submit & Download
# -------------------------------------------------------------------------
st.markdown("---")
st.subheader("📤 Submit Maintenance Review")

if st.button("✅ Submit and Lock Progress"):
    st.success("✅ Submission recorded! Download your progress below.")

    def to_excel(df_):
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df_.to_excel(writer, index=False, sheet_name="Maintenance_Review")
        out.seek(0)
        return out

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"Maintenance_Review_{ts}.xlsx"
    st.download_button("💾 Download Maintenance Review File",
                       data=to_excel(edited_df),
                       file_name=fname)
else:
    st.info("Mark all tasks and then click Submit when done.")
