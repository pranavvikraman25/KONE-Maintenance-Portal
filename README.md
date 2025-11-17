Project Link: https://kone-maintenance-website.streamlit.app/



© Credits

Developed with dedication by PRANAV VIKRAMAN S S

KONE Digital Maintenance • 2025




# KONE Predictive Maintenance Portal

# A unified platform for trend analysis, anomaly detection, report generation, and equipment health forecasting.

<br>
📘 Overview

This project is a complete maintenance analytics portal built using Python, Streamlit, Plotly, and local AI (LLaMA-3 via Ollama).
It integrates multiple tools used by engineering and field-maintenance teams to interpret CKPI data, analyze patterns, detect anomalies, generate formatted reports, and forecast equipment health.

The platform is designed to resemble a real, production-style internal tool used by enterprise engineering teams.

<br>
🧩 Core Modules

Each module inside the portal functions independently and can be accessed from the sidebar navigation.

1. Trend Analyzer

Visualizes CKPI patterns for each equipment & floor.
Includes:

Multi-KPI selection & filtering

Floor-wise trend visualization

Peak/Low detection using statistical methods

Timeline selectors (1W, 1M, 3M, 6M, 1Y, custom date range)

Threshold-based point coloring

2. JSON → Excel Converter

Converts raw maintenance JSON logs into structured Excel files
Used by field technicians who need readable versions of telemetry data.

3. Word Report Generator

Creates a fully formatted .docx report from CKPI data.

Key features:

Threshold-based color shading

One page per Date × EQ

Auto-aligned table structure

“No Corrective Action Required” / “Corrective Action Required” indicators

Technician-friendly layout

4. Maintenance Tracker

Allows technicians to mark issues as:

Checked

Resolved

This helps maintain clear maintenance history inside the team.

5. Equipment Health Score

Assigns a weighted score to each equipment based on available KPIs
Used to prioritize inspection schedules.

6. Report Archive

Stores generated reports for future lookup
Supports:

Filtering by Date

Filtering by KPIs

Filtering by Equipment ID

<br>
🎨 Design & UX

The portal follows KONE’s internal design language:

Deep Blue primary theme

Clean, modern sidebar

Fully responsive layout

Custom CSS for typography, spacing, and animations

Company logo integration

Clickable footer linking to developer profile

Everything is styled to feel like a real internal corporate dashboard.

<br>
🧠 AI Integration (Local LLaMA-3)

The portal embeds an AI engine powered by Ollama + LLaMA-3 for:

Summarizing anomaly patterns

Generating actionable insights

Conversational Q&A on dataset contents

Producing technician-level explanations

Setup is simple:

ollama pull llama3
ollama serve

<br>
🛠 Tech Stack
Frontend / Visualization

Streamlit

Plotly

Custom CSS

Responsive layout system

Backend / Processing

Python

Pandas / NumPy

python-docx

Date normalization logic

KPI threshold mapping

Peak/Low detection algorithms

AI / NLP

Local inference with Ollama

LLaMA-3 model

Shell-based model interaction

<br>
📂 Project Structure
project-root/
│
├── app.py                     # Main dashboard homepage
├── assets/
│   ├── logo.png               # KONE logo
│   └── style.css              # Theme + UI styling
│
├── pages/                     # Streamlit multipage modules
│   ├── 1_Trend_Analyzer.py
│   ├── 2_JSON_to_Excel.py
│   ├── 3_Report_Generator.py
│   ├── 4_Maintenance_Tracker.py
│   ├── 5_Equipment_Health_Score.py
│   ├── 6_Report_Archive.py
│
├── modules/                   # Core business logic
│   ├── trend_logic.py
│   ├── word_report_logic.py
│   ├── json_to_excel_logic.py
│   ├── health_score_logic.py
│   └── ai_engine.py
│
└── requirements.txt

<br>
📦 Installation & Setup

Clone the repository:

git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>


Install dependencies:

pip install -r requirements.txt


Start the application:

streamlit run app.py


(Optional) Enable the AI engine:

ollama pull llama3
ollama serve

<br>
🧪 Features in Detail
✔ Smart Column Detection

Automatically identifies:

EQUIPMENT column

KPI column

FLOOR column

DATE column

VALUE/AVE column

Even when file formats vary.

✔ Robust Date Parsing

Supports:

dd/mm/yyyy

mm/dd/yyyy

yyyy-mm-dd

Auto-correction for ambiguous formats

✔ Threshold-Based KPI Interpretation

Applies defined limits for each KPI
Colors points accordingly:

🟢 within limits

🟡 outside limits

🔺 peak

🔻 low

✔ Supports Multiple File Types

Excel (.xlsx, .xls)

CSV

JSON (single document or list of objects)

<br>
# 🖼 Screenshots (Recommended)

Add clean screenshots of each module for better clarity:

Trend Analyzer View

Word Report Output

JSON-to-Excel Converter

Dashboard Home Page

AI Insights Page

<br>
🤝 # Contribution

This project is open for learning and enhancements.
Contributions such as UI improvements, code optimizations, and new modules are welcome.

<br>
# 👤 Developer

PRANAV VIKRAMAN S S
Engineering Student — Electronics & Communication
Specializing in Predictive Maintenance, Data Analytics, and AI.

🔗 LinkedIn:
https://www.linkedin.com/in/pranav-vikraman-322020242/

<br>
⭐ Support

If this project helped you or inspired you —
leave a star on the repository! ⭐
It helps others discover the work and motivates continued development.

<br>



