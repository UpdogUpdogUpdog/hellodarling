import requests
import json
import re

GITHUB_API = "https://api.github.com"
REPO = "updogupdogupdog/hellodarling"
HEADERS = {"Accept": "application/vnd.github.v3+json"}
RAW_BASE = "https://raw.githubusercontent.com/updogupdogupdog/hellodarling/main"

def get_latest_file_path(subdir):
    url = f"{GITHUB_API}/repos/{REPO}/contents/{subdir}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    files = r.json()

    # Extract YYYY-MM-DD.txt files and sort by name (newest last)
    txt_files = [
        f["name"] for f in files
        if f["name"].endswith(".txt") and re.match(r"\\d{4}-\\d{2}-\\d{2}\\.txt", f["name"])
    ]
    txt_files.sort()
    return txt_files[-1]  # latest file

def fetch_txt(path):
    r = requests.get(f"{RAW_BASE}/{path}")
    r.raise_for_status()
    return r.text.strip()

def particle_paragraph(text):
    return {
        "type": "paragraph",
        "text": text.replace("\r\n", "\n").replace("\r", "\n")
    }

latest_file = get_latest_file_path("originals")  # same name used in both dirs
date_str = latest_file.removesuffix(".txt")

japanese_text = fetch_txt(f"originals/{latest_file}")
english_text = fetch_txt(f"translations/{latest_file}")

with open("index.json", "w", encoding="utf-8") as f:
    json.dump({
        "format": "particle",
        "title": f"{date_str} — Darling (JP)",
        "content": [
            {
                "type": "button",
                "label": "Show Translation",
                "action": "/translation"
            },
            particle_paragraph(japanese_text)
        ]
    }, f, ensure_ascii=False, indent=2)

with open("translation.json", "w", encoding="utf-8") as f:
    json.dump({
        "format": "particle",
        "title": f"{date_str} — Darling (EN)",
        "content": [
            {
                "type": "button",
                "label": "Back to Japanese",
                "action": "/"
            },
            particle_paragraph(english_text)
        ]
    }, f, ensure_ascii=False, indent=2)
