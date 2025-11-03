# backend/translate_utils.py
from deep_translator import GoogleTranslator
import streamlit as st

# Keep translator settings in session
if "target_lang" not in st.session_state:
    st.session_state["target_lang"] = "en"

def auto_translate(text: str, target_lang: str = "en") -> str:
    """
    Translate text using Deep Translator (Google Translate backend).
    Compatible with Python 3.13 and Streamlit Cloud.
    """
    if not text or target_lang == "en":
        return text
    try:
        translated = GoogleTranslator(source="auto", target=target_lang).translate(text)
        return translated
    except Exception as e:
        # Fallback: return original text if translation fails
        return text

