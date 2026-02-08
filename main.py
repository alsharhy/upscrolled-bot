from playwright.sync_api import sync_playwright
from config import *
from telegram import send_telegram_notification
from storage import is_already_posted, save_post


def get_latest_facebook_post():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(FACEBOOK_PAGE)
        page.wait_for_timeout(WAIT_TIME)

        post = page.locator("div[data-ad-preview='message']").first
        text = post.inner_text().strip()

        browser.close()
        return text


def post_to_upscrolled(content):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://upscrolled.com/login")
        page.wait_for_timeout(WAIT_TIME)

        page.fill("input[type='email']", UPSCROLLED_EMAIL)
        page.fill("input[type='password']", UPSCROLLED_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_timeout(WAIT_TIME)

        page.goto("https://upscrolled.com")
        page.wait_for_timeout(WAIT_TIME)

        page.fill("textarea", content)
        page.click("button:has-text('Post')")
        page.wait_for_timeout(WAIT_TIME)

        page.goto("https://upscrolled.com/profile")
        page.wait_for_timeout(WAIT_TIME)

        post_link = page.locator("a[href*='/post/']").first.get_attribute("href")

        browser.close()
        return post_link


if __name__ == "__main__":
    post_text = get_latest_facebook_post()

    if is_already_posted(post_text):
        send_telegram_notification("ℹ️ لا يوجد خبر جديد (تم نشره سابقًا)")
        exit()

    post_url = post_to_upscrolled(post_text)
    save_post(post_text)

    message = (
        "✅ <b>تم نشر خبر جديد على أبسكرولد</b>\n\n"
        f"📝 <b>النص:</b>\n{post_text[:1200]}\n\n"
        f"🔗 <b>الرابط:</b>\n{post_url}"
    )

    send_telegram_notification(message)