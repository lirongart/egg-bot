from flask import Flask
import threading
import telebot
import os
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL")

import psycopg2
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    name TEXT,
    balance REAL DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    name TEXT,
    quantity INTEGER,
    size TEXT,
    ordered_date TEXT,
    fulfilled INTEGER DEFAULT 0,
    fulfilled_quantity INTEGER DEFAULT 0,
    fulfilled_date TEXT
)
""")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return f"Bot is alive! {datetime.now()}"

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    if not user:
        bot.reply_to(message, "ברוך הבא! אנא שלח את שמך:")
        bot.register_next_step_handler(message, register_user)
    else:
        bot.reply_to(message, "כבר נרשמת! שלח /menu להמשך")

def register_user(message):
    user_id = message.from_user.id
    name = message.text
    cursor.execute('INSERT INTO users (id, name, balance) VALUES (%s, %s, %s)', (user_id, name, 0))
    bot.send_message(user_id, f"הרשמה הושלמה, {name}! שלח /menu כדי להתחיל.")

@bot.message_handler(commands=['ping'])
def ping(message):
    bot.reply_to(message, "פונג! הבוט פעיל.")

@bot.message_handler(commands=['menu'])
def menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('הפקדה לקופה', 'הזמנת תבניות')
    markup.row('בדיקת יתרה')
    if message.from_user.id == ADMIN_ID:
        markup.row('ניהול הזמנות', 'סיכום כללי')
    bot.send_message(message.chat.id, "בחר פעולה:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'בדיקת יתרה')
def check_balance(message):
    user_id = message.from_user.id
    cursor.execute('SELECT balance FROM users WHERE id = %s', (user_id,))
    result = cursor.fetchone()
    if result:
        bot.send_message(user_id, f"היתרה שלך: {result[0]} ש"ח")
    else:
        bot.send_message(user_id, "לא נמצא משתמש.")

def run_bot():
    print("Bot is starting...")
    bot.polling(none_stop=True)

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
