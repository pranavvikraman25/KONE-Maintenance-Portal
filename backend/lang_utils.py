# backend/lang_utils.py

TRANSLATIONS = {
    "en": {
        "home_title": "Welcome to KONE Maintenance Dashboard",
        "home_info": "Use the sidebar to navigate between modules.",
        "trend_analyzer": "Trend Analyzer",
        "json_to_excel": "JSON to Excel",
        "report_generator": "Report Generator",
        "maintenance_tracker": "Maintenance Tracker",
        "equipment_health_score": "Equipment Health Score",
        "report_archive": "Report Archive",
        "select_language": "Select Language",
        "download_report": "Download Report",
    },
    "fi": {  # Finnish 🇫🇮
        "home_title": "Tervetuloa KONE:n huoltotyökalun hallintapaneeliin",
        "home_info": "Käytä sivupalkkia siirtyäksesi moduulien välillä.",
        "trend_analyzer": "Trendianalysaattori",
        "json_to_excel": "JSON Exceliksi",
        "report_generator": "Raporttigeneraattori",
        "maintenance_tracker": "Huollon Seuranta",
        "equipment_health_score": "Laitteen Kuntoindeksi",
        "report_archive": "Raporttiarkisto",
        "select_language": "Valitse kieli",
        "download_report": "Lataa Raportti",
    }
}

def get_text(lang, key):
    """Return translated text or fallback to English."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
