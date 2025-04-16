from keyboards.user_cancel_menu import build_cancel_menu, confirm_cancel_menu
from utils.logger import log
from utils.db_utils import execute_query, get_db_connection
from utils.exception_handler import safe_execution
from utils.thread_safety import user_lock

# כפתור ❌ ביטול ההזמנות שלי
@bot.message_handler(func=lambda m: m.text == "❌ ביטול ההזמנות שלי")
@user_lock('order')
@safe_execution("שגיאה בשליפת ההזמנות שלך")
def cancel_my_orders_menu(message):
    user_id = message.from_user.id
    orders = execute_query(
        "SELECT id, quantity, size FROM orders WHERE user_id = %s AND fulfilled = 0",
        (user_id,), fetch='all'
    )
    if not orders:
        bot.send_message(user_id, "אין לך הזמנות שניתן לבטל.", reply_markup=main_menu())
        return

    bot.send_message(user_id, "בחר את ההזמנה שברצונך לבטל:", reply_markup=build_cancel_menu(orders))

# לחיצה על אחת ההזמנות לביטול (callback)
@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_me_"))
def ask_cancel_confirmation(call):
    bot.answer_callback_query(call.id)
    order_id = int(call.data.split("_")[-1])
    bot.edit_message_text("האם אתה בטוח שברצונך לבטל את ההזמנה?",
                          call.message.chat.id,
                          call.message.message_id,
                          reply_markup=confirm_cancel_menu(order_id))

# אישור ביטול
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_cancel_"))
@user_lock('order')
@safe_execution("שגיאה בביטול ההזמנה")
def confirm_cancel_order(call):
    bot.answer_callback_query(call.id)
    order_id = int(call.data.split("_")[-1])
    user_id = call.from_user.id

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT quantity, size FROM orders
                WHERE id = %s AND user_id = %s AND fulfilled = 0
            """, (order_id, user_id))
            order = cursor.fetchone()
            if not order:
                bot.edit_message_text("⚠️ ההזמנה כבר בוטלה או סופקה.",
                                      call.message.chat.id,
                                      call.message.message_id,
                                      reply_markup=None)
                return

            qty, size = order
            price = 36 if size == 'L' else 39
            refund = qty * price

            cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
            cursor.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (refund, user_id))

        conn.commit()

    bot.edit_message_text(f"❌ ההזמנה #{order_id} בוטלה.\n💸 זיכוי: {refund} ש\"ח",
                          call.message.chat.id,
                          call.message.message_id,
                          reply_markup=None)
    log(f"[USER CANCEL] {user_id} ביטל הזמנה #{order_id}, זיכוי {refund} ש\"ח", category="admin")

# דחיית ביטול
@bot.callback_query_handler(func=lambda call: call.data == "cancel_ignore")
def cancel_ignore(call):
    bot.answer_callback_query(call.id, "ביטול בוטל.")
    bot.edit_message_text("הפעולה בוטלה.", call.message.chat.id, call.message.message_id)
