from functools import wraps
from typing import Callable

from telegram import Update, ChatAction, ParseMode
from telegram.ext import CallbackContext
from tgbot.handlers.utils.info import get_tele_command
from users.models import User
from dtb.settings import get_plugins_for_roles
from tgbot import plugins
# import pprint as pp

def check_groupe_user(func: Callable):
    """
    check_groupe_user decorator
    Used for handlers that check_groupe_user have access to
    """
    @wraps(func)
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        upms = get_tele_command(update)
        if upms.chat.id<0: # публичные группы имеют отрицательный номер
            plugins.admin_plugin.universal_message_handler(update, context, func)
            return
        plugin_func=func.__doc__.split('plugin ')[1].split(':')[0] if func.__doc__ else None
        print('- func plugin ',plugin_func)

        if plugin_func==None:
            print(' команда не имеет в __doc__ признака plugin ',func.__name__,func.__module__)
            return        
        elif plugin_func !='HELP':
            u, created = User.get_user_and_created(update, context)
            user_roles = u.get_all_roles()
            user_plugins = get_plugins_for_roles(user_roles)   # проверка пользователя на роль и соответсвие ее неблокированным плагинам
            # print('-user plugins ',user_plugins.get(plugin_func))
            if user_plugins.get(plugin_func)==None:
                print(' команда блокирована для ',u.first_name)
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
        #print('-user-',user,user.is_superadmin)
        #pp.pprint(update.to_dict())
        if not user.is_superadmin:
            #print('--user-',user,user.is_superadmin)
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
