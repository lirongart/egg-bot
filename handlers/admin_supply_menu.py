from telebot.types import Message, CallbackQuery
from keyboards.admin import get_open_orders_keyboard, get_supply_input_keyboard
from utils.db_utils import execute_query
from utils.decorators import admin_only, safe_execution
from loader import bot

@bot.message_handler(commands=['supply_menu'])
@admin_only
@safe_execution
def show_open_orders(message: Message):
    query = "SELECT id, user_id, full_name, quantity_l, quantity_xl FROM orders WHERE status = 'pending'"
    orders = execute_query(query, fetch=True)
    if not orders:
        bot.send_message(message.chat.id, 'אין הזמנות ממתינות כרגע.')
        return
    keyboard = get_open_orders_keyboard(orders)
    bot.send_message(message.chat.id, 'בחר הזמנה לעדכון אספקה:', reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith('supply_order_'))
@safe_execution
def prompt_supply_input(call: CallbackQuery):
    order_id = int(call.data.split('_')[-1])
    keyboard = get_supply_input_keyboard(order_id)
    bot.edit_message_text('בחר כמות שסופקה מכל מידה:', call.message.chat.id, call.message.message_id, reply_markup=keyboard)
