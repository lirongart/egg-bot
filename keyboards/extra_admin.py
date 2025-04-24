# keyboards/extra_admin_reply.py
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def extra_admin_reply_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        KeyboardButton("📦 אספקה מדויקת"),
        KeyboardButton("🔄 אספקה שונה")
    )
    markup.row(
        KeyboardButton("📢 שלח הודעה לכולם"),
        KeyboardButton("↩️ חזור לתפריט ראשי")
    )
    return markup
