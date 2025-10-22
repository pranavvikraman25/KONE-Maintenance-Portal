# 6_Equipment_Health_Forecast.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from sklearn.linear_model import LinearRegression
import subprocess, shlex
from datetime import timedelta

# Try importing Prophet safely
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

# --- Page Config ---
st.set_page_config(page_title="Equipment Health & Forecast Intelligence", layout="wide")
st.title("⚙️ Equipment Health & Forecast Intelligence Dashboard")

st.markdown("""
This module combines **Equipment Health Scoring** 🩺 and **Predictive Forecasting** 📈  
to help you visualize **current stability** and **future performance trends** of key KPIs.
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

# ---------------- HEALTH SCORE ----------------
st.subheader("🩺 Equipment Health Status")

scores = (
    df_filtered
    .groupby(["eq", "ckpi"])
    .agg(avg_ave=("ave", "mean"), std_ave=("ave", "std"))
    .reset_index()
)
scores["norm_std"] = scores["std_ave"] / (scores["std_ave"].max() + 1e-9)
scores["HealthScore"] = (100 - scores["norm_std"] * 100).round(2)
scores["_ckpi_norm"] = scores["ckpi"].astype(str).apply(lambda s: "".join(ch for ch in s.lower() if ch.isalnum()))
scores["Weight"] = scores["_ckpi_norm"].map(weights).fillna(0.5)
scores["WeightedScore"] = (scores["HealthScore"] * scores["Weight"]).round(2)

eq_health = (
    scores.groupby("eq")["WeightedScore"]
    .mean()
    .reset_index()
    .rename(columns={"WeightedScore": "HealthScore"})
)
eq_health["HealthScore"] = pd.to_numeric(eq_health["HealthScore"], errors="coerce").fillna(0)
if not eq_health.empty:
    eq_health["HealthStatus"] = np.select(
        [
            eq_health["HealthScore"] >= 85,
            (eq_health["HealthScore"] >= 70) & (eq_health["HealthScore"] < 85),
            eq_health["HealthScore"] < 70
        ],
        ["✅ Excellent", "🟡 Needs Monitoring", "🔴 Critical"],
        default="⚙️ Unknown"
    )

st.dataframe(eq_health)

# --- Health Bar Chart ---
fig_bar = go.Figure()
for _, row in eq_health.iterrows():
    color = "green" if "Excellent" in row["HealthStatus"] else "orange" if "Needs" in row["HealthStatus"] else "red"
    fig_bar.add_trace(go.Bar(
        x=[row["eq"]],
        y=[row["HealthScore"]],
        marker_color=color,
        hovertext=row["HealthStatus"]
    ))
fig_bar.update_layout(
    xaxis_title="Equipment",
    yaxis_title="Health Score",
    yaxis=dict(range=[0, 100]),
    height=450,
    plot_bgcolor="white"
)
st.plotly_chart(fig_bar, use_container_width=True)

# ---------------- FORECAST SECTION ----------------
st.markdown("---")
st.subheader("📈 Predictive Maintenance — KPI Failure Forecast")

if not PROPHET_AVAILABLE:
    st.warning("⚠️ Prophet not installed. Run `pip install prophet` to enable forecasting.")
else:
    kpi_list = sorted(df_filtered["ckpi"].dropna().unique())
    kpi_selected = st.selectbox("Select KPI for Forecast", kpi_list)
    df_kpi = df_filtered[df_filtered["ckpi"] == kpi_selected][["ckpi_statistics_date", "ave"]].rename(
        columns={"ckpi_statistics_date": "ds", "ave": "y"}
    )

    if len(df_kpi) >= 10:
        from prophet import Prophet
        KPI_THRESHOLDS = {
            "doorfriction": (30.0, 50.0),
            "cumulativedoorspeederror": (0.05, 0.08),
            "lockhookclosingtime": (0.2, 0.6),
            "lockhooktime": (0.3, None),
            "maximumforceduringcompress": (5.0, 28.0),
            "landingdoorlockrollerclearance": (None, 0.029)
        }
        low_thresh, high_thresh = KPI_THRESHOLDS.get(kpi_selected.lower(), (None, None))

        period_days = st.slider("🔮 Forecast Period (days)", 30, 730, 365, step=30)
        m = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        m.fit(df_kpi)
        future = m.make_future_dataframe(periods=period_days)
        forecast = m.predict(future)

        predicted_failure_date = None
        if high_thresh is not None:
            exceed = forecast[forecast["yhat"] > high_thresh]
            if not exceed.empty:
                predicted_failure_date = exceed.iloc[0]["ds"].date()
        elif low_thresh is not None:
            drop = forecast[forecast["yhat"] < low_thresh]
            if not drop.empty:
                predicted_failure_date = drop.iloc[0]["ds"].date()

        # Forecast Plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_kpi["ds"], y=df_kpi["y"],
            name="Actual", mode="lines+markers",
            line=dict(color="#0071B9", width=2)
        ))
        fig.add_trace(go.Scatter(
            x=forecast["ds"], y=forecast["yhat"],
            name="Forecast", mode="lines", line=dict(color="#00B5E2", width=3)
        ))
        fig.add_trace(go.Scatter(
            x=pd.concat([forecast["ds"], forecast["ds"][::-1]]),
            y=pd.concat([forecast["yhat_upper"], forecast["yhat_lower"][::-1]]),
            fill="toself", fillcolor="rgba(0,113,185,0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip", showlegend=False
        ))

        if high_thresh:
            fig.add_hline(y=high_thresh, line_dash="dot", line_color="red", annotation_text="High Threshold")
        if low_thresh:
            fig.add_hline(y=low_thresh, line_dash="dot", line_color="orange", annotation_text="Low Threshold")

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

        # Summary
        st.markdown("### 📅 Forecast Summary")
        if predicted_failure_date:
            days_remaining = (predicted_failure_date - pd.Timestamp.today().date()).days
            st.success(f"⚠️ **Predicted Failure Date:** {predicted_failure_date}  \n"
                       f"⏳ Estimated Remaining Life: **{days_remaining} days (~{days_remaining/365:.1f} years)**")
        else:
            st.info("✅ No predicted failure within forecast period.")
    else:
        st.warning("Not enough data for forecasting. At least 10 points required.")

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
