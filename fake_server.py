from flask import Flask
import threading
import telebot
import os
from datetime import datetime
import psycopg2

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL")

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

@bot.message_handler(func=lambda m: m.text == 'הפקדה לקופה')
def deposit_prompt(message):
    bot.send_message(message.chat.id, "כמה כסף אתה מפקיד?")
    bot.register_next_step_handler(message, handle_deposit)

def handle_deposit(message):
    try:
        amount = float(message.text)
        user_id = message.from_user.id
        cursor.execute('UPDATE users SET balance = balance + %s WHERE id = %s', (amount, user_id))
        cursor.execute('SELECT name FROM users WHERE id = %s', (user_id,))
        name = cursor.fetchone()[0]
        bot.send_message(user_id, f'הפקדה של {amount} ש"ח עודכנה בהצלחה.')
        if ADMIN_ID:
            bot.send_message(ADMIN_ID, f'🟢 {name} הפקיד {amount} ש"ח לקופה.')
    except:
        bot.send_message(message.chat.id, "נא להזין סכום תקין.")
    show_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == 'הזמנת תבניות')
def order_prompt(message):
    user_id = message.from_user.id
    cursor.execute('SELECT balance FROM users WHERE id = %s', (user_id,))
    result = cursor.fetchone()
    if not result or result[0] <= 0:
        bot.send_message(user_id, "אין לך מספיק יתרה להזמנה. בצע הפקדה תחילה.")
        show_menu(user_id)
        return
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('L', 'XL', 'ביטול')
    bot.send_message(user_id, "בחר מידה להזמנה:", reply_markup=markup)
    bot.register_next_step_handler(message, ask_quantity)

def ask_quantity(message):
    if message.text == 'ביטול':
        show_menu(message.chat.id)
        return
    size = message.text
    if size not in ['L', 'XL']:
        bot.send_message(message.chat.id, "נא לבחור מידה חוקית (L או XL).")
        show_menu(message.chat.id)
        return
    bot.send_message(message.chat.id, "כמה תבניות תרצה להזמין?")
    bot.register_next_step_handler(message, lambda msg: confirm_order(msg, size))

def confirm_order(message, size):
    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError
        user_id = message.from_user.id
        cursor.execute('SELECT name, balance FROM users WHERE id = %s', (user_id,))
        name, balance = cursor.fetchone()
        price = 36 if size == 'L' else 39
        total = price * quantity
        if balance < total:
            bot.send_message(user_id, f'יתרה לא מספיקה. דרושים {total} ש"ח ויש לך {balance}.')
            show_menu(user_id)
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('INSERT INTO orders (user_id, name, quantity, size, ordered_date) VALUES (%s, %s, %s, %s, %s)', (user_id, name, quantity, size, now))
        cursor.execute('UPDATE users SET balance = balance - %s WHERE id = %s', (total, user_id))
        bot.send_message(user_id, f'הוזמן: {quantity} תבניות {size}. עלות: {total} ש"ח.')
        if ADMIN_ID:
            bot.send_message(ADMIN_ID, f"🔵 {name} הזמין {quantity} תבניות {size}")
    except:
        bot.send_message(message.chat.id, "נא להזין כמות תקינה.")
    show_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == 'ההזמנות שלי')
def my_orders(message):
    user_id = message.from_user.id

    # שליפת שם המשתמש
    cursor.execute('SELECT name FROM users WHERE id = %s', (user_id,))
    result = cursor.fetchone()
    name = result[0] if result else 'משתמש'

    # שליפת ההזמנה האחרונה
    cursor.execute('''
        SELECT id, size, quantity, fulfilled, fulfilled_quantity, ordered_date, fulfilled_date 
        FROM orders 
        WHERE user_id = %s 
        ORDER BY ordered_date DESC 
        LIMIT 1
    ''', (user_id,))
    order = cursor.fetchone()

    if not order:
        bot.send_message(user_id, "אין הזמנות.")
    else:
        oid, size, qty, fulfilled, f_qty, ordered_at, f_date = order
        price = 36 if size == 'L' else 39
        status = "סופק" if fulfilled else "ממתין"
        total = (f_qty if fulfilled else qty) * price

        # בניית הודעה
        response = f"👤 היי {name}!\n"
        response += f"📦 הזמנה מספר {oid}:\n"
        response += f"🔢 הוזמן: {qty} תבניות מידה {size}\n"
        response += f"💰 עלות: – {total} ש\"ח\n"
        response += f"🚚 סטטוס: {status}"

        bot.send_message(user_id, response)

    show_menu(user_id)


@bot.message_handler(func=lambda m: m.text == 'ניהול הזמנות' and m.from_user.id == ADMIN_ID)
def manage_orders(message):
    cursor.execute('SELECT id, name, size, quantity FROM orders WHERE fulfilled = 0 ORDER BY ordered_date')
    orders = cursor.fetchall()
    if not orders:
        bot.send_message(message.chat.id, "אין הזמנות ממתינות.")
    else:
        response = "הזמנות ממתינות:"
        for order_id, name, size, quantity in orders:
            response += f"#{order_id} - {name}: {quantity} ({size})\n"
        response += "להשלמת הזמנה, שלח:\n/fulfill order_id כמות_שסופקה"
        bot.send_message(message.chat.id, response)
    show_menu(message.chat.id)

@bot.message_handler(commands=['fulfill'])
def fulfill_order(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.send_message(user_id, "רק מנהל יכול לבצע פעולה זו.")
        return

    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(user_id, "פורמט שגוי. השתמש: /fulfill [מספר_הזמנה] [כמות_שסופקה]")
            return

        order_id = int(parts[1])
        fulfilled_quantity = int(parts[2])

        cursor.execute('SELECT user_id, name, quantity, size FROM orders WHERE id = %s AND fulfilled = 0', (order_id,))
        order = cursor.fetchone()

        if not order:
            bot.send_message(user_id, f"הזמנה מס' {order_id} לא נמצאה או כבר סופקה.")
            return

        customer_id, customer_name, ordered_quantity, size = order

        # 🔒 הגנת ערכים
        if fulfilled_quantity < 0:
            bot.send_message(user_id, "הכמות שסופקה לא יכולה להיות שלילית.")
            return

        if fulfilled_quantity > ordered_quantity:
            bot.send_message(user_id, f"הוזמנו רק {ordered_quantity} תבניות. לא ניתן לעדכן אספקה גבוהה יותר.")
            return
        
        if fulfilled_quantity == 0:
            #bot.send_message(user_id, f"הוזנה כמות אספקה 0 להזמנה #{order_id}. ההזמנה תישאר במצב ממתין.")
            print(">> 0 quantity detected")
            bot.send_message(user_id, "🟡 אספקה 0 — הודעה נשלחה")
            return

        price = PRICE_L if size == 'L' else PRICE_XL
        actual_cost = fulfilled_quantity * price
        original_cost = ordered_quantity * price
        refund = original_cost - actual_cost
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
            UPDATE orders 
            SET fulfilled = 1, fulfilled_quantity = %s, fulfilled_date = %s 
            WHERE id = %s
        ''', (fulfilled_quantity, now, order_id))

        if refund > 0:
            cursor.execute('UPDATE users SET balance = balance + %s WHERE id = %s', (refund, customer_id))

        conn.commit()

        bot.send_message(user_id, f"הזמנה #{order_id} עודכנה: {fulfilled_quantity}/{ordered_quantity} ({size})\n"
                                  f"חיוב סופי: {actual_cost} ש\"ח" +
                                  (f"\nזיכוי: {refund} ש\"ח" if refund > 0 else ""))

        bot.send_message(customer_id, f"הזמנתך #{order_id} סופקה: {fulfilled_quantity}/{ordered_quantity} תבניות {size}.\n"
                                      f"חיוב סופי: {actual_cost} ש\"ח" +
                                      (f"\nזיכוי לחשבונך: {refund} ש\"ח" if refund > 0 else ""))

    except ValueError:
        bot.send_message(user_id, "שגיאה בפורמט. השתמש: /fulfill [מספר_הזמנה] [כמות_שסופקה]")
    except Exception as e:
        bot.send_message(user_id, f"שגיאה: {str(e)}")


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
        summary_text += f'{name} - יתרה: {balance} ש"ח, בהמתנה: {spent} ש"ח, פנוי: {available} ש"ח'
    bot.send_message(message.chat.id, summary_text, parse_mode="Markdown")
    show_menu(message.chat.id)

def run_bot():
    print("Bot is starting...")
    bot.polling(none_stop=True)

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))




