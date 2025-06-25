# Plugin for ADMIN
# Name Plugin: ADMIN
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
#from tgbot.handlers.utils.decorators import check_blocked_user
from tgbot.handlers.utils.info import get_tele_command
from users.models import User
import pprint as pp
import string

try:
    option = get_plugins('').get('ADMIN').get("option")
except Exception as e:
    option = ''

# Список запрещенных слов (в нижнем регистре) TODO - в будущем хранить в бд
FORBIDDEN_WORDS = {"укра", "хох", "сво", "русня","хуй","пизд","еба"}

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

    # # Разбиваем текст на слова
    # words = text_lower.split()
    
    # # Очищаем слова от пунктуации
    # cleaned_words = [
    #     word.strip(ALL_PUNCTUATION)
    #     for word in words
    # ]
    
    # # Проверяем каждое слово
    # for word in cleaned_words:
    #     if word in forbidden_words:
    #         return True
    # return False


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
            if delete_message(update, context,upms.chat.id, message.message_id)==200:
                context.bot.send_message(
                    chat_id=upms.chat.id,
                    text=f"⚠️ Обнаружены запрещенные слова! Пожалуйста, соблюдайте правила чата.",
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.HTML
                    )
                return 
        if '/help' in message.text:
            return #func(update, context) # Ошибка и при бродкаст
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
