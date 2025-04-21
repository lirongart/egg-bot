from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def extra_admin_menu():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📦 אספקה מדויקת", callback_data="cmd_fulfill_exact_menu"),
        InlineKeyboardButton("אספקה שונה", callback_data="cmd_fulfill_partial_menu")
    )
    markup.row(
        InlineKeyboardButton("❌ ביטול הזמנה", callback_data="cmd_cancel"),
        InlineKeyboardButton("🆔 מה ה־ID שלי?", callback_data="cmd_me")
    )
    return markup


