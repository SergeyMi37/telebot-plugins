# Plugin for giga-chat bot
# Name Plugin: GIGA
# pip install langchain-gigachat
# https://developers.sber.ru/docs/ru/gigachain/overview
# https://developers.sber.ru/docs/ru/gigachat/api/images-generation?tool=python&lang=py
#	// 🚀 ракета 🎯 дартс 🎥 камера 🖼 картина 🔥 fire 📖 book 🔍 find 🐍 питон 📌 закреп  📆 дата 🕐 часы 🌴 дерев 🚧 debug  🅿 Postgres
#	// шарики разноцветные ⭕ 🔴 крас  🟠 оранж  🟡 жел  🟢 зел  ⚪️ голубелый  🔵 син  🟣 фиол  🟤 корич ⚫ черный
#	// 🌞 солнце 😌 нейтральная 😡 красная ⚠️🚨 авария 📂 Каталог ➡ стрелка 👉 указ ✅ чекед  🖐 😎
#   // ✨ звёздочки 🔶 🔸 крас 🔷 🔹 син ромб 
#	// https://apps.timwhitlock.info/emoji/tables/unicode
#	🆕 Событие: Изменение объекта.#	📌 Объект события: 📋 Задача: #	📂 Проект: "Test".#	🎯 Спринт: "Тест2".
#	🕒 Время события: 18:30 15.03.2025#	👤 Инициатор:#	👥 Ответственный(е):#	🔄 Изменения:#	⬇️
from telegram import ParseMode, Update
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
from dtb.settings import get_plugins
from dtb.settings import logger
from tgbot.handlers.utils.decorators import check_blocked_user
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

@check_blocked_user
def text_message(update, context):
    u = User.get_user(update, context)
    telecmd, upms = get_tele_command(update)
    resp = ask_giga(telecmd)
    # Ответ пользователю

    context.bot.send_message(
        chat_id=u.user_id,
        text=f"Ответ Гиги: {resp} \n\r /help /plugins",
        parse_mode=ParseMode.HTML
    )