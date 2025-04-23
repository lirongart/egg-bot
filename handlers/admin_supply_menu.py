@bot.callback_query_handler(func=lambda call: call.data == 'cmd_fulfill_partial_menu')
@admin_only
@safe_execution
def open_partial_supply_menu(call):
    orders = execute_query("SELECT id, user_id, full_name, quantity_l, quantity_xl FROM orders WHERE status = 'pending'", fetch=True)
    if not orders:
        bot.answer_callback_query(call.id, 'אין הזמנות פתוחות כרגע.')
        return
    keyboard = InlineKeyboardMarkup()
    for oid, _, name, l, xl in orders:
        label = f'#{oid} - {name} ({l}L/{xl}XL)'
        keyboard.add(InlineKeyboardButton(label, callback_data=f'edit_partial_{oid}'))
    bot.edit_message_text('בחר הזמנה לעדכון אספקה חלקית:', call.message.chat.id, call.message.message_id, reply_markup=keyboard)

