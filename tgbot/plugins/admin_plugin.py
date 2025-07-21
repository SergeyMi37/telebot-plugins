# Name Plugin: ADMIN
    # - ADMIN:
    #     - desc = Модуль создания, просмотра, удаления, редактирования и запуска регулярных задач /tasks
# имя плагина CHAT должно совпадать с именем в конфигурации Dynaconf
# имя плагина chat должно быть первым полем от _ в имени файла chat_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class Plugin(BasePlugin):
#    def setup_handlers(self, dp):
# Определены функции 
# _admin_help - определена переменная, которая используется в button_admin, и command_admin
# ADMIN_INPUT = range(1)  - определена переменная, которая используется в диалогах

from django.utils.timezone import now
from datetime import timedelta
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.admin import static_text
from users.models import User
import pprint as pp
import string
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from tgbot.plugins.base_plugin import BasePlugin
from dtb.settings import TELEGRAM_LOGS_CHAT_ID, DEBUG, settings
from tgbot.handlers.utils.decorators import check_groupe_user, superadmin_only, send_typing_action
from tgbot.handlers.admin.utils import _get_csv_from_qs_values, GetExtInfo
from users.models import Options

ADMIN_INPUT = range(1)
_admin_help = '🌏/ask_location: Отправить локацию \n👇/broadcast Текст рассылаемого сообщения ' \
'\n👥/admin_export_users: Экспорт users.csv\n⬇️/admin_info - информация о состоянии бота'
            
# try:
#     option = get_plugins('').get('ADMIN').get("option")
# except Exception as e:
#     option = '' # ??? нужны ли 

# Список запрещенных слов (в нижнем регистре) TODO - в будущем хранить в бд
FORBIDDEN_WORDS = ["укра", "хох", "сво", "русня"]
obj = Options.get_by_name_and_category(name="FORBIDDEN_WORDS")
if obj:
    FORBIDDEN_WORDS = obj.value.split(",")
else:
    print("Объект FORBIDDEN_WORDS не найден.")

print("Запрещенные слова",FORBIDDEN_WORDS) # При изменении словаря, нужно перезагружать бота

# Создаем строку с дополнительными символами пунктуации
EXTRA_PUNCTUATION = '«»„“‟‘’‚‛”’–—…•‹›'
ALL_PUNCTUATION = string.punctuation + EXTRA_PUNCTUATION

def contains_forbidden_words(text: str, forbidden_words: set) -> bool:
    """
    Проверяет текст на наличие запрещенных слов.
    
    :param text: текст сообщения
    :param forbidden_words: множество запрещенных слов
    :return: True если найдено запрещенное слово, иначе False
    """
    # Приводим текст к нижнему регистру
    text_lower = text.lower()

    # Проверяем каждое запрещенное слово как подстроку
    for word in forbidden_words:
        if word in text_lower:
            return True
    return False

def universal_message_handler(update, context, func=""):
    upms = get_tele_command(update)
    # todo сохранять в бд все обновления
    message = upms
    #pp.pprint(update.to_dict())
    funcname = func.__name__ if func else ''
    if message.text:
        log = (f"Из {upms.chat.id} Пользователь {upms.from_user.id} отправил текст: {message.text} функция {funcname} ")
        logger.info(log)
        if contains_forbidden_words(message.text, FORBIDDEN_WORDS):
            delete_message(update, context,upms.chat.id, message.message_id)
            delete_user(update, context,upms.chat.id, upms.from_user.id)
            context.bot.send_message(
                chat_id=upms.chat.id,
                text=f"⚠️ Обнаружены запрещенные слова! Пожалуйста, соблюдайте правила чата.",
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML
                )
            # kick_user(update, context, upms.chat.id, upms.from_user.id)
            return 
        if '/help' in message.text:
            return #func(update, context) # Ошибка и при бродкаст
    elif message.document:
        log = (f"Из {upms.chat.id} Пользователь {upms.from_user.id} прислал документ: {message.document.file_name}")
        logger.info(log)
    elif message.audio or message.voice:
        log = (f"Из {upms.chat.id} Пользователь {upms.from_user.id} прислал голосовое сообщение")
        logger.info(log)
    elif message.new_chat_members:
        log = (f"Добавлен член: {message.new_chat_members}")
        logger.info(log)
        delete_message(update, context,upms.chat.id, message.message_id)
    elif message.left_chat_member:
        log = (f"Член оставил группу: {message.left_chat_member}")
        logger.info(log)
        delete_message(update, context,upms.chat.id, message.message_id)
    elif message.new_chat_photo:
        log = (f"Изменено фото группы:  Пользователь {upms.from_user.id} {message.new_chat_photo}")
        logger.info(log)
        delete_message(update, context,upms.chat.id, message.message_id)
    
    else:
        log = (f"!Поступило другое событие: {message}")
        logger.info(log)
        pp.pprint(update.to_dict())  # , depth=2)
    #pp.pprint(upms.to_dict())

# Забанить пользователя
def delete_user(update: Update, context: CallbackContext,chat_id, user_id):
    try:
        # Удаление пользователя
        #TelegramDeprecationWarning: `bot.kick_chat_member` is deprecated. Use `bot.ban_chat_member` instead.
        #context.bot.kick_chat_member(chat_id=chat_id, user_id=user_id)
        context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        return 200
    except Exception as e:
        print(e)
        #update.message.reply_text(f"Произошла ошибка при удалении сообщения {message_id}.")
        return f'{e}'

# Функция обработки команды delete_message
def delete_message(update: Update, context: CallbackContext,chat_id, message_id):
    try:
        # Удаление указанного сообщения
        context.bot.deleteMessage(chat_id=chat_id, message_id=message_id)
        #update.message.reply_text(f"Сообщение {message_id} успешно удалено!")
        return 200
    except Exception as e:
        print(e)
        #update.message.reply_text(f"Произошла ошибка при удалении сообщения {message_id}.")
        return f'{e}'

# Функция Блокирования пользователя
def kick_user(update: Update, context: CallbackContext,chat_id, user_id):
    try:
        # Удаление указанного сообщения
        context.bot.kick_chat_member(chat_id=chat_id,user_id=user_id)
        # Метод unban_chat_member автоматически делает временный бан (удаление без полного запрета)
        #context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        return 200
    except Exception as e:
        print(e)
        #update.message.reply_text(f"Произошла ошибка при удалении сообщения {message_id}.")
        return f'{e}'


@check_groupe_user
@superadmin_only
def admin_info(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    a24 = User.objects.filter(updated_at__gte=now() - timedelta(hours=24))
    text = static_text.users_amount_stat.format(
        user_count = f'{User.objects.count()} /admin_export_users',  # count may be ineffective if there are a lot of users.
        active_24 = f"{a24.count()} {list(a24.values_list('first_name', flat=True))}"
        )
    #print(list(a24.values_list('user_id', flat=True)))
    works = 1 if DEBUG else settings.get("workers", 4)
    text += f' {GetExtInfo.GetOS()}\n🚧 DEBUG: {DEBUG}\n Потоков: {works}\n😎 chat_id: {u.user_id} \
        \n🚨 TELEGRAM_LOGS_CHAT_ID: {TELEGRAM_LOGS_CHAT_ID} {GetExtInfo.GetHostInfo()} \
        {GetExtInfo.GetExtIp()} {GetExtInfo.GetGitInfo()} \
        \n\n🔸/help: Перечень команд'
    context.bot.send_message(
        chat_id=u.user_id, # вернуть личный чат сурепадмина
        text=text,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
    

@check_groupe_user
@superadmin_only
@send_typing_action
def admin_export_users(update: Update, context: CallbackContext) -> None:
    # in values argument you can specify which fields should be returned in output csv
    upms = get_tele_command(update)
    # Если команда редакрирован, то upms
    users = User.objects.all().values()
    csv_users = _get_csv_from_qs_values(users)
    upms.reply_document(csv_users)


class AdminPlugin(BasePlugin):
    def setup_handlers(self, dp):

        # conv_handler = ConversationHandler(
        #     entry_points=[CommandHandler('chat_giga_', request_chat)],
        #     states={
        #         CODE_INPUT: [
        #             MessageHandler(Filters.text & (~Filters.command), check_chat),
        #         ],
        #     },
        #     fallbacks=[
        #         CommandHandler('cancel', cancel_chat),
        #     ]
        # )
        # dp.add_handler(conv_handler)
        # admin commands
        dp.add_handler(CommandHandler("admin_info", admin_info))
        #dp.add_handler(CommandHandler("stats", admin_handlers.stats))
        dp.add_handler(CommandHandler('admin_export_users', admin_export_users))
        dp.add_handler(MessageHandler(Filters.regex(rf'^/admin(/s)?.*'), commands_admin))
        #dp.add_handler(CallbackQueryHandler(button, pattern="^button_admin"))
        dp.add_handler(CallbackQueryHandler(button, pattern="^button_admin"))


@check_groupe_user
@superadmin_only
def button(update: Update, context: CallbackContext) -> None:
    #user_id = extract_user_data_from_update(update)['user_id']
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    #print('-------------',upms,'-------------')
    text = _admin_help
    context.bot.edit_message_text(
        text=text,
        chat_id=upms.chat.id, #  u.user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )

@check_groupe_user
@superadmin_only
def commands_admin(update: Update, context: CallbackContext) -> None:
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    telecmd = upms.text
    _output = _admin_help

    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )