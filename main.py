import sys, os
#sys.path.insert(0, '/opt/render/project/src')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
import threading
import logging
from flask import Flask
from telebot import TeleBot
from config import TOKEN
from utils.decorators import admin_only
from utils.exception_handler import safe_execution
from handlers import user_commands, admin_commands, admin_broadcast, admin_supply_menu, admin_fulfill_exact_menu


# === הגדרות לוגים בסיסיות ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# === אתחול האפליקציה והבוט ===
bot = TeleBot(TOKEN)
app = Flask(__name__)

# === רישום הפקודות מהמודולים ===
try:
    user_commands.register(bot)
    admin_commands.register(bot)
    logger.info("✅ כל הפקודות נרשמו בהצלחה.")
except Exception as e:
    logger.exception("❌ שגיאה ברישום פקודות: %s", e)

# === מסך חיים לשירות ה־Render ===
@app.route('/')
def home():
    return "✅ EggBot PRO is alive and running!"

# === הפעלת הבוט בלולאה אינסופית בתוך Thread נפרד ===
# def run_bot():
#     logger.info("🤖 EggBot PRO v2 is starting polling...")
#     try:
#         bot.infinity_polling(timeout=60, long_polling_timeout=40)
#     except Exception as e:
#         logger.exception("❌ שגיאה בהפעלת הבוט: %s", e)

import time  # ודא שהשורה הזו למעלה ב-main.py

def run_bot():
    bot.remove_webhook(drop_pending_updates=True)
    logger.info("🤖 EggBot PRO v2 is starting polling...")
    try:
        bot.remove_webhook()
        bot.infinity_polling(timeout=60, long_polling_timeout=40)
    except Exception as e:
        logger.exception("❌ שגיאה בהפעלת הבוט: %s", e)
        time.sleep(15)
        run_bot()


# === נקודת כניסה עיקרית ===
if __name__ == '__main__':
    logger.info("🚀 Starting Flask + Telegram bot combo service...")
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
