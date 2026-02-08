import requests, re, hashlib, os, time, threading
from html import unescape
from datetime import datetime
from flask import Flask

# ====================
# إعدادات
# ====================
FACEBOOK_PAGE = "https://mbasic.facebook.com/AlArabiya"

TELEGRAM_BOT_TOKEN = "7522002533:AAEQzquyk1AOV71gtyljXeMHfCBJyKv3iE0"
TELEGRAM_CHAT_ID = "5442141079"

HASH_FILE = "last_post_hash.txt"
STATE_FILE = "state.txt"

CHECK_INTERVAL = 300  # 5 دقائق
HEADERS = {"User-Agent": "Mozilla/5.0"}

app = Flask(__name__)

# ====================
# أدوات مساعدة
# ====================
def fetch_page(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return None


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})


def get_last_hash():
    return open(HASH_FILE).read().strip() if os.path.exists(HASH_FILE) else ""


def save_hash(h):
    open(HASH_FILE, "w").write(h)


def save_state(text):
    open(STATE_FILE, "w", encoding="utf-8").write(text)


def get_state():
    return open(STATE_FILE).read() if os.path.exists(STATE_FILE) else "لا توجد بيانات بعد"


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

# ====================
# المراقبة التلقائية
# ====================
def auto_monitor():
    while True:
        post_url, text = extract_latest_post()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if post_url:
            h = hashlib.sha1((post_url + text).encode()).hexdigest()
            if h != get_last_hash():
                save_hash(h)
                send_telegram(f"🆕 منشور جديد تلقائيًا\n\n{text[:1200]}\n\n{post_url}")
                save_state(f"✔️ آخر فحص: {now}\n🆕 تم العثور على منشور جديد")
            else:
                save_state(f"✔️ آخر فحص: {now}\nℹ️ لا يوجد منشور جديد")
        else:
            save_state(f"⚠️ آخر فحص: {now}\nلم يتم العثور على منشورات")

        time.sleep(CHECK_INTERVAL)

# ====================
# الاستماع لأوامر تلجرام
# ====================
def telegram_listener():
    offset = 0
    while True:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        r = requests.get(url, params={"offset": offset, "timeout": 30}).json()

        for update in r.get("result", []):
            offset = update["update_id"] + 1
            msg = update.get("message", {}).get("text", "").strip()

            if msg == "الجديد":
                post_url, text = extract_latest_post()
                if not post_url:
                    send_telegram("❌ لم أستطع جلب أي منشور")
                    continue

                h = hashlib.sha1((post_url + text).encode()).hexdigest()
                if h == get_last_hash():
                    send_telegram("ℹ️ هذا المنشور تم جلبه مسبقًا")
                else:
                    save_hash(h)
                    send_telegram(f"🆕 منشور جديد (يدوي)\n\n{text[:1200]}\n\n{post_url}")

            elif msg == "الحالة":
                send_telegram("📊 حالة المراقبة:\n\n" + get_state())

        time.sleep(5)

# ====================
# Flask (عشان Render)
# ====================
@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    threading.Thread(target=auto_monitor, daemon=True).start()
    threading.Thread(target=telegram_listener, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
