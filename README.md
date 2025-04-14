# 🥚 EggBot PRO – גרסה 2

בוט טלגרם חכם לניהול קופה קבוצתית ורכישות תבניות ביצים 💸🐣  
כולל ממשק מנהל מלא, לוגיקה מדויקת של הזמנות, ניהול יתרות, הפקדות bit, ו־QA אוטומטי!

---

## 🚀 מה חדש בגרסה 2?

- 🎛 ממשק מודולרי מלא – קוד מסודר לפי תיקיות (handlers, keyboards, utils, etc.)
- 🧠 תפריט אינטראקטיבי מותאם לפי תפקיד (משתמש רגיל / מנהל)
- 📥 הפקדות באמצעות bit – ניתוח אוטומטי של הודעת SMS ועדכון יתרות
- 🧾 ניהול הזמנות חכם – כולל אספקה חלקית, ביטולים, סיכומים ויתרות
- 📊 תיעוד Google Sheets של בדיקות QA
- 🔒 בדיקות שגיאה, פורמטים שגויים, וחוויית משתמש חלקה

---

## 🧱 מבנה תיקיות

```
📦eggbot_pro_v2
├── main.py                     # קובץ ההפעלה
├── config.py                   # משתני סביבה ו־ENV
├── requirements.txt            # ספריות נדרשות
│
├── handlers/
│   ├── user_commands.py        # כל פעולות המשתמש
│   ├── admin_commands.py       # פעולות הניהול
│   └── ...
│
├── keyboards/
│   ├── user_menu.py            # תפריט משתמש
│   ├── admin_menu.py           # תפריט מנהל
│   └── extra_admin.py          # פקודות נוספות (inline)
│
├── utils/
│   ├── logger.py               # לוגים
│   └── validators.py           # בדיקת is_admin
│
└── qa/
    └── qa_runner_pro.py        # בדיקות אוטומטיות ל־QA
```

---

## 🛠 התקנה מקומית

```bash
git clone https://github.com/yourname/eggbot_pro_v2.git
cd eggbot_pro_v2
pip install -r requirements.txt
python main.py
```

🔐 ודא שהגדרת את משתני הסביבה:
- `TELEGRAM_BOT_TOKEN`
- `ADMIN_TELEGRAM_ID`
- `DATABASE_URL`
- `GOOGLE_SHEET_ID`
- `GOOGLE_SERVICE_ACCOUNT_FILE`

---

## 🧪 הרצת QA אוטומטית

```bash
python qa/qa_runner_pro.py
```

התוצאות נשלחות ישירות ל־Google Sheets!

---

## 🧑‍💻 תודות

פיתוח: **לירון**  
הכוונה טכנית, QA, ותיעוד: **ChatGPT שותף פיתוח מלא 🤝**

---

## 📜 רישיון

MIT License – חופשי לשימוש, לשכפל, ולשדרג.
