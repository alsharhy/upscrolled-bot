import requests
import re
import hashlib
import os
from html import unescape

# ====================
# الإعدادات
# ====================
FACEBOOK_PAGE = "https://mbasic.facebook.com/AlArabiya"
TELEGRAM_BOT_TOKEN = "7522002533:AAEQzquyk1AOV71gtyljXeMHfCBJyKv3iE0"
TELEGRAM_CHAT_ID = "5442141079"

HASH_FILE = "last_post_hash.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ====================
# دوال مساعدة
# ====================
def fetch_page(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return None


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": False
    }
    requests.post(url, data=data)


def get_last_hash():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def save_hash(h):
    with open(HASH_FILE, "w", encoding="utf-8") as f:
        f.write(h)

# ====================
# جلب آخر منشور
# ====================
html = fetch_page(FACEBOOK_PAGE)

if not html:
    send_telegram("⚠️ فشل جلب صفحة فيسبوك")
    exit()

match = re.search(r'/story\.php\?story_fbid=([0-9]+)&id=([0-9]+)', html)

if not match:
    send_telegram("⚠️ لم يتم العثور على منشور")
    exit()

story_fbid, page_id = match.groups()
post_url = f"https://www.facebook.com/story.php?story_fbid={story_fbid}&id={page_id}"

# ====================
# جلب نص المنشور
# ====================
post_html = fetch_page("https://mbasic.facebook.com" + match.group(0))

text = ""
if post_html:
    text_match = re.search(r'<div[^>]*>(.*?)</div>', post_html, re.S)
    if text_match:
        text = unescape(
            re.sub(r'<[^>]+>', '', text_match.group(1))
        ).strip()

# ====================
# منع التكرار
# ====================
current_hash = hashlib.sha1((post_url + text).encode("utf-8")).hexdigest()
last_hash = get_last_hash()

if current_hash == last_hash:
    # لا يوجد جديد
    exit()

save_hash(current_hash)

# ====================
# إرسال إشعار تلجرام
# ====================
message = "🆕 منشور جديد من صفحة العربية\n\n"

if text:
    message += "📝 النص:\n" + text[:1500] + "\n\n"

message += "🔗 الرابط:\n" + post_url

send_telegram(message)
