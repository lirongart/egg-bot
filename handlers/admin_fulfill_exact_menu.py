from loader import bot
from keyboards.admin_supply_menu import get_open_orders_keyboard
from utils.decorators import admin_only, safe_execution
from utils.db_utils import execute_query
from telebot.types import CallbackQuery
def register(bot):

    @bot.callback_query_handler(func=lambda call: call.data == 'cmd_fulfill_exact_menu')
    @admin_only
    @safe_execution
    def open_exact_fulfill_menu(call: CallbackQuery):
    orders = execute_query("SELECT id, user_id, full_name, quantity_l, quantity_xl FROM orders WHERE status = 'pending'", fetch=True)
    if not orders:
        bot.answer_callback_query(call.id, 'אין הזמנות פתוחות כרגע.')
        return
    keyboard = get_open_orders_keyboard(orders, prefix='exact')
    bot.edit_message_text('בחר הזמנה שסופקה במדויק:', call.message.chat.id, call.message.message_id, reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('exact_order_'))
    @admin_only
    @safe_execution
    def mark_as_fulfilled_exact(call: CallbackQuery):
    order_id = int(call.data.split('_')[-1])

    # שליפת הכמויות המקוריות
    res = execute_query("SELECT quantity_l, quantity_xl FROM orders WHERE id = %s", (order_id,), fetch=True)
    if not res:
        bot.answer_callback_query(call.id, 'הזמנה לא נמצאה.')
        return
    l, xl = res[0]

    execute_query("""
        UPDATE orders 
        SET supplied_l = %s, supplied_xl = %s, status = 'supplied' 
        WHERE id = %s
    """, (l, xl, order_id))

    bot.answer_callback_query(call.id, f'הזמנה #{order_id} עודכנה כסופקה במדויק.')
