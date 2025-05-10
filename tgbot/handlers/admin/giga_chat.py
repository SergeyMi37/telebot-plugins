# Plugin for giga-chat bot
# Name Plugin: GIGA
# pip install langchain-gigachat
# https://developers.sber.ru/docs/ru/gigachain/overview
# https://developers.sber.ru/docs/ru/gigachat/api/images-generation?tool=python&lang=py
#	// 🚀 ракета 🎯 дартс 🎥 камера 🖼 картина 🔥 fire 📖 book 🔍 find 🐍 питон 📌 закреп  📆 дата 🕐 часы 🌴 дерев 🚧 debug  🅿 Postgres
#	// шарики разноцветные ⭕ 🔴 крас  🟠 оранж  🟡 жел  🟢 зел  ⚪️ голубелый  🔵 син  🟣 фиол  🟤 корич ⚫ черный
#	// 😌 нейтральная 😡 красная 🚨 авария 📂 Каталог ➡ стрелка 👉 указ ✅ чекед 🔶 🔸 крас 🔷 🔹 син ромб 🌞 солнце 🖐 😎
#   // ✨ звёздочки
#	// https://apps.timwhitlock.info/emoji/tables/unicode
#	🆕 Событие: Изменение объекта.
#	📌 Объект события: 📋 Задача: 
#	📂 Проект: "Test".
#	🎯 Спринт: "Тест2".
#	🕒 Время события: 18:30 15.03.2025
#	👤 Инициатор:
#	👥 Ответственный(е):
#	🔄 Изменения:#	⬇️

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
from dtb.settings import get_plugins
from dtb.settings import logger

# Добавить проверку на роль 
GIGA_TOKEN = get_plugins('').get('GIGA').get("GIGA_CHAT")
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
            #content="Ты бот-собеседник, который помогает пользователю провести время с пользой."
            content="Ты бот супер программист на питон, который помогает пользователю провести время с пользой."
        )
    ]
    messages.append(HumanMessage(content=prompt))
    res = giga.invoke(messages)
    messages.append(res)
    return res.content + "\n /help"
'''
"""Пример работы с чатом"""
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

payload = Chat(
    messages=[
        Messages(
            role=MessagesRole.SYSTEM,
            content="Ты внимательный бот-психолог, который помогает пользователю решить его проблемы."
        )
    ],
    temperature=0.7,
    max_tokens=100,
)

# Используйте токен, полученный в личном кабинете из поля Авторизационные данные
with GigaChat(credentials=..., verify_ssl_certs=False) as giga:
    while True:
        user_input = input("User: ")
        payload.messages.append(Messages(role=MessagesRole.USER, content=user_input))
        response = giga.chat(payload)
        payload.messages.append(response.choices[0].message)
        print("Bot: ", response.choices[0].message.content)


# Пример использования  python tgbot/handlers/admin/giga_chat.py 
if __name__ == "__main__":
    giga = GigaChat(
        # Для авторизации запросов используйте ключ, полученный в проекте GigaChat API
        credentials=GIGA_TOKEN,
        verify_ssl_certs=False,
    )
    messages = [
        SystemMessage(
            content="Ты бот-собеседник, который помогает пользователю провести время с пользой."
        )
    ]
    print('--------',GIGA_TOKEN,"- Что бы выйти - введи 'пока'")
    while(True):
        user_input = input("Пользователь: ")
        if user_input == "пока":
            break
        messages.append(HumanMessage(content=user_input))
        res = giga.invoke(messages)
        messages.append(res)
        print("GigaChat: ", res.content)
'''