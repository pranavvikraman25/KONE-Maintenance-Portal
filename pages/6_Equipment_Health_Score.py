# 6_Equipment_Health_Score.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from sklearn.linear_model import LinearRegression
import subprocess, shlex

# --- Page Config ---
st.set_page_config(page_title="Equipment Health Intelligence", layout="wide")
st.title("⚙️ Equipment Health Intelligence Dashboard")

st.markdown("""
This module analyzes **equipment health** based on KPI performance stability.  
Lower score = ⚠️ higher attention needed.  
Includes **AI Summary, KPI weighting, predictive health, and visual gauges**.
""")

# --- File Upload ---
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

required_cols = {"eq", "ckpi", "ave", "ckpi_statistics_date"}
if not required_cols.issubset(df.columns):
    st.error(f"Columns required: {', '.join(required_cols)}")
    st.stop()

# --- Normalize ---
def normalize_text(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())

df["_ckpi_norm"] = df["ckpi"].astype(str).apply(normalize_text)

main_kpis = [
    "doorfriction",
    "cumulativedoorspeederror",
    "lockhookclosingtime",
    "lockhooktime",
    "maximumforceduringcompress",
    "landingdoorlockrollerclearance"
]
df = df[df["_ckpi_norm"].isin(main_kpis)]

df["ckpi_statistics_date"] = pd.to_datetime(df["ckpi_statistics_date"], errors="coerce")

# --- Sidebar Filters ---
st.sidebar.header("🔧 Filter Options")

eq_choices = sorted(df["eq"].dropna().unique())
selected_eq = st.sidebar.multiselect("Select Equipment", eq_choices, default=eq_choices)

kpi_choices = sorted(df["ckpi"].dropna().unique())
selected_kpi = st.sidebar.multiselect("Select KPI(s)", kpi_choices, default=kpi_choices)

# KPI weights
st.sidebar.markdown("### ⚖️ KPI Weights")
weights = {k: st.sidebar.slider(k, 0.0, 1.0, 0.5, 0.1) for k in main_kpis}

df_filtered = df[df["eq"].isin(selected_eq) & df["ckpi"].isin(selected_kpi)]
if df_filtered.empty:
    st.warning("No data after filtering.")
    st.stop()

# --- Compute Health Score ---
scores = (
    df_filtered
    .groupby(["eq", "ckpi"])
    .agg(avg_ave=("ave", "mean"), std_ave=("ave", "std"))
    .reset_index()
)

scores["norm_std"] = scores["std_ave"] / (scores["std_ave"].max() + 1e-9)
scores["HealthScore"] = (100 - scores["norm_std"] * 100).round(2)
scores["Weight"] = scores["_ckpi_norm"].map(weights).fillna(0.5)
scores["WeightedScore"] = (scores["HealthScore"] * scores["Weight"]).round(2)

eq_health = (
    scores.groupby("eq")["WeightedScore"]
    .mean()
    .reset_index()
    .rename(columns={"WeightedScore": "HealthScore"})
)

eq_health["HealthStatus"] = np.select(
    [
        eq_health["HealthScore"] >= 85,
        (eq_health["HealthScore"] >= 70) & (eq_health["HealthScore"] < 85),
        eq_health["HealthScore"] < 70
    ],
    ["✅ Excellent", "🟡 Needs Monitoring", "🔴 Critical"]
)

# --- Trend Over Time ---
st.markdown("### 🧩 Health Trend Over Time")

trend = (
    df_filtered.groupby(["eq", pd.Grouper(key="ckpi_statistics_date", freq="M")])["ave"]
    .std().reset_index()
)
trend["HealthScore"] = 100 - (trend["ave"] / (trend["ave"].max() + 1e-9) * 100)

fig_trend = go.Figure()
for eq in trend["eq"].unique():
    sub = trend[trend["eq"] == eq]
    fig_trend.add_trace(go.Scatter(
        x=sub["ckpi_statistics_date"], y=sub["HealthScore"], mode="lines+markers",
        name=eq, line=dict(width=2)
    ))
fig_trend.update_layout(
    yaxis_title="Health Score", xaxis_title="Date", height=400, plot_bgcolor="white"
)
st.plotly_chart(fig_trend, use_container_width=True)

# --- Health Bar Chart ---
st.markdown("### 📊 Current Equipment Health Score")

fig_bar = go.Figure()
for _, row in eq_health.iterrows():
    color = "green" if "Excellent" in row["HealthStatus"] else "orange" if "Needs" in row["HealthStatus"] else "red"
    fig_bar.add_trace(go.Bar(x=[row["eq"]], y=[row["HealthScore"]],
                             marker_color=color, hovertext=row["HealthStatus"]))
fig_bar.update_layout(
    xaxis_title="Equipment", yaxis_title="Health Score", yaxis=dict(range=[0, 100]),
    height=450, plot_bgcolor="white", paper_bgcolor="white"
)
st.plotly_chart(fig_bar, use_container_width=True)

# --- Maintenance Priority ---
eq_health["Priority"] = eq_health["HealthScore"].rank(ascending=True).astype(int)
st.markdown("### 🧾 Maintenance Priority List")
st.dataframe(eq_health.sort_values("Priority"))

# --- Predictive Estimate ---
st.markdown("### 🔮 Predicted Health (Next Month Estimate)")
predictions = []
for eq in trend["eq"].unique():
    sub = trend[trend["eq"] == eq].dropna()
    if len(sub) >= 3:
        X = np.arange(len(sub)).reshape(-1, 1)
        y = sub["HealthScore"].values
        model = LinearRegression().fit(X, y)
        next_pred = model.predict([[len(sub) + 1]])[0]
        predictions.append((eq, next_pred))
pred_df = pd.DataFrame(predictions, columns=["Equipment", "Predicted_Next_Month"])
st.dataframe(pred_df)

# --- AI Insight ---
st.markdown("### 🤖 AI Summary Insight (LLaMA 3)")
try:
    summary_text = None
    csv_text = eq_health.to_csv(index=False)
    prompt = f"Summarize this equipment health report in 3 insights:\n{csv_text}"
    cmd = f"ollama run llama3 \"{prompt}\""
    result = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if result.returncode == 0:
        summary_text = result.stdout.strip()
    st.write(summary_text or "Ollama not available or returned no summary.")
except Exception as e:
    st.info("AI Summary unavailable. Please ensure Ollama is running.")

# --- Download ---
def df_to_excel_bytes(df_):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df_.to_excel(writer, index=False, sheet_name="Health_Score")
    out.seek(0)
    return out

st.download_button("📥 Download Full Health Report (Excel)",
                   data=df_to_excel_bytes(eq_health),
                   file_name="Equipment_Health_Score.xlsx")

st.caption("© 2025 KONE Internal Analytics | Developed by PRANAV VIKRAMAN S S")
