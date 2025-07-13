# Name Plugin: TASKS
    # - TASKS:
    #     - desc = Модуль создания, просмотра, удаления, редактирования и запуска регулярных задач /tasks
# имя плагина TASKS должно совпадать с именем в конфигурации Dynaconf
# имя плагина tasks должно быть первым полем от _ в имени файла tasks_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class TasksPlugin(BasePlugin):
#    def setup_handlers(self, dp):

# РегулярнаяПроверкаИсообщения
# users.tasks.broadcast_custom_message
# Positional Arguments:
# [["Roles(iris) Condition(PROD_SYS_AlertsView)",504026852],
# "Вам пришло сообщение о проблеме на сервере <b>PROD_SYS_AlertsView</b>\n команды:\n/s_PROD_SYS"
# ]
# Тестирование прикладной процедуры users.tasks.broadcast_custom_message
# Роли, которые должны быть у пользователей которым посылать сообщения
# [["Roles(iris) Condition(PROD_SYS_AlertsView)",504026852],
# "Вам пришло сообщение о проблеме на сервере <b>PROD_SYS_AlertsView</b>\n команды:\n/s_PROD_SYS"
# ]

from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_groupe_user
from users.models import User
import wikipediaapi
# plugins/news_rss_plugin.py
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler

from tgbot.plugins.base_plugin import BasePlugin

# Добавить проверку на роль ''
plugin_wiki = get_plugins('').get('TASKS')

CODE_INPUT = range(1)
_tasks_help = 'Модуль создания, просмотра, удаления, редактирования и запуска регулярных задач' \
'\n/task_list - какие задачи актуальны' \
'\n/task_add - добавить новую задачу' \
'\n/task_del - удалить задачу'

def request_tasks(update: Update, context):
    """Запрашиваем у пользователя"""
    upms = get_tele_command(update)
    upms.reply_text("Введите слово для поиска на сайте Википедии. /cancel - отмена")
    return CODE_INPUT

def check_tasks(update: Update, context):
    upms = get_tele_command(update)
    _input = upms.text
    _output = '!!!'
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

def cancel_tasks(update: Update, context):
    """Завершаем диалог"""
    upms = get_tele_command(update)
    upms.reply_text("отмена.")
    return ConversationHandler.END

class TasksPlugin(BasePlugin):
    def setup_handlers(self, dp):

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('tasks_new_', request_tasks)],
            states={
                CODE_INPUT: [
                    MessageHandler(Filters.text & (~Filters.command), check_tasks),
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel_tasks),
            ]
        )
        dp.add_handler(conv_handler)
        cmd = "/tasks"
        dp.add_handler(MessageHandler(Filters.regex(rf'^{cmd}(/s)?.*'), commands_tasks))
        dp.add_handler(MessageHandler(Filters.regex(rf'^wiki(/s)?.*'), commands_tasks))
        dp.add_handler(CallbackQueryHandler(button_tasks, pattern="^button_task"))

@check_groupe_user
def button_tasks(update: Update, context: CallbackContext) -> None:
    #user_id = extract_user_data_from_update(update)['user_id']
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    #print('-------------',upms,'-------------')
    text = "Введите слово или фразу..."
    #text += _wiki_help
    context.bot.edit_message_text(
        text=text,
        chat_id=upms.chat.id, #  u.user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )

@check_groupe_user
def commands_tasks(update: Update, context: CallbackContext) -> None:
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    telecmd = upms.text
    _input = telecmd.split('tasks')[1].replace("_"," ")
    _output = 'режим в разработке'
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )