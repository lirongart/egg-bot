from loader import bot
from keyboards.admin_supply_menu import get_open_orders_keyboard, get_supply_input_keyboard
from utils.decorators import admin_only, safe_execution
from utils.db_utils import execute_query
from telebot.types import Message, CallbackQuery
def register(bot):

    supply_state = {}

    @bot.callback_query_handler(func=lambda call: call.data == 'cmd_fulfill_partial_menu')
    @admin_only
    @safe_execution
    def open_partial_supply_menu(call: CallbackQuery):
    orders = execute_query("SELECT id, user_id, full_name, quantity_l, quantity_xl FROM orders WHERE status = 'pending'", fetch=True)
    if not orders:
        bot.answer_callback_query(call.id, 'אין הזמנות פתוחות כרגע.')
        return
    keyboard = get_open_orders_keyboard(orders, prefix='partial')
    bot.edit_message_text('בחר הזמנה לעדכון אספקה שונה:', call.message.chat.id, call.message.message_id, reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('partial_order_'))
    @admin_only
    @safe_execution
    def prompt_supply_input(call: CallbackQuery):
    order_id = int(call.data.split('_')[-1])
    supply_state[call.from_user.id] = {'order_id': order_id}
    bot.send_message(call.message.chat.id, 'הכנס כמה תבניות L סופקו בפועל להזמנה זו:')

    @bot.message_handler(func=lambda msg: supply_state.get(msg.from_user.id, {}).get('order_id') and 'supplied_l' not in supply_state[msg.from_user.id])
    @admin_only
    @safe_execution
    def get_supplied_l(msg: Message):
    if not msg.text.isdigit():
        bot.send_message(msg.chat.id, 'נא להזין מספר תקני.')
        return
    supply_state[msg.from_user.id]['supplied_l'] = int(msg.text)
    bot.send_message(msg.chat.id, 'הכנס כמה תבניות XL סופקו להזמנה זו:')

    @bot.message_handler(func=lambda msg: supply_state.get(msg.from_user.id, {}).get('supplied_l') is not None and 'supplied_xl' not in supply_state[msg.from_user.id])
    @admin_only
    @safe_execution
    def get_supplied_xl(msg: Message):
    if not msg.text.isdigit():
        bot.send_message(msg.chat.id, 'נא להזין מספר תקני.')
        return

    state = supply_state.pop(msg.from_user.id)
    supplied_l = state['supplied_l']
    supplied_xl = int(msg.text)
    order_id = state['order_id']

    # עדכון במסד
    execute_query("""
        UPDATE orders 
        SET supplied_l = %s, supplied_xl = %s, status = 'supplied' 
        WHERE id = %s
    """, (supplied_l, supplied_xl, order_id))

    bot.send_message(msg.chat.id, f'הוזן בהצלחה: {supplied_l} תבניות L ו־{supplied_xl} תבניות XL להזמנה #{order_id}.')
