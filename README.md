🚀 KONE Predictive Maintenance Portal

A complete maintenance intelligence dashboard built for real-world elevator analytics.

🏗️ Overview

This project is a fully-functional Predictive Maintenance Web Portal designed to help engineers analyze elevator performance, detect anomalies, and automatically create professional maintenance reports.

Built from scratch using Python + Streamlit, the portal brings multiple maintenance tools together in one clean interface — no complicated setup, no external cloud APIs, and 100% local processing.

If you work with raw KPI files, JSON reports, or day-to-day cloud data, this portal simplifies everything into a single workflow.

🌟 Features (What This Portal Can Do)
🔍 1. Trend Analyzer

Visualize CKPI curves for any equipment.
Supports:

Multi-KPI selection

Floor-wise graph plotting

Peak/Low detection

Date presets (1W, 1M, 3M, 6M, 1Y, Custom)

Actionable insights (color-coded)

📂 2. JSON → Excel Converter

Upload KONE CloudView JSON files and instantly convert them into readable Excel reports.
Useful for technicians and analytics teams.

📝 3. Live Cloud Data → Word Report

Generates a clean, formatted Word report for each EQ and date:

KPI tables

Threshold-based color coding

Floor-wise actual values

Ready for field documentation

🧠 4. Local AI Assistant (LLaMA-3 via Ollama)

Summarizes maintenance reports into simple manager-friendly bullet points.
No API key needed — everything runs locally.

🛠️ 5. Maintenance Tracker

Mark issues as “Checked” / “Resolved”.
Helps track technician-level follow-ups.

📈 6. Equipment Health Score

Computes weighted KPI health for each unit.
Ranks which equipment needs attention first.

📁 7. Report Archive

Automatically stores and lists previously generated reports.
Easy to download anytime.

🧰 Tech Stack

Frontend / Dashboard:

Streamlit

Custom CSS (KONE theme)

Backend / Logic:

Python

Pandas

NumPy

Plotly

python-docx

openpyxl

xlrd

JSON parsing

AI:

LLaMA-3 using Ollama (local inference)

📦 Installation (Simple Setup)

Clone the repository:

git clone https://github.com/your-repo-name/kone-predictive-maintenance.git
cd kone-predictive-maintenance


Install dependencies:

pip install -r requirements.txt


Install Ollama (for AI summary):
https://ollama.com/download

Run the app:

streamlit run app.py


You’re live 🎉

📁 Folder Structure
/app.py                       → Main portal loader  
/pages/                       → Each module (Trend Analyzer, Report Generator, etc.)
/assets/                      → CSS, logo, icons  
/archive/                     → Saved reports  
/requirements.txt             → Dependencies  

🎯 How To Use the Portal

Launch the app

Use the left sidebar to choose a module

Upload your KPI file / JSON / Excel

Apply filters (EQ, floor, KPI, date)

View graphs, AI summaries, and generate reports

Download results from the archive

That’s it — no complications.

💡 Why This Project Matters

This tool bridges the gap between raw maintenance data and actionable engineering insights.
Instead of reading thousands of rows manually, teams can:

Spot unusual behavior instantly

Generate formatted official documents

Forecast equipment health

Save hours of manual reporting

Built to support analytics, technicians, and field teams — all in one place.

🤝 Contributing

Results improve when more engineers contribute.
If you want to refine UI/UX, add modules, or improve AI logic — PRs are welcome.

⭐ Acknowledgements

Special thanks to the engineering teams whose real-world problems inspired this project.

© Credits

Developed with dedication by PRANAV VIKRAMAN S S

KONE Digital Maintenance • 2025
