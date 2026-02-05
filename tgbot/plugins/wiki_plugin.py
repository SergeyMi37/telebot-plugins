# Name Plugin: WIKI
    # - WIKI:
    #     - desc = Получить статью из википедии по поисковой фразе. Например /wiki Соль
# имя плагина WIKI должно совпадать с именем в конфигурации Dynaconf
# имя плагина wiki должно быть первым полем от _ в имени файла wiki_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class WIKIPlugin(BasePlugin):
#    def setup_handlers(self, dp):

from telegram import ParseMode, Update
from telegram.ext import CallbackContext
# from dtb.settings import get_plugins_for_roles
# from dtb.settings import logger
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_groupe_user
from users.models import User
import wikipediaapi
# plugins/news_rss_plugin.py
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler

from tgbot.plugins.base_plugin import BasePlugin

CODE_INPUT = range(1)
_wiki_help = 'Поиск на https://ru.wikipedia.org Введите слово после ключевого wiki ' \
'например:\n\r /wiki_Rainbow или ' \
'\n\r /wiki_ - диалог для введения слова ' \
'\n\r🔸/help /wiki /wiki_'

def fetch_page_data(page_title):
    # Создаем объект API с использованием русского раздела Wikipedia
    wiki_api = wikipediaapi.Wikipedia(
            language='ru',     # русский язык
            extract_format=wikipediaapi.ExtractFormat.WIKI,   # извлекаем содержимое в формате MediaWiki
            user_agent="MswApp/1.0"  # Добавляем user agent
    )
    page = wiki_api.page(page_title)
    if not page.exists():
        return None, (f"Страница '{page_title}' не найдена."), None
    summ = page.summary[:12500] + f'\n\r{page.fullurl}\n\r{page.title}'
    return 200, summ, page.fullurl

def request_wiki(update: Update, context):
    """Запрашиваем у пользователя"""
    upms = get_tele_command(update)
    upms.reply_text("Введите слово для поиска на сайте Википедии. /cancel_wiki - отмена")
    return CODE_INPUT

def check_wiki(update: Update, context):
    upms = get_tele_command(update)
    _input = upms.text
    if _input:
       code, _output, link = fetch_page_data(_input)
    else:
        _output = _wiki_help
    if '🔸/help' not in _output:
        _output += '\n\r🔸/help /wiki /wiki_' 
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

def cancel_wiki(update: Update, context):
    """Завершаем диалог"""
    upms = get_tele_command(update)
    upms.reply_text("отмена.")
    return ConversationHandler.END

# def error(update, context):
#     logger.warning('Update "%s" caused error "%s"', update, context.error)

class WikiPlugin(BasePlugin):
    def setup_handlers(self, dp):
        cmd = "/wiki"

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('wiki_', request_wiki)],
            states={
                CODE_INPUT: [
                    MessageHandler(Filters.text & (~Filters.command), check_wiki),
                ],
            },
            fallbacks=[
                CommandHandler('cancel_wiki', cancel_wiki),
            ]
        )
        dp.add_handler(conv_handler)
        dp.add_handler(MessageHandler(Filters.regex(rf'^{cmd}(/s)?.*'), commands))
        dp.add_handler(MessageHandler(Filters.regex(rf'^wiki(/s)?.*'), commands))
        dp.add_handler(CallbackQueryHandler(button_wiki, pattern="^button_wiki"))

@check_groupe_user
def button_wiki(update: Update, context: CallbackContext) -> None:
    '''
    plugin WIKI:
    '''
    #user_id = extract_user_data_from_update(update)['user_id']
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    text = "Введите слово или фразу..."
    text += _wiki_help
    query = update.callback_query
    query.answer(text=text, show_alert=True) # вывести всплывающее окно
    
    context.bot.edit_message_text(
        text=text,
        chat_id=upms.chat.id, #  u.user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )

@check_groupe_user
def commands(update: Update, context: CallbackContext) -> None:
    '''
    plugin WIKI:
    '''
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    telecmd = upms.text
    _input = telecmd.split('wiki')[1].replace("_"," ")
    if _input:
       code, _output, link = fetch_page_data(_input)
    else:
        _output = _wiki_help
    
    if '🔸/help' not in _output:
        _output += '\n\r🔸/help /wiki' 
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )