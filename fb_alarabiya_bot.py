import requests
import re
import hashlib
import os
import time
import threading
from html import unescape
from datetime import datetime
from flask import Flask, jsonify

# =========================
# بياناتك
# =========================
TELEGRAM_BOT_TOKEN = "7522002533:AAEQzquyk1AOV71gtyljXeMHfCBJyKv3iE0"
OWNER_CHAT_ID = 5442141079

FACEBOOK_PAGE = "https://mbasic.facebook.com/AlArabiya"

CHECK_INTERVAL = 300  # 5 دقائق

HASH_FILE = "last_post_hash.txt"
STATE_FILE = "state.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

app = Flask(__name__)

# =========================
# أدوات عامة
# =========================
def delete_webhook():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    r = requests.post(url, timeout=20)
    print("Webhook deleted:", r.text)


def fetch_page(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        print("Fetch error:", e)
    return None


def telegram_request(method, data):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    return requests.post(url, data=data, timeout=20)


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": False
    }
    if keyboard:
        data["reply_markup"] = keyboard
    telegram_request("sendMessage", data)


def main_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "🆕 الجديد", "callback_data": "new"},
                {"text": "📊 الحالة", "callback_data": "status"}
            ]
        ]
    }


def get_last_hash():
    return open(HASH_FILE).read().strip() if os.path.exists(HASH_FILE) else ""


def save_hash(h):
    open(HASH_FILE, "w").write(h)


def save_state(text):
    open(STATE_FILE, "w", encoding="utf-8").write(text)


def get_state():
    return open(STATE_FILE, encoding="utf-8").read() if os.path.exists(STATE_FILE) else "لا توجد بيانات بعد"


# =========================
# استخراج آخر منشور
# =========================
def extract_latest_post():
    html = fetch_page(FACEBOOK_PAGE)
    if not html:
        return None, None

    m = re.search(r'/story\.php\?story_fbid=(\d+)&id=(\d+)', html)
    if not m:
        return None, None

    post_url = f"https://www.facebook.com/story.php?story_fbid={m.group(1)}&id={m.group(2)}"
    post_html = fetch_page("https://mbasic.facebook.com" + m.group(0))

    text = ""
    if post_html:
        t = re.search(r'<div[^>]*>(.*?)</div>', post_html, re.S)
        if t:
            text = unescape(re.sub(r'<[^>]+>', '', t.group(1))).strip()

    return post_url, text


# =========================
# المراقبة التلقائية
# =========================
def auto_monitor():
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        post_url, text = extract_latest_post()

        if post_url:
            h = hashlib.sha1((post_url + text).encode()).hexdigest()
            if h != get_last_hash():
                save_hash(h)
                send_message(
                    OWNER_CHAT_ID,
                    f"🆕 منشور جديد تلقائيًا\n\n{text[:1200]}\n\n🔗 {post_url}",
                    main_keyboard()
                )
                save_state(f"✔️ آخر فحص: {now}\n🆕 تم العثور على منشور جديد")
            else:
                save_state(f"✔️ آخر فحص: {now}\nℹ️ لا يوجد منشور جديد")
        else:
            save_state(f"⚠️ آخر فحص: {now}\nلم يتم العثور على منشورات")

        time.sleep(CHECK_INTERVAL)


# =========================
# أوامر تلجرام + الأزرار
# =========================
def telegram_listener():
    print("✅ Telegram listener started")
    offset = 0

    while True:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=40
            ).json()

            for update in r.get("result", []):
                offset = update["update_id"] + 1

                # رسالة نصية
                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")

                    if chat_id != OWNER_CHAT_ID:
                        continue

                    if text in ("/start", "start", "Start"):
                        send_message(
                            chat_id,
                            "✅ البوت يعمل ويراقب صفحة العربية تلقائيًا\n\nاختر من الأزرار 👇",
                            main_keyboard()
                        )

                # زر شفاف
                if "callback_query" in update:
                    cb = update["callback_query"]
                    chat_id = cb["message"]["chat"]["id"]
                    data = cb["data"]

                    if chat_id != OWNER_CHAT_ID:
                        continue

                    if data == "new":
                        post_url, text = extract_latest_post()
                        if not post_url:
                            send_message(chat_id, "❌ لم أستطع جلب أي منشور", main_keyboard())
                        else:
                            h = hashlib.sha1((post_url + text).encode()).hexdigest()
                            if h == get_last_hash():
                                send_message(chat_id, "ℹ️ هذا المنشور تم جلبه مسبقًا", main_keyboard())
                            else:
                                save_hash(h)
                                send_message(
                                    chat_id,
                                    f"🆕 منشور جديد (يدوي)\n\n{text[:1200]}\n\n🔗 {post_url}",
                                    main_keyboard()
                                )

                    elif data == "status":
                        send_message(chat_id, "📊 حالة المراقبة:\n\n" + get_state(), main_keyboard())

        except Exception as e:
            print("Telegram error:", e)

        time.sleep(5)


# =========================
# Flask (لـ Render)
# =========================
@app.route("/")
def home():
    return jsonify({"status": "Bot is running"})


# =========================
# تشغيل
# =========================
if __name__ == "__main__":
    delete_webhook()  # 🔥 حل مشكلة /start نهائيًا

    threading.Thread(target=auto_monitor, daemon=True).start()
    threading.Thread(target=telegram_listener, daemon=True).start()

    app.run(host="0.0.0.0", port=8080)
