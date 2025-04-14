from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def extra_admin_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📦 /fulfill", callback_data="cmd_fulfill"))
    markup.row(InlineKeyboardButton("❌ /cancel", callback_data="cmd_cancel"))
    markup.row(InlineKeyboardButton("🆔 /me", callback_data="cmd_me"))
    return markup
