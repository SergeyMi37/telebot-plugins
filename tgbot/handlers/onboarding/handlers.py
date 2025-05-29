import datetime

from django.utils import timezone
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.handlers.onboarding import static_text
from tgbot.handlers.utils.info import extract_user_data_from_update, get_tele_command
from users.models import User
from tgbot.handlers.onboarding.keyboards import make_keyboard_for_start_command
from tgbot.handlers.admin.static_text import CRLF
from tgbot.plugins import reports_gitlab
from tgbot.handlers.broadcast_message.static_text import reports_wrong_format
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.utils.decorators import check_blocked_user

@check_blocked_user
def command_dispatcher(update: Update, context: CallbackContext) -> None:
    u, created = User.get_user_and_created(update, context)
    telecmd, upms = get_tele_command(update)
    plugins = get_plugins(u.roles)
    text = CRLF+'dispatcher '+telecmd
    context.bot.send_message(
        chat_id=u.user_id,
        text=text,
        parse_mode=ParseMode.HTML
    )
@check_blocked_user
def command_help(update: Update, context: CallbackContext) -> None:
    u, created = User.get_user_and_created(update, context)
    user_id = extract_user_data_from_update(update)['user_id']
    if created:
        text = static_text.start_created.format(first_name=u.first_name)
    else:
        text = static_text.start_not_created.format(first_name=u.first_name)

    plugins = get_plugins(u.roles)
    #print(u.roles,plugins)
    text += CRLF+'/start: Кнопки ссылок'
    if plugins:
        text += CRLF+'/plugins: список приложений - плагинов'
    if plugins.get('IRIS'):
        # Если есть доступ к плпгину IRIS
        text += CRLF+'👉----plugin-IRIS---------'
        text += CRLF+'/servers: Смотреть статус всех серверов IRIS'
        text += CRLF+'/s_TEST: Смотреть продукции сервера TEST'
        text += CRLF
    if plugins.get('GITLAB'):
        # Если есть доступ к плагину GITLAB
        text += CRLF+'👉----plugin-GITLAB---------'
        text += CRLF+'/daily: Отчет ежедневный по меткам проекта'
        text += CRLF+'/yesterday: Отчет вчерашний по меткам проекта'
        text += CRLF+CRLF
        _i = 0
        if reports_gitlab.PROJ_RU:
            for _ru in reports_gitlab.PROJ_RU.split(','):
                if _ru in u.roles or "All" in u.roles:
                    _en = reports_gitlab.PROJ_EN.split(',')[_i]
                    text += CRLF+f'/yesterday_{_en}: Отчет за вчера по метке "{_ru}"'
                    text += CRLF+f'/daily_{_en}: Отчет за сегодня по метке "{_ru}"'
                    text += CRLF+f'/daily_{_en}_noname: Отчет ежедневный по метке "{_ru}" обезличенный'
                    text += CRLF+f'/weekly_{_en}: Отчет еженедельный по первой части $"'
                    text += CRLF
                _i += 1

        text += CRLF
        text += CRLF + reports_wrong_format
    if plugins.get('GIGA'):
        # Если есть доступ к плпгину GIGA
        text += CRLF+'👉----plugin-GIGA---------'
        text += CRLF + 'Задавайте вопросы к Гига-ИИ'+CRLF
    Roles=u.roles
    for pl,val in plugins.items():
        if not (pl in ['GIGA','GITLAB','IRIS']): # кроме встроенных модулей
            if pl in Roles.split(',') or "All" in Roles.split(','):
                text += CRLF + f'👉----plugin-{pl}---------'
                text += CRLF + f"/{pl.lower()} {val.get('desc')}{CRLF}"
    if u.is_superadmin:
        text += CRLF+'👉----Super admin options--------'
        # Если есть доступ к роли суперадмин
        text += CRLF+'/ask_location: Отправить локацию 📍'
        text += CRLF+'/broadcast Текст рассылаемого сообщения'
        text += CRLF+'/export_users: Экспорт users.csv 👥'
    
    text += CRLF+CRLF+'/help: Перечень команд'
    context.bot.send_message(
        chat_id=u.user_id,
        text=text,
        parse_mode=ParseMode.HTML
    )

@check_blocked_user
def command_start(update: Update, context: CallbackContext) -> None:
    u, created = User.get_user_and_created(update, context)

    if created:
        text = static_text.start_created.format(first_name=u.first_name)
    else:
        text = static_text.start_not_created.format(first_name=u.first_name)
    
    '''
    markup = InlineKeyboardMarkup('',row_width=2)
    
    # Добавляем первую строку с двумя кнопками
    button1 = InlineKeyboardButton("Кнопка 1", callback_data="button1")
    button2 = InlineKeyboardButton("Кнопка 2", callback_data="button2")
    markup.add(button1, button2)
    
    # Вторая строка с одной кнопкой
    button3 = InlineKeyboardButton("Кнопка 3", callback_data="button3")
    markup.add(button3)
    update.message.reply_text(text=text, reply_markup=markup)

    '''
    update.message.reply_text(text=text, reply_markup=make_keyboard_for_start_command(u.roles))
   
@check_blocked_user
def command_plugins(update: Update, context: CallbackContext) -> None:
    u, created = User.get_user_and_created(update, context)

    if created:
        text = static_text.start_created.format(first_name=u.first_name)
    else:
        text = static_text.start_not_created.format(first_name=u.first_name)
    Roles=u.roles
    plugins = get_plugins('')
    text += f"{CRLF}Вам доступны следующие плагины:"
    for pl,val in plugins.items():
        if pl in Roles.split(',') or "All" in Roles.split(','):
            text += f"{CRLF}/{pl.lower()} - {val.get('desc')}{CRLF}"
    update.message.reply_text(text=text)

# depricate
@check_blocked_user
def secret_level(update: Update, context: CallbackContext) -> None:
    # callback_data: SECRET_LEVEL_BUTTON variable from manage_data.py
    """ Pressed 'secret_level_button_text' after /start command"""
    user_id = extract_user_data_from_update(update)['user_id']
    text = static_text.unlock_secret_room.format(
        user_count=User.objects.count(),
        active_24=User.objects.filter(updated_at__gte=timezone.now() - datetime.timedelta(hours=24)).count()
    )

    context.bot.edit_message_text(
        text=text,
        chat_id=user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )