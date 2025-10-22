# 6_Equipment_Health_Score.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- Page Config ---
st.set_page_config(page_title="Equipment Health Score", layout="wide")
st.title("⚙️ Equipment Health Score")

st.markdown("""
This page computes a **weighted KPI health score** for each equipment (EQ).  
Lower score = ⚠️ more attention needed.  
A healthy EQ will have **stable KPI averages with minimal fluctuation**.
""")

# --- Upload File ---
uploaded = st.file_uploader("📁 Upload KPI Dataset", type=["xlsx", "csv", "json"])
if not uploaded:
    st.info("Upload KPI file first.")
    st.stop()

# --- Read File ---
if uploaded.name.endswith(".csv"):
    df = pd.read_csv(uploaded)
elif uploaded.name.endswith(".xlsx"):
    df = pd.read_excel(uploaded)
else:
    df = pd.read_json(uploaded)

# --- Validation ---
required_cols = {"eq", "ckpi", "ave", "ckpi_statistics_date"}
if not required_cols.issubset(df.columns):
    st.error(f"Columns required: {', '.join(required_cols)}")
    st.stop()

# --- Normalize KPI names ---
def normalize_text(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())

df["_ckpi_norm"] = df["ckpi"].astype(str).apply(normalize_text)

# --- Only consider 6 major KPIs ---
main_kpis = [
    "doorfriction",
    "cumulativedoorspeederror",
    "lockhookclosingtime",
    "lockhooktime",
    "maximumforceduringcompress",
    "landingdoorlockrollerclearance"
]
df = df[df["_ckpi_norm"].isin(main_kpis)]

# --- Sidebar Filters ---
st.sidebar.header("Filter Options")

eq_choices = sorted(df["eq"].dropna().unique())
selected_eq = st.sidebar.multiselect("Select Equipment", eq_choices, default=eq_choices)

kpi_choices = sorted(df["ckpi"].dropna().unique())
selected_kpi = st.sidebar.multiselect("Select KPI(s)", kpi_choices, default=kpi_choices)

df_filtered = df[df["eq"].isin(selected_eq) & df["ckpi"].isin(selected_kpi)]

if df_filtered.empty:
    st.warning("No data after filtering.")
    st.stop()

# --- Compute Health Score ---
# Formula: health = 100 - (normalized_std * weight)
scores = (
    df_filtered
    .groupby(["eq", "ckpi"])
    .agg(avg_ave=("ave", "mean"), std_ave=("ave", "std"))
    .reset_index()
)

# Normalization
scores["norm_std"] = scores["std_ave"] / (scores["std_ave"].max() + 1e-9)
scores["HealthScore"] = (100 - scores["norm_std"] * 100).round(2)

# Weighted KPI (each KPI contributes equally)
eq_health = (
    scores.groupby("eq")["HealthScore"]
    .mean()
    .reset_index()
    .sort_values("HealthScore", ascending=False)
)

# Health Status
eq_health["HealthStatus"] = np.select(
    [
        eq_health["HealthScore"] >= 85,
        (eq_health["HealthScore"] >= 70) & (eq_health["HealthScore"] < 85),
        eq_health["HealthScore"] < 70
    ],
    ["✅ Excellent", "🟡 Needs Monitoring", "🔴 Critical"],
    default="⚙️ Unknown"
)

# --- Show Data ---
st.markdown("### 📊 Equipment Health Overview")
st.dataframe(eq_health)

# --- Graph Visualization ---
st.markdown("### 📈 Equipment Health Chart")

fig = go.Figure()

for _, row in eq_health.iterrows():
    color = (
        "green" if "Excellent" in row["HealthStatus"] else
        "orange" if "Needs" in row["HealthStatus"] else
        "red"
    )
    fig.add_trace(go.Bar(
        x=[row["eq"]],
        y=[row["HealthScore"]],
        marker_color=color,
        name=row["HealthStatus"],
        hovertemplate=f"<b>{row['eq']}</b><br>Health Score: {row['HealthScore']}<br>Status: {row['HealthStatus']}<extra></extra>"
    ))

fig.update_layout(
    xaxis_title="Equipment",
    yaxis_title="Health Score",
    yaxis=dict(range=[0, 100]),
    height=550,
    showlegend=False,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=60, r=60, t=80, b=100),
    font=dict(size=12),
    bargap=0.4
)

st.plotly_chart(fig, use_container_width=True)

# --- Optional: Downloadable Excel Report ---
def df_to_excel_bytes(df_):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df_.to_excel(writer, index=False, sheet_name="Health_Score")
    out.seek(0)
    return out

st.download_button(
    "📥 Download Health Score Report (Excel)",
    data=df_to_excel_bytes(eq_health),
    file_name="Equipment_Health_Score.xlsx"
)

st.caption("© 2025 KONE Internal Analytics | Developed by PRANAV VIKRAMAN S S")
