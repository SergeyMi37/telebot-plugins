# Plugin for ADMIN
# Name Plugin: ADMIN
from telegram import ParseMode, Update, CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
#from tgbot.handlers.utils.decorators import check_blocked_user
from tgbot.handlers.utils.info import get_tele_command
from users.models import User
import pprint as pp

try:
    option = get_plugins('').get('ADMIN').get("option")
except Exception as e:
    option = ''

def universal_message_handler(update, context, func=""):
    upms = get_tele_command(update)
    message = upms
    #pp.pprint(update.to_dict())
    funcname = func.__name__ if func else ''
    if message.text:
        log = (f"Из {upms.chat.id} Пользователь {upms.from_user.id} отправил текст: {message.text} функция {funcname} ")
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


# Функция обработки команды delete_message
def delete_message(update: Update, context: CallbackContext):
    # Проверяем наличие аргументов
    if len(context.args) != 1 or not context.args[0].isdigit():
        update.message.reply_text("Укажите ID сообщения для удаления.")
        return
    message_id = int(context.args[0])
    try:
        # Удаление указанного сообщения
        context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=message_id)
        update.message.reply_text(f"Сообщение {message_id} успешно удалено!")
    except Exception as e:
        print(e)
        update.message.reply_text(f"Произошла ошибка при удалении сообщения {message_id}.")
