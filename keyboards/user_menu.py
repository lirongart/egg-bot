from telebot.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("הזמנת תבניות"), KeyboardButton("בדיקת יתרה"))
    markup.row(KeyboardButton("ההזמנות שלי"), KeyboardButton("❌ ביטול ההזמנות שלי"))
    return markup

