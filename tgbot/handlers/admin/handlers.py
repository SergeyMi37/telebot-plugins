from datetime import timedelta
from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from tgbot.handlers.admin.utils import _get_csv_from_qs_values, GetExtInfo
from tgbot.handlers.admin import static_text
from tgbot.handlers.utils.decorators import admin_only, send_typing_action, superadmin_only, check_groupe_user
from users.models import User
from tgbot.plugins import reports_gitlab
from dtb.settings import TELEGRAM_LOGS_CHAT_ID, DEBUG


# @admin_only
# def admin2(update: Update, context: CallbackContext) -> None:
#     """ Show help info about all secret admins commands """
#     update.message.reply_text(static_text.secret_admin_commands)
