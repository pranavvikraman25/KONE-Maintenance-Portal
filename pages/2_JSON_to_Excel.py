# app.py
import streamlit as st
import pandas as pd
import json
import io
import tempfile
from docx import Document
import os

# -----------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------
FIXED_LOOKUP_FILE = "kpid_names.csv"  # must exist in same folder
OUTPUT_EXCEL_FILE = "Elevator_KPI_Final_Report.xlsx"

st.set_page_config(page_title="Live Elevator KPI Report", layout="wide")
st.title("📊 Live Elevator KPI Data → Named Excel Report")
st.write("Upload your live elevator JSON or Word file. The app automatically merges with fixed KPI names and gives you a final Excel report.")

# -----------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------

def load_fixed_lookup():
    """Read the fixed CSV (ID,Name) mapping."""
    try:
        df_lookup = pd.read_csv(FIXED_LOOKUP_FILE, header=None)
        df_lookup.columns = ["ID", "Name"]
        df_lookup["ID"] = df_lookup["ID"].astype(str).str.strip()
        return df_lookup
    except Exception as e:
        st.error(f"❌ Failed to read fixed lookup file: {e}")
        return None

def read_json_from_word(uploaded_file):
    """If a Word file (.docx) contains embedded JSON text, extract it."""
    try:
        doc = Document(uploaded_file)
        full_text = "\n".join(p.text for p in doc.paragraphs)
        # Try to find JSON content inside
        json_start = full_text.find("{")
        json_end = full_text.rfind("}")
        if json_start != -1 and json_end != -1:
            json_str = full_text[json_start:json_end+1]
            return json.loads(json_str)
        else:
            st.error("No JSON data found inside the Word file.")
            return None
    except Exception as e:
        st.error(f"Failed to extract JSON from Word: {e}")
        return None

def find_messages(obj):
    """Search for list of dicts inside the JSON structure."""
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        return obj
    if isinstance(obj, dict):
        for key in ["messages", "data", "records", "items"]:
            if key in obj and isinstance(obj[key], list):
                return obj[key]
    return None

def safe_load_json(uploaded_file):
    try:
        return json.load(uploaded_file)
    except Exception as e:
        st.error(f"Failed to parse JSON: {e}")
        return None

# -----------------------------------------------------------
# FILE UPLOAD SECTION
# -----------------------------------------------------------

uploaded_file = st.file_uploader("Upload live JSON or Word file containing JSON", type=["json", "docx"])

if uploaded_file:
    lookup_df = load_fixed_lookup()
    if lookup_df is None:
        st.stop()

    st.info(f"✅ Fixed lookup file '{FIXED_LOOKUP_FILE}' loaded successfully with {len(lookup_df)} entries.")

    with st.spinner("Reading uploaded file..."):
        # Determine file type
        if uploaded_file.name.endswith(".docx"):
            data = read_json_from_word(uploaded_file)
        else:
            data = safe_load_json(uploaded_file)

        if data is None:
            st.stop()

        messages = find_messages(data)
        if messages is None:
            st.error("Could not find a list of message records in JSON. Ensure your file contains a 'messages' array.")
            st.stop()

        df_raw = pd.DataFrame(messages)
        st.write("📋 Detected columns:", list(df_raw.columns))

        # Expected columns
        expected_cols = ["kpiId", "data", "floor", "timestamp"]
        missing = [c for c in expected_cols if c not in df_raw.columns]
        if missing:
            st.warning(f"⚠️ Missing some keys: {missing}. The app will continue if partial data exists.")

        # Select relevant data
        available_cols = [c for c in expected_cols if c in df_raw.columns]
        df_live = df_raw[available_cols].copy()

        # Rename and prepare
        rename_map = {
            "kpiId": "ID",
            "data": "KPI Value",
            "floor": "Floor",
            "timestamp": "Timestamp"
        }
        df_live = df_live.rename(columns=rename_map)
        df_live["ID"] = df_live["ID"].astype(str).str.strip()

        # Merge with fixed lookup
        merged = pd.merge(df_live, lookup_df, on="ID", how="left")

        # Reorder columns
        final_cols = ["Name", "ID", "KPI Value", "Floor", "Timestamp"]
        merged = merged[[c for c in final_cols if c in merged.columns]]

        # Sort by timestamp
        merged["Timestamp"] = pd.to_numeric(merged["Timestamp"], errors="coerce")
        merged = merged.sort_values(by="Timestamp", ascending=True)

        # Show preview
        st.subheader("Merged Data Preview")
        st.dataframe(merged.head(100))

        st.success(f"Total records processed: {len(merged)}")

        # Export Excel file to memory
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            merged.to_excel(writer, index=False, sheet_name="Final_Report")
        buffer.seek(0)

        st.download_button(
            label="⬇ Download Final Excel Report",
            data=buffer.getvalue(),
            file_name=OUTPUT_EXCEL_FILE,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Summary
        if "Name" in merged.columns:
            st.markdown("### Summary — Records by KPI")
            summary = merged["Name"].value_counts().reset_index()
            summary.columns = ["KPI Name", "Count"]
            st.table(summary)
