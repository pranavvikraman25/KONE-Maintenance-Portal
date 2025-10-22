# 7_Prediction_Module.py
import streamlit as st
import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
import numpy as np
from datetime import timedelta

st.set_page_config(page_title="KONE Prediction Module", layout="wide")

st.title("📈 Predictive Maintenance — KPI Failure Forecast")

st.markdown("""
This module uses **time-series forecasting (Prophet)** to predict **when a KPI or component may cross its failure limit**.  
Upload a dataset containing `ckpi_statistics_date`, `ave`, and `ckpi` columns.
""")

# ------------------ File Upload ------------------
uploaded = st.file_uploader("📂 Upload KPI Dataset (CSV or Excel)", type=["csv", "xlsx"])
if not uploaded:
    st.info("Upload a file to forecast KPI trends.")
    st.stop()

if uploaded.name.endswith(".csv"):
    df = pd.read_csv(uploaded)
else:
    df = pd.read_excel(uploaded)

# ------------------ Data Validation ------------------
required_cols = {"ckpi_statistics_date", "ave", "ckpi"}
if not required_cols.issubset(df.columns):
    st.error(f"Dataset must contain columns: {', '.join(required_cols)}")
    st.stop()

df["ckpi_statistics_date"] = pd.to_datetime(df["ckpi_statistics_date"], errors="coerce")
df = df.dropna(subset=["ckpi_statistics_date", "ave"])

# ------------------ KPI Selection ------------------
kpi_list = sorted(df["ckpi"].dropna().unique())
kpi_selected = st.selectbox("Select KPI for Forecast", kpi_list)
df_kpi = df[df["ckpi"] == kpi_selected][["ckpi_statistics_date", "ave"]].rename(
    columns={"ckpi_statistics_date": "ds", "ave": "y"}
)

if len(df_kpi) < 10:
    st.warning("Not enough data for forecasting. At least 10 points required.")
    st.stop()

# ------------------ Threshold Setup ------------------
# Default thresholds — you can later import these from your KPI_THRESHOLDS dict
KPI_THRESHOLDS = {
    "doorfriction": (30.0, 50.0),
    "cumulativedoorspeederror": (0.05, 0.08),
    "lockhookclosingtime": (0.2, 0.6),
    "lockhooktime": (0.3, None),
    "maximumforceduringcompress": (5.0, 28.0),
    "landingdoorlockrollerclearance": (None, 0.029)
}

low_thresh, high_thresh = KPI_THRESHOLDS.get(kpi_selected.lower(), (None, None))

# ------------------ Prophet Forecast ------------------
period_days = st.slider("🔮 Forecast Period (days)", 30, 730, 365, step=30)
m = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
m.fit(df_kpi)
future = m.make_future_dataframe(periods=period_days)
forecast = m.predict(future)

# ------------------ Predict Failure Point ------------------
predicted_failure_date = None
if high_thresh is not None:
    exceed = forecast[forecast["yhat"] > high_thresh]
    if not exceed.empty:
        predicted_failure_date = exceed.iloc[0]["ds"].date()

elif low_thresh is not None:
    drop = forecast[forecast["yhat"] < low_thresh]
    if not drop.empty:
        predicted_failure_date = drop.iloc[0]["ds"].date()

# ------------------ Visualization ------------------
fig = go.Figure()

# Historical data
fig.add_trace(go.Scatter(
    x=df_kpi["ds"],
    y=df_kpi["y"],
    name="Actual",
    mode="lines+markers",
    line=dict(color="#0071B9", width=2),
    marker=dict(size=6)
))

# Forecast line
fig.add_trace(go.Scatter(
    x=forecast["ds"],
    y=forecast["yhat"],
    name="Forecast",
    mode="lines",
    line=dict(color="#00B5E2", width=3)
))

# Confidence intervals
fig.add_trace(go.Scatter(
    x=pd.concat([forecast["ds"], forecast["ds"][::-1]]),
    y=pd.concat([forecast["yhat_upper"], forecast["yhat_lower"][::-1]]),
    fill="toself",
    fillcolor="rgba(0,113,185,0.15)",
    line=dict(color="rgba(255,255,255,0)"),
    hoverinfo="skip",
    showlegend=False
))

# Threshold lines
if high_thresh:
    fig.add_hline(y=high_thresh, line_dash="dot", line_color="red", annotation_text="High Threshold", annotation_position="top left")
if low_thresh:
    fig.add_hline(y=low_thresh, line_dash="dot", line_color="orange", annotation_text="Low Threshold", annotation_position="bottom left")

# Predicted failure marker
if predicted_failure_date:
    fail_y = forecast.loc[forecast["ds"].dt.date == predicted_failure_date, "yhat"].values[0]
    fig.add_trace(go.Scatter(
        x=[predicted_failure_date],
        y=[fail_y],
        mode="markers+text",
        text=["⚠️ Predicted Fault"],
        textposition="bottom center",
        marker=dict(color="red", size=14, symbol="x"),
        name="Predicted Fault"
    ))

fig.update_layout(
    title=f"Forecast for {kpi_selected}",
    xaxis_title="Date",
    yaxis_title="Average (ave)",
    hovermode="x unified",
    height=600,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# ------------------ Summary ------------------
st.markdown("### 📅 Forecast Summary")

if predicted_failure_date:
    days_remaining = (predicted_failure_date - pd.Timestamp.today().date()).days
    st.success(f"**⚠️ Predicted Failure Date:** {predicted_failure_date}  \n"
               f"📆 Estimated Remaining Life: **{days_remaining} days (~{days_remaining/365:.1f} years)**")
else:
    st.info("✅ No predicted failure within forecast period.")

# ------------------ Download ------------------
st.markdown("### 📥 Download Forecast Results")
csv = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].to_csv(index=False).encode()
st.download_button(
    "Download Forecast Data (CSV)",
    data=csv,
    file_name=f"Forecast_{kpi_selected}.csv",
    mime="text/csv"
)
