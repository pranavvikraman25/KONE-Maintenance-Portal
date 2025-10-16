import streamlit as st
import pandas as pd
import numpy as np

st.title("⚙️ Equipment Health Score")

st.markdown("""
This page computes a **weighted KPI score** for each equipment (EQ).  
Lower score = more attention needed.
""")

uploaded = st.file_uploader("Upload KPI Dataset", type=["xlsx","csv","json"])
if not uploaded:
    st.info("Upload KPI file first.")
    st.stop()

if uploaded.name.endswith(".csv"):
    df = pd.read_csv(uploaded)
elif uploaded.name.endswith(".xlsx"):
    df = pd.read_excel(uploaded)
else:
    df = pd.read_json(uploaded)

if not {"eq","ckpi","ave"}.issubset(df.columns):
    st.error("Columns 'eq', 'ckpi', 'ave' required.")
    st.stop()

# Normalize and compute health score
scores = df.groupby("eq")["ave"].agg(['mean','std']).reset_index()
scores["HealthScore"] = 100 - (scores["std"] * 10)
scores["HealthStatus"] = np.where(scores["HealthScore"] < 70, "⚠️ Check", "✅ Healthy")

st.dataframe(scores)

st.download_button(
    "Download Equipment Health Scores (Excel)",
    data=scores.to_csv(index=False).encode(),
    file_name="Equipment_Health_Score.csv"
)
