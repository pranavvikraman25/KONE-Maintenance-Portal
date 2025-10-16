import streamlit as st
import pandas as pd
import subprocess, shlex, tempfile, os

st.set_page_config(page_title="Anomaly Chatbot AI", layout="wide")

st.title("🤖 Anomaly Detection Chatbot (Local AI – Llama 3)")

st.markdown("""
This chatbot helps you analyze uploaded KPI data directly using **Llama 3 (via Ollama)** —  
no API keys, no internet connection required.  

You can ask questions like:
- *“Which EQ had the highest Door Friction last month?”*  
- *“How many anomalies were recorded in July?”*  
- *“Which floor had maximum peaks?”*  
""")

# --- Upload Data ---
uploaded = st.file_uploader("📂 Upload your KPI dataset", type=["csv", "xlsx", "json"])
if not uploaded:
    st.info("Upload a data file to begin chatting with your KPIs.")
    st.stop()

# Read file flexibly
try:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    elif uploaded.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded)
    else:
        df = pd.read_json(uploaded)
except Exception as e:
    st.error(f"Error reading file: {e}")
    st.stop()

st.success(f"✅ File loaded successfully — {len(df)} records found.")
st.dataframe(df.head())

# --- Question Input ---
query = st.text_area("💬 Ask your question to the AI:", placeholder="Example: Which EQ has the highest average doorFriction?")
ask_button = st.button("Ask")

# --- Ollama Query Function ---
def query_ollama(prompt, model="llama3"):
    """Send prompt to local Ollama model and return AI response."""
    try:
        cmd = f"ollama run {model} \"{prompt}\""
        result = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=90)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"⚠️ Ollama returned an error: {result.stderr}"
    except FileNotFoundError:
        return "❌ Ollama not found. Please install it from https://ollama.com/download and restart."
    except subprocess.TimeoutExpired:
        return "⏳ Model took too long to respond. Try shortening your query."
    except Exception as e:
        return f"❌ Unexpected error: {e}"

# --- Process Question ---
if ask_button and query:
    with st.spinner("💭 Thinking... Llama 3 is analyzing your data..."):
        # Save dataframe temporarily to describe structure
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        df.head(25).to_csv(tmp.name, index=False)
        tmp.flush()

        prompt = (
            f"You are an expert maintenance AI working for KONE.\n"
            f"Here is a dataset sample (first 25 rows):\n"
            f"{df.head(25).to_csv(index=False)}\n\n"
            f"Answer clearly and briefly this question:\n{query}\n"
            f"Provide numeric details when possible and respond as a maintenance analyst."
        )

        response = query_ollama(prompt)
        st.markdown("### 🧠 AI Response")
        st.write(response)
        os.unlink(tmp.name)
