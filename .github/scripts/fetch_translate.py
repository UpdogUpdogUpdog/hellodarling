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

    try:
        more_button = driver.find_element(By.PARTIAL_LINK_TEXT, "つづきを読む")
        more_button.click()
        time.sleep(1)
    except:
        pass

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    darling_div = soup.select_one("div.darling__txt")
    if not darling_div:
        raise Exception("Could not find today's darling post.")

    return darling_div.get_text("\n", strip=True).replace("\u3000", " ")

def translate(text):
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise RuntimeError("TOGETHER_API_KEY not found in environment")

    print("Sending text to translation API...")
    res = requests.post(
        "https://api.together.xyz/inference",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": f"Please translate the following Japanese text into natural English. There's an obvious blog post entry, you don't need to translate any UI element text:\n---\n{text}",
            "max_tokens": 1024,
            "temperature": 0.7,
        }
    )

    res.raise_for_status()
    data = res.json()
    print("Together API raw response:", data)

    try:
        output = data["choices"][0]["text"].strip()
        if output.endswith("...") or len(output) > 900:
            print("⚠️  Output may be truncated.")
        return output
    except (KeyError, IndexError) as e:
        raise RuntimeError("Unexpected response format: " + str(data))

def main():
    jp_text = fetch_today_post()
    print("Japanese text fetched:\n", jp_text)

    en_text = translate(jp_text)
    print("Translated text:\n", en_text)

    today = datetime.date.today().isoformat()
    os.makedirs("translations", exist_ok=True)
    with open(f"translations/{today}.txt", "w", encoding="utf-8") as f:
        f.write(en_text)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)
        raise
