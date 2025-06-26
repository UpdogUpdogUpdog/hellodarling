# .github/scripts/fetch_translate.py

import os
import time
import datetime
import requests
from openai import OpenAI
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

    title_el = soup.select_one("div.darling-title h2")
    author_el = soup.select_one("div.darling-title h3")
    body_el = soup.select_one("div.darling-text")
    
    if title_el and title_el.get_text(strip=True):
        title = title_el.get_text(strip=True)
    else:
        darling_div = soup.select_one("div.darling")
        if darling_div and darling_div.has_attr("x-data"):
            import re
            match = re.search(r"darlingTitle:\s*`(.*?)`", darling_div["x-data"])
            if match:
                title = match.group(1)

    if not (title and author_el and body_el):
        raise Exception("Could not find all required elements (title, author, body).")

    author = author_el.get_text(strip=True)

    raw_lines = []
    paragraph_lines = []

    for child in body_el.children:
        if getattr(child, "name", None) == "p":
            for elem in child.contents:
                if isinstance(elem, str):
                    paragraph_lines.append(elem.strip())
                elif elem.name == "br":
                    paragraph_lines.append("\n")
                elif elem.name == "br" and "br" in elem.get("class", []):
                    raw_lines.append("".join(paragraph_lines).replace("\u3000", "　").strip())
                    raw_lines.append("")  # paragraph break
                    paragraph_lines = []
                elif elem.name == "span" and "pc_space" in elem.get("class", []):
                    paragraph_lines.append("　")  # ideographic space

            if paragraph_lines:
                raw_lines.append("".join(paragraph_lines).replace("\u3000", "　").strip())
                paragraph_lines = []

    body_text = "\n".join(raw_lines).strip()
    full_text = f"{title}\n{author}\n\n{body_text}"

    return full_text



def translate(text):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in environment")

    client = OpenAI(api_key=api_key)

    prompt = (
        "You are translating a Japanese personal essay into natural, literary English.\n"
        "Do not translate word-for-word—your goal is to preserve the author's original voice, tone, and nuance for a native English reader.\n"
        "Do not include boilerplate like 'Here is the translation.' Do not explain your output.\n"
        "Preserve paragraph breaks (two line breaks = new paragraph).\n"
        "Respect any formatting (e.g., unusual spacing, symbols like ・, etc.) where it contributes to tone.\n"
        "If there is a phrase or idiom that doesn't translate easily, include a minimal footnote only if necessary.\n"
        "---\n"
        f"{text}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=4096
    )

    return response.choices[0].message.content.strip()



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
