from functools import wraps
from telebot.types import Message, CallbackQuery
from utils.validators import is_admin

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
