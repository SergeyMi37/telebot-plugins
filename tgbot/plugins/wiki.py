# Name Plugin: WIKI
    # - WIKI:
    #     - desc = Получить статью из википедии по поисковой фразе. Например /wiki Соль

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

@check_blocked_user
def button(update: Update, context: CallbackContext) -> None:
    #user_id = extract_user_data_from_update(update)['user_id']
    u = User.get_user(update, context)
    text = "Введите слово или фразу..."
    text += '\n\r/help /wiki'
    '''
    context.bot.send_message(
        chat_id=u.user_id,
        text=text,
        parse_mode=ParseMode.HTML
    )
    '''
    context.bot.edit_message_text(
        text=text,
        chat_id=u.user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )


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

@check_blocked_user
def commands(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    telecmd, upms = get_tele_command(update)
    _input = telecmd.split('wiki')[1].replace("_"," ")
    if _input:
       code, _output, link = fetch_page_data(_input)
    else:
        _output = "Введите слово или фразу, после ключевого wiki например:\n\r /wiki_Rainbow или wiki_Звездочет"
    _output += '\n\r/help /wiki'
    context.bot.send_message(
        chat_id=u.user_id,
        text=_output,
        parse_mode=ParseMode.HTML
    )