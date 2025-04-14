import re

def sanitize_name(name):
    """
    מנקה קלט של שם משתמש
    מסיר תווים מיוחדים ומגביל אורך
    """
    if not name:
        return ""
    # הסרת תווים מיוחדים שעלולים לשמש להזרקת קוד
    sanitized = re.sub(r'[^\w\s\-\u0590-\u05FF]', '', name)
    # הגבלת אורך
    return sanitized[:50]

def validate_quantity(quantity_str):
    """
    מוודא שהכמות היא מספר חיובי שלם
    
    Returns:
        int: כמות מתוקנת או None אם לא תקין
    """
    try:
        quantity = int(quantity_str)
        return quantity if quantity > 0 else None
    except (ValueError, TypeError):
        return None

def validate_size(size):
    """
    מוודא שהמידה היא אחת מהאפשרויות המותרות
    """
    return size if size in ['L', 'XL'] else None

def is_valid_bit_message(text):
    """
    בודק אם הודעת bit היא בפורמט תקין
    """
    # בדיקה בסיסית שההודעה מכילה את כל הפרטים הדרושים
    has_amount = bool(re.search(r'(\d+(?:\.\d+)?)\s*ש[״"]?ח', text))
    has_name = bool(re.search(r'מחכים לך מ(.*?)\s*באפליקציית bit', text))
    has_url = bool(re.search(r'(https://www\.bitpay\.co\.il/app/transaction-info\?i=\S+)', text))
    
    return has_amount and has_name and has_url