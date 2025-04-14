from psycopg2 import pool
from config import DATABASE_URL
import logging

logger = logging.getLogger(__name__)

class DatabasePool:
    """
    מנהל מאגר חיבורים לבסיס הנתונים
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
            try:
                cls._instance.connection_pool = pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=20,  # מספר החיבורים המקסימלי יכול להשתנות לפי צורך
                    dsn=DATABASE_URL
                )
                logger.info("Database connection pool created")
            except Exception as e:
                logger.error(f"Error creating connection pool: {e}")
                raise
        return cls._instance
    
    def get_connection(self):
        """מחזיר חיבור מהמאגר"""
        return self.connection_pool.getconn()
    
    def release_connection(self, connection):
        """מחזיר חיבור למאגר"""
        self.connection_pool.putconn(connection)
    
    def close_all(self):
        """סוגר את כל החיבורים במאגר"""
        self.connection_pool.closeall()

# פונקציית עזר לשימוש עם מנהל הקשר
def get_connection():
    """מחזיר חיבור מהמאגר"""
    return DatabasePool().get_connection()

def release_connection(connection):
    """מחזיר חיבור למאגר"""
    DatabasePool().release_connection(connection)