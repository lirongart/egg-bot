from telebot.types import Message
from utils.db_utils import execute_query
from utils.decorators import admin_only, safe_execution
from loader import bot

admin_broadcast_state = {}

@bot.message_handler(commands=['broadcast'])
@admin_only
@safe_execution
def start_broadcast(message: Message):
    admin_broadcast_state[message.chat.id] = True
    bot.send_message(message.chat.id, 'שלח את ההודעה שברצונך להעביר לכל המשתמשים:')

@bot.message_handler(func=lambda msg: admin_broadcast_state.get(msg.chat.id))
@admin_only
@safe_execution
def send_broadcast(msg: Message):
    admin_broadcast_state.pop(msg.chat.id, None)
    text = msg.text
    users = execute_query("SELECT telegram_id FROM users", fetch=True)
    count = 0
    for uid, in users:
        try:
            bot.send_message(uid, text)
            count += 1
        except:
            pass
    bot.send_message(msg.chat.id, f'הודעה נשלחה ל־{count} משתמשים.')
