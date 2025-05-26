import datetime

from django.utils import timezone
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from tgbot.handlers.onboarding import static_text
from tgbot.handlers.utils.info import extract_user_data_from_update
from users.models import User
from tgbot.handlers.onboarding.keyboards import make_keyboard_for_start_command
from tgbot.handlers.admin.static_text import BR
from tgbot.handlers.admin.reports_gitlab import PROJ_EN, PROJ_RU
from tgbot.handlers.broadcast_message.static_text import reports_wrong_format
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.utils.decorators import check_blocked_user

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
    text += BR+'/start: Кнопки ссылок'
    if plugins:
        text += BR+'/plugins: список приложений - плагинов'
    if plugins.get('IRIS'):
        # Если есть доступ к плпгину IRIS
        text += BR+'👉----plugin-IRIS-'
        text += BR+'/servers: Смотреть статус всех серверов IRIS'
        text += BR+'/s_TEST: Смотреть продукции сервера TEST'
        text += BR
    if plugins.get('GITLAB'):
        # Если есть доступ к плагину GITLAB
        text += BR+'👉----plugin-GITLAB-'
        text += BR+'/daily: Отчет ежедневный по меткам "{proj_labels}"'
        text += BR+'/yesterday: Отчет вчерашний по меткам "{proj_labels}"'
        text += BR
        _i = 0
        if PROJ_RU:
            for _ru in PROJ_RU.split(','):
                if _ru in u.roles or "All" in u.roles:
                    _en = PROJ_EN.split(',')[_i]
                    text += BR+f'/yesterday_{_en}: Отчет за вчера по метке "{_ru}"'
                    text += BR+f'/daily_{_en}: Отчет за сегодня по метке "{_ru}"'
                    text += BR+f'/daily_{_en}_noname: Отчет ежедневный по метке "{_ru}" обезличенный'
                    text += BR+f'/weekly_{_en}: Отчет еженедельный по первой части $"'
                    text += BR
                _i += 1

        text += BR
        text += BR + reports_wrong_format
    if plugins.get('GIGA'):
        # Если есть доступ к плпгину GIGA
        text += BR+'👉----plugin-GIGA-'
        text += BR + 'Задавайте вопросы к Гига-ИИ'
    for pl in plugins.items():
        if not (pl in ['GIGA,"GITLAB','IRIS']):
            pass
    if u.is_superadmin:
        # Если есть доступ к роли суперадмин
        text += BR+'/ask_location: Отправить локацию 📍'
        text += BR+'/export_users: Экспорт users.csv 👥'
    
    text += BR+'/help: Перечень команд'
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
    text += f"{BR}Вам доступны следующие плагины:"
    for pl,val in plugins.items():
        if pl in Roles.split(',') or "All" in Roles.split(','):
            text += f"{BR}/{pl} - {val.get('desc')}"
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