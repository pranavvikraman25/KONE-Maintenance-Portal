# pages/2_JSON_to_Excel.py
import json
import io
from docx import Document
from pathlib import Path
import pandas as pd
import streamlit as st
import os
from io import BytesIO
from datetime import datetime
from backend.report_utils import save_report
import os
import io
from datetime import datetime    
# -----------------------------------------------------------


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


# -----------------------------------------------------------
st.set_page_config(page_title="Live Elevator KPI Report", layout="wide")
st.title("📊 Live Elevator KPI Data → Named Excel Report")
st.write("""
Upload your live elevator **JSON** or **Word (.docx)** file.  
The app automatically merges it with your fixed KPI names and produces a final Excel report.
""")

# -----------------------------------------------------------
# FILE LOCATIONS
# -----------------------------------------------------------
# Determine path dynamically (always works, even on Streamlit Cloud)
CURRENT_DIR = Path(__file__).parent
ASSETS_DIR = Path(__file__).parents[1] / "assets"
LOOKUP_FILE = ASSETS_DIR / "kpid_names.csv"



# -----------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------

def load_fixed_lookup():
    """Load the KPI ID → Name mapping file from /assets/kpid_names.csv."""
    if not LOOKUP_FILE.exists():
        st.error(f"❌ Lookup file not found at: {LOOKUP_FILE}")
        st.stop()
    try:
        df = pd.read_csv(LOOKUP_FILE, header=None)
        df.columns = ["ID", "Name"]
        df["ID"] = df["ID"].astype(str).str.strip()
        st.success(f"✅ Loaded lookup file: {LOOKUP_FILE.name} with {len(df)} entries.")
        return df
    except Exception as e:
        st.error(f"❌ Failed to read lookup file: {e}")
        st.stop()

def read_json_from_word(uploaded_file):
    """Extract embedded JSON text from a Word (.docx) file."""
    try:
        doc = Document(uploaded_file)
        full_text = "\n".join(p.text for p in doc.paragraphs)
        json_start = full_text.find("{")
        json_end = full_text.rfind("}")
        if json_start != -1 and json_end != -1:
            json_str = full_text[json_start:json_end + 1]
            return json.loads(json_str)
        st.error("⚠️ No JSON content found inside the Word file.")
        return None
    except Exception as e:
        st.error(f"Failed to extract JSON from Word: {e}")
        return None

def find_messages(obj):
    """Locate list of dict messages inside JSON."""
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        return obj
    if isinstance(obj, dict):
        for key in ["messages", "data", "records", "items"]:
            if key in obj and isinstance(obj[key], list):
                return obj[key]
    return None

def safe_load_json(uploaded_file):
    """Safe JSON loader for uploaded files."""
    try:
        return json.load(uploaded_file)
    except Exception as e:
        st.error(f"Failed to parse JSON: {e}")
        return None

# -----------------------------------------------------------
# FILE UPLOAD SECTION
# -----------------------------------------------------------

uploaded_file = st.file_uploader("📂 Upload live JSON or Word (.docx) file", type=["json", "docx"])
if not uploaded_file:
    st.info("Please upload a JSON or DOCX file to begin.")
    st.stop()

lookup_df = load_fixed_lookup()

with st.spinner("🔄 Reading uploaded file..."):
    # Detect file type
    if uploaded_file.name.endswith(".docx"):
        data = read_json_from_word(uploaded_file)
    else:
        data = safe_load_json(uploaded_file)

    if data is None:
        st.stop()

    messages = find_messages(data)
    if messages is None:
        st.error("⚠️ Could not find 'messages' or list of data in JSON.")
        st.stop()

    df_raw = pd.DataFrame(messages)
    st.write("📋 Detected columns:", list(df_raw.columns))

    # Expected columns
    expected_cols = ["kpiId", "data", "floor", "timestamp"]
    available_cols = [c for c in expected_cols if c in df_raw.columns]
    missing = [c for c in expected_cols if c not in df_raw.columns]
    if missing:
        st.warning(f"⚠️ Missing keys: {missing}. Proceeding with available columns.")

    # Select and clean
    df_live = df_raw[available_cols].copy()
    rename_map = {
        "kpiId": "ID",
        "data": "KPI Value",
        "floor": "Floor",
        "timestamp": "Timestamp"
    }
    df_live = df_live.rename(columns=rename_map)
    df_live["ID"] = df_live["ID"].astype(str).str.strip()

    # Merge with lookup table
    merged = pd.merge(df_live, lookup_df, on="ID", how="left")

    # Arrange columns
    final_cols = ["Name", "ID", "KPI Value", "Floor", "Timestamp"]
    merged = merged[[c for c in final_cols if c in merged.columns]]

    # Sort by timestamp if numeric
    merged["Timestamp"] = pd.to_numeric(merged["Timestamp"], errors="coerce")
    merged = merged.sort_values(by="Timestamp", ascending=True)

    # Preview
    st.subheader("📊 Merged Data Preview")
    st.dataframe(merged.head(100), use_container_width=True)
    st.success(f"✅ Processed {len(merged)} records successfully!")

   

    
    
    # Export Excel
    output_name = f"Elevator_KPI_Final_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        merged.to_excel(writer, index=False, sheet_name="Final_Report")
    buffer.seek(0)
    excel_bytes = buffer.getvalue()
    
    # ✅ Add a single button to trigger save and download
    if st.button("💾 Generate & Save Final Excel Report", key="save_json_excel"):
        # Auto-save
        saved_path = save_report(
            excel_bytes,
            module_name="JSON_to_Excel",
            filter_label="Final_Report",
            extension="xlsx"
        )
    
        st.success(f"✅ Excel Report saved: `{os.path.basename(saved_path)}`")
    
        # Download button appears only after save
        st.download_button(
            label="⬇ Download Final Excel Report",
            data=excel_bytes,
            file_name=os.path.basename(saved_path),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_json_excel"
        )
    
    # KPI Summary
    if "Name" in merged.columns:
        st.markdown("### 📈 Summary — Records by KPI")
        summary = merged["Name"].value_counts().reset_index()
        summary.columns = ["KPI Name", "Count"]
        st.table(summary)





