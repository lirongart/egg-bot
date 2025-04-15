# 🥚 EggBot PRO v2.0.1 – Optimized Architecture Release

מערכת ניהול הזמנות וביצוע תשלומים אוטומטית בטלגרם, עם תמיכה מלאה במנהל ומשתמשים, אינטגרציה עם bit, עיצוב מודולרי, ולוגיקה עסקית מתקדמת.

---

## 🚀 מה חדש ב־v2.0.1

- ✅ **אופטימיזציה מלאה של הקוד**: החלפה ל־`execute_query`, טיפול חריגות עקבי עם `@safe_execution`, ומנעולי משתמש `@user_lock`
- 🧩 **מודולריות מקצועית**: קוד מפורק לתיקיות `handlers`, `keyboards`, `utils` – קל לתחזוקה והרחבה
- 🔐 **אבטחת קלט**: ולידציות חכמות, סניטיזציה לשמות, זיהוי הודעות bit תקינות בלבד
- 🧪 **תמיכה מלאה ב־QA**: אינטגרציה עם Google Sheets, כולל סקריפטים להרצת בדיקות מרובות משתמשים

---

## 🧠 יכולות עיקריות

### 👤 למשתמש רגיל
- הזמנת תבניות ביצים לפי מידה וכמות
- בדיקת יתרה
- צפייה בהזמנות פעילות
- ביטול עצמאי של הזמנות ממתינות
- תפריט אינטראקטיבי פשוט בעברית

### 🛠 למנהל
- תפריט מנהל אינטראקטיבי (כולל כפתור פקודות נוספות)
- הפקדה אוטומטית מ־bit (באמצעות הודעת SMS)
- ניהול מלא של ההזמנות:
  - אספקה גורפת או פרטנית
  - ביטול כללי או לפי מזהה
  - ניתוח כללי של יתרות מול התחייבויות
- לוגים אוטומטיים (admin log / bit log)

---

## 🧰 טכנולוגיות וכלים

- `python-telegram-bot` + `pyTelegramBotAPI`
- PostgreSQL
- Flask (לרנדר)
- Google Sheets API + gspread
- Telethon (לבדיקות אוטומטיות)
- Render – ענן להפעלה 24/7

---

## 🧱 מבנה הפרויקט

├── main.py 
├── .env (לא ב־repo, מאוחסן באופן מאובטח)
├── handlers/ │ ├── user_commands.py │ └── admin_commands.py
├── keyboards/ │ 
├── user_menu.py
│ └── admin_menu.py 
├── utils/ │ ├── db_utils.py │ ├── thread_safety.py │ ├── input_validators.py │ ├── exception_handler.py │ └── logger.py ├── logs/ │ ├── bit_log.txt │ └── admin_actions.txt
├── requirements.txt 
└── README.md


---

## ⚙️ הגדרת קובץ `.env` לדוגמה

```env
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_TELEGRAM_ID=123456789
DATABASE_URL=postgresql://user:password@host:port/dbname
GOOGLE_SHEET_ID=spreadsheet_id_here
GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json

 בדיקות QA
כל הבדיקות מריצות תרחישים ידועים

תוצאות נרשמות אוטומטית לגיליון Google Sheets

תמיכה בסימולציה של 3 משתמשים במקביל (Telethon)

🛡️ אבטחה והתמודדות עם עומסים
הגנה על פעולות רגישות עם מנעולים לפי משתמש (@user_lock)

שימוש ב־safe SQL עם פרמטרים

סניטיזציה לקלטים קריטיים

pool של חיבורי DB (תמיכה ב־multithreading)

📦 תוכניות עתידיות (v2.1.x+)
ממשק ויזואלי מתקדם למנהל (תפריט גרפי)

ניהול יתרות לפי קבוצות

התממשקות עם מערכות תשלומים נוספות (לצד bit)

תזכורות אוטומטיות להזמנות פתוחות

חיבור לממשק ניהול מבוסס דפדפן (Dashboard)

📜 רישיון
MIT License

נוצר באהבה ❤ ע״י [לירון] בעזרת ChatGPT


---

💡 **טיפ לסיום**: כדאי גם להוסיף Badge בראש ה־README כמו:

```markdown
![Render Status](https://img.shields.io/badge/render-deployed-brightgreen)
![Version](https://img.shields.io/badge/version-2.0.1-blue)
