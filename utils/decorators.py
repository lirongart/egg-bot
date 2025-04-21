from functools import wraps
from telebot.types import Message, CallbackQuery
from utils.validators import is_admin

def safe_execution(error_message="שגיאה כללית בביצוע הפעולה"):
    def decorator(func):
        @wraps(func)
        def wrapper(message_or_call, *args, **kwargs):
            try:
                return func(message_or_call, *args, **kwargs)
            except Exception as e:
                print(f'[⚠️ EXCEPTION] {e}')
                try:
                    chat_id = (
                        message_or_call.chat.id
                        if isinstance(message_or_call, Message)
                        else message_or_call.message.chat.id
                    )
                    func_name = getattr(func, '__name__', 'פונקציה')
                    func.__globals__['bot'].send_message(chat_id, f'{error_message} ({func_name})')
                except:
                    pass
        return wrapper
    return decorator

def admin_only(func):
    @wraps(func)
    def wrapper(message_or_call, *args, **kwargs):
        user_id = (
            message_or_call.from_user.id
            if isinstance(message_or_call, (Message, CallbackQuery))
            else None
        )
        if user_id is None or not is_admin(user_id):
            return
        return func(message_or_call, *args, **kwargs)
    return wrapper
