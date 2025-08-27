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
# from tgbot.plugins import reports_gitlab, admin_plugin
from tgbot.handlers.broadcast_message.static_text import reports_wrong_format
from dtb.settings import settings, get_plugins_for_roles
from dtb.settings import logger
from tgbot.handlers.utils.decorators import check_groupe_user

@check_groupe_user
def command_dispatcher(update: Update, context: CallbackContext) -> None:
    u, created = User.get_user_and_created(update, context)
    upms = get_tele_command(update)
    telecmd = upms.text
    #plugins = get_plugins(u.get_all_roles())
    text = CRLF+f' dispatcher '+telecmd
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=text,
        parse_mode=ParseMode.HTML
    )
    
@check_groupe_user
def command_help(update: Update, context: CallbackContext) -> None:
    u, created = User.get_user_and_created(update, context)
    upms = get_tele_command(update)
    #user_id = extract_user_data_from_update(update)['user_id']
    if created:
        text = static_text.start_created.format(first_name=u.first_name)
    else:
        text = static_text.start_not_created.format(first_name=u.first_name)

    # Все роли пользователя
    users_roles = u.get_all_roles()
    plugins = get_plugins_for_roles(users_roles) # Получить все доступные плагины пользователю из неблокированных
    #plugins = get_plugins(users_roles) # Получить все доступные плагины пользователю из неблокированных
    # todo get_unblock_plugins 
    text += CRLF+'🔸/start: Кнопки ссылок на модули'
    url = settings.get("SUPPORT_GROUP", "https://t.me/+__Qezxf7-E0xY2I6")
    text += CRLF+f'<a href=\"{url}\">🎯Группа поддержки. Обсуждаем ошибки и разработку новых модулей</a>'
    if u.is_admin:
        url = settings.get("DEVELOP_GROUP", "https://t.me/+LXQkVtnHqSM1ZmZi")
        text += CRLF+f'<a href=\"{url}\">🎯Группа разработки. Обсуждаем и участвуем в разработке бота</a>'
    #if plugins:
    #    text += CRLF+'/plugins: список приложений - плагинов'
    if plugins.get('IRIS'):
        # Если есть доступ к плпгину IRIS
        #text += CRLF+'👉---модуль-IRIS---------'
        text += CRLF+'🔸/servers: Смотреть статус всех серверов IRIS'
        text += CRLF+'/s_TEST: Смотреть продукции сервера TEST'
    if plugins.get('GITLAB'):
        # Если есть доступ к плагину GITLAB
        #text += CRLF+'👉---модуль-GITLAB---------'
        text += CRLF+'🔸/daily: Отчет ежедневный по меткам проекта'
        text += CRLF+'/yesterday: Отчет вчерашний по меткам проекта'
        _i = 0
        
        if reports_gitlab.PROJ_RU:
            for _ru in reports_gitlab.PROJ_RU.split(','):
                if users_roles is not None and (_ru in users_roles or "All" in users_roles):
                    _en = reports_gitlab.PROJ_EN.split(',')[_i]
                    text += CRLF+f'/yesterday_{_en}: Отчет за вчера по метке "{_ru}"'
                    text += CRLF+f'/daily_{_en}: Отчет за сегодня по метке "{_ru}"'
                    text += CRLF+f'/daily_{_en}_noname: Отчет ежедневный по метке "{_ru}" обезличенный'
                    text += CRLF+f'/weekly_{_en}: Отчет еженедельный по первой части $"'
                    text += CRLF
                _i += 1

        text += CRLF
        text += CRLF + reports_wrong_format
    # if plugins.get('GIGA'):
    #     # Если есть доступ к плпгину GIGA
    #     text += CRLF+'👉---модуль-GIGA---------'
    #     text += CRLF+plugins.get('GIGA').get('desc')
    #     text += CRLF + '/giga - список опций модели или задавайте вопросы без команд. Модель пока не помнит контекста'+CRLF

    for pl,val in plugins.items():
        if not (pl in ['GIGA','GITLAB','IRIS']): # кроме встроенных модулей
            if users_roles is not None and (pl in users_roles or "All" in users_roles):
                #text += CRLF + f'👉---модуль-{pl}---------'
                text += CRLF + f"🔸/{pl.lower()} {val.get('desc')}"

    #if u.is_superadmin and (upms.chat.id==u.user_id): # если суперадмин и мы в личном чате с ним
        # text += CRLF+'👉----Super admin options--------'
        # # Если есть доступ к роли суперадмин
        # text += admin_plugin._admin_help
        # # text += CRLF+' 📍/ask_location: Отправить локацию'
        # text += CRLF+' /broadcast Текст рассылаемого сообщения'
        # text += CRLF+' 👥/export_users: Экспорт users.csv'
        # text += CRLF+' /ask_info - информация о состоянии бота'
    
    #text += CRLF+CRLF+'🔸/help: Перечень команд'
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=text,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )

@check_groupe_user
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
    update.message.reply_text(text=text, reply_markup=make_keyboard_for_start_command(u.get_all_roles()))
   
