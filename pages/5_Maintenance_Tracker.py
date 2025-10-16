import streamlit as st
import pandas as pd

st.title("🧰 Maintenance Tracker")

st.markdown("""
Technicians can mark **checked/resolved** for each flagged KPI issue.  
Upload the latest actionable report below:
""")

uploaded = st.file_uploader("Upload Actionable Report (Excel)", type=["xlsx", "csv"])
if not uploaded:
    st.info("Upload a file to track maintenance actions.")
    st.stop()

# Read file
if uploaded.name.endswith(".csv"):
    df = pd.read_csv(uploaded)
else:
    df = pd.read_excel(uploaded)

if 'Action Needed' not in df.columns:
    st.warning("Expected 'Action Needed' column in the report.")
    st.stop()

df['Checked'] = False
df['Resolved'] = False

edited_df = st.data_editor(
    df,
    use_container_width=True,
    num_rows="dynamic",
    key="tracker_table"
)

st.markdown("### ✅ Updated Maintenance Status")
st.dataframe(edited_df)

# Download updated tracker
@st.cache_data
def to_excel(df):
    from io import BytesIO
    with pd.ExcelWriter(BytesIO(), engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
        writer.save()
        writer.seek(0)
        return writer

st.download_button(
    "💾 Download Updated Tracker",
    data=to_excel(edited_df),
    file_name="Maintenance_Tracker_Updated.xlsx"
)
