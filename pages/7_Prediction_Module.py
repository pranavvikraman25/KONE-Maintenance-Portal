import streamlit as st
import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go

st.title("📈 Prediction Module — KPI Forecast")

st.markdown("""
Forecast KPI trends using **Prophet (time-series)**.  
Upload a KPI dataset and select the KPI to forecast.
""")

uploaded = st.file_uploader("Upload KPI File (CSV/Excel)", type=["csv","xlsx"])
if not uploaded:
    st.info("Upload a file to forecast KPI trends.")
    st.stop()

if uploaded.name.endswith(".csv"):
    df = pd.read_csv(uploaded)
else:
    df = pd.read_excel(uploaded)

if not {"ckpi_statistics_date","ave","ckpi"}.issubset(df.columns):
    st.error("Dataset must contain 'ckpi_statistics_date', 'ave', 'ckpi'.")
    st.stop()

df["ckpi_statistics_date"] = pd.to_datetime(df["ckpi_statistics_date"], errors="coerce")
df = df.dropna(subset=["ckpi_statistics_date"])

kpi_selected = st.selectbox("Select KPI", sorted(df["ckpi"].unique()))
df_kpi = df[df["ckpi"] == kpi_selected][["ckpi_statistics_date","ave"]].rename(
    columns={"ckpi_statistics_date":"ds", "ave":"y"}
)

if len(df_kpi) < 10:
    st.warning("Not enough data for forecasting.")
    st.stop()

# Prophet forecast
m = Prophet()
m.fit(df_kpi)
future = m.make_future_dataframe(periods=30)
forecast = m.predict(future)

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_kpi["ds"], y=df_kpi["y"], name="Actual"))
fig.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat"], name="Forecast"))
fig.update_layout(title=f"Forecast for {kpi_selected}", xaxis_title="Date", yaxis_title="Ave")
st.plotly_chart(fig, use_container_width=True)
