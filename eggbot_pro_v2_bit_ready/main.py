from telebot import TeleBot
from config import TOKEN
from handlers import user_commands, admin_commands

bot = TeleBot(TOKEN)

user_commands.register(bot)
admin_commands.register(bot)

print("EggBot PRO v2 is running...")
bot.infinity_polling()
