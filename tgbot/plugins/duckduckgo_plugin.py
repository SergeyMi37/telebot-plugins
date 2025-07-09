# Name Plugin: DUCKDUCKGO
    # - DUCKDUCKGO:
    #- desc = Поиск в интернете в поисковой системе DuckDuckGo. /duckduckgo_
# имя плагина DUCKDUCKGO должно совпадать с именем в конфигурации Dynaconf
# имя плагина duckduckgo должно быть первым полем от _ в имени файла duckduckgo_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class DDGPlugin(BasePlugin):
#    def setup_handlers(self, dp):

import requests
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_groupe_user
from users.models import User
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from tgbot.plugins.base_plugin import BasePlugin
#from duckduckgo_search import ddg
from duckduckgo_search import DDGS

def search_on_russian(query, num_results=3):
    """
    Поиск в DuckDuckGo с русскоязычными результатами
    :param query: поисковый запрос
    :param num_results: количество результатов (по умолчанию 5)
    :return: список результатов
    """
    results = []
    with DDGS() as ddgs:
        # Добавляем "lang:ru" к запросу для русскоязычных результатов
        search_query = f"{query} lang:ru"
        
        for result in ddgs.text(search_query, max_results=num_results):
            results.append({
                'title': result.get('title', ''),
                'url': result.get('href', ''),
                'description': result.get('body', '')
            })
    
    return results

# if __name__ == "__main__":
#     # Пример использования
#     search_query = "лучшие программируемые калькуляторы"
#     search_results = search_on_russian(search_query, 3)
    
#     print(f"Результаты поиска для '{search_query}':\n")
#     for i, result in enumerate(search_results, 1):
#         print(f"{i}. {result['title']}")
#         print(f"   Ссылка: {result['url']}")
#         print(f"   Описание: {result['description']}\n")

def get_ddg_search_results(query, num_results=10):
    results = []
    with DDGS() as ddgs:
        for result in ddgs.text(query, max_results=num_results):
            results.append(result)  # Collect results
    return results

# Добавить проверку на роль ''
plugin_ddg = get_plugins('').get('DUCKDUCKGO')

CODE_INPUT = range(1)
_ddg_help = 'Введите поисковый запрос после :\n\r /duckduckgo_ \n\r🔸/help /duckduckgo'

def search_duckduckgo(query):
    # Параметры запроса
    params = {
        'q': query,
        'format': 'json',
        'pretty': '1'  # Для удобочитаемого вывода
    }
    
    # Отправляем GET-запрос на DuckDuckGo Instant Answer API
    response = requests.get('https://api.duckduckgo.com/', params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def request_ddg(update: Update, context):
    """Запрашиваем у пользователя"""
    upms = get_tele_command(update)
    upms.reply_text("Введите поисковый запрос. /cancel_ddg - отмена")
    return CODE_INPUT

def check_ddg(update: Update, context):
    upms = get_tele_command(update)
    _input = upms.text
    if _input:
       _output = search_on_russian(_input) #get_ddg_search_results(_input) # search_duckduckgo(_input)
    else:
        _output = _ddg_help
    print(_output)
    
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

def cancel_ddg(update: Update, context):
    """Завершаем диалог"""
    upms = get_tele_command(update)
    upms.reply_text("отмена ddg")
    return ConversationHandler.END

def error(update, context):
    logger.warning('Update "%s" вызвало ошибку "%s"', update, context.error)

class DDGPlugin(BasePlugin):
    def setup_handlers(self, dp):

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('duckduckgo_', request_ddg)],
            states={
                CODE_INPUT: [
                    MessageHandler(Filters.text & (~Filters.command), check_ddg),
                ],
            },
            fallbacks=[
                CommandHandler('cancel_ddg', cancel_ddg),
            ]
        )
        dp.add_handler(conv_handler)
        dp.add_handler(MessageHandler(Filters.regex(rf'^/duckduckgo(/s)?.*'), commands))
        dp.add_handler(CallbackQueryHandler(button, pattern="^button_ddg"))

@check_groupe_user
def button(update: Update, context: CallbackContext) -> None:
    #user_id = extract_user_data_from_update(update)['user_id']
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    text = _ddg_help
    context.bot.edit_message_text(
        text=text,
        chat_id=upms.chat.id, #  u.user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )

@check_groupe_user
def commands(update: Update, context: CallbackContext) -> None:
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    telecmd = upms.text
    text = _ddg_help
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=text,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )