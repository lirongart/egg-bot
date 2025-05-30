from keyboards.user_menu import main_menu
from keyboards.admin_menu import admin_main_menu
from utils.validators import is_admin
from utils.logger import log
from config import ADMIN_ID
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from utils.db_utils import execute_query, get_db_connection
from utils.input_validators import sanitize_name, validate_quantity, validate_size
from utils.exception_handler import safe_execution
from utils.thread_safety import user_lock
from datetime import datetime

def register(bot):

    @bot.message_handler(commands=['start'])
    @safe_execution("שגיאה בתחילת רישום")
    def start(message):
        user_id = message.from_user.id
        bot.reply_to(message, "ברוך הבא! אנא הזן את שמך:")
        bot.register_next_step_handler(message, register_user)

    @safe_execution("שגיאה ברישום משתמש")
    def register_user(message):
        user_id = message.from_user.id
        new_name = sanitize_name(message.text.strip())
    
        # 🎯 שליפת שם קודם מהטבלה (אם קיים)
        existing = execute_query("SELECT name FROM users WHERE id = %s",(user_id,),fetch="one")
        old_name = existing[0] if existing else None
    
        # 🔁 הכנסת/עדכון טבלת users
        execute_query("""
            INSERT INTO users (id, name, balance)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
        """, (user_id, new_name, 0))
    
        # 🔁 הכנסת/עדכון טבלת bit_users
        execute_query("""
            INSERT INTO bit_users (user_id, bit_name)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET bit_name = EXCLUDED.bit_name
        """, (user_id, new_name))
    
        # ✏️ הודעה למשתמש אם השם עודכן
        if old_name and old_name != new_name:
            print(f"old={old_name}, new={new_name}")
            bot.send_message(user_id, f"✏️ שמך עודכן מ־{old_name} ל־{new_name}.")
    
        # ✅ תפריט מותאם לפי הרשאות
        if is_admin(user_id):
            bot.send_message(user_id, f"הרשמה או עדכון הושלמו בהצלחה, {new_name}!", reply_markup=admin_main_menu())
        else:
            bot.send_message(user_id, f"הרשמה או עדכון הושלמו בהצלחה, {new_name}!", reply_markup=main_menu())
    
        # 🆔 הצגת מזהה טלגרם
        bot.send_message(user_id, f"ℹ️ ה־Telegram ID שלך הוא: {user_id}")
    
        # 📬 עדכון למנהל
        if user_id != ADMIN_ID:
            if old_name and old_name != new_name:
                log(f"[USER UPDATE] המשתמש {user_id} עדכן את שמו מ־{old_name} ל־{new_name}", category="admin")
            else:
                log(f"[USER REGISTER] משתמש חדש: {user_id}, שם: {new_name}", category="admin")
    
            bot.send_message(ADMIN_ID,
                f"📬 משתמש {'עודכן' if old_name else 'נרשם'}:\nשם: {new_name}\nID: {user_id}\nעודכן בטבלאות users ו־bit_users")

    @bot.message_handler(commands=['menu'])
    def menu(message):
        if is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "תפריט מנהל:", reply_markup=admin_main_menu())
        else:
            bot.send_message(message.chat.id, "בחר פעולה:", reply_markup=main_menu())

    @bot.message_handler(func=lambda m: m.text == "❌ ביטול ההזמנות שלי")
    @user_lock("order")
    @safe_execution("שגיאה בטעינת תפריט ביטול ההזמנות")
    def show_cancel_menu(message):
        user_id = message.from_user.id
        cursor = execute_query(
            "SELECT id, size, quantity FROM orders WHERE user_id = %s AND fulfilled = 0",
            (user_id,), fetch='all'
        )
    
        if not cursor:
            bot.send_message(user_id, "אין הזמנות ממתינות לביטול.")
            return
    
        from keyboards.user_cancel_menu import build_cancel_menu
        bot.send_message(user_id, "בחר את ההזמנה שברצונך לבטל:", reply_markup=build_cancel_menu(cursor))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
    @user_lock("order")
    @safe_execution("שגיאה בביטול ההזמנה")
    def cancel_selected_order(call):
        order_id = int(call.data.split("_")[2])
        user_id = call.from_user.id
        
        order = execute_query(
            "SELECT quantity, size FROM orders WHERE id = %s AND user_id = %s AND fulfilled = 0",
            (order_id, user_id), fetch='one'
        )
    
        if not order:
            bot.answer_callback_query(call.id, "ההזמנה כבר בוטלה או סופקה.")
            return
    
        qty, size = order
        price = 36 if size == "L" else 39
        refund = qty * price
    
        execute_query("DELETE FROM orders WHERE id = %s", (order_id,))
        execute_query("UPDATE users SET balance = balance + %s WHERE id = %s", (refund, user_id))
    
        log(f"[USER CANCEL] {user_id} ביטל הזמנה #{order_id}, זיכוי {refund} ש\"ח")
    
        bot.send_message(user_id, f"❌ הזמנתך #{order_id} בוטלה.\n💸 היתרה זוכתה ב־{refund} ש\"ח.")



    @bot.message_handler(func=lambda m: m.text == "הזמנת תבניות")
    def order_eggs(message):
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row(KeyboardButton("L"), KeyboardButton("XL"))
        sent = bot.send_message(message.chat.id, "בחר מידה:", reply_markup=markup)
        bot.register_next_step_handler(sent, lambda msg: ask_quantity_step(msg, msg.text))


    @safe_execution("שגיאה בבדיקת המידה")
    def ask_quantity_step(message, size):
        user_id = message.from_user.id
        valid_size = validate_size(size)
        if not valid_size:
            bot.send_message(user_id, "❌ מידה לא חוקית.\nנא לבחור רק 'L' או 'XL'.", reply_markup=main_menu())
            return
    
        sent = bot.send_message(user_id, f"איזו כמות של תבניות {valid_size} תרצה להזמין?")
        bot.register_next_step_handler(sent, lambda msg: process_order_step(msg, valid_size))


    @user_lock("order")
    @safe_execution("שגיאה בביצוע ההזמנה")
    def process_order_step(message, size):
        quantity = validate_quantity(message.text)
        if quantity is None:
            bot.send_message(message.chat.id, "❌ נא להזין מספר חיובי שלם בלבד.", reply_markup=main_menu())
            return
    
        user_id = message.from_user.id
        user_data = execute_query(
            "SELECT balance, name FROM users WHERE id = %s",
            (user_id,), fetch="one"
        )
    
        if not user_data:
            bot.send_message(user_id, "משתמש לא נמצא.", reply_markup=main_menu())
            return
    
        balance, name = user_data
        price = 36 if size == 'L' else 39
        total = quantity * price
    
        if balance < total:
            bot.send_message(user_id,
                             f"אין לך מספיק יתרה.\nעלות ההזמנה: {total} ש\"ח\nהיתרה שלך: {balance} ש\"ח",
                             reply_markup=main_menu())
            return
    
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("BEGIN")
    
                    cursor.execute("""
                        INSERT INTO orders (user_id, name, quantity, size, ordered_date)
                        VALUES (%s, %s, %s, %s, %s) RETURNING id
                    """, (user_id, name, quantity, size, now))
                    order_id = cursor.fetchone()[0]
    
                    cursor.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (total, user_id))
                    cursor.execute("COMMIT")
    
                    bot.send_message(user_id,
                                     f"✅ הזמנה #{order_id} התקבלה: {quantity} תבניות מידה {size}\n"
                                     f"💰 חיוב: {total} ש\"ח",
                                     reply_markup=main_menu())
                    log(f"[ORDER] משתמש {user_id} הזמין {quantity} ({size}) - חיוב {total} ש\"ח")
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    raise


    @bot.message_handler(func=lambda m: m.text == "בדיקת יתרה")
    @user_lock("payment")
    @safe_execution("שגיאה בבדיקת יתרה")
    def check_balance(message):
        user_id = message.from_user.id
        balance = execute_query(
            "SELECT balance FROM users WHERE id = %s",
            (user_id,),
            fetch="one"
        )
        if balance:
            bot.send_message(user_id, f"💰 היתרה שלך: {balance[0]:.2f} ש\"ח")
        else:
            bot.send_message(user_id, "❌ לא נמצאה יתרה.")

    @bot.message_handler(func=lambda m: m.text == "ההזמנות שלי")
    @safe_execution("שגיאה בשליפת הזמנות")
    def my_orders(message):
        user_id = message.from_user.id
        name_result = execute_query("SELECT name FROM users WHERE id = %s", (user_id,), fetch='one')
        if not name_result:
            bot.send_message(user_id, "❌ לא נמצא משתמש.")
            return

        name = name_result[0]
        orders = execute_query("""
            SELECT id, size, quantity, ordered_date
            FROM orders
            WHERE user_id = %s AND fulfilled = 0
            ORDER BY ordered_date
        """, (user_id,), fetch='all')

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
