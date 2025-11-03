# backend/translate_utils.py
from googletrans import Translator
import streamlit as st

# Keep one Translator instance in session to avoid repeated initialization
if "translator" not in st.session_state:
    st.session_state["translator"] = Translator()

def auto_translate(text: str, target_lang: str = "en") -> str:
    """
    Translate any string using Google Translate free API.
    target_lang: 'en', 'fi', 'fr', 'de', 'it', 'zh-cn', etc.
    """
    if not text:
        return ""
    try:
        translator = st.session_state["translator"]
        result = translator.translate(text, dest=target_lang)
        return result.text
    except Exception as e:
        # fallback – return original text if API fails
        return text
