from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from utils.db_utils import execute_query

supply_state = {}

def register(bot):

    # ──────────────────────────────────────────────────────────
    # פונקציה גמישה: יכולה לקבל גם Message וגם CallbackQuery
    # ──────────────────────────────────────────────────────────
    def open_partial_supply_menu(obj):
        try:
            # קביעה האם זה CallbackQuery או Message
            is_cb = isinstance(obj, CallbackQuery)
            user_id = obj.from_user.id if is_cb else obj.from_user.id
            if user_id != ADMIN_ID:
                return

            chat_id    = obj.message.chat.id if is_cb else obj.chat.id
            message_id = obj.message.message_id if is_cb else obj.message_id

            if is_cb:                         # השתקת אנימציית "גלגל"
                bot.answer_callback_query(obj.id)

            orders = execute_query("""
                SELECT id, user_id, name, quantity_l, quantity_xl
                FROM orders
                WHERE status = 'pending'
            """, fetch=True)

            if not orders:
                bot.send_message(chat_id, 'אין הזמנות פתוחות כרגע.')
                return

            markup = InlineKeyboardMarkup()
            for oid, uid, name, l, xl in orders:
                label = f'#{oid} - {name} ({l}L/{xl}XL)'
                markup.add(
                    InlineKeyboardButton(label, callback_data=f'partial_order_{oid}')
                )

            bot.edit_message_text(
                'בחר הזמנה לעדכון אספקה חלקית:',
                chat_id, message_id,
                reply_markup=markup
            )
        except Exception as e:
            print(f'[EXCEPTION] {e}')
            bot.send_message(chat_id, 'שגיאה בביצוע הפעולה.')

    # ────────────────────────────────
    # 1. לחיצה על כפתור Reply ("אספקה שונה")
    #    -> admin_commands יקרא לפונקציה הזו עם Message
    # ────────────────────────────────
    # (אין כאן decorator כי נזמין אותה ידנית)

    # ────────────────────────────────
    # 2. לחיצה על כפתור Inline ("cmd_fulfill_partial_menu")
    #    -> כאן נשאר CallbackQuery קיימת
    # ────────────────────────────────
    @bot.callback_query_handler(func=lambda call: call.data == 'cmd_fulfill_partial_menu')
    def _inline_open_partial(call: CallbackQuery):
        open_partial_supply_menu(call)   # מעביר CallbackQuery

    # ────────────────────────────────
    # שאר הפונקציות (prompt_supply_input, get_supplied_l, get_supplied_xl)
    # נשארות בדיוק כפי שהיו — ללא שינוי
    # ────────────────────────────────

    @bot.callback_query_handler(func=lambda call: call.data.startswith('partial_order_'))
    def prompt_supply_input(call: CallbackQuery):
        try:
            if call.from_user.id != ADMIN_ID:
                return
            order_id = int(call.data.split('_')[-1])
            supply_state[call.from_user.id] = {'order_id': order_id}
            bot.send_message(call.message.chat.id, 'כמה תבניות L סופקו בפועל? (מספר בלבד)')
        except Exception as e:
            print(f'[EXCEPTION] {e}')
            bot.send_message(call.message.chat.id, 'שגיאה בביצוע הפעולה.')

    @bot.message_handler(func=lambda msg: supply_state.get(msg.from_user.id, {}).get('order_id') and 'supplied_l' not in supply_state[msg.from_user.id])
    def get_supplied_l(msg: Message):
        try:
            if msg.from_user.id != ADMIN_ID:
                return
            if not msg.text.isdigit():
                bot.send_message(msg.chat.id, 'נא להזין מספר תקני עבור L.')
                return
            supply_state[msg.from_user.id]['supplied_l'] = int(msg.text)
            bot.send_message(msg.chat.id, 'כמה תבניות XL סופקו בפועל? (מספר בלבד)')
        except Exception as e:
            print(f'[EXCEPTION] {e}')
            bot.send_message(msg.chat.id, 'שגיאה בביצוע הפעולה.')

    @bot.message_handler(func=lambda msg: supply_state.get(msg.from_user.id, {}).get('supplied_l') is not None and 'supplied_xl' not in supply_state[msg.from_user.id])
    def get_supplied_xl(msg: Message):
        try:
            if msg.from_user.id != ADMIN_ID:
                return
            if not msg.text.isdigit():
                bot.send_message(msg.chat.id, 'נא להזין מספר תקני עבור XL.')
                return

            state = supply_state.pop(msg.from_user.id)
            supplied_l = state['supplied_l']
            supplied_xl = int(msg.text)
            order_id = state['order_id']

            res = execute_query("SELECT quantity_l, quantity_xl FROM orders WHERE id = %s", (order_id,), fetch=True)
            if not res:
                bot.send_message(msg.chat.id, '⚠️ ההזמנה לא נמצאה.')
                return

            original_l, original_xl = res[0]
            if supplied_l > original_l or supplied_xl > original_xl:
                bot.send_message(msg.chat.id, f'❌ הכמות שסופקה חורגת מההזמנה ({original_l}L / {original_xl}XL)')
                return

            execute_query("""
                UPDATE orders 
                SET supplied_l = %s, supplied_xl = %s, status = 'supplied' 
                WHERE id = %s
            """, (supplied_l, supplied_xl, order_id))

            bot.send_message(msg.chat.id, f'✅ עודכנה אספקה להזמנה #{order_id}: {supplied_l}L / {supplied_xl}XL')
        except Exception as e:
            print(f'[EXCEPTION] {e}')
            bot.send_message(msg.chat.id, 'שגיאה בביצוע הפעולה.')

    # ========== סוף register ==========
    # ניתן לייצא את open_partial_supply_menu אם תרצה לגשת אליו מבחוץ:
    register.open_partial_supply_menu = open_partial_supply_menu
