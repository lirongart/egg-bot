import psycopg2
from config import DATABASE_URL
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """מספק חיבור לבסיס נתונים בצורה בטוחה עם טיפול בסגירת חיבור"""
    connection = None
    try:
        connection = psycopg2.connect(DATABASE_URL)
        connection.autocommit = True
        yield connection
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

def execute_query(query, params=None, fetch=None):
    """
    מבצע שאילתה למסד הנתונים עם טיפול שגיאות
    
    Args:
        query: שאילתת SQL
        params: פרמטרים לשאילתה (tuple או dict)
        fetch: אחד מ-'one', 'all', או None אם לא נדרשת תוצאה
        
    Returns:
        תוצאת השאילתה לפי הפרמטר fetch
    """
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                
                if fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'all':
                    return cursor.fetchall()
                return None
        except psycopg2.Error as e:
            logger.error(f"Query execution error: {e}")
            logger.error(f"Query: {query}, Params: {params}")
            raise