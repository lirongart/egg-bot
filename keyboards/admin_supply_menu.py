from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_open_orders_keyboard(orders, prefix):
    markup = InlineKeyboardMarkup()
    for oid, uid, name, l, xl in orders:
        text = f'#{oid} - {name} ({l}L/{xl}XL)'
        markup.add(InlineKeyboardButton(text, callback_data=f'{prefix}_order_{oid}'))
    return markup
