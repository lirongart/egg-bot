import re
from config import ADMIN_ID
from datetime import datetime
from keyboards.admin_menu import admin_panel_inline
from utils.logger import log

pending_bit_payment = {}

def register(bot):
    @bot.message_handler(commands=['admin'])
    def admin_entry(message):
        if message.from_user.id != ADMIN_ID:
            return
        bot.send_message(message.chat.id, "תפריט ניהול:", reply_markup=admin_panel_inline())

    @bot.callback_query_handler(func=lambda call: call.data == "bit_deposit")
    def prompt_bit_sms(call):
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📨 הדבק עכשיו את הודעת ה־SMS שקיבלת מ־bit.")
        pending_bit_payment[call.message.chat.id] = True

    @bot.message_handler(func=lambda m: pending_bit_payment.get(m.chat.id) and m.from_user.id == ADMIN_ID)
    def handle_bit_sms(message):
        pending_bit_payment.pop(message.chat.id, None)
        text = message.text

        # חילוץ פרטים
        amount_match = re.search(r'(\d+(?:\.\d+)?) ש\\"ח', text)
        name_match = re.search(r'מ(.*?) באפליקציית bit', text)
        url_match = re.search(r'(https://www\\.bitpay\\.co\\.il/app/transaction-info\\?i=\\S+)', text)

        if not (amount_match and name_match and url_match):
            bot.send_message(message.chat.id, "⚠️ לא זוהתה הודעת bit תקינה. ודא שהעתקת את כל ההודעה כולל שם, סכום וקישור.")
            return

        amount = float(amount_match.group(1))
        full_name = name_match.group(1).strip()
        bit_url = url_match.group(1)

        # בדיקה אם הקישור כבר טופל
        cursor.execute("SELECT id FROM bit_transactions WHERE url = %s", (bit_url,))
        exists = cursor.fetchone()
        if exists:
            bot.send_message(message.chat.id, "⚠️ ההפקדה הזו כבר תועדה בעבר (לפי הקישור).")
            return

        # חיפוש fuzzy לפי שם
        cursor.execute("SELECT user_id, bit_name FROM bit_users WHERE bit_name ILIKE %s", (f"%{full_name}%",))
        results = cursor.fetchall()

        if not results:
            bot.send_message(message.chat.id, f"⚠️ לא נמצאו התאמות לשם '{full_name}' בטבלת bit_users.")
            return
        elif len(results) > 1:
            matches = ', '.join(name for _, name in results)
            bot.send_message(message.chat.id, f"⚠️ נמצאו מספר התאמות:\n{matches}\nאנא דייק את שם המפקיד.")
            return

        user_id, matched_name = results[0]

        # עדכון יתרה
        cursor.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (amount, user_id))

        # תיעוד
        cursor.execute("""
            INSERT INTO bit_transactions (user_id, full_name, amount, url, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, matched_name, amount, bit_url, datetime.now()))

        conn.commit()

        # לוג לאדמין
        log(f"[BIT DEPOSIT] {matched_name} → {amount} ש\"ח עודכן למשתמש {user_id}. לינק: {bit_url}")

        # הודעות
        bot.send_message(user_id, f"💰 הופקדו {amount} ש\"ח לחשבונך. יתרתך עודכנה.")
        bot.send_message(message.chat.id, f"✅ ההפקדה עבור {matched_name} עודכנה בהצלחה ({amount} ש\"ח).")