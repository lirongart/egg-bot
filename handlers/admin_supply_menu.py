from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.db_utils import execute_query
from utils.decorators import admin_only, safe_execution

supply_state = {}

def register(bot):

    # שלב 1: פתיחת רשימת ההזמנות הפתוחות לבחירה
    @bot.callback_query_handler(func=lambda call: call.data == 'cmd_fulfill_partial_menu')
    @admin_only
    @safe_execution
    def open_partial_supply_menu(call: CallbackQuery):
        orders = execute_query("SELECT id, user_id, full_name, quantity_l, quantity_xl FROM orders WHERE status = 'pending'", fetch=True)
        if not orders:
            bot.answer_callback_query(call.id, 'אין הזמנות פתוחות כרגע.')
            return

        markup = InlineKeyboardMarkup()
        for oid, uid, name, l, xl in orders:
            label = f'#{oid} - {name} ({l}L/{xl}XL)'
            markup.add(InlineKeyboardButton(label, callback_data=f'partial_order_{oid}'))

        bot.edit_message_text('בחר הזמנה לעדכון אספקה חלקית:', call.message.chat.id, call.message.message_id, reply_markup=markup)

    # שלב 2: התחלת תהליך האספקה להזמנה שנבחרה
    @bot.callback_query_handler(func=lambda call: call.data.startswith('partial_order_'))
    @admin_only
    @safe_execution
    def prompt_supply_input(call: CallbackQuery):
        order_id = int(call.data.split('_')[-1])
        supply_state[call.from_user.id] = {'order_id': order_id}
        bot.send_message(call.message.chat.id, 'כמה תבניות **L** סופקו בפועל? (מספר בלבד)')

    # שלב 3: קליטת כמות L
    @bot.message_handler(func=lambda msg: supply_state.get(msg.from_user.id, {}).get('order_id') and 'supplied_l' not in supply_state[msg.from_user.id])
    @admin_only
    @safe_execution
    def get_supplied_l(msg: Message):
        if not msg.text.isdigit():
            bot.send_message(msg.chat.id, 'נא להזין מספר תקני עבור L.')
            return

        supply_state[msg.from_user.id]['supplied_l'] = int(msg.text)
        bot.send_message(msg.chat.id, 'כמה תבניות **XL** סופקו בפועל? (מספר בלבד)')

    # שלב 4: קליטת כמות XL וסיום
    @bot.message_handler(func=lambda msg: supply_state.get(msg.from_user.id, {}).get('supplied_l') is not None and 'supplied_xl' not in supply_state[msg.from_user.id])
    @admin_only
    @safe_execution
    def get_supplied_xl(msg: Message):
        if not msg.text.isdigit():
            bot.send_message(msg.chat.id, 'נא להזין מספר תקני עבור XL.')
            return

        state = supply_state.pop(msg.from_user.id)
        supplied_l = state['supplied_l']
        supplied_xl = int(msg.text)
        order_id = state['order_id']

        # שליפת ההזמנה מהמסד לאימות
        res = execute_query("SELECT quantity_l, quantity_xl FROM orders WHERE id = %s", (order_id,), fetch=True)
        if not res:
            bot.send_message(msg.chat.id, '⚠️ ההזמנה לא נמצאה.')
            return

        original_l, original_xl = res[0]
        if supplied_l > original_l or supplied_xl > original_xl:
            bot.send_message(msg.chat.id, f'❌ לא ניתן לעדכן. הכמות שסופקה חורגת מהכמות המקורית: {original_l}L / {original_xl}XL')
            return

        execute_query("""
            UPDATE orders 
            SET supplied_l = %s, supplied_xl = %s, status = 'supplied' 
            WHERE id = %s
        """, (supplied_l, supplied_xl, order_id))

        bot.send_message(msg.chat.id, f'✅ עודכנה אספקה להזמנה #{order_id}: {supplied_l}L / {supplied_xl}XL')
