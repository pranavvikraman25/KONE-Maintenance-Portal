# app.py
import streamlit as st
import pandas as pd
import io
import math
import json
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

st.set_page_config(page_title="KPI Word Report", layout="wide")
st.title("KPI Report Generator (KONE Elevator Analysis)")

# -----------------------------------------------------------
# KPI definitions
KPI_MAP = {
    "Door Friction": "doorFriction",
    "Door Speed Error": "cumulativeDoorSpeedError",
    "Landing Door Lock Hook Closing Time": "lockHookClosingTime",
    "Landing Door Lock Hook Open Time": "lockHookTime",
    "Maximum Force During Coupler Compress": "maximumForceDuringCompress",
    "Landing Door Lock Roller Clearance": "landingDoorLockRollerClearance",
}

# -----------------------------------------------------------
# Colors (business-look)
COLOR_HEADER = "D9D9D9"   # header gray
COLOR_PRESENT = "FFF200"  # rich yellow
COLOR_MISSING = "92D050"  # rich green
COLOR_BORDER = "000000"

def safe_float(v):
    try:
        return float(v)
    except Exception:
        return None

def set_cell_shading_hex(cell, hex_color):
    """Set background color of docx cell"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)

def set_cell_border(cell, color="000000", size="6"):
    """Draw grid around cell"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for edge in ("top","left","bottom","right"):
        tag = OxmlElement(f"w:{edge}")
        tag.set(qn("w:val"), "single")
        tag.set(qn("w:sz"), size)
        tag.set(qn("w:space"), "0")
        tag.set(qn("w:color"), color)
        tcPr.append(tag)

# -----------------------------------------------------------
def build_word_report(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    cols = {c.lower(): c for c in df.columns}
    ckpi_col = cols.get("ckpi")
    date_col = cols.get("ckpi_statistics_date") or cols.get("date")
    floor_col = cols.get("floor")
    ave_col = cols.get("ave")

    if not (ckpi_col and date_col and floor_col and ave_col):
        raise ValueError("Missing required columns (ckpi, ckpi_statistics_date, floor, ave).")

    # normalize
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df[date_col] = df[date_col].dt.strftime("%Y-%m-%d")
    df[floor_col] = pd.to_numeric(df[floor_col], errors="coerce").astype("Int64")
    df[ave_col] = pd.to_numeric(df[ave_col], errors="coerce")

    # map ckpi to canonical keys
    lower_map = {}
    for dname, key in KPI_MAP.items():
        lower_map[dname.lower()] = key
        lower_map[key.lower()] = key
    df["ckpi_key"] = df[ckpi_col].astype(str).str.lower().map(lower_map)

    # filter only our six KPIs
    df = df[df["ckpi_key"].notna()]
    if df.empty:
        raise ValueError("No matching CKPI data found for the defined 6 KPIs.")

    doc = Document()
    section = doc.sections[-1]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Inches(14)
    section.page_height = Inches(8.5)
    section.left_margin = Inches(0.4)
    section.right_margin = Inches(0.4)
    section.top_margin = Inches(0.4)
    section.bottom_margin = Inches(0.4)

    all_dates = sorted(df[date_col].unique())
    for i, d in enumerate(all_dates):
        if i > 0:
            doc.add_page_break()
        p = doc.add_paragraph()
        run = p.add_run(f"KPI Report — {d}")
        run.bold = True
        run.font.size = Pt(14)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph("")

        date_df = df[df[date_col] == d]
        floors = sorted(date_df[floor_col].dropna().unique())
        if not floors:
            doc.add_paragraph("No floor data available.")
            continue

        # decide font size dynamically
        font_size = 10
        if len(floors) > 20:
            font_size = 8
        elif len(floors) > 15:
            font_size = 9

        # prepare table columns
        cols = ["CKPI", "No Corrective Action Required", "Corrective Action Required"] + [f"Floor {f}" for f in floors]
        table = doc.add_table(rows=1, cols=len(cols))
        table.style = "Table Grid"
        table.autofit = True

        hdr = table.rows[0].cells
        for j, name in enumerate(cols):
            hdr[j].text = name
            set_cell_shading_hex(hdr[j], COLOR_HEADER)
            set_cell_border(hdr[j], COLOR_BORDER)
            para = hdr[j].paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.bold = True
                run.font.size = Pt(font_size)

        # add KPI rows
        for display, key in KPI_MAP.items():
            # gather all entries for this KPI and date
            kdf = date_df[date_df["ckpi_key"] == key]
            if kdf.empty:
                continue
            # sometimes multiple rows per floor
            floors_with_data = kdf[floor_col].unique()

            # add as many rows as needed (one per measurement group)
            for idx in range(len(kdf)):
                row = table.add_row().cells
                row[0].text = display
                row[1].text = ""
                row[2].text = ""
                for f in floors:
                    cell = row[3 + floors.index(f)]
                    match = kdf[kdf[floor_col] == f]
                    if not match.empty:
                        val = match.iloc[0][ave_col]
                        if pd.notna(val):
                            cell.text = f"{val:.2f}"
                            set_cell_shading_hex(cell, COLOR_PRESENT)
                        else:
                            cell.text = "-"
                            set_cell_shading_hex(cell, COLOR_MISSING)
                    else:
                        cell.text = "-"
                        set_cell_shading_hex(cell, COLOR_MISSING)
                    set_cell_border(cell, COLOR_BORDER)
                    para = cell.paragraphs[0]
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        run.font.size = Pt(font_size)
                        run.font.color.rgb = RGBColor(0, 0, 0)

        doc.add_paragraph("")

    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out

# -----------------------------------------------------------
# Upload handler
uploaded = st.file_uploader("Upload KPI Excel/CSV/JSON", type=["xlsx", "xls", "csv", "json"])
if uploaded:
    try:
        if uploaded.name.lower().endswith((".xlsx", ".xls")):
            xls = pd.ExcelFile(uploaded)
            sheet = None
            for s in xls.sheet_names:
                c = [x.lower() for x in pd.read_excel(xls, sheet_name=s, nrows=1).columns]
                if "ckpi" in c:
                    sheet = s
                    break
            if sheet is None:
                sheet = xls.sheet_names[0]
            df = pd.read_excel(xls, sheet_name=sheet)
        elif uploaded.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            data = json.load(uploaded)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                        df = pd.DataFrame(v)
                        break
                else:
                    df = pd.DataFrame([data])
            else:
                df = pd.DataFrame(data)

        buf = build_word_report(df)
        st.success("✅ Report generated successfully.")
        st.download_button("Download Word Report", buf, file_name="KPI_Report.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    except Exception as e:
        st.error(f"Error: {e}")
