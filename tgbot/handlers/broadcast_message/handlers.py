import re
from dtb.settings import logger
import telegram
from telegram import ParseMode, Update
from telegram.ext import CallbackContext

from dtb.settings import DEBUG
from .manage_data import CONFIRM_DECLINE_BROADCAST, CONFIRM_BROADCAST
from .keyboards import keyboard_confirm_decline_broadcasting
from .static_text import broadcast_command, broadcast_wrong_format, broadcast_no_access, error_with_html, \
    message_is_sent, declined_message_broadcasting,reports_command, reports_no_access, reports_wrong_format
from users.models import User
from users.tasks import broadcast_message
from datetime import datetime, timedelta
from tgbot.plugins import servers_iris, reports_gitlab
import os
from tgbot.handlers.utils.decorators import check_blocked_user

GITLAB_LABELS = os.getenv('GITLAB_LABELS')

def is_permiss(user: User,roleslist: list):
    '''
    Проверить права доступа по спискам ролей
    '''
    if user.is_superadmin:
        return True
    elif user.is_admin:
        if user.roles:
            _rol = user.roles.split(",")
            if set(roleslist).intersection(_rol):
                print('---',_rol)
                return True
    return False

@check_blocked_user
def server(update: Update, context: CallbackContext):
    """ Работа с серверами ИРИС """
    u = User.get_user(update, context)
    telecmd, upms = reports_gitlab.get_tele_command(update)
    if not is_permiss(u,['iris']):
        upms.reply_text(
            text="В этом режиме можно работать только после одобрения Администратора",
        )
    else:
        if telecmd == "/s":
            # user typed only command without text for the message.
            upms.reply_text(
                text="Команду нужно ввести в правильном формате, наприме /s_TEST_SYS",
                parse_mode=telegram.ParseMode.HTML,
            )
            return
        cmd = upms.text.replace(f'/s_', '')+"_____" # Добавим подчеркивание чтоб не ломалось по несуществующему элементу списка _
        upms.reply_text(
          text = servers_iris.command_server(cmd),
          parse_mode=ParseMode.HTML,
          disable_web_page_preview=True,
          )

def reports(update: Update, context: CallbackContext):
    """ Reports."""
    telecmd, upms = reports_gitlab.get_tele_command(update)

    u = User.get_user(update, context)
    if not u.is_admin:
        upms.reply_text(
            text=reports_no_access,
        )
    else:
        if telecmd == reports_command:
            # user typed only command without text for the message.
            upms.reply_text(
                text=reports_wrong_format,
                parse_mode=telegram.ParseMode.HTML,
            )
            return
        if f'{reports_command} ' in telecmd:
            params = f"{telecmd.replace(f'{reports_command} ', '')}"
        else:
            par = f"{telecmd.replace(f'{reports_command}_', '')}"
            #/reports_date_20240813_20240813_mode_name_labels_tabel
            fd = par.split("date_")[1].split("_")[0]
            td = par.split("date_")[1].split("_")[1]
            md="name"
            try:
                md = par.split("mode_")[1].split("_")[0]
            except:
                pass
            lbl=GITLAB_LABELS
            try:
                lb = par.split("labels_")[1] #.split("_")[0:-1]
                #lbl=lb.replace("rating","Рейтинг").replace("vpr","ВПР").replace("tabel","Табель").replace("_",",")
                lbl = reports_gitlab.lab_replay(lb,"en_ru")
                #print("---====-en_ru-",lb,lbl)
            except Exception as err:
                #print("---err-lbl-",err)
                logger.error("---err-lbl-"+err)
            fda = f'{fd[0:4]}-{fd[4:6]}-{fd[6:8]}'
            tda = f'{td[0:4]}-{td[4:6]}-{td[6:8]}'
            #print(fda,td,md,lbl)
            params = f'date:{fda}:{tda} mode:{md} labels:{lbl}'
        # Логика разбора параметров
        mode="name"
        labels=GITLAB_LABELS
        #print('---params----',params)
        if 'date:yesterday' in params:
            _fromDate = datetime.now() + timedelta(days=-1)
            fromDate=_fromDate.date()
            toDate=fromDate
        if 'date:today' in params:
            fromDate = datetime.today().date()
            toDate=fromDate
        if 'date:weekly' in params:
            _fromDate = datetime.now() + timedelta(days=-7)
            fromDate=_fromDate.date()
            toDate = datetime.today().date()
        if 'mode:' in params:
            mode = params.split('mode:')[1].split(" ")[0]
        if 'labels:' in params:
            labels = params.split('labels:')[1]
        if 'date:20' in params:
            _fromDate = f"{params} ".split('date:')[1].split(" ")[0].split(":")[0]
            fromDate = datetime.strptime(_fromDate, "%Y-%m-%d").date()
            _toDate = f"{params} ".split('date:')[1].split(" ")[0].split(":")[1]
            toDate = datetime.strptime(_toDate,  "%Y-%m-%d").date()
        
        reports_gitlab.put_report(update=update, fromDate=fromDate,toDate=toDate,label=labels,mode=mode)

def broadcast_command_with_message(update: Update, context: CallbackContext):
    """ Type /broadcast <some_text>. Then check your message in HTML format and broadcast to users."""
    u = User.get_user(update, context)
    telecmd, upms = reports_gitlab.get_tele_command(update)
    if not u.is_superadmin:
        upms.reply_text(
            text=broadcast_no_access,
        )
    else:
        if telecmd == broadcast_command:
            # user typed only command without text for the message.
            upms.reply_text(
                text=broadcast_wrong_format,
                parse_mode=telegram.ParseMode.HTML,
            )
            return

        text = f"{upms.text.replace(f'{broadcast_command} ', '')}"
        markup = keyboard_confirm_decline_broadcasting()

        try:
            upms.reply_text(
                text=text,
                parse_mode=telegram.ParseMode.HTML,
                reply_markup=markup,
            )
        except telegram.error.BadRequest as e:
            upms.reply_text(
                text=error_with_html.format(reason=e),
                parse_mode=telegram.ParseMode.HTML,
            )


def broadcast_decision_handler(update: Update, context: CallbackContext) -> None:
    # callback_data: CONFIRM_DECLINE_BROADCAST variable from manage_data.py
    """ Entered /broadcast <some_text>.
        Shows text in HTML style with two buttons:
        Confirm and Decline
    """
    broadcast_decision = update.callback_query.data[len(CONFIRM_DECLINE_BROADCAST):]

    entities_for_celery = update.callback_query.message.to_dict().get('entities')
    entities, text = update.callback_query.message.entities, update.callback_query.message.text

    if broadcast_decision == CONFIRM_BROADCAST:
        admin_text = message_is_sent
        user_ids = list(User.objects.all().values_list('user_id', flat=True))

        if DEBUG:
            broadcast_message(
                user_ids=user_ids,
                text=text,
                entities=entities_for_celery,
            )
        else:
            # send in async mode via celery
            broadcast_message.delay(
                user_ids=user_ids,
                text=text,
                entities=entities_for_celery,
            )
    else:
        context.bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=declined_message_broadcasting,
        )
        admin_text = text

    context.bot.edit_message_text(
        text=admin_text,
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
        entities=None if broadcast_decision == CONFIRM_BROADCAST else entities,
    )
