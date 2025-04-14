import threading
import functools
import logging

logger = logging.getLogger(__name__)

# מנעולים לפי פעולות וזהויות משתמשים
_order_locks = {}
_payment_locks = {}
_global_locks = {}

def user_lock(lock_type='order'):
    """
    דקורטור שמבטיח שרק תהליך אחד בו-זמנית מטפל בפעולה עבור משתמש מסוים
    
    Args:
        lock_type: סוג המנעול (order, payment, וכו')
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(message, *args, **kwargs):
            user_id = message.from_user.id
            
            # בחירת המנעול המתאים
            if lock_type == 'order':
                locks_dict = _order_locks
            elif lock_type == 'payment':
                locks_dict = _payment_locks
            else:
                locks_dict = _global_locks
                
            # יצירת מנעול חדש אם לא קיים
            if user_id not in locks_dict:
                locks_dict[user_id] = threading.RLock()
                
            # נעילה והרצת הפונקציה
            lock = locks_dict[user_id]
            try:
                acquired = lock.acquire(timeout=5)  # נסיון להשיג נעילה עם timeout
                if not acquired:
                    logger.warning(f"Lock timeout for user {user_id} on {func.__name__}")
                    bot = kwargs.get('bot')
                    if bot:
                        bot.send_message(user_id, "המערכת עמוסה, נסה שוב מאוחר יותר")
                    return
                    
                return func(message, *args, **kwargs)
            finally:
                if acquired:
                    lock.release()
                    
        return wrapper
    return decorator

def global_lock(name):
    """
    דקורטור שמבטיח שרק תהליך אחד בו-זמנית מטפל בפעולה גלובלית מסוימת
    
    Args:
        name: שם הפעולה הגלובלית
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if name not in _global_locks:
                _global_locks[name] = threading.RLock()
                
            lock = _global_locks[name]
            try:
                acquired = lock.acquire(timeout=10)  # timeout ארוך יותר לפעולות גלובליות
                if not acquired:
                    logger.warning(f"Global lock timeout for {name}")
                    message = args[0] if args else None
                    if message and hasattr(message, 'chat'):
                        bot = kwargs.get('bot')
                        if bot:
                            bot.send_message(message.chat.id, "המערכת עמוסה, נסה שוב מאוחר יותר")
                    return
                    
                return func(*args, **kwargs)
            finally:
                if acquired:
                    lock.release()
                    
        return wrapper
    return decorator