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

def run_bot():
    print("Bot is starting...")
    bot.polling(none_stop=True)

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
