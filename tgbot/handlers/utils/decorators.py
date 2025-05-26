from functools import wraps
from typing import Callable

from telegram import Update, ChatAction, ParseMode
from telegram.ext import CallbackContext

from users.models import User

def check_blocked_user(func: Callable):
    """
    check_blocked_user decorator
    Used for handlers that check_blocked_user have access to
    """
    @wraps(func)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user = User.get_user(update, context)
        if user.is_blocked_bot:
            text = 'you are blocked'
            context.bot.send_message(
                chat_id=user.user_id,
                text=text,
                parse_mode=ParseMode.HTML
            )
            return
        return func(update, context, *args, **kwargs)
    return wrapper

def admin_only(func: Callable):
    """
    Admin only decorator
    Used for handlers that only admins have access to
    """

    @wraps(func)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user = User.get_user(update, context)

        if not user.is_admin:
            return

        return func(update, context, *args, **kwargs)

    return wrapper

def superadmin_only(func: Callable):
    """
    Super Admin only decorator
    Used for handlers that only superadmins have access to
    """

    @wraps(func)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        user = User.get_user(update, context)

        if not user.is_superadmin:
            return

        return func(update, context, *args, **kwargs)

    return wrapper


def send_typing_action(func: Callable):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update: Update, context: CallbackContext, *args, **kwargs):
        update.effective_chat.send_chat_action(ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func
