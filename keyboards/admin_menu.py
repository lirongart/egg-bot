from telebot.types import ReplyKeyboardMarkup

def admin_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("הפקדה מ־bit", "בדיקת יתרות כוללת")
    markup.row("ניהול הזמנות", "סיכום כללי")
    markup.row("אספקה גורפת", "ביטול כל ההזמנות")
    return markup
