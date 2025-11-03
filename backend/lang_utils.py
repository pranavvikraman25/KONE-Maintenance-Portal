# -*- coding: utf-8 -*-
import streamlit as st

# Global translation dictionary
TRANSLATIONS = {
    "en": {
        "app_title": "KONE Maintenance Dashboard",
        "welcome": "Welcome to KONE Predictive Maintenance Portal",
        "info": "Use the sidebar to navigate between modules.",
        "modules": "Available Modules",
        "trend": "Trend Analyzer",
        "json": "JSON to Excel Converter",
        "report": "Report Generator",
        "maint": "Maintenance Tracker",
        "health": "Equipment Health Score",
        "archive": "Report Archive",
        "footer": "© 2025 KONE Internal Dashboard | Developed by PRANAV VIKRAMAN S S",
    },
    "fi": {
        "app_title": "KONE Huoltohallintapaneeli",
        "welcome": "Tervetuloa KONE:n ennakoivan huollon portaaliin",
        "info": "Käytä sivupalkkia siirtyäksesi moduulien välillä.",
        "modules": "Saatavilla olevat moduulit",
        "trend": "Trendianalysaattori",
        "json": "JSON Excel-muuntimeen",
        "report": "Raporttigeneraattori",
        "maint": "Huoltoseuranta",
        "health": "Laitteiston kuntopisteet",
        "archive": "Raporttiarkisto",
        "footer": "© 2025 KONE Sisäinen Hallintapaneeli | Kehittänyt PRANAV VIKRAMAN S S",
    },
    "fr": {
        "app_title": "Tableau de maintenance KONE",
        "welcome": "Bienvenue sur le portail de maintenance prédictive KONE",
        "info": "Utilisez la barre latérale pour naviguer entre les modules.",
        "modules": "Modules disponibles",
        "trend": "Analyseur de tendances",
        "json": "Convertisseur JSON vers Excel",
        "report": "Générateur de rapports",
        "maint": "Suivi de maintenance",
        "health": "Score de santé de l’équipement",
        "archive": "Archive de rapports",
        "footer": "© 2025 Tableau interne KONE | Développé par PRANAV VIKRAMAN S S",
    },
    "de": {
        "app_title": "KONE Wartungs-Dashboard",
        "welcome": "Willkommen beim KONE Predictive Maintenance Portal",
        "info": "Verwenden Sie die Seitenleiste, um zwischen den Modulen zu navigieren.",
        "modules": "Verfügbare Module",
        "trend": "Trend-Analyse",
        "json": "JSON-zu-Excel-Konverter",
        "report": "Berichtsgenerator",
        "maint": "Wartungs-Tracker",
        "health": "Gerätezustandspunktzahl",
        "archive": "Berichtsarchiv",
        "footer": "© 2025 KONE Internes Dashboard | Entwickelt von PRANAV VIKRAMAN S S",
    },
    "it": {
        "app_title": "Dashboard di manutenzione KONE",
        "welcome": "Benvenuto nel portale di manutenzione predittiva KONE",
        "info": "Usa la barra laterale per navigare tra i moduli.",
        "modules": "Moduli disponibili",
        "trend": "Analizzatore di tendenze",
        "json": "Convertitore da JSON a Excel",
        "report": "Generatore di rapporti",
        "maint": "Tracker di manutenzione",
        "health": "Punteggio stato apparecchiatura",
        "archive": "Archivio rapporti",
        "footer": "© 2025 Dashboard interno KONE | Sviluppato da PRANAV VIKRAMAN S S",
    },
    "zh": {
        "app_title": "KONE维护仪表板",
        "welcome": "欢迎使用KONE预测性维护门户",
        "info": "使用侧边栏在模块之间导航。",
        "modules": "可用模块",
        "trend": "趋势分析器",
        "json": "JSON到Excel转换器",
        "report": "报告生成器",
        "maint": "维护跟踪器",
        "health": "设备健康评分",
        "archive": "报告存档",
        "footer": "© 2025 KONE内部仪表板 | 由 PRANAV VIKRAMAN S S 开发",
    }
}


def get_text(lang, key):
    """Return translated text for given key."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))


def language_selector():
    """Show dropdown and store choice in session_state."""
    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"

    lang = st.selectbox(
        "🌐 Language",
        ["en", "fi", "fr", "de", "it", "zh"],
        index=["en", "fi", "fr", "de", "it", "zh"].index(st.session_state["lang"]),
        format_func=lambda x: {
            "en": "English 🇬🇧",
            "fi": "Finnish 🇫🇮",
            "fr": "French 🇫🇷",
            "de": "German 🇩🇪",
            "it": "Italian 🇮🇹",
            "zh": "Chinese 🇨🇳",
        }[x]
    )
    st.session_state["lang"] = lang
    return lang
