# 📦 EggBot PRO – CHANGELOG

## 🧾 Version: 2.0.1 – Optimized Architecture (2025-04-16)

### 🎯 Overview:
גרסה זו משדרגת את הארכיטקטורה של הבוט באופן יסודי, תוך התמקדות באבטחה, ביצועים, נגישות לתחזוקה, וריבוי משתמשים בו־זמנית.

---

### ✅ Improvements

#### 🔹 DB Interaction (psycopg2)
- הוספה של מודול `db_utils.py`:
  - פונקציית `execute_query(...)` לביצוע שאילתות בצורה בטוחה.
  - פונקציית `get_db_connection()` לניהול חיבורים עם context manager.
- כל השאילתות הועברו ל־`execute_query(...)`.

#### 🔹 Error Handling
- יצירת `exception_handler.py` כולל:
  - דקורטור `@safe_execution` המונע קריסת הפונקציה במקרה של שגיאה.
  - הודעות שגיאה מותאמות למשתמש, ולוגים מסודרים.

#### 🔹 Concurrency Locking
- הוספת `thread_safety.py`:
  - `@user_lock()` – למניעת גישה כפולה לאותו משתמש.
  - `@global_lock()` – לפעולות מנהל גלובליות כמו `אספקה גורפת`.

#### 🔹 Input Validators
- הוספת `input_validators.py`:
  - פונקציות `sanitize_name`, `validate_quantity`, `validate_size`, `is_valid_bit_message`.

#### 🔹 Code Modularity
- פיצול מלא לפי תחומי אחריות:
  - `handlers/user_commands.py` – פעולות משתמש.
  - `handlers/admin_commands.py` – פעולות מנהל.
  - `keyboards/user_menu.py`, `admin_menu.py`, `extra_admin.py`, `user_cancel_menu.py`.
  - `utils/` – קבצים תשתיתיים (DB, Errors, Validators, Logging...).

---

### 🧑‍💼 Admin Features

- 🟢 **הפקדה דרך bit**: זיהוי אוטומטי מתוך הודעת SMS.
- 🟢 **סיכום כללי** של יתרות משתמשים והזמנות פתוחות.
- 🟢 **ניהול הזמנות**: צפייה, ביטול, אספקה מדויקת או גורפת.
- 🟢 **פקודות נוספות** דרך תפריט אינטראקטיבי (`/cancel`, `/fulfill`, `/me`).
- 🟢 **לוגים מנהליים** נשמרים בקובץ `logs/admin_actions.txt`.

---

### 🙋 User Features

- ✅ תפריט מותאם אישי (משתמש/מנהל).
- ✅ הרשמה חדשה עם שם → הזנת ID → עדכון `bit_users` אוטומטי.
- ✅ הזמנת תבניות (L / XL) עם ולידציה מלאה.
- ✅ הצגת הזמנות פתוחות בלבד.
- ✅ ביטול עצמי של הזמנות (דרך תפריט אינטראקטיבי).
- ✅ בדיקת יתרה עם פירוט סכומים בהמתנה.

---

### 🛠 Fixes

- ⚠️ תיקון כפילות בקוד `admin_summary`.
- 🧹 הוספת `datetime` בכל הקבצים החסרים.
- 💥 הגנה מפני הזנת כמות שלילית/שגויה.
- 🚫 הגנה על אספקה לא חוקית (XL במקום L).

---

### 📁 File Structure (חדש)

project-root/ │ 
├── main.py 
├── config.py 
├── requirements.txt │ 
├── handlers/ │ ├── user_commands.py │ └── admin_commands.py │ 
├── keyboards/ │ ├── user_menu.py │ ├── admin_menu.py │ ├── extra_admin.py │ └── user_cancel_menu.py │ 
├── utils/ │ ├── db_utils.py │ ├── db_pool.py │ ├── exception_handler.py │ ├── input_validators.py │ ├── logger.py 
│ └── thread_safety.py 
│ └── logs/ 
├── bit_log.txt 
└── admin_actions.txt


---

### 🔜 Coming Soon (v2.1.x)
- 🔍 לוח ניתוחים למנהל (מכירות, יתרות).
- 📤 שליחת סיכום שבועי אוטומטי.
- 🧾 מערכת חיוב ללקוחות.
- 📱 התממשקות ל־CRM או וואטסאפ ביזנס.

