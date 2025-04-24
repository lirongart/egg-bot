from config import ADMIN_ID
from keyboards.admin_menu import admin_main_menu
from keyboards.extra_admin_reply import extra_admin_reply_menu
# from keyboards.extra_admin import extra_admin_menu
from handlers import admin_supply_menu
from utils.logger import log
from utils.db_utils import execute_query
from utils.thread_safety import user_lock, global_lock
from utils.exception_handler import safe_execution
from datetime import datetime
import re

pending_bit_payment = {}

def register(bot):

	# ⬅️ לחיצה על “🔄 אספקה שונה”
    @bot.message_handler(func=lambda m: m.text == "🔄 אספקה שונה" and m.from_user.id == ADMIN_ID)
    def trigger_partial_menu(message):
	    # קודם מנקה את המקלדת כדי שלא נטמיע עוד כפתורים
	    admin_supply_menu.register.open_partial_supply_menu(message)
	    #bot.send_message(message.chat.id,
	     "📥 בחר הזמנה לעדכון אספקה חלקית:",
	     reply_markup=None)
	    admin_supply_menu.register.open_partial_supply_menu(message)
    # קורא לפונקציה הגמישה (Message או CallbackQuery) שהגדרנו ב-admin_supply_menu
    	

	
     # ⬅️ תפריט בדיקת היתרות הכוללת
    @bot.message_handler(func=lambda m: m.text == "בדיקת יתרות כוללת" and m.from_user.id == ADMIN_ID)
    @safe_execution("שגיאה בבדיקת היתרות הכוללת")
    def check_total_balances(message):
        total = execute_query("SELECT SUM(balance) FROM users", fetch="one")
        if total and total[0] is not None:
            bot.send_message(message.chat.id, f'💼 סך כל היתרות בקופה: {total[0]:.2f} ש"ח')
        else:
            bot.send_message(message.chat.id, "לא נמצאו יתרות.")

    
    # ⬅️ תפריט ניהול
    @bot.message_handler(commands=['admin'])
    def admin_entry(message):
        if message.from_user.id == ADMIN_ID:
            bot.send_message(message.chat.id, "תפריט ניהול:", reply_markup=admin_main_menu())

    # ⬅️ תפריט פקודות נוספות
    # @bot.message_handler(func=lambda m: m.text == "פקודות נוספות" and m.from_user.id == ADMIN_ID)
    # def extra_commands(message):
    #     bot.send_message(message.chat.id, "בחר פקודה נוספת:", reply_markup=extra_admin_menu())

    # חזרה לתפריט הראשי
    @bot.message_handler(func=lambda m: m.text == "↩️ חזור לתפריט ראשי" and m.from_user.id == ADMIN_ID)
    def back_to_main_menu(message):
         bot.send_message(message.chat.id, "חזרת לתפריט הראשי.", reply_markup=admin_main_menu())

     # לחיצה על "פקודות נוספות" → מציגה מקלדת Reply החדשה
    @bot.message_handler(func=lambda m: m.text == "פקודות נוספות" and m.from_user.id == ADMIN_ID)
    def show_extra_reply_menu(message):
         bot.send_message(message.chat.id, "בחר פעולה נוספת:", reply_markup=extra_admin_reply_menu())

    # מאזין לכפתורי המקלדת החדשה
    @bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text in
                     ["📦 אספקה מדויקת", "🔄 אספקה שונה", "📢 שלח הודעה לכולם"])
    def handle_extra_reply_buttons(message):

        if message.text == "📦 אספקה מדויקת":
        # מפעיל את הפקודה /fulfill_exact (מוכר מהקוד שלך)
            bot.send_message(message.chat.id, "📥 שלח פקודה:\n/fulfill_exact מספר_הזמנה")

        elif message.text == "🔄 אספקה שונה":
        # מפעיל את מודול admin_supply_menu (הממשק החדש שיצרנו)
            bot.send_message(message.chat.id, "📥 בחר הזמנה לעדכון אספקה חלקית:",
                         reply_markup=None)   # נקה מקלדת לפני שה-handler שלך יפיק רשימה
        # קורא ידנית לפונקציה הראשונה במודול:
            from handlers import admin_supply_menu
            admin_supply_menu.open_partial_supply_menu(message)  # צריך להתאים את הפונקציה לקבל Message

        elif message.text == "📢 שלח הודעה לכולם":
            bot.send_message(message.chat.id, "💬 הקלד את ההודעה שברצונך לשלוח לכל המשתמשים:")
            pending_broadcast[message.chat.id] = True

        pending_broadcast = {}
        @bot.message_handler(func=lambda m: pending_broadcast.get(m.chat.id) and m.from_user.id == ADMIN_ID)
        def do_broadcast(message):
            pending_broadcast.pop(message.chat.id, None)
            text = message.text
            users = execute_query("SELECT telegram_id FROM users", fetch=True)
            sent = 0
            for uid, in users:
                try:
                    bot.send_message(uid, text)
                    sent += 1
                except:
                    pass
            bot.send_message(message.chat.id, f"✅ ההודעה נשלחה ל-{sent} משתמשים.")


    # # ⬅️ מאזין לכל כפתורי התפריט של "פקודות נוספות"
    # @bot.callback_query_handler(func=lambda call: call.data.startswith("cmd_"))
    # def handle_admin_inline_cmds(call):
    #     bot.answer_callback_query(call.id)
     
    #     if call.data == "cmd_fulfill_exact":
    #         bot.send_message(call.message.chat.id, "📥 שלח פקודה: /fulfill_exact מספר_הזמנה")
    #     elif call.data == "cmd_fulfill_alt":
    #         bot.send_message(call.message.chat.id, "🔁 שלח פקודה: /fulfill_alt מספר_הזמנה מידה_סופקה כמות")
    #     elif call.data == "cmd_cancel":
    #         bot.send_message(call.message.chat.id, "❌ שלח פקודה: /cancel מספר_הזמנה")
    #     elif call.data == "cmd_me":
    #         bot.send_message(call.message.chat.id, f"🆔 ה־Telegram ID שלך הוא: {call.from_user.id}")
    #     elif call.data == "cmd_fulfill":
    #         bot.send_message(call.message.chat.id, "📦 שלח פקודה: /fulfill מספר_הזמנה כמות")

    @bot.message_handler(commands=['fulfill_exact'])
    @safe_execution("שגיאה באספקה מדויקת")
    def fulfill_exact(message):
        if message.from_user.id != ADMIN_ID:
            return
     
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "⚠️ פורמט שגוי. השתמש:\n/fulfill_exact מספר_הזמנה")
            return
     
        order_id = int(parts[1])
        order = execute_query("""
            SELECT user_id, name, quantity, size FROM orders
            WHERE id = %s AND fulfilled = 0
        """, (order_id,), fetch="one")
     
        if not order:
            bot.send_message(message.chat.id, "❌ ההזמנה לא קיימת או כבר סופקה.")
            return
     
        user_id, name, qty, size = order
        price = 36 if size == 'L' else 39
        total = qty * price
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
     
        execute_query("""
            UPDATE orders
            SET fulfilled = 1,
                fulfilled_quantity = %s,
                fulfilled_date = %s,
                actual_total = %s
            WHERE id = %s
        """, (qty, now, total, order_id))
     
        bot.send_message(message.chat.id, f"✅ הזמנה #{order_id} עודכנה כסופקה במדויק.\nחיוב: {total} ש\"ח")
        bot.send_message(user_id, f"📦 ההזמנה שלך #{order_id} סופקה במלואה ({qty} × {size})\n💰 חיוב: {total} ש\"ח")

    @bot.message_handler(commands=['fulfill_alt'])
    @safe_execution("שגיאה באספקה עם מידה שונה")
    def fulfill_alt(message):
        if message.from_user.id != ADMIN_ID:
            return
    
        parts = message.text.split()
        if len(parts) != 4:
            bot.send_message(message.chat.id, "⚠️ פורמט שגוי. השתמש:\n/fulfill_alt מספר_הזמנה מידה_סופקה כמות")
            return
     
        order_id = int(parts[1])
        actual_size = parts[2].upper()
        fulfilled_qty = int(parts[3])
     
        if actual_size not in ['L', 'XL']:
            bot.send_message(message.chat.id, "⚠️ מידה לא חוקית. מותר רק L או XL.")
            return
     
        order = execute_query("""
            SELECT user_id, name, quantity, size FROM orders
            WHERE id = %s AND fulfilled = 0
        """, (order_id,), fetch="one")
     
        if not order:
            bot.send_message(message.chat.id, "❌ ההזמנה לא קיימת או כבר סופקה.")
            return
     
        user_id, name, ordered_qty, original_size = order
     
        if fulfilled_qty > ordered_qty:
            bot.send_message(message.chat.id, f"⚠️ הוזמנו רק {ordered_qty}. לא ניתן לעדכן יותר.")
            return
     
        # רק מידה זולה יותר מותרת
        size_prices = {'L': 36, 'XL': 39}
        if size_prices[actual_size] > size_prices[original_size]:
            bot.send_message(message.chat.id, f"❌ לא ניתן לספק מידה יקרה יותר ממה שהוזמן.")
            return
     
        actual_total = fulfilled_qty * size_prices[actual_size]
        refund = (ordered_qty * size_prices[original_size]) - actual_total
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
     
        execute_query("""
            UPDATE orders
            SET fulfilled = 1,
                fulfilled_quantity = %s,
                fulfilled_date = %s,
                actual_total = %s
            WHERE id = %s
        """, (fulfilled_qty, now, actual_total, order_id))
     
        if refund > 0:
            execute_query("UPDATE users SET balance = balance + %s WHERE id = %s", (refund, user_id))
     
        bot.send_message(message.chat.id, f"✅ הזמנה #{order_id} עודכנה עם שינוי מידה ({original_size} → {actual_size}).")
        bot.send_message(user_id,
            f"📦 ההזמנה שלך #{order_id} סופקה במידה שונה: {size} ➝ {supplied_size}\n"
            f"🥚 כמות שסופקה: {qty_supplied}/{ordered_qty}\n"
            f"💰 חיוב בפועל: {actual_total} ש\"ח" +
            (f"\n💸 זיכוי לחשבונך: {refund} ש\"ח" if refund > 0 else "")
        )



    @bot.message_handler(commands=['cancel'])
    @safe_execution("שגיאה בביטול ההזמנה")
    def cancel_order(message):
        if message.from_user.id != ADMIN_ID:
            return
    
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "⚠️ פורמט שגוי. השתמש:\n/cancel מספר_הזמנה")
            return
     
        order_id = int(parts[1])
        order = execute_query(
            "SELECT user_id, name, quantity, size FROM orders WHERE id = %s AND fulfilled = 0",
            (order_id,), fetch="one"
        )
     
        if not order:
            bot.send_message(message.chat.id, "❌ ההזמנה לא קיימת או כבר בוטלה/סופקה.")
            return
     
        user_id, name, quantity, size = order
        price = 36 if size == 'L' else 39
        refund = quantity * price
     
        execute_query("DELETE FROM orders WHERE id = %s", (order_id,))
        execute_query("UPDATE users SET balance = balance + %s WHERE id = %s", (refund, user_id))
     
        log(f"[CANCEL] ההזמנה #{order_id} של {name} בוטלה. זיכוי: {refund} ש\"ח", category="admin")
    
        bot.send_message(message.chat.id, f"❌ ההזמנה #{order_id} בוטלה.\n💸 היתרה זוכתה ב־{refund} ש\"ח")
        bot.send_message(user_id, f"❌ ההזמנה שלך #{order_id} בוטלה.\n💸 היתרה שלך זוכתה ב־{refund} ש\"ח")

    @bot.message_handler(commands=['fulfill'])
    @safe_execution("שגיאה בעדכון אספקה")
    def fulfill_order(message):
        if message.from_user.id != ADMIN_ID:
            return
     
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, "⚠️ פורמט שגוי. השתמש:\n/fulfill מספר_הזמנה כמות_שסופקה")
            return
     
        order_id = int(parts[1])
        qty = int(parts[2])
        if qty < 0:
            bot.send_message(message.chat.id, "❌ כמות שסופקה לא יכולה להיות שלילית.")
            return
     
        order = execute_query("""
            SELECT user_id, name, quantity, size FROM orders
            WHERE id = %s AND fulfilled = 0
        """, (order_id,), fetch="one")
     
        if not order:
            bot.send_message(message.chat.id, "❌ ההזמנה לא קיימת או כבר סופקה.")
            return
     
        user_id, name, ordered_qty, size = order
        if qty > ordered_qty:
            bot.send_message(message.chat.id, f"⚠️ הוזמנו רק {ordered_qty}. לא ניתן לעדכן יותר.")
            return
     
        price = 36 if size == 'L' else 39
        actual_total = qty * price
        refund = (ordered_qty - qty) * price
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
     
        execute_query("""
            UPDATE orders SET fulfilled = 1,
                              fulfilled_quantity = %s,
                              fulfilled_date = %s,
                              actual_total = %s
            WHERE id = %s
        """, (qty, now, actual_total, order_id))
     
        if refund > 0:
            execute_query("UPDATE users SET balance = balance + %s WHERE id = %s", (refund, user_id))
     
        log(f"[FULFILL] הזמנה #{order_id} סופקה: {qty}/{ordered_qty} ({size}). חיוב: {actual_total} ש\"ח", category="admin")
     
        bot.send_message(message.chat.id, f"✅ הזמנה #{order_id} עודכנה.\nחיוב בפועל: {actual_total} ש\"ח")
        bot.send_message(user_id,
            f"📦 ההזמנה שלך #{order_id} סופקה: {qty}/{ordered_qty} ({size})\n"
            f"💰 חיוב: {actual_total} ש\"ח" + (f"\n💸 זיכוי: {refund} ש\"ח" if refund > 0 else ""))


    # ⬅️ הפקדה מ־bit
    @bot.message_handler(func=lambda m: m.text == "הפקדה מ־bit" and m.from_user.id == ADMIN_ID)
    def bit_deposit(message):
        bot.send_message(message.chat.id, "📨 הדבק עכשיו את הודעת ה־SMS שקיבלת מ־bit.")
        pending_bit_payment[message.chat.id] = True

    @bot.message_handler(func=lambda m: pending_bit_payment.get(m.chat.id) and m.from_user.id == ADMIN_ID)
    @user_lock('payment')
    @safe_execution("שגיאה בעיבוד הודעת bit")
    def handle_bit_sms(message):
        pending_bit_payment.pop(message.chat.id, None)
        text = re.sub(r'[\n\u200f\u00a0]', ' ', message.text).strip()

        amount_match = re.search(r'(\d+(?:\.\d+)?)\s*ש[״"]?ח', text)
        name_match = re.search(r'מחכים לך מ(.*?)\s*באפליקציית bit', text)
        url_match = re.search(r'(https://www\.bitpay\.co\.il/app/transaction-info\?i=\S+)', text)

        if not (amount_match and name_match and url_match):
            bot.send_message(message.chat.id, "⚠️ לא זוהתה הודעת bit תקינה.")
            return

        amount = float(amount_match.group(1))
        full_name = name_match.group(1).strip()
        bit_url = url_match.group(1)

        exists = execute_query("SELECT id FROM bit_transactions WHERE url = %s", (bit_url,), fetch="one")
        if exists:
            bot.send_message(message.chat.id, "⚠️ ההפקדה הזו כבר תועדה.")
            return

        results = execute_query("SELECT user_id, bit_name FROM bit_users WHERE bit_name ILIKE %s",
                                (f"%{full_name}%",), fetch="all")
        if not results:
            bot.send_message(message.chat.id, f"⚠️ לא נמצאו התאמות לשם '{full_name}'.")
            return
        if len(results) > 1:
            matches = ', '.join(name for _, name in results)
            bot.send_message(message.chat.id, f"⚠️ נמצאו מספר התאמות: {matches}")
            return

        user_id, matched_name = results[0]
        now = datetime.now()
        execute_query("UPDATE users SET balance = balance + %s WHERE id = %s", (amount, user_id))
        execute_query(
            """INSERT INTO bit_transactions (user_id, full_name, amount, url, timestamp)
               VALUES (%s, %s, %s, %s, %s)""",
            (user_id, matched_name, amount, bit_url, now)
        )

        try:
            bot.send_message(user_id, f"💰 הופקדו {amount} ש\"ח לחשבונך.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"⚠️ לא ניתן לשלוח למשתמש {user_id}. שגיאה: {e}")
        bot.send_message(message.chat.id, f"✅ ההפקדה עודכנה ({matched_name} - {amount} ש\"ח).")
        log(f"[BIT] {matched_name} → {amount} ש\"ח למשתמש {user_id}", category="bit")

    # ⬅️ סיכום כללי
    @bot.message_handler(func=lambda m: m.text == "סיכום כללי" and m.from_user.id == ADMIN_ID)
    @safe_execution("שגיאה בהפקת סיכום כללי")
    def admin_summary(message):
        users = execute_query("SELECT name, balance FROM users ORDER BY name", fetch="all")
        orders = execute_query("SELECT name, size, quantity FROM orders WHERE fulfilled = 0", fetch="all")

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

    # ⬅️ ביטול כל ההזמנות
    @bot.message_handler(func=lambda m: m.text == "ביטול כל ההזמנות" and m.from_user.id == ADMIN_ID)
    @global_lock("cancel_all")
    @safe_execution("שגיאה בביטול הזמנות")
    def cancel_all_orders(message):
        execute_query("DELETE FROM orders WHERE fulfilled = 0")
        bot.send_message(message.chat.id, "❌ כל ההזמנות הממתינות בוטלו.")

    # ⬅️ ניהול הזמנות
    @bot.message_handler(func=lambda m: m.text == "ניהול הזמנות" and m.from_user.id == ADMIN_ID)
    @safe_execution("שגיאה בניהול הזמנות")
    def manage_orders(message):
        orders = execute_query(
            "SELECT id, name, size, quantity, ordered_date FROM orders WHERE fulfilled = 0 ORDER BY ordered_date",
            fetch="all"
        )
        if not orders:
            bot.send_message(message.chat.id, "אין הזמנות ממתינות.")
            return

        response = "📋 הזמנות ממתינות:\n\n"
        for order_id, name, size, quantity, ordered_at in orders:
            response += f"#{order_id} - {name}: {quantity} תבניות ({size})\nתאריך הזמנה: {ordered_at}\n\n"
        response += "לספק הזמנה:\n/fulfill מספר_הזמנה כמות_שסופקה"
        bot.send_message(message.chat.id, response)

    # ⬅️ אספקה גורפת
    @bot.message_handler(func=lambda m: m.text == "אספקה גורפת" and m.from_user.id == ADMIN_ID)
    @global_lock("fulfill_all")
    @safe_execution("שגיאה באספקה גורפת")
    def fulfill_all_orders(message):
        orders = execute_query("SELECT id, user_id, quantity, size FROM orders WHERE fulfilled = 0", fetch="all")
        if not orders:
            bot.send_message(message.chat.id, "אין הזמנות פעילות לעדכון.")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        size_prices = {'L': 36, 'XL': 39}
        total_sum = 0
        updated = 0

        for order_id, uid, qty, size in orders:
            price = size_prices.get(size, 0)
            total = qty * price
            execute_query("""
                UPDATE orders SET fulfilled = 1, fulfilled_quantity = %s, fulfilled_date = %s, actual_total = %s
                WHERE id = %s
            """, (qty, now, total, order_id))
            updated += 1
            total_sum += total

        bot.send_message(message.chat.id, f"✅ {updated} הזמנות עודכנו.\n💰 חיוב כולל: {total_sum} ש\"ח")

    # ⬅️ פקודות /cancel /fulfill
    @bot.message_handler(commands=['cancel'])
    @user_lock()
    @safe_execution("שגיאה בביטול הזמנה")
    def cancel_order(message):
        parts = message.text.split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❌ פורמט שגוי. /cancel מספר_הזמנה")
            return

        order_id = int(parts[1])
        order = execute_query("SELECT user_id, name, quantity, size FROM orders WHERE id = %s AND fulfilled = 0",
                              (order_id,), fetch="one")
        if not order:
            bot.send_message(message.chat.id, "❌ ההזמנה לא קיימת או כבר סופקה.")
            return

        user_id, name, quantity, size = order
        price = 36 if size == 'L' else 39
        refund = quantity * price
        execute_query("DELETE FROM orders WHERE id = %s", (order_id,))
        execute_query("UPDATE users SET balance = balance + %s WHERE id = %s", (refund, user_id))

        bot.send_message(message.chat.id, f"❌ הזמנה #{order_id} של {name} בוטלה.\nהחזר: {refund} ש\"ח")
        bot.send_message(user_id, f"❌ ההזמנה שלך #{order_id} בוטלה.\nהחזר: {refund} ש\"ח")
        log(f"[ADMIN CANCEL] {name} - #{order_id} - {refund} ש\"ח", category="admin")

    @bot.message_handler(commands=['fulfill'])
    @user_lock()
    @safe_execution("שגיאה בעדכון אספקה")
    def fulfill_order(message):
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(message.chat.id, "❌ פורמט שגוי. /fulfill מספר_הזמנה כמות")
            return

        order_id = int(parts[1])
        qty = int(parts[2])
        if qty < 0:
            bot.send_message(message.chat.id, "❌ כמות לא חוקית.")
            return

        order = execute_query("SELECT user_id, name, quantity, size FROM orders WHERE id = %s AND fulfilled = 0",
                              (order_id,), fetch="one")
        if not order:
            bot.send_message(message.chat.id, "❌ ההזמנה לא קיימת או כבר סופקה.")
            return

        user_id, name, ordered_qty, size = order
        if qty > ordered_qty:
            bot.send_message(message.chat.id, f"❌ הוזמנו רק {ordered_qty}. לא ניתן לספק יותר.")
            return

        price = 36 if size == 'L' else 39
        actual_total = qty * price
        refund = (ordered_qty - qty) * price
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        execute_query("""
            UPDATE orders SET fulfilled = 1, fulfilled_quantity = %s, fulfilled_date = %s, actual_total = %s
            WHERE id = %s
        """, (qty, now, actual_total, order_id))

        if refund > 0:
            execute_query("UPDATE users SET balance = balance + %s WHERE id = %s", (refund, user_id))

        bot.send_message(message.chat.id, f"✅ עודכן #{order_id}: {qty}/{ordered_qty} ({size})\nחיוב: {actual_total} ש\"ח")
        bot.send_message(user_id, f"📦 ההזמנה שלך #{order_id} סופקה ({qty}/{ordered_qty})\nחיוב: {actual_total} ש\"ח")
        log(f"[FULFILL] #{order_id} → {qty}/{ordered_qty} ({size})", category="admin")
