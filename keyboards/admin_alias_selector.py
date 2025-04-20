from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def build_alias_options(users):
    markup = InlineKeyboardMarkup()
    for user_id, bit_name in users:
        btn = InlineKeyboardButton(text=f"{bit_name} (ID: {user_id})", callback_data=f"alias_{user_id}")
        markup.add(btn)
    return markup
