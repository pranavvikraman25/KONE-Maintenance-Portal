# backend/report_utils.py

import os
from datetime import datetime

REPORTS_DIR = "backend/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

def get_module_folder(module_name):
    """Ensure a folder exists for each module (Trend_Analyzer, JSON_to_Excel, etc.)"""
    module_path = os.path.join(REPORTS_DIR, module_name)
    os.makedirs(module_path, exist_ok=True)
    return module_path

def save_report(file_bytes, module_name, filter_label=None, extension="xlsx"):
    """Save file uniquely based on module, filter, and timestamp."""
    module_folder = get_module_folder(module_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filter_str = f"_{filter_label}" if filter_label else ""
    filename = f"{module_name}{filter_str}_{timestamp}.{extension}"
    file_path = os.path.join(module_folder, filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    return file_path

def list_all_reports(max_reports=50):
    """List up to max_reports latest reports (prevent too many open files)."""
    all_files = []
    if not os.path.exists(REPORTS_DIR):
        return all_files
    for root, _, files in os.walk(REPORTS_DIR):
        for f in files:
            if not f.startswith("."):
                full_path = os.path.join(root, f)
                all_files.append(full_path)
    # sort by modified time
    all_files = sorted(all_files, key=os.path.getmtime, reverse=True)
    return all_files[:max_reports]  # limit to 50 latest reports

    
def delete_report(file_path):
    """Delete a report file safely."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting {file_path}: {e}")
        return False
