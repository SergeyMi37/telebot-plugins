# Name Plugin: INET
    # - INET:
    #     - blocked = 0
    #     - desc = Поиск в интернете в поисковых системах. /inet_ddg_ - DuckDuckGo
# имя плагина INET должно совпадать с именем в конфигурации Dynaconf
# имя плагина duckduckgo должно быть первым полем от _ в имени файла inet_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class InetPlugin(BasePlugin):
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
            #print('===',result)
            results.append({
                'title': result.get('title', ''),
                'url': result.get('href', ''),
                'description': result.get('body', '')
            })
    
    return results

# Добавить проверку на роль ''
plugin_ddg = get_plugins('').get('INET')

CODE_INPUT = range(1)
_inet_help = 'Введите поисковый запрос после команды /inet_ddg_ ' \
    '\n/inet_dflt_result_55 - Изменить количество строк вывода результата на 55'

def write_duckduckgo(context, upms, res, count = 100):
    num=0
    text=''
    for _item in res[:count]:  # выводим первые 100 результатов
        #text +=f"\n👉{news_item['title']} 🎯{news_item['source']} 📆({news_item['published']})"
        #print(_item) 
        num += 1
        #it = f"\n{num}.🔍<a href=\"{news_item['link']}\">{news_item['title']} 📆({news_item['published'][:16]})</a>"
        it = f"\n{num}.🔶<a href=\"{_item['url']}\">{_item['description']}</a> {_item['title'][:16]}..."
        if len(text+it)>4081:
            context.bot.send_message(
                chat_id=upms.chat.id,
                text = text+"\n🔸/help\n", 
                disable_web_page_preview=True,
                parse_mode=ParseMode.HTML)
            text=it
        else:
            text += f"{it}"

    msg = text[:4081]+"...\n\n🔸/help /inet_ddg_ "
    context.bot.send_message( 
        chat_id=upms.chat.id, text=msg, 
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML )

def request_ddg(update: Update, context):
    """Запрашиваем у пользователя"""
    upms = get_tele_command(update)
    upms.reply_text("Введите поисковый запрос. /cancel_ddg - отмена")
    return CODE_INPUT

def check_ddg(update: Update, context):
    upms = get_tele_command(update)
    _input = upms.text
    upms.reply_text("🕒.минутку..")
    if _input:
        res = search_on_russian(_input, 50)
        write_duckduckgo(context, upms, res)
        return ConversationHandler.END
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
    upms = get_tele_command(update)
    upms.reply_text("отмена")
    return ConversationHandler.END

class InetPlugin(BasePlugin):
    def setup_handlers(self, dp):

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('inet_ddg_', request_ddg)],
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
        dp.add_handler(MessageHandler(Filters.regex(rf'^/inet(/s)?.*'), commands))
        dp.add_handler(CallbackQueryHandler(button, pattern="^button_ddg"))

@check_groupe_user
def button(update: Update, context: CallbackContext) -> None:
    #user_id = extract_user_data_from_update(update)['user_id']
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    text = _inet_help
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
    text = _inet_help
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=text,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )