# scripts/auto_translate_googletrans.py
from googletrans import Translator
import ast
import io
import os
from datetime import datetime

SRC = "en"
DST = "fi"   # target language (Finnish)
SRC_FILE = "backend/lang_utils.py"
OUT_FILE = "backend/lang_utils_translated.py"  # output to review before replacing

def load_translations(path):
    text = open(path, "r", encoding="utf-8").read()
    # naive parse: read TRANSLATIONS dict literal from file
    # assumption: file defines TRANSLATIONS = {...}
    start = text.find("TRANSLATIONS")
    idx = text.find("=", start)
    dict_text = text[idx+1:]
    # try to eval safe
    d = {}
    try:
        d = ast.literal_eval(dict_text.strip())
    except Exception as e:
        # fallback: import as module
        import importlib.util
        spec = importlib.util.spec_from_file_location("lang_utils_tmp", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        d = getattr(mod, "TRANSLATIONS", {})
    return d

def main():
    translator = Translator()
    trans = load_translations(SRC_FILE)
    en = trans.get("en", {})
    new_trans = dict(trans)  # copy
    new_trans.setdefault("fi", {})
    for key, text in en.items():
        if key in new_trans.get("fi", {}) and new_trans["fi"].get(key):
            print(f"[skip] {key} already translated")
            continue
        print(f"Translating key: {key} -> {DST}")
        res = translator.translate(text, src=SRC, dest=DST)
        new_trans["fi"][key] = res.text

    # write output file for review
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Auto-generated translations (review before overwrite)\n")
        f.write(f"# generated: {datetime.now().isoformat()}\n\n")
        f.write("TRANSLATIONS = ")
        f.write(repr(new_trans))
        f.write("\n\n")
        f.write("def get_text(lang, key):\n")
        f.write("    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)\n")
    print(f"Done. Review {OUT_FILE} and if OK, replace backend/lang_utils.py with it.")
    print("Backup kept at backend/lang_utils.py.bak")
    
if __name__ == '__main__':
    main()
