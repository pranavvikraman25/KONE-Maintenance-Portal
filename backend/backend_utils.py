# backend/backend_utils.py

import streamlit as st
import os
from io import BytesIO

# Directory to store uploaded files
UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file):
    """Save uploaded file both in memory (session) and on disk."""
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    # Store info in session
    st.session_state['uploaded_file_path'] = file_path
    st.session_state['uploaded_file_name'] = uploaded_file.name
    return file_path

def get_uploaded_file():
    """Return file path if exists in session."""
    return st.session_state.get('uploaded_file_path', None)

def clear_uploaded_file():
    """Clear uploaded file from session."""
    st.session_state.pop('uploaded_file_path', None)
    st.session_state.pop('uploaded_file_name', None)
    st.success("File cleared. Upload a new one.")
