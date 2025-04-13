from keyboards.user_menu import main_menu
from keyboards.admin_menu import admin_main_menu
from utils.validators import is_admin
from config import DATABASE_URL
import psycopg2

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cursor = conn.cursor()


def register(bot):
    # @bot.message_handler(commands=['start'])
    # def start(message):
    #     user_id = message.from_user.id
    #     bot.reply_to(message, f"👋 ברוך הבא, {message.from_user.first_name}!\nלהמשך, השתמש בתפריט או בפקודה /menu.")

    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        bot.reply_to(message, "ברוך הבא! אנא הזן את שמך:")
        bot.register_next_step_handler(message, register_user)
        
    def register_user(message):
        name = message.text
        user_id = message.from_user.id
    
        # 1. הוספה לטבלת users
        cursor.execute('INSERT INTO users (id, name, balance) VALUES (%s, %s, %s)', (user_id, name, 0))
        conn.commit()
    
        # 2. הוספה לטבלת bit_users
        cursor.execute("""
            INSERT INTO bit_users (user_id, bit_name)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET bit_name = EXCLUDED.bit_name
        """, (user_id, name))

    
        # 3. הצגת תפריט מותאם
        if is_admin(user_id):
            bot.send_message(user_id, f"הרשמה הושלמה, {name}!", reply_markup=admin_main_menu())
        else:
            bot.send_message(user_id, f"הרשמה הושלמה, {name}!", reply_markup=main_menu())
    
        # 4. הצגת ה־user_id למשתמש
        bot.send_message(user_id, f"ℹ️ ה־Telegram ID שלך הוא: {user_id}")
    
        # 5. עדכון למנהל
        bot.send_message(ADMIN_ID, f"🆕 משתמש חדש נרשם:\nשם: {name}\nID: {user_id}\nנוסף ל־bit_users")

        
    @bot.message_handler(commands=['menu'])
    def menu(message):
        if is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "תפריט מנהל:", reply_markup=admin_main_menu())
        else:
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
