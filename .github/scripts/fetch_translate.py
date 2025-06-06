# .github/scripts/fetch_translate.py

import os
import time
import datetime
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def init_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.binary_location = "/usr/bin/chromium-browser"
    return webdriver.Chrome(options=options)

def fetch_today_post():
    driver = init_driver()
    driver.get("https://www.1101.com/")
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    title_el = soup.select_one("div.home-first-darling-title h2")
    author_el = soup.select_one("div.home-first-darling-title h3")
    body_el = soup.select_one("div.home-first-darling-text")

    if not (title_el and author_el and body_el):
        raise Exception("Could not find all required elements (title, author, body).")

    title = title_el.get_text(strip=True)
    author = author_el.get_text(strip=True)

    raw_lines = []
    paragraph_lines = []

    for child in body_el.children:
        if getattr(child, "name", None) == "p":
            for elem in child.contents:
                if isinstance(elem, str):
                    paragraph_lines.append(elem.strip())
                elif elem.name == "br":
                    # default <br>
                    paragraph_lines.append("\n")
                elif elem.name == "br" and "br" in elem.get("class", []):
                    # paragraph break
                    raw_lines.append("".join(paragraph_lines).replace("\u3000", "　").strip())
                    raw_lines.append("")  # empty line for paragraph break
                    paragraph_lines = []
                elif elem.name == "span" and "pc_space" in elem.get("class", []):
                    paragraph_lines.append("　")  # manually add ideographic space

            # After last line if no <br class="br"> followed
            if paragraph_lines:
                raw_lines.append("".join(paragraph_lines).replace("\u3000", "　").strip())
                paragraph_lines = []

    body_text = "\n".join(raw_lines).strip()
    full_text = f"{title}\n{author}\n\n{body_text}"

    return full_text

def translate(text):
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise RuntimeError("TOGETHER_API_KEY not found in environment")

    res = requests.post(
        "https://api.together.xyz/inference",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "meta-llama/Llama-3-70b-chat-hf",
            "prompt": f"Translate the following Japanese essay into natural, literary English. Do not merge lines that are visually separated by paragraph breaks, but do not treat single newlines as paragraph breaks themselves. Paragraphs are separated by two line breaks (\\n\\n). Retain tone and formatting. If there are idioms or cultural anomalies that don't translate well without losing meaning, include footnotes to help clarify them, but they are not always going to be present or necessary.\n---\n{text}",
            "max_tokens": 2048,
            "temperature": 0.7,
        }
    )

    res.raise_for_status()
    data = res.json()

    # DEBUG print of full response
    print("TOGETHER API RESPONSE:\n", data)

    # Defensive parse
    output = data.get("output")
    if isinstance(output, str) and output.strip():
        return output.strip()
    elif isinstance(output, dict):
        # Depending on model, the format may change
        return output.get("choices", [{}])[0].get("text", "").strip()
    else:
        raise RuntimeError("Empty or malformed API response: " + str(data))



def main():
    jp_text = fetch_today_post()
    print("Japanese text fetched:\n", jp_text)

    en_text = translate(jp_text)
    print("Translated text:\n", en_text)

    today = datetime.date.today().isoformat()
    os.makedirs("translations", exist_ok=True)
    os.makedirs("originals", exist_ok=True)

    with open(f"translations/{today}.txt", "w", encoding="utf-8") as f:
        f.write(en_text)

    with open(f"originals/{today}.txt", "w", encoding="utf-8") as f:
        f.write(jp_text.strip())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)
        raise
