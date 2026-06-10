import logging
import sys, os

import telegram
from telegram import Bot
from telegram.utils.request import Request
from dtb.settings import TELEGRAM_TOKEN

PROXY_URL = os.environ.get("PROXY_URL",None)

if PROXY_URL:
    request = Request(proxy_url=PROXY_URL)
    bot = Bot(token=TELEGRAM_TOKEN, request=request)
else:
    bot = Bot(token=TELEGRAM_TOKEN)
#bot = Bot(TELEGRAM_TOKEN)

TELEGRAM_BOT_USERNAME = bot.get_me()["username"]
# Global variable - the best way I found to init Telegram bot
try:
    pass
except telegram.error.Unauthorized:
    logging.error("Invalid TELEGRAM_TOKEN.")
    sys.exit(1)
