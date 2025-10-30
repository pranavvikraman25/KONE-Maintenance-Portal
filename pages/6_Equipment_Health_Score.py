# pages/6_Equipment_Health_Forecast_with_ref.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from sklearn.linear_model import LinearRegression
import subprocess, shlex
from datetime import timedelta

# Optional libs
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except Exception:
    PROPHET_AVAILABLE = False

# --- Page config ---
st.set_page_config(page_title="Health & Forecast (with KPI Reference)", layout="wide")
st.title("⚙️ Equipment Health & Forecast — (Reference + Analysis)")

# ---------------- KPI reference table (render as styled HTML) ----------------
# Reference strings (No visit / DMP visit / Repair needed)
KPI_REFERENCE = {
    "doorfriction": {
        "label": "Door friction",
        "no_visit": "40N to 54N",
        "dmp_visit": "> 54N or < 40N",
        "repair": "> 90N or < 35N"
    },
    "cumulativedoorspeederror": {
        "label": "Door speed error",
        "no_visit": "0.06m/s to 0.08m/s",
        "dmp_visit": "> 0.08m/s or < 0.06m/s",
        "repair": "> 0.15m/s or < 0.02m/s"
    },
    "lockhookclosingtime": {
        "label": "Landing door lock hook closing time",
        "no_visit": "0.2s to 0.6s",
        "dmp_visit": "> 0.6s or < 0.2s",
        "repair": "> 1.2s or < -0.5s"
    },
    "lockhooktime": {
        "label": "Landing door lock hook open time",
        "no_visit": "> 0.4s",
        "dmp_visit": "< 0.4s",
        "repair": "< 0.1s"
    },
    "maximumforceduringcompress": {
        "label": "Maximum force during coupler compress",
        "no_visit": "5N to 28N",
        "dmp_visit": "< 5N or > 28N",
        "repair": "> 40N or < -10N"
    },
    "landingdoorlockrollerclearance": {
        "label": "Landing door lock roller clearance",
        "no_visit": "< 0.029m",
        "dmp_visit": "> 0.029m",
        "repair": "> 0.04m"
    }
}

# Small helper to build the HTML table
def render_reference_table(kpi_ref):
    css = """
    <style>
    .ref-table {border-collapse: collapse; width: 100%; font-family: "Segoe UI", Roboto, Arial;}
    .ref-table th, .ref-table td {border: 1px solid #e6e6e6; padding: 8px; text-align: center;}
    .ref-table thead th {background:#f7f7f8; font-size:14px; padding-top:10px; padding-bottom:10px;}
    .ref-ok {background: #dff0d8;}           /* green */
    .ref-warn {background: #fff3cd;}         /* yellow */
    .ref-critical {background: #f8d7da;}     /* red */
    .ref-label {text-align:left; font-weight:600; padding-left:12px;}
    .ref-tooltip {position:relative;}
    .ref-tooltip:hover {filter: brightness(0.98); cursor:help;}
    .ref-caption {font-size:13px; color:#444; margin-bottom:8px;}
    </style>
    """
    html = css + '<div class="ref-caption"><strong>cKPI Reference Ranges</strong> — Green = No visit required • Yellow = DMP visit required • Red = Repair needed</div>'
    html += '<table class="ref-table"><thead><tr><th>cKPI</th><th class="ref-ok">No visit required</th><th class="ref-warn">DMP visit required</th><th class="ref-critical">Repair needed (SN trigger)</th></tr></thead><tbody>'
    for key, v in kpi_ref.items():
        html += f'<tr><td class="ref-label">{v["label"]}</td>'
        html += f'<td class="ref-ok">{v["no_visit"]}</td>'
        html += f'<td class="ref-warn">{v["dmp_visit"]}</td>'
        html += f'<td class="ref-critical">{v["repair"]}</td></tr>'
    html += '</tbody></table>'
    return html

st.markdown(render_reference_table(KPI_REFERENCE), unsafe_allow_html=True)
st.markdown("---")

# ---------------- Helpers ----------------
def normalize_text(s: str):
    if s is None: return ""
    return "".join(ch for ch in str(s).lower() if ch.isalnum())

def df_to_excel_bytes(df_):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df_.to_excel(writer, index=False, sheet_name="report")
    out.seek(0)
    return out

# ---------------- Upload / read ----------------
uploaded = st.file_uploader("Upload KPI dataset (xlsx / csv / json)", type=["xlsx","csv","json"])
if not uploaded:
    st.info("Upload a KPI file to begin. Required columns: eq, ckpi, ckpi_statistics_date, ave, floor (optional).")
    st.stop()

try:
    name = uploaded.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    elif name.endswith(".xlsx"):
        df = pd.read_excel(uploaded)
    else:
        df = pd.read_json(uploaded)
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

required = {"eq","ckpi","ave","ckpi_statistics_date"}
if not required.issubset(set(df.columns)):
    st.error(f"File missing required columns. Need: {', '.join(required)}")
    st.stop()

# Normalize and parse dates intelligently:
# If majority of month values > 12 then treat as dd/mm/yyyy else month/day/year preference isn't perfect for all files,
# but we coerce and attempt both formats; here we assume mm/dd/yyyy as default (as you requested earlier).
df["ckpi_statistics_date"] = pd.to_datetime(df["ckpi_statistics_date"], dayfirst=False, errors="coerce")
if df["ckpi_statistics_date"].isna().all():
    # fallback try dayfirst True
    df["ckpi_statistics_date"] = pd.to_datetime(df["ckpi_statistics_date"].astype(str), dayfirst=True, errors="coerce")

df["_ckpi_norm"] = df["ckpi"].astype(str).apply(normalize_text)
df["ave"] = pd.to_numeric(df["ave"], errors="coerce")

# Keep only the 6 main KPIs (normalize keys)
MAIN_KPIS = [
    "doorfriction",
    "cumulativedoorspeederror",
    "lockhookclosingtime",
    "lockhooktime",
    "maximumforceduringcompress",
    "landingdoorlockrollerclearance"
]
# map available display names for sidebar
kpi_display_map = {normalize_text(k):k for k in df["ckpi"].dropna().unique()}
# unify df to only include main KPIs present in file
df = df[df["_ckpi_norm"].isin(MAIN_KPIS)].copy()
if df.empty:
    st.error("No rows found for the 6 main KPIs in your file.")
    st.stop()

# ---------------- Sidebar filters ----------------
st.sidebar.header("Global Filters")
eq_choices = sorted(df["eq"].dropna().astype(str).unique())
selected_eq = st.sidebar.multiselect("Select EQ(s)", eq_choices, default=eq_choices[:3] if eq_choices else [])

# list display names for KPI selector (user-friendly)
display_kpis = sorted(df["ckpi"].dropna().unique())
selected_kpis = st.sidebar.multiselect("Select KPI(s)", display_kpis, default=display_kpis[:6] if display_kpis else [])



#-------------------------date filter -----------------------------------------



# --- Dynamic Date Range Handling ---
# Always use the latest date in the dataset, not today's date
date_series = pd.to_datetime(df["ckpi_statistics_date"], errors="coerce")
latest_date = date_series.max().date() if not date_series.isna().all() else pd.Timestamp.today().date()

# Define date presets based on latest date from file
preset_range = st.sidebar.selectbox(
    "Quick Select",
    ["Custom", "Past Week", "Past Month", "Past 3 Months", "Past 6 Months", "Past Year"]
)

if preset_range == "Custom":
    min_date = date_series.min().date() if not date_series.isna().all() else latest_date - timedelta(days=30)
    start_date, end_date = st.sidebar.date_input(
        "Select Custom Date Range",
        [min_date, latest_date]
    )
elif preset_range == "Past Week":
    start_date, end_date = latest_date - timedelta(days=7), latest_date
elif preset_range == "Past Month":
    start_date, end_date = latest_date - timedelta(days=30), latest_date
elif preset_range == "Past 3 Months":
    start_date, end_date = latest_date - timedelta(days=90), latest_date
elif preset_range == "Past 6 Months":
    start_date, end_date = latest_date - timedelta(days=180), latest_date
else:  # Past Year
    start_date, end_date = latest_date - timedelta(days=365), latest_date

st.sidebar.markdown(f"**🕒 Reference period:** up to {latest_date.strftime('%d-%b-%Y')}")



std_factor = st.sidebar.slider("Peak/Low Sensitivity", 0.5, 3.0, 1.0, 0.1)




#-------------------------date filter -----------------------------------------

# smart KPI weights UI: show sliders only for selected KPIs
st.sidebar.markdown("### ⚖️ KPI Weights")
selected_kpi_norms = [normalize_text(x) for x in selected_kpis]
weights = {}
if selected_kpi_norms:
    base = 1.0 / len(selected_kpi_norms)
    st.sidebar.caption("Adjust weights (relative importance). Values are normalized to sum=1.")
    for k in selected_kpi_norms:
        # display friendly name if present else the normalized key
        label = next((x for x in display_kpis if normalize_text(x) == k), k)
        weights[k] = st.sidebar.slider(label, 0.0, 1.0, float(base), 0.05)
else:
    # default balanced weights for all main KPIs
    st.sidebar.caption("No KPI selected — using equal weights for all main KPIs.")
    for k in MAIN_KPIS:
        weights[k] = 1.0 / len(MAIN_KPIS)

# normalize weights to sum 1
total_w = sum(weights.values()) if sum(weights.values())>0 else 1.0
for k in weights:
    weights[k] = float(weights[k]) / float(total_w)

# sensitivity slider for peak/low detection (if you keep that feature)
sensitivity = st.sidebar.slider("Peak sensitivity (std factor)", 0.5, 3.0, 1.0, 0.1)

# apply filters to dataframe
start_date = pd.to_datetime(start_date).date()
end_date = pd.to_datetime(end_date).date()

mask = (
    df["eq"].astype(str).isin(selected_eq) &
    df["ckpi"].isin(selected_kpis) &
    (df["ckpi_statistics_date"].dt.date >= start_date) &
    (df["ckpi_statistics_date"].dt.date <= end_date)
)

df_filtered = df[mask].copy()
if df_filtered.empty:
    st.warning("No data after applying filters.")
    st.stop()

# ---------------- Health Score calculation (stable approach) ----------------
st.header("🩺 Equipment Health Summary")

# compute per eq-per-kpi stats
stats = (
    df_filtered.groupby(["eq","_ckpi_norm","ckpi"])
    .agg(avg_ave=("ave","mean"), std_ave=("ave","std"), cnt=("ave","count"))
    .reset_index()
)

# normalize std within file
max_std = stats["std_ave"].max() if not np.isnan(stats["std_ave"].max()) else 0.0
stats["norm_std"] = stats["std_ave"] / (max_std + 1e-9)
# base health per KPI (100 best, 0 worst)
stats["HealthScoreKPI"] = (100 - stats["norm_std"] * 100).clip(0,100).round(2)

# map weights (use normalized _ckpi_norm keys)
stats["_ckpi_norm"] = stats["_ckpi_norm"].astype(str)
stats["Weight"] = stats["_ckpi_norm"].map(weights).fillna(0.0)
# aggregated weighted health per equipment
eq_health = (
    stats.groupby("eq").apply(lambda g: np.average(g["HealthScoreKPI"], weights=g["Weight"]) if g["Weight"].sum()>0 else g["HealthScoreKPI"].mean())
    .reset_index(name="HealthScore")
)
eq_health["HealthScore"] = eq_health["HealthScore"].fillna(0).round(2)

# HealthStatus (safe)
eq_health["HealthScore"] = pd.to_numeric(eq_health["HealthScore"], errors="coerce").fillna(0)
conds = [
    eq_health["HealthScore"] >= 85,
    (eq_health["HealthScore"] >= 70) & (eq_health["HealthScore"] < 85),
    eq_health["HealthScore"] < 70
]
choices = ["✅ Excellent","🟡 Needs Monitoring","🔴 Critical"]
eq_health["HealthStatus"] = np.select(conds, choices, default="⚙️ Unknown")

# make eq string to avoid scientific axis labels
eq_health["eq"] = eq_health["eq"].astype(str)

# show summary top area
st.subheader("Health scores (per EQ)")
st.dataframe(eq_health.sort_values("HealthScore", ascending=False).reset_index(drop=True))

# show KPI-weight contribution heatmap table (colored)
st.subheader("KPI contribution (weighted per EQ)")
pivot = stats.pivot_table(index="eq", columns="ckpi", values="HealthScoreKPI", aggfunc=np.mean).fillna(0)
# multiply columns by weights to visualize contribution
for col in pivot.columns:
    pivot[col] = pivot[col] * weights.get(normalize_text(col), 0.0)
st.dataframe(pivot.style.background_gradient(cmap="RdYlGn", axis=None).format("{:.2f}"))

# bar chart of current health
fig = go.Figure()
fig.add_trace(go.Bar(
    x=eq_health["eq"],
    y=eq_health["HealthScore"],
    marker_color=[ "green" if s>=85 else "orange" if s>=70 else "red" for s in eq_health["HealthScore"]],
    text=eq_health["HealthScore"],
    textposition="auto",
    hovertemplate="EQ: %{x}<br>HealthScore: %{y}<extra></extra>"
))
fig.update_layout(xaxis_title="Equipment", yaxis_title="Health Score (0-100)", height=450, template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# ---------------- Forecast section (Prophet) ----------------
st.markdown("---")
st.header("📈 Forecast & Failure Prediction (per KPI)")

if not PROPHET_AVAILABLE:
    st.warning("Prophet not installed in environment. Forecasting disabled. Install via `pip install prophet`.")
else:
    # KPI selector for forecast (only those present after filters)
    available_kpis = sorted(df_filtered["ckpi"].unique())
    sel_kpi = st.selectbox("Select KPI to forecast", available_kpis)

    df_kpi = df_filtered[df_filtered["ckpi"] == sel_kpi][["ckpi_statistics_date","ave","eq","floor"]].rename(columns={"ckpi_statistics_date":"ds","ave":"y"})
    # require per-eq forecasting; allow selection of eq to forecast
    eqs_for_kpi = sorted(df_kpi["eq"].astype(str).unique())
    sel_eq_for_forecast = st.selectbox("Select EQ for forecasting (per KPI)", eqs_for_kpi)
    df_kpi_eq = df_kpi[df_kpi["eq"].astype(str) == str(sel_eq_for_forecast)].sort_values("ds")
    if len(df_kpi_eq) < 10:
        st.info("Not enough points for reliable Prophet forecast (>=10 recommended). Select another EQ or KPI or widen date range.")
    else:
        # thresholds: try to use KPI_REFERENCE mapping if present
        k_norm = normalize_text(sel_kpi)
        # attempt to parse high/low numerics from KPI_REFERENCE strings if possible (best-effort)
        low_thresh = None
        high_thresh = None
        # If your KPI threshold dict (original) exists, you could map numeric; here we try simple parse
        # Build Prophet model
        period_days = st.slider("Forecast horizon (days)", 30, 730, 365, step=30)
        m = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        with st.spinner("Fitting forecast model..."):
            m.fit(df_kpi_eq[["ds","y"]])
            future = m.make_future_dataframe(periods=period_days)
            forecast = m.predict(future)

        # find predicted exceed / drop using best-effort thresholds if provided in KPI_REFERENCE (non-numeric strings ignored)
        # visualize
        figf = go.Figure()
        figf.add_trace(go.Scatter(x=df_kpi_eq["ds"], y=df_kpi_eq["y"], name="Actual", mode="lines+markers"))
        figf.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat"], name="Forecast", mode="lines", line=dict(width=3)))
        figf.add_trace(go.Scatter(
            x=pd.concat([forecast["ds"], forecast["ds"][::-1]]),
            y=pd.concat([forecast["yhat_upper"], forecast["yhat_lower"][::-1]]),
            fill="toself", fillcolor="rgba(0,113,185,0.12)", line=dict(color="rgba(255,255,255,0)"), hoverinfo="skip", showlegend=False
        ))
        figf.update_layout(title=f"Forecast for KPI: {sel_kpi} · EQ: {sel_eq_for_forecast}", xaxis_title="Date", yaxis_title="ave", height=600, template="plotly_white")
        st.plotly_chart(figf, use_container_width=True)

        # detect earliest breach if thresholds are numeric (we did not parse; leave for future enhancement)
        st.markdown("**Forecast table (downloadable)**")
        st.download_button("Download forecast CSV", data=forecast[["ds","yhat","yhat_lower","yhat_upper"]].to_csv(index=False).encode(), file_name=f"forecast_{normalize_text(sel_kpi)}_{sel_eq_for_forecast}.csv")

# ---------------- AI summary (Ollama) ----------------
st.markdown("---")
st.header("🤖 AI Summary (optional, local Ollama)")

def run_ollama_summary(text, model="llama3"):
    ollama_path = shutil_which_ollama()
    if not ollama_path:
        return None, "ollama_not_found"
    prompt = f"Summarize this equipment health report in 3 concise bullet points for a maintenance manager:\n\n{text}"
    try:
        cmd = f"\"{ollama_path}\" run {model} \"{prompt}\""
        proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=60)
        if proc.returncode == 0:
            return proc.stdout.strip(), None
        else:
            return None, proc.stderr.strip()
    except Exception as e:
        return None, str(e)

def shutil_which_ollama():
    import shutil, os
    # first try PATH
    p = shutil.which("ollama")
    if p: return p
    # check common windows path for local dev (adjust username if needed)
    possible = [
        os.path.expanduser(r"~\AppData\Local\Programs\Ollama\ollama.exe"),
        "/usr/local/bin/ollama",
        "/opt/homebrew/bin/ollama",
    ]
    for pp in possible:
        if os.path.exists(pp):
            return pp
    return None

# small dataset summary for AI
summary_df = eq_health.copy()
if not summary_df.empty:
    csv_text = summary_df.to_csv(index=False)
    ollama_path = shutil_which_ollama()
    if not ollama_path:
        st.info("Ollama not found on host. Install Ollama and ensure `ollama serve` is running to enable local AI summaries.")
    else:
        st.info("Ollama found. Running local summary (may take a few seconds)...")
        summary_text, err = run_ollama_summary(csv_text, model="llama3")
        if summary_text:
            st.markdown("**AI Insights:**")
            st.write(summary_text)
        else:
            st.info("Ollama returned no summary or error; check logs. Error: " + (err or "unknown"))

# ---------------- Download combined report ----------------
st.markdown("---")
st.subheader("📥 Export")
st.download_button("Download Health (Excel)", data=df_to_excel_bytes(eq_health), file_name="equipment_health.xlsx")
st.download_button("Download Stats (Excel)", data=df_to_excel_bytes(stats), file_name="kpi_stats.xlsx")

st.caption("© Your Project — Equipment Health & Forecast Portal")
st.caption("© 2025 KONE Internal Analytics | Developed by PRANAV VIKRAMAN S S")
