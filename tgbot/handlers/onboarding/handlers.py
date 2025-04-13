import datetime

from django.utils import timezone
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from tgbot.handlers.onboarding import static_text
from tgbot.handlers.utils.info import extract_user_data_from_update
from users.models import User
from tgbot.handlers.onboarding.keyboards import make_keyboard_for_start_command
from tgbot.handlers.admin.static_text import BR
from tgbot.handlers.admin.reports_gitlab import PROJ_EN, PROJ_RU
from tgbot.handlers.broadcast_message.static_text import reports_wrong_format


def command_help(update: Update, context: CallbackContext) -> None:
    u, created = User.get_user_and_created(update, context)
    user_id = extract_user_data_from_update(update)['user_id']
    if created:
        text = static_text.start_created.format(first_name=u.first_name)
    else:
        text = static_text.start_not_created.format(first_name=u.first_name)

    text += BR+'/start: Кнопки ссылок'
    # Если есть доступ к плпгину IRIS
    text += BR+'/servers: Смотреть статус всех серверов IRIS'
    text += BR+'/s_TEST: Смотреть продукции сервера TEST'
    text += BR
    # Если есть доступ к плагину Issue Time tracking
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
    
    text += BR+'/ask_location: Отправить локацию 📍'
    text += BR+'/export_users: Экспорт users.csv 👥'
    text += BR+'/help: Перечень команд'
    context.bot.send_message(
        chat_id=u.user_id,
        text=text,
        parse_mode=ParseMode.HTML
    )

def command_start(update: Update, context: CallbackContext) -> None:
    u, created = User.get_user_and_created(update, context)

    if created:
        text = static_text.start_created.format(first_name=u.first_name)
    else:
        text = static_text.start_not_created.format(first_name=u.first_name)

    update.message.reply_text(text=text,
                              reply_markup=make_keyboard_for_start_command())


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