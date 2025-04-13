from keyboards.user_menu import main_menu

def register(bot):
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        bot.reply_to(message, f"👋 ברוך הבא, {message.from_user.first_name}!\nלהמשך, השתמש בתפריט או בפקודה /menu.")

    @bot.message_handler(commands=['menu'])
    def menu(message):
        bot.send_message(message.chat.id, "בחר פעולה:", reply_markup=main_menu())

    @bot.message_handler(func=lambda m: m.text == "הזמנת תבניות")
    def order_eggs(message):
        bot.send_message(message.chat.id, "🥚 פיצ׳ר ההזמנה יתווסף בהמשך לגרסה 2.")

    @bot.message_handler(func=lambda m: m.text == "בדיקת יתרה")
    def check_balance(message):
        bot.send_message(message.chat.id, "💰 בדיקת יתרה תתווסף בהמשך.")

    @bot.message_handler(func=lambda m: m.text == "ההזמנות שלי")
    def my_orders(message):
        bot.send_message(message.chat.id, "📦 צפייה בהזמנות תתווסף בהמשך.")

    @bot.message_handler(commands=['me'])
    def whoami(message):
    bot.send_message(message.chat.id, f"ה־Telegram ID שלך הוא: {message.from_user.id}")

