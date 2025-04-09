import telebot
import psycopg2
import os
from datetime import datetime

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

bot = telebot.TeleBot(TOKEN)

ADMIN_ID = int(os.environ.get('ADMIN_TELEGRAM_ID', '0'))

PRICE_L = 36
PRICE_XL = 39

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL found in environment variables")

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    name TEXT,
    balance REAL DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    name TEXT,
    quantity INTEGER,
    size TEXT,
    ordered_date TEXT,
    fulfilled INTEGER DEFAULT 0,
    fulfilled_quantity INTEGER DEFAULT 0,
    fulfilled_date TEXT
)
""")

# (המשך הקוד שלך אמור להיות כאן: handlers וכו')
print("Bot is starting...")
bot.polling(none_stop=True)
