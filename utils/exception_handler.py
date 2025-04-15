# utils/exception_handler.py
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def safe_execution(error_message="שגיאה כללית בביצוע הפעולה"):
    """
    דקורטור לטיפול בחריגות בפונקציות של הבוט
    """
    def decorator(func):
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            try:
                return func(message, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                if hasattr(message, 'chat'):
                    bot = kwargs.get('bot', None)
                    if bot:
                        bot.send_message(message.chat.id, f"⚠️ {error_message}: {str(e)}")
                    else:
                        print(f"⚠️ {error_message}: {str(e)}")
        return wrapper
    return decorator
