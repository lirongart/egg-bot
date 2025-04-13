from config import ADMIN_ID, DATABASE_URL
from keyboards.admin_menu import admin_main_menu
from utils.logger import log
import psycopg2
from datetime import datetime
import re

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cursor = conn.cursor()

pending_bit_payment = {}

def register(bot):
    # ⬅️ כניסה לתפריט הניהול (admin)
    @bot.message_handler(commands=['admin'])
    def admin_entry(message):
        if message.from_user.id != ADMIN_ID:
            return
        bot.send_message(message.chat.id, "תפריט ניהול:", reply_markup=admin_main_menu())

    # ⬅️ התחלת תהליך הדבקת הודעת bit (כפתור הפקדה מ־bit)
    @bot.message_handler(func=lambda m: m.text == "הפקדה מ־bit" and m.from_user.id == ADMIN_ID)
    def bit_deposit(message):
        bot.send_message(message.chat.id, "📨 הדבק עכשיו את הודעת ה־SMS שקיבלת מ־bit.")
        pending_bit_payment[message.chat.id] = True

    # ⬅️ קליטת הודעת ה־bit והוצאת פרטים ממנה (סכום, שם, קישור)
    @bot.message_handler(func=lambda m: pending_bit_payment.get(m.chat.id) and m.from_user.id == ADMIN_ID)
    def handle_bit_sms(message):
        pending_bit_payment.pop(message.chat.id, None)
        text = re.sub(r'[\n\u200f\u00a0]', ' ', message.text).strip()

        amount_match = re.search(r'(\d+(?:\.\d+)?)\s*ש[״"]?ח', text)
        name_match = re.search(r'מחכים לך מ(.*?)\s*באפליקציית bit', text)
        url_match = re.search(r'(https://www\.bitpay\.co\.il/app/transaction-info\?i=\S+)', text)

        if not (amount_match and name_match and url_match):
            bot.send_message(message.chat.id, "⚠️ לא זוהתה הודעת bit תקינה. ודא שהעתקת את כל ההודעה כולל שם, סכום וקישור.")
            return

        amount = float(amount_match.group(1))
        full_name = name_match.group(1).strip()
        bit_url = url_match.group(1)

        cursor.execute("SELECT id FROM bit_transactions WHERE url = %s", (bit_url,))
        exists = cursor.fetchone()
        if exists:
            bot.send_message(message.chat.id, "⚠️ ההפקדה הזו כבר תועדה בעבר (לפי הקישור).")
            return

        cursor.execute("SELECT user_id, bit_name FROM bit_users WHERE bit_name ILIKE %s", (f"%{full_name}%",))
        results = cursor.fetchall()
        if not results:
            bot.send_message(message.chat.id, f"⚠️ לא נמצאו התאמות לשם '{full_name}' בטבלת bit_users.")
            return
        elif len(results) > 1:
            matches = ', '.join(name for _, name in results)
            bot.send_message(message.chat.id, f"⚠️ נמצאו מספר התאמות:
{matches}
אנא דייק את שם המפקיד.")
            return

        user_id, matched_name = results[0]
        cursor.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (amount, user_id))
        cursor.execute("""
            INSERT INTO bit_transactions (user_id, full_name, amount, url, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, matched_name, amount, bit_url, datetime.now()))
        conn.commit()

        try:
            bot.send_message(user_id, f"💰 הופקדו {amount} ש"ח לחשבונך. יתרתך עודכנה.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"⚠️ לא ניתן לשלוח למשתמש {user_id}. סיבה: {e}")

        bot.send_message(message.chat.id, f"✅ ההפקדה עבור {matched_name} עודכנה בהצלחה ({amount} ש"ח).")
        log(f"[BIT DEPOSIT] {matched_name} → {amount} ש"ח עודכן למשתמש {user_id}. לינק: {bit_url}")

    # ⬅️ סך כל היתרות של כל המשתמשים יחד (כפתור בדיקת יתרות כוללת)
    @bot.message_handler(func=lambda m: m.text == "בדיקת יתרות כוללת" and m.from_user.id == ADMIN_ID)
    def check_total_balances(message):
        cursor.execute("SELECT SUM(balance) FROM users")
        total = cursor.fetchone()[0] or 0
        bot.send_message(message.chat.id, f"💼 סך כל היתרות בקופה: {total} ש"ח")

    # ⬅️ סיכום כללי של יתרות מול הזמנות (כפתור סיכום כללי)
    @bot.message_handler(func=lambda m: m.text == "סיכום כללי" and m.from_user.id == ADMIN_ID)
    def admin_summary(message):
        cursor.execute("SELECT name, balance FROM users ORDER BY name")
        users = cursor.fetchall()
        cursor.execute("SELECT name, size, quantity FROM orders WHERE fulfilled = 0")
        orders = cursor.fetchall()
        summary_text = "*📊 סיכום מצב הקופה:*

"
        user_orders = {}
        size_prices = {'L': 36, 'XL': 39}
        for name, size, quantity in orders:
            price = size_prices.get(size, 0)
            user_orders[name] = user_orders.get(name, 0) + quantity * price
        for name, balance in users:
            spent = user_orders.get(name, 0)
            available = balance - spent
            status = "✅" if available >= 0 else "❌"
            summary_text += f"{status} {name} - יתרה: {balance} ש"ח "
            if spent > 0:
                summary_text += f"(בהמתנה: {spent} ש"ח, פנוי: {available} ש"ח)"
            summary_text += "\n"
        bot.send_message(message.chat.id, summary_text, parse_mode="Markdown")

    # ⬅️ מחיקת כל ההזמנות שלא סופקו (כפתור ביטול כל ההזמנות)
    @bot.message_handler(func=lambda m: m.text == "ביטול כל ההזמנות" and m.from_user.id == ADMIN_ID)
    def cancel_all_orders(message):
        cursor.execute("DELETE FROM orders WHERE fulfilled = 0")
        conn.commit()
        bot.send_message(message.chat.id, "❌ כל ההזמנות הממתינות בוטלו.")

    # ⬅️ הצגת כל ההזמנות הממתינות לאספקה (כפתור ניהול הזמנות)
    @bot.message_handler(func=lambda m: m.text == "ניהול הזמנות" and m.from_user.id == ADMIN_ID)
    def manage_orders(message):
        cursor.execute("SELECT id, name, size, quantity FROM orders WHERE fulfilled = 0 ORDER BY ordered_date")
        orders = cursor.fetchall()
        if not orders:
            bot.send_message(message.chat.id, "אין הזמנות ממתינות.")
        else:
            response = "📋 הזמנות ממתינות:

"
            for order_id, name, size, quantity in orders:
                response += f"#{order_id} - {name}: {quantity} ({size})\n"
            response += "\nלספק הזמנה, שלח: /fulfill order_id כמות_שסופקה"
            bot.send_message(message.chat.id, response)

    # ⬅️ סימון כל ההזמנות כסופקו לפי הכמות שהוזמנה (כפתור אספקה גורפת)
    @bot.message_handler(func=lambda m: m.text == "אספקה גורפת" and m.from_user.id == ADMIN_ID)
    def fulfill_all_orders(message):
        cursor.execute("SELECT id, user_id, quantity, size FROM orders WHERE fulfilled = 0")
        orders = cursor.fetchall()
        if not orders:
            bot.send_message(message.chat.id, "אין הזמנות פעילות לעדכון.")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for order_id, uid, qty, size in orders:
            price = 36 if size == 'L' else 39
            total = qty * price
            cursor.execute("""
                UPDATE orders SET fulfilled = 1, fulfilled_quantity = %s, fulfilled_date = %s, actual_total = %s
                WHERE id = %s
            """, (qty, now, total, order_id))
        conn.commit()

        cursor.execute("SELECT SUM(actual_total) FROM orders WHERE DATE(fulfilled_date) = CURRENT_DATE")
        total_sum = cursor.fetchone()[0] or 0
        bot.send_message(message.chat.id, f"✅ כל ההזמנות עודכנו כסופקו.\n💰 סה\"כ חיוב כולל היום: {total_sum} ש\"ח")
