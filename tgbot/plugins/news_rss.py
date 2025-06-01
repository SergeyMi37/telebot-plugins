# Plugin Новости из ленты rss
# Name Plugin: NEWS
    # - NEWS:
    #     - blocked = 1
    #     - desc = Сервис агрегации новостей 

from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.admin.static_text import CRLF, only_for_admins
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_blocked_user
from users.models import User

# Добавить проверку на роль ''
plugin_news = get_plugins('').get('NEWS')

@check_blocked_user
def commands(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    telecmd, upms = get_tele_command(update)
    update.message.reply_text(telecmd)