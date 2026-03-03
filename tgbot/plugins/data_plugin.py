# Name Plugin: DATA
    # - DATA:
    #     - desc = Получить данные из портала mos.ru .
# имя плагина DATA должно совпадать с именем в конфигурации Dynaconf
# имя плагина data должно быть первым полем от _ в имени файла data_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# https://catalog.eaist.mos.ru/catalog
# https://data.mos.ru/developers/documentation
# https://dadata.ru/api/find-party/
# https://dadata.ru/api/find-address/
# class DATAPlugin(BasePlugin):
#    def setup_handlers(self, dp):

# !!! в разработке

from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins_for_roles
from dtb.settings import logger
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_groupe_user
from users.models import User
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from tgbot.plugins.base_plugin import BasePlugin
from dadata import Dadata
from tgbot.plugins.data_dadata import get_adress_fias, get_phone #,token,secret

# проверка пользователя на роль в декораторе @check_groupe_user
#plugin_data = get_plugins_for_roles('').get('DATA')
# token = plugin_data.get('dadata_token','')
# secret = plugin_data.get('dadata_secret','')

CODE_INPUT = range(1)
_data_help = 'Поиск на dadata.ru Введите контекст поиска ' \
'\n\r /data_phone_ - проверка телефона' \
'\n\r /data_org_ - проверка организации' \
'\n\r🔸/help /data'


def request_data(update: Update, context):
    """Запрашиваем у пользователя контекст"""
    upms = get_tele_command(update)
    context.user_data['cmd'] = upms.text # запоминаем команду
    upms.reply_text("Введите код  /cancel_data - закончить диалог")
    return CODE_INPUT

def check_data(update: Update, context):
    upms = get_tele_command(update)
    cmd_type = context.user_data.get('cmd')
    _input = upms.text
    _output = _data_help
    if _input:
        if cmd_type=='/data_phone_':
            val, json = get_phone(_input)
        elif cmd_type=='/data_org_':
            val, json = get_adress_fias(_input)
        else:
            val, json = get_phone(_input)

        if val:
          _output = f'{val}\n🔷 {json} \n\r🔸/help /data {cmd_type}'
        else:
          _output = f'Не найдено\n🔴 {json} \n\r🔸/help /data {cmd_type}'

    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

def cancel_data(update: Update, context):
    """Завершаем диалог"""
    upms = get_tele_command(update)
    upms.reply_text("отмена.")
    return ConversationHandler.END

class DataPlugin(BasePlugin):
    def setup_handlers(self, dp):
        cmd = "/data"

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('data_phone_', request_data),
                          CommandHandler('data_fias_', request_data),
                          CommandHandler('data_org_', request_data)],
            states={
                CODE_INPUT: [
                    MessageHandler(Filters.text & (~Filters.command), check_data),
                ],
            },
            fallbacks=[
                CommandHandler('cancel_data', cancel_data),
            ]
        )
        dp.add_handler(conv_handler)
        dp.add_handler(MessageHandler(Filters.regex(rf'^{cmd}(/s)?.*'), commands))
        dp.add_handler(CallbackQueryHandler(button_data, pattern="^button_data"))

@check_groupe_user
def button_data(update: Update, context: CallbackContext) -> None:
    '''
    plugin DATA:
    '''
    #user_id = extract_user_data_from_update(update)['user_id']
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    text = "Введите слово или фразу..."
    text += _data_help
    query = update.callback_query
    query.answer(text=text, show_alert=True) # вывести всплывающее окно
    
    context.bot.edit_message_text(
        text=text,
        chat_id=upms.chat.id, #  u.user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )

@check_groupe_user
def commands(update: Update, context: CallbackContext) -> None:
    '''
    plugin DATA:
    '''
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    telecmd = upms.text
    _input = telecmd.split('data')[1] #.replace("_"," ")
    _output = ""
    if "_fias" == _input:
       _output = get_adress_fias("")
    elif "_fias_" in _input:
       _output = get_adress_fias(_input.split('_fias_')[1])
    else:
        _output = _data_help
    
    if '🔸/help' not in _output:
        _output += '\n\r🔸/help /data_' 
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )


