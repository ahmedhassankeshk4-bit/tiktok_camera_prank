FILES
app.py
index.html
requirements.txt

Render:
Build: pip install -r requirements.txt
Start: gunicorn --workers 1 app:app

Environment variables:
BOT_TOKEN = Telegram bot token
SITE_URL = your Render https URL, e.g. https://my-prank.onrender.com
ADMIN_CHAT_ID = your Telegram chat id
WEBHOOK_SECRET = any long random string

Use /id in the bot after deployment to get your chat ID.
