# תיקון ממוקד: הפיכת כפתור "פקודות נוספות" לתפריט אינטראקטיבי בלבד

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.admin_menu import admin_main_menu
from utils.exception_handler import safe_execution
from utils.admin_check import admin_only
import handlers.admin_fulfill_exact_menu as fulfill_exact_menu
import handlers.admin_supply_menu as supply_menu
import handlers.admin_broadcast as broadcast

# תפריט אינליין חדש עבור כפתור "פקודות נוספות"
def get_admin_extra_menu():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("📦 אספקה מדויקת", callback_data="cmd_fulfill_exact_menu"),
        InlineKeyboardButton("🔄 אספקה עם מידה שונה", callback_data="cmd_fulfill_partial_menu"),
        InlineKeyboardButton("📢 שלח הודעה", callback_data="cmd_broadcast")
    )
    return markup

# מאזין לכפתור הישן מסוג ReplyKeyboardButton
@bot.message_handler(func=lambda msg: msg.text == "פקודות נוספות")
@safe_execution
@admin_only
def handle_extra_menu_entry(msg):
    bot.send_message(msg.chat.id, "בחר פעולה נוספת:", reply_markup=get_admin_extra_menu())

# הרשמה של המודולים שכבר קיימים
fulfill_exact_menu.register(bot)
supply_menu.register(bot)
broadcast.register(bot)

# ודא שכל callback_data שהוגדר בתפריט הזה באמת נתמך על ידי המודולים לעיל
