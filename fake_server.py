# fake_server.py - Telegram Egg Bot PRO version with full admin features
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

def show_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('הפקדה לקופה', 'הזמנת תבניות')
    markup.row('בדיקת יתרה', 'ההזמנות שלי')
    if chat_id == ADMIN_ID:
        markup.row('ניהול הזמנות', 'סיכום כללי')
    bot.send_message(chat_id, ".", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    if not user:
        bot.reply_to(message, "ברוך הבא! אנא שלח את שמך:")
        bot.register_next_step_handler(message, register_user)
    else:
        show_menu(user_id)

def register_user(message):
    user_id = message.from_user.id
    name = message.text
    cursor.execute('INSERT INTO users (id, name, balance) VALUES (%s, %s, %s)', (user_id, name, 0))
    bot.send_message(user_id, f'ההרשמה הושלמה, {name}!')
    show_menu(user_id)

@bot.message_handler(commands=['ping'])
def ping(message):
    bot.reply_to(message, "פונג! הבוט פעיל.")

@bot.message_handler(commands=['menu'])
def menu(message):
    show_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == 'בדיקת יתרה')
def check_balance(message):
    user_id = message.from_user.id
    cursor.execute('SELECT balance FROM users WHERE id = %s', (user_id,))
    result = cursor.fetchone()
    if result:
        bot.send_message(user_id, f'היתרה שלך: {result[0]} ש"ח')
    else:
        bot.send_message(user_id, "לא נמצא משתמש.")
    show_menu(user_id)

@bot.message_handler(func=lambda m: m.text == 'ניהול הזמנות' and m.from_user.id == ADMIN_ID)
def manage_orders(message):
    cursor.execute('SELECT id, name, size, quantity FROM orders WHERE fulfilled = 0 ORDER BY ordered_date')
    orders = cursor.fetchall()
    if not orders:
        bot.send_message(message.chat.id, "אין הזמנות ממתינות.")
    else:
        response = "הזמנות ממתינות:\n"
        for order_id, name, size, quantity in orders:
            response += f"#{order_id} - {name}: {quantity} ({size})"
        response += "
להשלמת הזמנה, שלח:
/fulfill order_id כמות_שסופקה"
        bot.send_message(message.chat.id, response)
    show_menu(message.chat.id)

@bot.message_handler(commands=['fulfill'])
def fulfill_order(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        _, order_id, qty = message.text.split()
        order_id = int(order_id)
        qty = int(qty)
        cursor.execute('SELECT user_id, name, quantity, size FROM orders WHERE id = %s AND fulfilled = 0', (order_id,))
        data = cursor.fetchone()
        if not data:
            bot.send_message(message.chat.id, f"הזמנה #{order_id} לא קיימת או כבר סופקה.")
            return
        user_id, name, ordered_qty, size = data
        price = 36 if size == 'L' else 39
        actual_total = qty * price
        original_total = ordered_qty * price
        refund = original_total - actual_total
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE orders SET fulfilled = 1, fulfilled_quantity = %s, fulfilled_date = %s
            WHERE id = %s
        """, (qty, now, order_id))
        if refund > 0:
            cursor.execute('UPDATE users SET balance = balance + %s WHERE id = %s', (refund, user_id))
        bot.send_message(message.chat.id, f"הזמנה #{order_id} עודכנה. חיוב סופי: {actual_total} ש"ח.")
        bot.send_message(user_id, f"הזמנתך #{order_id} סופקה: {qty}/{ordered_qty} ({size})
סה"כ חיוב: {actual_total} ש"ח
זיכוי: {refund} ש"ח")
    except:
        bot.send_message(message.chat.id, "שימוש: /fulfill order_id כמות_שסופקה")

@bot.message_handler(func=lambda m: m.text == 'סיכום כללי' and m.from_user.id == ADMIN_ID)
def summary(message):
    cursor.execute('SELECT name, balance FROM users ORDER BY name')
    users = cursor.fetchall()
    cursor.execute('SELECT name, size, quantity FROM orders WHERE fulfilled = 0')
    orders = cursor.fetchall()
    summary_text = "*סיכום מצב הקופה:*"
    user_orders = {}
    size_prices = {'L': 36, 'XL': 39}
    for name, size, quantity in orders:
        price = size_prices.get(size, 0)
        user_orders[name] = user_orders.get(name, 0) + quantity * price
    for name, balance in users:
        spent = user_orders.get(name, 0)
        available = balance - spent
        summary_text += f"{name} - יתרה: {balance} ש"ח, בהמתנה: {spent} ש"ח, פנוי: {available} ש"ח
"
    bot.send_message(message.chat.id, summary_text, parse_mode="Markdown")
    show_menu(message.chat.id)

def run_bot():
    print("Bot is starting...")
    bot.polling(none_stop=True)

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
