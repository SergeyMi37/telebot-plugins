# Plugin Новости из ленты rss
# Name Plugin: NEWS

from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.utils.info import get_tele_command

# Добавить проверку на роль ''
plugin_news = get_plugins('').get('NEWS')

