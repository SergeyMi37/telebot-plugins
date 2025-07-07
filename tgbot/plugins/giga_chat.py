# Plugin for giga-chat bot ----- нестандарный
# Name Plugin: GIGA
# pip install langchain-gigachat
# https://developers.sber.ru/docs/ru/gigachain/overview
# https://developers.sber.ru/docs/ru/gigachat/api/images-generation?tool=python&lang=py
from telegram import ParseMode, Update
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.utils.decorators import check_groupe_user
from tgbot.handlers.utils.info import get_tele_command
from users.models import User

# Добавить проверку на роль 
try:
    GIGA_TOKEN = get_plugins('').get('GIGA').get("GIGA_CHAT")
except Exception as e:
    GIGA_TOKEN = ''
#logger.info('--- plugin GIGA: '+str(get_plugins('GIGA')))

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