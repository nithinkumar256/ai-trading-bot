import os
import requests
from dotenv import load_dotenv

# ✅ Load .env
load_dotenv()

# ✅ Read values
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

last_update_id = None


def send_telegram(message):
    url = f"{BASE_URL}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, data=payload)
        print("Telegram response:", response.text)
    except Exception as e:
        print("Telegram Error:", e)


def get_updates():
    global last_update_id

    url = f"{BASE_URL}/getUpdates"

    params = {}

    if last_update_id:
        params["offset"] = last_update_id + 1

    try:
        response = requests.get(url, params=params).json()

        if response.get("ok"):
            updates = response.get("result", [])

            if updates:
                last_update_id = updates[-1]["update_id"]

            return updates

    except Exception as e:
        print("Telegram fetch error:", e)

    return []