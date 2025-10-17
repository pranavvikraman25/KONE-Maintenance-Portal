# 4_Anomaly_Chatbot_AI.py
import streamlit as st
import pandas as pd
import requests, json, os, subprocess, shlex

# Optional dependency (OpenAI for cloud fallback)
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

st.set_page_config(page_title="Anomaly Chatbot AI", layout="wide")
st.title("🤖 Anomaly Detection Chatbot — Hybrid AI (Ollama + Cloud)")

st.markdown("""
This chatbot works in **dual mode**:
- 🧠 **Offline Mode (Local)** → Uses **Llama 3 via Ollama**  
- ☁️ **Online Mode (Cloud)** → Uses **OpenAI API (gpt-4o-mini)**  

Ask questions like:
- *Which EQ had the highest door friction last month?*  
- *How many anomalies occurred in July?*
""")

# --- File Upload ---
uploaded = st.file_uploader("📂 Upload your KPI dataset", type=["csv", "xlsx", "json"])
if not uploaded:
    st.info("Upload a file to begin chatting with your KPI data.")
    st.stop()

# --- Load Data ---
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

st.success(f"✅ File loaded — {len(df)} records found.")
st.dataframe(df.head())

# --- AI Query Section ---
query = st.text_area("💬 Ask your question:", placeholder="Example: Which EQ has the highest average door friction?")
ask_button = st.button("Ask")

# --- Check Ollama availability ---
def is_ollama_running():
    try:
        res = requests.get("http://localhost:11434")
        return res.status_code == 200
    except:
        return False

# --- Try connecting to Ollama first ---
OLLAMA_AVAILABLE = is_ollama_running()
if OLLAMA_AVAILABLE:
    st.success("🟢 Local Llama 3 (Ollama) detected — running in Offline Mode.")
else:
    st.warning("☁️ Ollama not found — switching to Cloud AI mode.")

# --- AI response handler ---
def query_ollama(prompt, model="llama3"):
    """Send prompt to local Ollama model"""
    url = "http://localhost:11434/api/generate"
    data = {"model": model, "prompt": prompt}
    try:
        response = requests.post(url, json=data, stream=True)
        output = ""
        for line in response.iter_lines():
            if line:
                res = json.loads(line.decode("utf-8"))
                if "response" in res:
                    output += res["response"]
        return output.strip() if output else "⚠️ No response from Ollama."
    except Exception as e:
        return f"❌ Ollama error: {e}"

def query_groq(prompt):
    """Use Groq free LLMs (Llama3, Mixtral, Gemma)"""
    try:
        import requests
        GROQ_KEY = os.getenv("GROQ_API_KEY")
        if not GROQ_KEY:
            return "❌ Missing GROQ_API_KEY. Add it in your secrets."

        headers = {
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": "You are a KONE maintenance AI analyst."},
                {"role": "user", "content": prompt}
            ]
        }
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
                             headers=headers, json=data, timeout=60)
        out = resp.json()
        return out["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"☁️ Groq API Error: {e}"


# --- Generate answer ---
if ask_button and query:
    with st.spinner("💭 Thinking... Analyzing your data..."):
        df_preview = df.head(25).to_csv(index=False)
        prompt = (
            f"You are an AI maintenance assistant for KONE elevators.\n"
            f"Dataset sample (first 25 rows):\n{df_preview}\n\n"
            f"Question: {query}\n"
            f"Analyze the data logically and respond in a short, precise format."
        )
        if OLLAMA_AVAILABLE:
            answer = query_ollama(prompt)
        elif os.getenv("OPENAI_API_KEY"):
            answer = query_openai(prompt)
        elif os.getenv("GROQ_API_KEY"):
            answer = query_groq(prompt)
        else:
            answer = "❌ No AI backend available."

        st.markdown("### 🧠 AI Response")
        st.write(answer)
