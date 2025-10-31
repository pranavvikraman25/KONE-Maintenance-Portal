import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta
import subprocess, shlex
import os
from backend.backend_utils import save_uploaded_file, get_uploaded_file, clear_uploaded_file
from io import BytesIO
from backend.report_utils import save_report  # make sure this import is at the top of your file
import os
from backend.report_utils import save_report, delete_report, list_all_reports
import os



UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file):
    """Save uploaded file both in memory and on disk."""
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    # store in session
    st.session_state['uploaded_file_path'] = file_path
    st.session_state['uploaded_file_name'] = uploaded_file.name
    return file_path

def get_uploaded_file():
    """Return file path if exists in session."""
    return st.session_state.get('uploaded_file_path', None)

#------changed code----------
# ---------------- Page config ----------------
st.set_page_config(page_title="CKPI Multi-KPI Analyzer", layout="wide")

#------------------------33 to 41 new code added----------------------------------------------------------------------

st.title("Trend Analysis for Different Equipments")

# ---------------- Load Custom CSS (KONE Theme) ----------------
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("assets/style.css")

# ---------------- Developer Badge & Logo ----------------
with st.sidebar:
    try:
        st.image("assets/logo.png", width=160)
    except Exception:
        st.write("")
    st.markdown("### KONE — Maintenance Dashboard")
    
    st.markdown("---")

# ---------------- Thresholds (normalized keys) ----------------
KPI_THRESHOLDS = {
    "doorfriction": (30.0, 50.0),
    "cumulativedoorspeederror": (0.05, 0.08),
    "lockhookclosingtime": (0.2, 0.6),
    "lockhooktime": (0.3, None),
    "maximumforceduringcompress": (5.0, 28.0),
    "landingdoorlockrollerclearance": (None, 0.029)
}

# ---------------- Helpers ----------------
def normalize_text(s: str):
    if s is None: return ""
    return "".join(ch for ch in str(s).lower() if ch.isalnum())

def read_file(uploaded):
    name = uploaded.name.lower()
    if name.endswith(".xlsx"):
        return pd.read_excel(uploaded, engine="openpyxl")
    if name.endswith(".xls"):
        return pd.read_excel(uploaded, engine="xlrd")
    if name.endswith(".csv"):
        return pd.read_csv(uploaded)
    if name.endswith(".json"):
        return pd.read_json(uploaded)
    return pd.read_csv(uploaded)
#----------------------------changed file down below--------------------------

@st.cache_data(show_spinner=False)
def read_input_file(uploaded):
    """
    Accept either an UploadedFile (streamlit) or None with session-saved path.
    Returns a dataframe or raises.
    """
    if uploaded is not None:
        try:
            df = read_file_from_uploaded(uploaded)
        except Exception as e:
            raise RuntimeError(f"Could not read uploaded file: {e}")
        try:
            save_uploaded_file(uploaded)
        except Exception:
            pass
        return df
    else:
        saved_path = get_uploaded_file()
        if saved_path:
            try:
                df = read_file_from_path(saved_path)
                return df
            except Exception as e:
                raise RuntimeError(f"Could not read saved file at {saved_path}: {e}")
        else:
            return None


#-------------------------changed file above-----------------
def parse_dates(df, col):
    df[col] = pd.to_datetime(df[col], dayfirst=False, errors="coerce")
    return df

def detect_peaks_lows(values, low_thresh, high_thresh, std_factor=1.0):
    arr = np.asarray(values, dtype=float)
    n = len(arr)
    peaks, lows = [], []
    if n < 3 or np.isnan(arr).all():
        return peaks, lows
    mean, std = np.nanmean(arr), np.nanstd(arr)
    upper_stat, lower_stat = mean + std_factor * std, mean - std_factor * std
    for i in range(1, n-1):
        a, b, c = arr[i-1], arr[i], arr[i+1]
        if np.isnan(b): continue
        if not np.isnan(a) and not np.isnan(c):
            if b > a and b > c and ((high_thresh is not None and b > high_thresh) or b > upper_stat):
                peaks.append(i)
            if b < a and b < c and ((low_thresh is not None and b < low_thresh) or b < lower_stat):
                lows.append(i)
    return peaks, lows

def point_status(value, thresh):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "nodata"
    low, high = thresh
    if low is not None and high is not None:
        return "ok" if low <= value <= high else "corrective"
    if low is None and high is not None:
        return "ok" if value <= high else "corrective"
    if low is not None and high is None:
        return "ok" if value >= low else "corrective"
    return "corrective"

def color_cycle(i):
    palette = ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b","#e377c2","#7f7f7f"]
    return palette[i % len(palette)]

def df_to_excel_bytes(df_):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df_.to_excel(writer, index=False, sheet_name="Actionable_Report")
    out.seek(0)
    return out

def ollama_summarize(text, model="mistral"):
    try:
        cmd = f"ollama run {model} \"Summarize this maintenance report in 4 bullet points for a manager: {text}\""
        proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=60)
        if proc.returncode == 0:
            return proc.stdout.strip()
    except Exception:
        pass
    return None

# ---------------- Upload ----------------
uploaded = st.file_uploader("Upload KPI file (xlsx/xls/csv/json)", type=["xlsx","xls","csv","json"])
if not uploaded:
    st.info("Upload a KPI file to begin. Required columns: eq, ckpi, ckpi_statistics_date, floor, ave")
    st.stop()

try:
    df = read_file(uploaded)
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

if df.empty:
    st.error("Uploaded file is empty.")
    st.stop()

cols_lower = {c.lower(): c for c in df.columns}
required = ["ckpi_statistics_date","ave","ckpi","floor","eq"]
for req in required:
    if req not in cols_lower:
        st.error(f"Required column '{req}' not found in file.")
        st.stop()

date_col, ave_col, ckpi_col, floor_col, eq_col = [cols_lower[c] for c in required]
df = parse_dates(df, date_col)
if df[date_col].isna().all():
    st.error("Could not parse any dates. Ensure format mm/dd/yyyy.")
    st.stop()

df["_ckpi_norm"] = df[ckpi_col].astype(str).apply(normalize_text)

# ---------------- Sidebar Filters ----------------
st.sidebar.header("Global Filters")

eq_choices = sorted(df[eq_col].dropna().unique())
selected_eq = st.sidebar.multiselect("Select EQ(s)", eq_choices, default=eq_choices[:2] if eq_choices else [])

floor_choices = sorted(df[floor_col].dropna().unique())
selected_floors = st.sidebar.multiselect("Select Floor(s)", floor_choices, default=floor_choices[:2] if floor_choices else [])

# --- Limit KPIs to only the 6 main ones defined in KPI_THRESHOLDS ---
file_kpis = df[["_ckpi_norm", ckpi_col]].drop_duplicates().set_index("_ckpi_norm")[ckpi_col].to_dict()

# Only include KPIs that match our defined six main KPI keys
main_kpis = list(KPI_THRESHOLDS.keys())
filtered_kpis = {k: file_kpis.get(k, k) for k in main_kpis if k in file_kpis or k in KPI_THRESHOLDS}

# Display names in sidebar (pretty form)
kpi_display = [filtered_kpis[k] for k in filtered_kpis.keys()]
selected_kpis_display = st.sidebar.multiselect("Select KPI(s)", kpi_display, default=kpi_display)
selected_kpis = [normalize_text(s) for s in selected_kpis_display]


# --- Date Range Filter ---
st.sidebar.markdown("### Date Range")

preset_range = st.sidebar.selectbox(
    "Quick Select",
    ["Custom", "Past Week", "Past Month", "Past 3 Months", "Past 6 Months", "Past Year"]
)

# Use the last date in the uploaded file instead of today
latest_date = df[date_col].max().date()
earliest_date = df[date_col].min().date()

if preset_range == "Custom":
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range", [earliest_date, latest_date]
    )
elif preset_range == "Past Week":
    start_date, end_date = latest_date - timedelta(days=7), latest_date
elif preset_range == "Past Month":
    start_date, end_date = latest_date - timedelta(days=30), latest_date
elif preset_range == "Past 3 Months":
    start_date, end_date = latest_date - timedelta(days=90), latest_date
elif preset_range == "Past 6 Months":
    start_date, end_date = latest_date - timedelta(days=180), latest_date
else:  # Past Year
    start_date, end_date = latest_date - timedelta(days=365), latest_date


std_factor = st.sidebar.slider("Peak/Low Sensitivity", 0.5, 3.0, 1.0, 0.1)

# ---------------- Apply Filters ----------------
@st.cache_data(show_spinner=False)
def filter_data(df, eqs, floors, kpis, date_col, start_date, end_date):
    mask = (
        df[eq_col].isin(eqs) &
        df[floor_col].isin(floors) &
        df["_ckpi_norm"].isin(kpis) &
        (df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)
    )
    return df[mask].copy()

df_filtered = filter_data(df, selected_eq, selected_floors, selected_kpis, date_col, start_date, end_date)
#-----------------changed file above-----------------------------

if df_filtered.empty:
    st.warning("No data after applying filters.")
    st.stop()

df_filtered[ave_col] = pd.to_numeric(df_filtered[ave_col], errors="coerce")

# ---------------- KPI Graphs (Single Column Layout) ----------------
st.markdown("### KPI Trends")

kpi_summary = []

for kpi_norm in selected_kpis:
    kpi_display_name = file_kpis.get(kpi_norm, kpi_norm)
    df_kpi = df_filtered[df_filtered["_ckpi_norm"] == kpi_norm]
    if df_kpi.empty:
        st.info(f"No data for KPI: {kpi_display_name}")
        continue

    st.subheader(f"KPI: {kpi_display_name}")
    fig = go.Figure()
    floors = sorted(df_kpi[floor_col].dropna().unique())
    for i, floor in enumerate(floors):
        df_floor = df_kpi[df_kpi[floor_col] == floor].sort_values(date_col)
        if df_floor.empty: continue
        color = color_cycle(i)
        thresh = KPI_THRESHOLDS.get(kpi_norm, (None, None))
        low_thresh, high_thresh = thresh

        status_colors = [
            "#2ca02c" if point_status(v, thresh) == "ok" else "#ffcc00"
            for v in df_floor[ave_col]
        ]

        fig.add_trace(go.Scatter(
            x=df_floor[date_col],
            y=df_floor[ave_col],
            mode="lines+markers",
            name=f"Floor {floor}",
            line=dict(color=color, width=2),
            marker=dict(size=8, color=status_colors, line=dict(color="#000", width=1)),
            hovertemplate="Date: %{x|%d.%m.%Y}<br>Floor: "+str(floor)+"<br>ave: %{y:.2f}<extra></extra>"

        ))

        peaks, lows = detect_peaks_lows(df_floor[ave_col].values, low_thresh, high_thresh, std_factor)
        if peaks:
            fig.add_trace(go.Scatter(
                x=df_floor[date_col].values[peaks],
                y=df_floor[ave_col].values[peaks],
                mode="markers",
                marker=dict(symbol="triangle-up", color="red", size=11),
                name=f"Peaks (Floor {floor})"
            ))
        if lows:
            fig.add_trace(go.Scatter(
                x=df_floor[date_col].values[lows],
                y=df_floor[ave_col].values[lows],
                mode="markers",
                marker=dict(symbol="triangle-down", color="blue", size=11),
                name=f"Lows (Floor {floor})"
            ))

        kpi_summary.append({
            "kpi": kpi_display_name,
            "floor": floor,
            "peaks": len(peaks),
            "lows": len(lows),
            "rows": len(df_floor)
        })

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="ave",
        height=450,
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(
            tickformat="%b %d, %Y",
            tickangle=-60,
            showgrid=True,
            tickmode="auto",
            nticks=len(df_floor[date_col].unique())  # keep natural spacing
        )
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

# ---------------- Legend ----------------
st.markdown("**Legend:** 🟢 Within threshold (OK) &nbsp;&nbsp; 🟡 Outside threshold (Corrective) &nbsp;&nbsp; 🔺 Peak &nbsp;&nbsp; 🔻 Low")
st.markdown("---")

# ---------------- Actionable Insights ----------------
st.subheader(" Actionable Insights Report ")

REMEDY_BY_KPI = {
    "doorfriction": "Lubricate guide rails; inspect rollers (Solution 1)",
    "cumulativedoorspeederror": "Check door motor encoder calibration (Solution 2)",
    "lockhookclosingtime": "Inspect lock hook mechanism and wiring",
    "lockhooktime": "Verify actuator response timing",
    "maximumforceduringcompress": "Check coupler alignment settings",
    "landingdoorlockrollerclearance": "Measure roller clearance; replace worn rollers"
}

report_rows = []
for rec in kpi_summary:
    if rec['rows'] == 0:
        continue
    if rec['peaks'] + rec['lows'] > rec['rows'] * 0.2:
        remedy = REMEDY_BY_KPI.get(normalize_text(rec['kpi']), "Follow standard inspection checklist")
        report_rows.append({
            "Floor": rec['floor'],
            "Affected KPI": rec['kpi'],
            "Action Needed": "⚠️ High uncertainty → Technician check",
            "Remedy": remedy
        })


#-------------------------------edited------------------------------------
report_df = pd.DataFrame(report_rows)

if not report_df.empty:
    st.dataframe(report_df)

    report_bytes = df_to_excel_bytes(report_df)
    filter_label = preset_range.replace(" ", "_") if "preset_range" in locals() else "Custom"

    # ✅ Button triggers saving only once
    if st.button("📊 Generate & Save Actionable Report", key="generate_report_btn"):
        saved_path = save_report(
            report_bytes.getvalue() if hasattr(report_bytes, "getvalue") else report_bytes,
            module_name="Trend_Analyzer",
            filter_label=filter_label,
            extension="xlsx"
        )
        st.success(f"✅ Report saved to archive: `{os.path.basename(saved_path)}`")

        # Single download button (after save)
        st.download_button(
            "⬇️ Download Actionable Report (Excel)",
            data=report_bytes,
            file_name=os.path.basename(saved_path),
            key="download_btn"
        )

else:
    st.info("No action needed for selected filters.")

