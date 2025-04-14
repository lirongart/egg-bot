from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def admin_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("📥הפקדה מ־bit"))
    markup.row(KeyboardButton("ביטול כל ההזמנות❌"), KeyboardButton("✅אספקה גורפת"))
    markup.row(KeyboardButton("💰בדיקת יתרות כוללת"), KeyboardButton("📊סיכום כללי"))
    markup.row(KeyboardButton("⚙️פקודות נוספות"), KeyboardButton("📋ניהול הזמנות"))
    return markup
