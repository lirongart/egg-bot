from keyboards.user_menu import main_menu
from keyboards.admin_menu import admin_main_menu
from utils.validators import is_admin
from config import DATABASE_URL
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import psycopg2

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cursor = conn.cursor()


def register(bot):

    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        bot.reply_to(message, "ברוך הבא! אנא הזן את שמך:")
        bot.register_next_step_handler(message, register_user)
        
    def register_user(message):
        name = message.text
        user_id = message.from_user.id
    
        # 1. הוספה לטבלת users
        cursor.execute('INSERT INTO users (id, name, balance) VALUES (%s, %s, %s)', (user_id, name, 0))
        conn.commit()
    
        # 2. הוספה לטבלת bit_users
        cursor.execute("""
            INSERT INTO bit_users (user_id, bit_name)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET bit_name = EXCLUDED.bit_name
        """, (user_id, name))

    
        # 3. הצגת תפריט מותאם
        if is_admin(user_id):
            bot.send_message(user_id, f"הרשמה הושלמה, {name}!", reply_markup=admin_main_menu())
        else:
            bot.send_message(user_id, f"הרשמה הושלמה, {name}!", reply_markup=main_menu())
    
        # 4. הצגת ה־user_id למשתמש
        bot.send_message(user_id, f"ℹ️ ה־Telegram ID שלך הוא: {user_id}")
    
        # 5. עדכון למנהל
        bot.send_message(ADMIN_ID, f"🆕 משתמש חדש נרשם:\nשם: {name}\nID: {user_id}\nנוסף ל־bit_users")

        
    @bot.message_handler(commands=['menu'])
    def menu(message):
        if is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "תפריט מנהל:", reply_markup=admin_main_menu())
        else:
            bot.send_message(message.chat.id, "בחר פעולה:", reply_markup=main_menu())

    def ask_quantity_step(message, size):
        user_id = message.from_user.id
        bot.send_message(user_id, f"איזו כמות של תבניות {size} תרצה להזמין?")
        bot.register_next_step_handler(message, lambda msg: process_order_step(msg, size))

    def process_order_step(message, size):
        try:
            quantity = int(message.text)
            user_id = message.from_user.id
            cursor.execute("SELECT balance, name FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            if not result:
                bot.send_message(user_id, "משתמש לא נמצא.")
                return
    
            balance, name = result
            price = 36 if size == 'L' else 39
            total = quantity * price
    
            if balance < total:
                bot.send_message(user_id, f"אין לך מספיק יתרה.\nעלות ההזמנה: {total} ש\"ח\nהיתרה שלך: {balance} ש\"ח\n\n לטעינת יתרה אנא העבר כסף ב bit לשמואל ורולקר/n/n בטלפון: 0547665847")
                return
    
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO orders (user_id, name, quantity, size, ordered_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, name, quantity, size, now))
    
            cursor.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (total, user_id))
            conn.commit()
    
            bot.send_message(user_id, f"הזמנה התקבלה: {quantity} תבניות מידה {size}\nחיוב: {total} ש\"ח")
    
        except Exception as e:
            bot.send_message(message.chat.id, f"שגיאה: {e}")
    
    @bot.message_handler(func=lambda m: m.text == "הזמנת תבניות")
    def order_eggs(message):
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row(KeyboardButton("L"), KeyboardButton("XL"))
        bot.send_message(message.chat.id, "בחר מידה:", reply_markup=markup)
        bot.register_next_step_handler(message, lambda msg: ask_quantity_step(msg, msg.text))


    @bot.message_handler(func=lambda m: m.text == "בדיקת יתרה")
    def check_balance(message):
        user_id = message.from_user.id
        cursor.execute("SELECT balance, name FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
    
        if not result:
            bot.send_message(user_id, "לא נמצא משתמש.")
            return
    
        balance, name = result
    
        # סך התחייבות להזמנות שעדיין לא סופקו
        cursor.execute("""
            SELECT size, quantity, fulfilled_quantity FROM orders
            WHERE user_id = %s AND fulfilled = 0
        """, (user_id,))
        orders = cursor.fetchall()
    
        size_prices = {'L': 36, 'XL': 39}
        pending_total = 0
        for size, quantity, fulfilled_qty in orders:
            remaining_qty = quantity - (fulfilled_qty or 0)
            pending_total += remaining_qty * size_prices.get(size, 0)
    
        available_balance = balance - pending_total
    
        response = f"💳 {name}, הנה פרטי היתרה שלך:\n"
        response += f"• יתרה כוללת: {balance:.2f} ש\"ח\n"
        response += f"• סכום שממתין להזמנות פתוחות: {pending_total:.2f} ש\"ח\n"
        #response += f"• זמין להזמנה חדשה: {available_balance:.2f} ש\"ח"
    
        bot.send_message(user_id, response)
    

    @bot.message_handler(func=lambda m: m.text == "ההזמנות שלי")
    def my_orders(message):
        user_id = message.from_user.id
        cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            bot.send_message(user_id, "לא נמצא משתמש.")
            return
        name = result[0]
    
        cursor.execute("""
            SELECT id, size, quantity, ordered_date
            FROM orders
            WHERE user_id = %s AND fulfilled = 0
            ORDER BY ordered_date
        """, (user_id,))
        orders = cursor.fetchall()
    
        if not orders:
            bot.send_message(user_id, "אין לך הזמנות ממתינות.")
            return
    
        response = f"👤 היי {name}, הנה ההזמנות הממתינות שלך:\n\n"
        for oid, size, qty, ordered_date in orders:
            price = 36 if size == 'L' else 39
            total = qty * price
            response += (
                f"📦 הזמנה #{oid}\n"
                f"🥚 כמות: {qty} ({size})\n"
                f"💰 עלות משוערת: {total} ש\"ח\n"
                f"🗓️ הוזמנה בתאריך: {ordered_date}\n\n"
            )
    
        bot.send_message(user_id, response)
        
    # 📌 שליחת קבלה (בשלב זה לא פעיל בתפריט)
    # @bot.message_handler(func=lambda m: m.text == "שליחת קבלה")
    # def receipt_placeholder(message):
    #     bot.send_message(message.chat.id, "📷 הפיצ'ר של שליחת קבלה יתוסף בקרוב.")

    
