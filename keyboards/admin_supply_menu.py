from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_open_orders_keyboard(orders, prefix):
    markup = InlineKeyboardMarkup()
    for oid, uid, name, l, xl in orders:
        text = f'#{oid} - {name} ({l}L/{xl}XL)'
        markup.add(InlineKeyboardButton(text, callback_data=f'{prefix}_order_{oid}'))
    return markup

def get_supply_input_keyboard(order_id):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton('🔻 עדכן L', callback_data=f'supply_input_{order_id}_L'),
        InlineKeyboardButton('🔻 עדכן XL', callback_data=f'supply_input_{order_id}_XL'),
    )
    markup.add(InlineKeyboardButton('✅ אשר אספקה', callback_data=f'confirm_supply_{order_id}'))
    return markup