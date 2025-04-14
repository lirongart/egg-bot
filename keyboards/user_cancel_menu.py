from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def build_cancel_menu(orders):
    markup = InlineKeyboardMarkup()
    for order_id, qty, size in orders:
        text = f"הזמנה #{order_id} – {qty} ({size})"
        markup.add(InlineKeyboardButton(text, callback_data=f"cancel_me_{order_id}"))
    return markup

def confirm_cancel_menu(order_id):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ כן, בטל", callback_data=f"confirm_cancel_{order_id}"),
        InlineKeyboardButton("❌ לא עכשיו", callback_data="cancel_ignore")
    )
    return markup
