from functools import wraps
from typing import Callable

from telegram import Update, ChatAction, ParseMode
from telegram.ext import CallbackContext
from tgbot.handlers.utils.info import get_tele_command
from users.models import User
from dtb.settings import logger
import pprint as pp

def universal_message_handler(update, context):
    upms = get_tele_command(update)
    message = upms
    #pp.pprint(update.to_dict())
    if message.text:
        log = (f"Из {upms.chat.id} Пользователь {upms.from_user.id} отправил текст: {message.text} ")
        logger.info(log)
    elif message.document:
        log = (f"Из {upms.chat.id} Пользователь {upms.from_user.id} прислал документ: {message.document.file_name}")
        logger.info(log)
    elif message.audio or message.voice:
        log = (f"Из {upms.chat.id} Пользователь {upms.from_user.id} прислал голосовое сообщение")
        logger.info(log)
    else:
        log = (f"!Поступило другое событие: {message}")
        logger.info(log)
    #pp.pprint(upms.to_dict())

def check_blocked_user(func: Callable):
    """
    check_blocked_user decorator
    Used for handlers that check_blocked_user have access to
    """
    @wraps(func)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        upms = get_tele_command(update)
        if upms.chat.id<0: # публичные группы имеют отрицательный номер
            universal_message_handler(update, context)
            return
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
