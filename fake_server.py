from flask import Flask
import threading
import telebot
import os
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return f"Bot is alive! {datetime.now()}"

# ✅ כאן התוספת:
@bot.message_handler(commands=['start'])
def start(message):
    print(f"/start received from {message.from_user.id}")
    bot.reply_to(message, "היי! הבוט עובד 🔥 נסיך שאתה פה.")

@bot.message_handler(commands=['ping'])
def ping(message):
    bot.reply_to(message, "פונג! הבוט פעיל.")

def run_bot():
    print("Bot is starting...")
    bot.polling(none_stop=True)

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
