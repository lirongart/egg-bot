from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_panel_inline():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("הפקדה מ־bit", callback_data="bit_deposit"))
    markup.add(InlineKeyboardButton("בדיקת יתרות כוללת", callback_data="total_balance"))
    markup.add(InlineKeyboardButton("ניהול הזמנות", callback_data="manage_orders"))
    markup.add(InlineKeyboardButton("סיכום כללי", callback_data="summary"))
    markup.add(
        InlineKeyboardButton("אספקה גורפת", callback_data="fulfill_all"),
        InlineKeyboardButton("ביטול כל ההזמנות", callback_data="cancel_all")
    )
    return markup
