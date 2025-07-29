# Name Plugin: CHAT
    # - CHAT:
    #     - desc = Модуль создания, просмотра, удаления, редактирования и запуска регулярных задач /tasks
# имя плагина CHAT должно совпадать с именем в конфигурации Dynaconf
# имя плагина chat должно быть первым полем от _ в имени файла chat_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class ChatPlugin(BasePlugin):
#    def setup_handlers(self, dp):

# pip install langchain-gigachat
# https://developers.sber.ru/docs/ru/gigachain/overview
# https://developers.sber.ru/docs/ru/gigachat/api/images-generation?tool=python&lang=py
from telegram import ParseMode, Update
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
from dtb.settings import get_plugins, unblock_plugins
from dtb.settings import logger
from tgbot.handlers.utils.decorators import check_groupe_user
from tgbot.handlers.utils.info import get_tele_command
from users.models import User
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from tgbot.plugins.base_plugin import BasePlugin

_chat_help = 'Диалог с ГигаЧат от Сбера /chat_giga_'
plugins = unblock_plugins.get('CHAT')
GIGA_TOKEN = '' if not plugins else plugins.get("GIGA_CHAT")
# Добавить проверку на роль 
# try:
#     GIGA_TOKEN = plugins.get("GIGA_CHAT")
# except Exception as e:
#     GIGA_TOKEN = ''
#logger.info('--- plugin GIGA: '+str(get_plugins('GIGA')))
# Вынести на параметр сделать возможность запоминать или изменять для каждого пользователя отдельно.
# content="Ты бот супер программист на питон, который помогает пользователю провести время с пользой."

def ask_giga(prompt):
    if not GIGA_TOKEN:
        return "Токен для Giga не опрделен"
    giga = GigaChat(
        # Для авторизации запросов используйте ключ, полученный в проекте GigaChat API
        credentials=GIGA_TOKEN,
        verify_ssl_certs=False,
    )
    messages = [
        SystemMessage(
            # content="Ты внимательный бот-психолог, который помогает пользователю решить его проблемы."
            # content="Ты бот-собеседник, который помогает пользователю провести время с пользой."
            content="Ты бот супер программист на питон, который помогает пользователю провести время с пользой."
        )
    ]
    messages.append(HumanMessage(content=prompt))
    try:
        res = giga.invoke(messages)
        messages.append(res)
        return res.content
    except Exception as e:
        return e.args.__repr__()

@check_groupe_user
def text_message(update, context):
    upms = get_tele_command(update)
    telecmd = upms.text
    resp = ask_giga(telecmd)
    # Ответ пользователю

    context.bot.send_message(
        chat_id=upms.chat.id,
        text=f"Ответ Гиги: {resp} \n\r🔸/help",
        parse_mode=ParseMode.HTML
    )

CODE_INPUT = range(1)

def request_chat(update: Update, context):
    upms = get_tele_command(update)
    upms.reply_text("😎Введите вопрос к ГигаЧату. /cancel - конец диалога")
    return CODE_INPUT

def check_chat(update: Update, context):
    upms = get_tele_command(update)
    _input = upms.text
    upms.reply_text("🕒.секундочку..")
    _output = ask_giga(_input)
    
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
    request_chat(update, context) # зацикливаем диалог
    #return ConversationHandler.END

def cancel_chat(update: Update, context):
    """Завершаем диалог"""
    upms = get_tele_command(update)
    upms.reply_text("диалог закончен \n\r🔸/help /chat /chat_giga_ - начать новый диалог")
    return ConversationHandler.END

class ChatPlugin(BasePlugin):
    def setup_handlers(self, dp):

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('chat_giga_', request_chat)],
            states={
                CODE_INPUT: [
                    MessageHandler(Filters.text & (~Filters.command), check_chat),
                ],
            },
            fallbacks=[
                CommandHandler('cancel', cancel_chat),
            ]
        )
        dp.add_handler(conv_handler)
        cmd = "/chat"
        dp.add_handler(MessageHandler(Filters.regex(rf'^{cmd}(/s)?.*'), commands_chat))
        dp.add_handler(CallbackQueryHandler(button_chat, pattern="^button_chat"))


@check_groupe_user
def button_chat(update: Update, context: CallbackContext) -> None:
    #user_id = extract_user_data_from_update(update)['user_id']
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    #print('-------------',upms,'-------------')
    text = _chat_help
    context.bot.edit_message_text(
        text=text,
        chat_id=upms.chat.id, #  u.user_id,
        message_id=update.callback_query.message.message_id,
        parse_mode=ParseMode.HTML
    )

@check_groupe_user
def commands_chat(update: Update, context: CallbackContext) -> None:
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    telecmd = upms.text
    _output = _chat_help
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )