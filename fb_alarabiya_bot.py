import requests, re, hashlib, os, time, threading
from html import unescape
from flask import Flask

app = Flask(__name__)

FACEBOOK_PAGE = "https://www.facebook.com/AlArabiya"
TELEGRAM_BOT_TOKEN = "7522002533:AAEQzquyk1AOV71gtyljXeMHfCBJyKv3iE0"
TELEGRAM_CHAT_ID = "5442141079"
HASH_FILE = "last_post_hash.txt"
CHECK_INTERVAL = 300

HEADERS = {"User-Agent": "Mozilla/5.0"}

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

def monitor():
    while True:
        html = fetch_page(FACEBOOK_PAGE)
        if html:
            m = re.search(r'/story\.php\?story_fbid=(\d+)&id=(\d+)', html)
            if m:
                post_url = f"https://www.facebook.com/story.php?story_fbid={m.group(1)}&id={m.group(2)}"
                post_html = fetch_page("https://mbasic.facebook.com" + m.group(0))
                text = ""
                if post_html:
                    t = re.search(r'<div[^>]*>(.*?)</div>', post_html, re.S)
                    if t:
                        text = unescape(re.sub(r'<[^>]+>', '', t.group(1))).strip()

                h = hashlib.sha1((post_url + text).encode()).hexdigest()
                if h != get_last_hash():
                    save_hash(h)
                    send_telegram(f"🆕 منشور جديد\n\n{text[:1000]}\n\n{post_url}")
        time.sleep(CHECK_INTERVAL)

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    threading.Thread(target=monitor, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)
