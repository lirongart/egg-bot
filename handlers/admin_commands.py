from config import ADMIN_ID, DATABASE_URL
from keyboards.admin_menu import admin_main_menu
from keyboards.extra_admin import extra_admin_menu
from utils.logger import log
from datetime import datetime
import psycopg2
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
            bot.send_message(message.chat.id, f"⚠️ נמצאו מספר התאמות:{matches}אנא דייק את שם המפקיד.")
            return

        user_id, matched_name = results[0]
        cursor.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (amount, user_id))
        cursor.execute("""
            INSERT INTO bit_transactions (user_id, full_name, amount, url, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, matched_name, amount, bit_url, datetime.now()))
        conn.commit()

        try:
            bot.send_message(user_id, f'💰 הופקדו {amount} ש"ח לחשבונך. יתרתך עודכנה.')
        except Exception as e:
            bot.send_message(ADMIN_ID, f"⚠️ לא ניתן לשלוח למשתמש {user_id}. סיבה: {e}")

        bot.send_message(message.chat.id, f'✅ ההפקדה עבור {matched_name} עודכנה בהצלחה ({amount} ש"ח).')
        log(f'[BIT DEPOSIT] {matched_name} → {amount} ש"ח עודכן למשתמש {user_id}. לינק: {bit_url}')


        # ⬅️ סך כל היתרות של כל המשתמשים יחד (כפתור בדיקת יתרות כוללת)
    @bot.message_handler(func=lambda m: m.text == "בדיקת יתרות כוללת" and m.from_user.id == ADMIN_ID)
    def check_total_balances(message):
        try:
            cursor.execute("SELECT SUM(balance) FROM users")
            total = cursor.fetchone()[0] or 0
            bot.send_message(message.chat.id, f'💼 סך כל היתרות בקופה: {total:.2f} ש"ח')
        except Exception as e:
            bot.send_message(message.chat.id, f"שגיאה: {e}")


    # ⬅️ סיכום כללי של יתרות מול הזמנות (כפתור סיכום כללי)
    @bot.message_handler(func=lambda m: m.text == "סיכום כללי" and m.from_user.id == ADMIN_ID)
    def admin_summary(message):
        try:
            cursor.execute("SELECT name, balance FROM users ORDER BY name")
            users = cursor.fetchall()
    
            cursor.execute("SELECT name, size, quantity FROM orders WHERE fulfilled = 0")
            orders = cursor.fetchall()
        except Exception as e:
            bot.send_message(message.chat.id, f"שגיאה בטעינת נתונים: {e}")
            return
    
        summary_text = "*📊 סיכום מצב הקופה:*\n\n"
        user_orders = {}
        size_prices = {'L': 36, 'XL': 39}
    
        for name, size, quantity in orders:
            price = size_prices.get(size, 0)
            user_orders[name] = user_orders.get(name, 0) + quantity * price
    
        for name, balance in users:
            spent = user_orders.get(name, 0)
            available = balance - spent
            status = "✅" if available >= 0 else "❌"
            summary_text += f"{status} {name} - יתרה: {balance} ש\"ח"
            if spent > 0:
                summary_text += f" (בהמתנה: {spent} ש\"ח, פנוי: {available} ש\"ח)"
            summary_text += "\n"
    
        bot.send_message(message.chat.id, summary_text, parse_mode="Markdown")

        # ⬅️ מחיקת כל ההזמנות שלא סופקו (כפתור ביטול כל ההזמנות)
    @bot.message_handler(func=lambda m: m.text == "ביטול כל ההזמנות" and m.from_user.id == ADMIN_ID)
    def cancel_all_orders(message):
        try:
            # שליפת כל ההזמנות הפתוחות
            cursor.execute("""
                SELECT id, user_id, name, quantity, size
                FROM orders
                WHERE fulfilled = 0
            """)
            orders = cursor.fetchall()
    
            if not orders:
                bot.send_message(message.chat.id, "ℹ️ אין הזמנות ממתינות לביטול.")
                return
    
            total_refunds = {}
            for order_id, uid, name, qty, size in orders:
                price = 36 if size == 'L' else 39
                refund = qty * price
    
                # עדכון יתרה
                total_refunds[uid] = total_refunds.get(uid, 0) + refund
    
                # מחיקת ההזמנה
                cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
    
                # לוג פעילות (אופציונלי לכל אחת)
                log(f"[CANCEL] #{order_id} של {name} (ID {uid}) בוטלה. הוחזר {refund} ש\"ח.")
    
            # עדכון יתרות בפועל
            for uid, amount in total_refunds.items():
                cursor.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (amount, uid))
    
                try:
                    bot.send_message(uid, f"❌ כל ההזמנות שלך בוטלו.\n💸 זיכוי כולל: {amount} ש\"ח.")
                except:
                    pass  # מונע תקיעת הבוט אם משתמש חסום
    
            conn.commit()
    
            total_orders = len(orders)
            total_amount = sum(total_refunds.values())
    
            # הודעת סיכום למנהל
            bot.send_message(message.chat.id,
                f"✅ בוטלו {total_orders} הזמנות.\n"
                f"💸 סך הכול זיכויים: {total_amount:.2f} ש\"ח.")
    
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ שגיאה בביטול כולל: {e}")
    


    # ⬅️ הצגת כל ההזמנות הממתינות לאספקה (כפתור ניהול הזמנות)
    @bot.message_handler(func=lambda m: m.text == "ניהול הזמנות" and m.from_user.id == ADMIN_ID)
    def manage_orders(message):
        try:
            cursor.execute("""
                SELECT id, name, size, quantity, ordered_date
                FROM orders
                WHERE fulfilled = 0
                ORDER BY ordered_date
            """)
            orders = cursor.fetchall()
    
            if not orders:
                bot.send_message(message.chat.id, "אין הזמנות ממתינות.")
                return
    
            response = "📋 הזמנות ממתינות:\n\n"
            for order_id, name, size, quantity, ordered_at in orders:
                response += f"#{order_id} - {name}: {quantity} תבניות ({size})\nתאריך הזמנה: {ordered_at}\n\n"
    
            response += "לספק הזמנה, שלח:\n/fulfill [מספר_הזמנה] [כמות_שסופקה]"
            bot.send_message(message.chat.id, response)
        except Exception as e:
            bot.send_message(message.chat.id, f"שגיאה בניהול הזמנות: {e}")


    # ⬅️ סימון כל ההזמנות כסופקו לפי הכמות שהוזמנה (כפתור אספקה גורפת)
    @bot.message_handler(func=lambda m: m.text == "אספקה גורפת" and m.from_user.id == ADMIN_ID)
    def fulfill_all_orders(message):
        try:
            cursor.execute("SELECT id, user_id, quantity, size FROM orders WHERE fulfilled = 0")
            orders = cursor.fetchall()
            if not orders:
                bot.send_message(message.chat.id, "אין הזמנות פעילות לעדכון.")
                return
    
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            size_prices = {'L': 36, 'XL': 39}
            updated_order_ids = []
    
            for order_id, uid, qty, size in orders:
                price = size_prices.get(size, 0)
                total = qty * price
    
                cursor.execute("""
                    UPDATE orders
                    SET fulfilled = 1,
                        fulfilled_quantity = %s,
                        fulfilled_date = %s,
                        actual_total = %s
                    WHERE id = %s
                """, (qty, now, total, order_id))
    
                updated_order_ids.append(order_id)
                
            # שליחת הודעה ללקוח
                # שליפת שם הלקוח
                cursor.execute("SELECT name FROM users WHERE id = %s", (uid,))
                name_result = cursor.fetchone()
                name = name_result[0] if name_result else "לקוח"
                
                try:
                    bot.send_message(uid,
                        f"👋 שלום {name}!\n"
                        f"📦 ההזמנה שלך סופקה במלואה:\n"
                        f"🔢 מספר הזמנה: {order_id}\n"
                        f"🥚 כמות: {qty} תבניות מידה {size}\n"
                        f"💰 חיוב: {total:.2f} ש\"ח\n"
                        f"✅ תודה ולהתראות!"
                    )
                except Exception as e:
                    bot.send_message(ADMIN_ID, f"⚠️ שגיאה בשליחת הודעה ללקוח {uid} על הזמנה #{order_id}: {e}")
    


            conn.commit()
    
            # שלב הסיכום — רק לפי ההזמנות שסופקו כעת
            format_ids = ','.join(str(i) for i in updated_order_ids)
            cursor.execute(f"SELECT SUM(actual_total) FROM orders WHERE id IN ({format_ids})")
            total_sum = cursor.fetchone()[0] or 0
    
            bot.send_message(message.chat.id, f'✅ {len(updated_order_ids)} הזמנות עודכנו כסופקו.\n💰 סה"כ חיוב כולל: {total_sum:.2f} ש"ח')
    
        except Exception as e:
            bot.send_message(message.chat.id, f"שגיאה באספקה גורפת: {e}")

    # ⬅️ כפתור פקודות נוספות - פותח תפריט אינטראקטיבי
    @bot.message_handler(func=lambda m: m.text == "פקודות נוספות" and m.from_user.id == ADMIN_ID)
    def extra_commands(message):
        bot.send_message(message.chat.id, "בחר פקודה נוספת:", reply_markup=extra_admin_menu())

    # ⬅️ תגובה ללחיצה על פקודות נוספות מהתפריט האינטראקטיבי
    @bot.callback_query_handler(func=lambda call: call.data.startswith("cmd_"))
    def handle_admin_inline_cmds(call):
        bot.answer_callback_query(call.id)
    
        if call.data == "cmd_fulfill":
            bot.send_message(call.message.chat.id, "📥 כתוב את הפקודה: /fulfill מספר_הזמנה כמות")
        elif call.data == "cmd_fulfill_exact":
            bot.send_message(call.message.chat.id, "📥 כתוב את הפקודה:\n/fulfill מספר_הזמנה")
        
        elif call.data == "cmd_fulfill_alt":
            bot.send_message(call.message.chat.id, "🔄 כתוב את הפקודה:\n/fulfill מספר_הזמנה כמות מידה (L או XL)")
        elif call.data == "cmd_cancel":
            bot.send_message(call.message.chat.id, "❌ כתוב את הפקודה: /cancel מספר_הזמנה")
        elif call.data == "cmd_me":
            bot.send_message(call.message.chat.id, f"🆔 Telegram ID שלך: {call.from_user.id}")


    @bot.message_handler(commands=['fulfill'])
    def fulfill_order(message):
        if message.from_user.id != ADMIN_ID:
            return
    
        try:
            parts = message.text.split()
            if len(parts) == 2:
                # אספקה מדויקת
                order_id = int(parts[1])
                cursor.execute("SELECT user_id, name, quantity, size FROM orders WHERE id = %s AND fulfilled = 0", (order_id,))
                order = cursor.fetchone()
                if not order:
                    bot.send_message(message.chat.id, "❌ הזמנה לא קיימת או כבר סופקה.")
                    return
                user_id, name, qty, size = order
    
            elif len(parts) == 4:
                # אספקה שונה
                order_id = int(parts[1])
                qty = int(parts[2])
                size = parts[3].upper()
                if size not in ['L', 'XL']:
                    bot.send_message(message.chat.id, "⚠️ מידה לא תקינה. השתמש ב־L או XL בלבד.")
                    return
                cursor.execute("SELECT user_id, name, quantity, size FROM orders WHERE id = %s AND fulfilled = 0", (order_id,))
                order = cursor.fetchone()
                if not order:
                    bot.send_message(message.chat.id, "❌ הזמנה לא קיימת או כבר סופקה.")
                    return
                user_id, name, ordered_qty, ordered_size = order
                if qty < 0 or qty > ordered_qty:
                    bot.send_message(message.chat.id, f"⚠️ כמות לא תקינה (מקסימום {ordered_qty}).")
                    
                    size_prices = {'L': 36, 'XL': 39}
                    ordered_price = size_prices.get(ordered_size)
                    new_price = size_prices.get(size)
            
                    if new_price > ordered_price:
                        bot.send_message(message.chat.id,
                            f"❌ לא ניתן לספק מידה יקרה יותר ({size}) במקום מה שהוזמן ({ordered_size}).\n"
                            f"חיוב עבור {size} גבוה יותר ולא ניתן לבצע זאת ללא אישור מראש מהלקוח.")
                        return

                    return
            else:
                bot.send_message(message.chat.id, "⚠️ פורמט שגוי.\n/fulfill [מספר_הזמנה] או\n/fulfill [מספר] [כמות] [מידה]")
                return
    
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            size_prices = {'L': 36, 'XL': 39}
            actual_price = size_prices.get(size, 0)
            actual_total = qty * actual_price
    
            # אם זו אספקה שונה – נחשב גם החזר
            if len(parts) == 4:
                ordered_total = ordered_qty * size_prices.get(ordered_size, 0)
                refund = ordered_total - actual_total
            else:
                refund = 0
    
            cursor.execute("""
                UPDATE orders
                SET fulfilled = 1,
                    fulfilled_quantity = %s,
                    fulfilled_date = %s,
                    actual_total = %s,
                    fulfilled_size = %s
                WHERE id = %s
            """, (qty, now, actual_total, size, order_id))
    
            if refund > 0:
                cursor.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (refund, user_id))
    
            conn.commit()
    
            bot.send_message(message.chat.id,
                f"✅ ההזמנה #{order_id} עודכנה ({qty} תבניות {size})\n"
                f"💰 חיוב בפועל: {actual_total} ש\"ח" +
                (f"\n💸 זיכוי: {refund} ש\"ח" if refund > 0 else "")
            )
    
            bot.send_message(user_id,
                f"📦 ההזמנה שלך #{order_id} עודכנה: {qty} תבניות {size}\n"
                f"💰 חיוב בפועל: {actual_total} ש\"ח" +
                (f"\n💸 זיכוי: {refund} ש\"ח" if refund > 0 else "")
            )
    
        except Exception as e:
            bot.send_message(message.chat.id, f"שגיאה: {e}")

    @bot.message_handler(commands=['cancel'])
    def cancel_order(message):
        if message.from_user.id != ADMIN_ID:
            return
    
        try:
            parts = message.text.split()
            if len(parts) != 2:
                bot.send_message(message.chat.id, "⚠️ פורמט שגוי. השתמש:\n/cancel מספר_הזמנה")
                return
    
            order_id = int(parts[1])
    
            cursor.execute("""
                SELECT user_id, name, quantity, size, fulfilled
                FROM orders
                WHERE id = %s
            """, (order_id,))
            order = cursor.fetchone()
    
            if not order:
                bot.send_message(message.chat.id, "❌ הזמנה לא נמצאה.")
                return
    
            user_id, name, quantity, size, fulfilled = order
    
            if fulfilled:
                bot.send_message(message.chat.id, "⚠️ לא ניתן לבטל הזמנה שכבר סופקה.")
                return
    
            price = 36 if size == 'L' else 39
            refund = quantity * price
    
            # מחיקת ההזמנה והחזר ליתרה
            cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
            cursor.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (refund, user_id))
            conn.commit()
    
            # שליחת הודעה ללקוח
            bot.send_message(user_id,
                f"❌ ההזמנה שלך #{order_id} בוטלה על ידי המנהל.\n"
                f"💸 היתרה שלך זוכתה ב־{refund} ש\"ח.")
    
            # הודעה למנהל
            bot.send_message(message.chat.id,
                f"✅ ההזמנה #{order_id} של {name} בוטלה.\n"
                f"💰 הוחזר: {refund} ש\"ח למשתמש {user_id}")
    
            # לוג פעילות
            log(f"[CANCEL] #{order_id} של {name} (ID {user_id}) בוטלה. הוחזר {refund} ש\"ח.")
    
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ שגיאה בביטול ההזמנה: {e}")
    
        
