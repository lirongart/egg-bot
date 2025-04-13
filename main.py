from telebot import TeleBot
from config import TOKEN
from handlers import user_commands, admin_commands
from flask import Flask
import threading
import os

bot = TeleBot(TOKEN)
app = Flask(__name__)

# רישום הפקודות
user_commands.register(bot)
admin_commands.register(bot)

@app.route('/')
def home():
    return "EggBot PRO is alive!"

def run_bot():
    print("EggBot PRO v2 is running...")
    bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
