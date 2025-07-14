from functools import wraps
from typing import Callable

from telegram import Update, ChatAction, ParseMode
from telegram.ext import CallbackContext
from tgbot.handlers.utils.info import get_tele_command
from users.models import User
from dtb.settings import logger
from tgbot import plugins

def check_groupe_user(func: Callable):
    """
    check_groupe_user decorator
    Used for handlers that check_groupe_user have access to
    """
    @wraps(func)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        # user = User.get_user(update, context)
        # if user.is_blocked_bot:
        #     text = 'вы блокированы" # you are blocked'
        #     print(text,user.first_name)
            # context.bot.send_message(
            #     chat_id=user.user_id,
            #     text=text,
            #     parse_mode=ParseMode.HTML
            # )
            #return
        upms = get_tele_command(update)
        if upms.chat.id<0: # публичные группы имеют отрицательный номер
            plugins.admin_plugin.universal_message_handler(update, context, func)
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
