# Name Plugin: WIKI
    # - WIKI:
    #     - desc = Получить статью из википедии по поисковой фразе. Например /wiki Соль
# имя плагина WIKI должно совпадать с именем в конфигурации Dynaconf
# имя плагина wiki должно быть первым полем от _ в имени файла wiki_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class WIKIPlugin(BasePlugin):
#    def setup_handlers(self, dp):


from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_groupe_user
from users.models import User
import wikipediaapi
# plugins/news_rss_plugin.py
from telegram.ext import MessageHandler, Filters, CallbackQueryHandler
from tgbot.plugins.base_plugin import BasePlugin

# Добавить проверку на роль ''
plugin_wiki = get_plugins('').get('WIKI')

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


class WikiPlugin(BasePlugin):
    def setup_handlers(self, dp):
        cmd = "/wiki"
        dp.add_handler(MessageHandler(Filters.regex(rf'^{cmd}(/s)?.*'), commands))
        dp.add_handler(MessageHandler(Filters.regex(rf'^wiki(/s)?.*'), commands))
        dp.add_handler(CallbackQueryHandler(button, pattern="^button_wiki"))

@check_groupe_user
def button(update: Update, context: CallbackContext) -> None:
    #user_id = extract_user_data_from_update(update)['user_id']
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    #print('-------------',upms,'-------------')
    text = "Введите слово или фразу..."
    text += '\n\r🔸/help /wiki'
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
    _input = telecmd.split('wiki')[1].replace("_"," ")
    if _input:
       code, _output, link = fetch_page_data(_input)
    else:
        _output = "Введите слово или фразу, после ключевого wiki например:\n\r /wiki_Rainbow или <code>wiki_Звездочет</code>"
    _output += '\n\r🔸/help /wiki'
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )