from telebot import TeleBot
from flask import Flask
from config import TOKEN

# יצירת מופע הבוט
bot = TeleBot(TOKEN)

# יצירת מופע Flask (לשימוש אם אתה מפעיל Webhook)
app = Flask(__name__)
