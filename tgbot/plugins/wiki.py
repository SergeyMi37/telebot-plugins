# Name Plugin: WIKI
    # - WIKI:
    #     - desc = Получить статью из википедии по поисковой фразе. Например /wiki Сублимация

from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.admin.static_text import CRLF, only_for_admins
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_blocked_user
from users.models import User
import wikipediaapi

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
        return None, (f"Страница '{page_title}' не найдена.")

    summ = page.summary[:12500] + f'\n\r{page.fullurl}\n\r{page.title}'
    return 200, summ

@check_blocked_user
def commands(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    telecmd, upms = get_tele_command(update)
    _input = telecmd.split('wiki')[1]
    if _input:
       code, _output = fetch_page_data(_input)
    else:
        _output = "Введите слово или фразу, после ключевого wiki например:\n\r /wikiКвинта или wikiСамурай"
    _output += '\n\r/help /wiki /plugins'
    context.bot.send_message(
        chat_id=u.user_id,
        text=_output,
        parse_mode=ParseMode.HTML
    )