from telebot.types import ReplyKeyboardMarkup

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("הזמנת תבניות")
    markup.row("בדיקת יתרה", "ההזמנות שלי")
    return markup
