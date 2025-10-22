# app.py
import streamlit as st
import pandas as pd
import json
from io import BytesIO
from datetime import datetime, date
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

st.set_page_config(page_title="KPI Word Report — EQ & Date Filters", layout="wide")
st.title("KPI Report Generator — Filter by EQ & Date Range")

# ------------------ KPI MAP & Colors ------------------
KPI_MAP = {
    "Door Friction": "doorFriction",
    "Door Speed Error": "cumulativeDoorSpeedError",
    "Landing Door Lock Hook Closing Time": "lockHookClosingTime",
    "Landing Door Lock Hook Open Time": "lockHookTime",
    "Maximum Force During Coupler Compress": "maximumForceDuringCompress",
    "Landing Door Lock Roller Clearance": "landingDoorLockRollerClearance"
}

COLOR_HEADER = "D9D9D9"
COLOR_GOOD = "92D050"   # green
COLOR_ACTION = "FFF200" # yellow
COLOR_BORDER = "000000"

THRESHOLDS = {
    "doorFriction": (30.0, 50.0),
    "cumulativeDoorSpeedError": (0.05, 0.08),
    "lockHookClosingTime": (0.2, 0.6),
    "lockHookTime": (0.2, 0.6),
    "maximumForceDuringCompress": (5.0, 28.0),
    "landingDoorLockRollerClearance": (0.0, 0.029)
}

# ------------------ Helpers ------------------
def safe_float(v):
    try:
        if pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None

def set_cell_shading_hex(cell, hex_color):
    if not hex_color:
        return
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)

def set_cell_border(cell, color="000000", size="6"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for edge in ("top","left","bottom","right"):
        tag = OxmlElement(f"w:{edge}")
        tag.set(qn("w:val"), "single")
        tag.set(qn("w:sz"), size)
        tag.set(qn("w:space"), "0")
        tag.set(qn("w:color"), color)
        tcPr.append(tag)

def detect_column(cols, candidates):
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        for k in lower:
            if cand in k:
                return lower[k]
    return None

def read_uploaded_file(uploaded):
    name = uploaded.name.lower()
    try:
        if name.endswith(".xlsx"):
            df = pd.read_excel(uploaded, engine="openpyxl")
        elif name.endswith(".xls"):
            try:
                df = pd.read_excel(uploaded, engine="xlrd")
            except ImportError:
                st.warning("⚠️ xlrd not installed — please install it to support .xls files.")
                return pd.DataFrame()
        elif name.endswith(".csv"):
            df = pd.read_csv(uploaded)
        elif name.endswith(".json"):
            data = json.load(uploaded)
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                        df = pd.DataFrame(v)
                        break
                else:
                    df = pd.DataFrame([data])
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
        else:
            df = pd.read_excel(uploaded)
        df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
        return df
    except Exception as e:
        raise

# ------------------ Upload UI ------------------
uploaded = st.file_uploader("Upload KPI Excel/CSV/JSON file", type=["xlsx","xls","csv","json"])
if not uploaded:
    st.info("Upload a data file that contains columns for EQ, Date, CKPI, Floor, and Ave/Value.")
    st.stop()

try:
    df = read_uploaded_file(uploaded)
except Exception as e:
    st.error(f"Error reading the uploaded file: {e}")
    st.stop()

if df.empty:
    st.error("Uploaded file is empty.")
    st.stop()

st.success("✅ File read successfully.")

# ------------------ Detect important columns ------------------
cols = list(df.columns)
eq_col = detect_column(cols, ["eq"])
date_col = detect_column(cols, ["date"])
ckpi_col = detect_column(cols, ["ckpi", "kpi"])
floor_col = detect_column(cols, ["floor"])
ave_col = detect_column(cols, ["ave", "value"])

# ------------------ Confirm or override column selection ------------------
st.subheader("Confirm or override column selection (if detection missed any)")

default_eq = "eq"
default_date = "ckpi_statistics_date"
default_ckpi = "ckpi"

eq_col = st.selectbox("EQ column", options=[None] + cols,
                      index=(cols.index(default_eq) + 1) if default_eq in cols else 0)
date_col = st.selectbox("Date column", options=[None] + cols,
                        index=(cols.index(default_date) + 1) if default_date in cols else 0)
ckpi_col = st.selectbox("CKPI/KPI column", options=[None] + cols,
                        index=(cols.index(default_ckpi) + 1) if default_ckpi in cols else 0)
floor_col = st.selectbox("Floor column", options=[None] + cols,
                         index=(cols.index(floor_col) + 1) if floor_col in cols else 0)
ave_col = st.selectbox("Value/Ave column", options=[None] + cols,
                       index=(cols.index(ave_col) + 1) if ave_col in cols else 0)

# Validate
required = {"EQ": eq_col, "Date": date_col, "CKPI": ckpi_col, "Floor": floor_col, "Value": ave_col}
missing = [k for k,v in required.items() if not v]
if missing:
    st.error(f"Missing column selections for: {', '.join(missing)}.")
    st.stop()

df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
if df[date_col].isna().all():
    st.error("Selected Date column could not be parsed to datetimes.")
    st.stop()

# ------------------ KPI selection ------------------
st.subheader("Select KPIs to include")
selected_kpis = st.multiselect("Choose KPI(s)", options=list(KPI_MAP.keys()), default=list(KPI_MAP.keys()))

# ------------------ EQ & Date filters ------------------
st.subheader("Select EQ(s) and Date Range")
eq_choices = df[eq_col].dropna().unique().tolist()
selected_eqs = st.multiselect("EQ(s)", options=eq_choices, default=[eq_choices[0]] if eq_choices else [])
min_dt = df[date_col].min().date()
max_dt = df[date_col].max().date()
start_date, end_date = st.date_input("Choose start and end date", [min_dt, max_dt])

# ------------------ Aggregation choice ------------------
st.subheader("Aggregation Rule")
agg_choice = st.radio(
    "If multiple readings exist for same EQ/date/floor/KPI, aggregate by:",
    options=["mean", "first"],
    index=0,
    help="‘mean’ averages all readings; ‘first’ takes only the first recorded value for that date."
)
if agg_choice not in ["mean", "first"]:
    agg_choice = "mean"

# ------------------ Apply filters ------------------
mask_eq = df[eq_col].isin(selected_eqs)
mask_date = (df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)
filtered = df[mask_eq & mask_date].copy()
if filtered.empty:
    st.warning("No data after applying filters.")
    st.stop()

# ------------------ Prepare for Word Report ------------------
def build_report_doc(df, selected_eqs):
    doc = Document()
    section = doc.sections[-1]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Inches(14)
    section.page_height = Inches(8.5)
    section.left_margin = Inches(0.4)
    section.right_margin = Inches(0.4)
    section.top_margin = Inches(0.4)
    section.bottom_margin = Inches(0.4)

    dates = sorted(df[date_col].dt.date.unique())
    for d in dates:
        for eq in selected_eqs:
            page_df = df[(df[eq_col] == eq) & (df[date_col].dt.date == d)]
            if page_df.empty:
                continue

            p = doc.add_paragraph()
            run = p.add_run(f"KPI Report — {d.strftime('%d-%m-%Y')} — EQ: {eq}")
            run.bold = True
            run.font.size = Pt(14)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            doc.add_paragraph("")

            # 🔧 FIX: Floors sorted numerically then alphabetically
            floors = sorted(page_df[floor_col].dropna().unique(),
                            key=lambda x: (int(x) if str(x).isdigit() else float('inf'), str(x)))

            cols_header = ["CKPI", "No Corrective Action Required", "Corrective Action Required"] + [f"Floor {f}" for f in floors]
            table = doc.add_table(rows=1, cols=len(cols_header))
            table.style = "Table Grid"
            hdr_cells = table.rows[0].cells
            for i, name in enumerate(cols_header):
                hdr_cells[i].text = name
                set_cell_shading_hex(hdr_cells[i], COLOR_HEADER)
                set_cell_border(hdr_cells[i], color=COLOR_BORDER)

            # Fill data
            for display_name, key in KPI_MAP.items():
                row_cells = table.add_row().cells
                row_cells[0].text = display_name
                low_high = THRESHOLDS.get(key)
                if low_high:
                    low, high = low_high
                    row_cells[1].text = f"{low} - {high}"
                    set_cell_shading_hex(row_cells[1], COLOR_GOOD)
                    row_cells[2].text = f"<{low} or >{high}"
                    set_cell_shading_hex(row_cells[2], COLOR_ACTION)
                for fi, f in enumerate(floors):
                    target_cell = row_cells[3 + fi]
                    match = page_df[(page_df[floor_col] == f)]
                    if match.empty:
                        target_cell.text = "-"
                        set_cell_shading_hex(target_cell, COLOR_ACTION)
                    else:
                        val = safe_float(match[ave_col].iloc[0])
                        if val is None:
                            target_cell.text = "-"
                        else:
                            target_cell.text = f"{val:.2f}"
                            low, high = low_high or (None, None)
                            if low is not None and high is not None and low <= val <= high:
                                set_cell_shading_hex(target_cell, COLOR_GOOD)
                            else:
                                set_cell_shading_hex(target_cell, COLOR_ACTION)
                    set_cell_border(target_cell)
            doc.add_page_break()
    return doc

# ------------------ Download Word ------------------
if st.button("Generate & Download Word Report"):
    with st.spinner("Building Word report..."):
        doc = build_report_doc(filtered, selected_eqs)
        buf = BytesIO()
        doc.save(buf)
        buf.seek(0)
        file_name = f"KPI_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        st.download_button("Download Word Report", data=buf, file_name=file_name,
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
