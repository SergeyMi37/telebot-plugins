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

@admin_only
def admin2(update: Update, context: CallbackContext) -> None:
    """ Show help info about all secret admins commands """
    update.message.reply_text(static_text.secret_admin_commands)

@check_groupe_user
@superadmin_only
def admin(update: Update, context: CallbackContext) -> None:
    u = User.get_user(update, context)
    """ Show help info about all secret admins commands """
    text = static_text.users_amount_stat.format(
        user_count=User.objects.count(),  # count may be ineffective if there are a lot of users.
        active_24=User.objects.filter(updated_at__gte=now() - timedelta(hours=24)).count()
        )
    text += f' /export_users {GetExtInfo.GetOS()}\n🚧 DEBUG: {DEBUG}\n😎 chat_id: {u.user_id}\n🚨 TELEGRAM_LOGS_CHAT_ID: {TELEGRAM_LOGS_CHAT_ID} {GetExtInfo.GetHostInfo()} {GetExtInfo.GetExtIp()} {GetExtInfo.GetGitInfo()} '
    text += f'\n\n🔸/help: Перечень команд'
    '''
    upms.reply_text(
          text = text,
          parse_mode=ParseMode.HTML,
          disable_web_page_preview=True,
          )
    '''
    context.bot.send_message(
        chat_id=u.user_id, # вернуть личный чат сурепадмина
        text=text,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
    

@check_groupe_user
@superadmin_only
@send_typing_action
def export_users(update: Update, context: CallbackContext) -> None:
    # in values argument you can specify which fields should be returned in output csv
    upms = reports_gitlab.get_tele_command(update)
    # Если команда редакрирован, то upms
    users = User.objects.all().values()
    csv_users = _get_csv_from_qs_values(users)
    upms.reply_document(csv_users)
