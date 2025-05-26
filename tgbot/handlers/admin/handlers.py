from datetime import timedelta

from django.utils.timezone import now
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from tgbot.handlers.admin import static_text
from tgbot.handlers.admin.utils import _get_csv_from_qs_values
from tgbot.handlers.utils.decorators import admin_only, send_typing_action, superadmin_only, check_blocked_user
from users.models import User
from tgbot.handlers.admin.reports_gitlab import get_tele_command

@admin_only
def admin2(update: Update, context: CallbackContext) -> None:
    """ Show help info about all secret admins commands """
    update.message.reply_text(static_text.secret_admin_commands)

@check_blocked_user
@superadmin_only
def admin(update: Update, context: CallbackContext) -> None:
    """ Show help info about all secret admins commands """
    text = static_text.users_amount_stat.format(
        user_count=User.objects.count(),  # count may be ineffective if there are a lot of users.
        active_24=User.objects.filter(updated_at__gte=now() - timedelta(hours=24)).count()
    )
    update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

@check_blocked_user
@superadmin_only
@send_typing_action
def export_users(update: Update, context: CallbackContext) -> None:
    # in values argument you can specify which fields should be returned in output csv
    telecmd, upms = get_tele_command(update)
    # Если команда редакрирован, то upms
    users = User.objects.all().values()
    csv_users = _get_csv_from_qs_values(users)
    upms.reply_document(csv_users)
