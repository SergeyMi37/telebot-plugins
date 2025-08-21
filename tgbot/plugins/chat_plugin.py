# Name Plugin: CHAT
    # - CHAT:
    #     - desc = Модуль работы с ГигаЧатом и другими моделями ollama
# имя плагина CHAT должно совпадать с именем в конфигурации Dynaconf
# имя плагина chat должно быть первым полем от _ в имени файла chat_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class ChatPlugin(BasePlugin):
#    def setup_handlers(self, dp):

# pip install langchain-gigachat
# https://developers.sber.ru/docs/ru/gigachain/overview
# https://developers.sber.ru/docs/ru/gigachat/api/images-generation?tool=python&lang=py
# С ollama работа по requests
# Долгое время отвечают
# gemma3:27b gpt-oss:120b

from telegram import ParseMode, Update
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
from dtb.settings import unblock_plugins
from dtb.settings import logger
from tgbot.handlers.utils.decorators import check_groupe_user
from tgbot.handlers.utils.info import get_tele_command
from users.models import User
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from tgbot.plugins.base_plugin import BasePlugin
import requests, json
import pprint as pp

chat_help = 'Диалог с ГигаЧат от Сбера /chat_giga_ \nи другими моделями ollama /chat_list /chat_listinfo'
plugins = unblock_plugins.get('CHAT')
GIGA_TOKEN = '' if not plugins else plugins.get("GIGA_CHAT")
URL_OLLAMA = '' if not plugins else plugins.get("URL_OLLAMA",'')
print('--- plugin GIGA: '+str(plugins),GIGA_TOKEN,URL_OLLAMA)
# Добавить проверку на роль 
# try:
#     GIGA_TOKEN = plugins.get("GIGA_CHAT")
# except Exception as e:
#     GIGA_TOKEN = ''
#logger.info('--- plugin GIGA: '+str(get_plugins('GIGA')))
# Вынести на параметр сделать возможность запоминать или изменять для каждого пользователя отдельно.
# content="Ты бот супер программист на питон, который помогает пользователю провести время с пользой."

def format_time(duration):
    # Преобразуем длительность из наносекунд в секунды
    seconds = duration / 1_000_000_000
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = round(seconds % 60, 2)
    
    return f"{hours}h {minutes}m {seconds}s"

def ask_giga(prompt):
    if not GIGA_TOKEN:
        return "Токен для GigaChat не опрделен"
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
    upms.reply_text("😎Введите вопрос к ГигаЧату. /cancel_giga - конец диалога")
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
                CommandHandler('cancel_giga', cancel_chat),
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
    text = chat_help
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
    output = ''
    telecmd = upms.text
    ret, list_model, dict_models  = get_models()
    if telecmd == "/chat_list":
        output = "😎<b>Список моделей ollama</b>\n"
        for i in range(1, len(dict_models)+1):
            output += f"/chat_o_{i} {str(dict_models.get(i)).replace('.co/','_')}\n"
    elif telecmd == "/chat_listinfo":
        output = "😎<b>Информация о моделях ollama</b>\n"
        for i in range(1, len(dict_models)+1):
            output += f"/chat_oi_{i} {dict_models.get(i)}\n"
    elif '/chat_o_' in telecmd:
        if telecmd == "/chat_o_":
            output = chat_help
        else:
            num = int(telecmd.replace('/chat_o_',''))
            name = dict_models.get(num)
            output = f"😎<b>{num}.Модель {name}</b>\n"
            msg = "Привет. Какая ты модель и что ты можешь ?"
            messages = [
                {"role": "system", "content": "Ты разговариваешь с пользователем, чтобы помочь ему с чем-то."},
                {"role": "user", "content": msg},
            ]
            output += f'<b>{msg}</b>\n'
            upms.reply_text("🕒..секундочку..")
            text, res = chat_ollama(name, messages)
            if "<" in text:
                text = text.replace('<', '&lt;').replace('>', '&gt;')
            output += text+ f"\n<b>Общая продолжительность: {format_time(res['total_duration'])}</b>\n\r🔸/help /chat_list"
            pp.pprint(res)
    elif '/chat_oi_' in telecmd:
        if telecmd == "/chat_oi_":
            output = chat_help
        else:
            num = int(telecmd.replace('/chat_oi_',''))
            name = dict_models.get(num)
            output = f"😎<b>Модель {name}</b>\n"
            output += show_model(name)
    else:
        output = chat_help
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=output,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )

def get_models():
    if URL_OLLAMA == '':
        return  'URL_OLLAMA is empty', [], {}
    r = requests.get(f"{URL_OLLAMA}/api/tags")
    str_models = ''
    list_models = []
    dict_model = {}
    number = 1
    # print(r.raise_for_status())
    for model in r.json()["models"]:
        # print(model,end='\n')
        str_models +=f'{model["name"]} {model["details"]["parameter_size"]} {model["details"]["quantization_level"]}\n'
        list_models.append(model["name"])
        dict_model[number]= model["name"] 
        number += 1
    return str_models , list_models, dict_model

def show_model(name):
    try:
        r = requests.get(f"{URL_OLLAMA}/api/show", params={"name": name})
        r.raise_for_status()

    except requests.HTTPError as e:
        print(f"GET failed: {e}")
        # fallback to POST
        r = requests.post(f"{URL_OLLAMA}/api/show", json={"name": name})
    return f"{name}\n {r.json().get('capabilities')}\n {r.json().get('model_info')}\n {r.json().get('modified_at')}\n"

def pull_model(name):
    r = requests.post(f"{URL_OLLAMA}/api/pull", json={"name": name})
    r.raise_for_status()
    # stream
    for line in r.iter_lines():
        if line:
            print(json.loads(line))

def chat_ollama(name, messages):
    try:
        r = requests.post(
            f"{URL_OLLAMA}/api/chat",
            json={"model": name, "messages": messages, "stream": False},
        )
        r.raise_for_status()
        text = r.json().get('message', {}).get('content', '')
        return text, r.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к Ollama API: {e}")
        return None, e

#print(list_models())
# _list, list_models = list_models()
# for i in list_models:
#     if True:
#         print(show_model(i))
#         print(chat(i, [{"role":"user","content":"Привет, Перечисли планеты солнечной системы"}]))
        #print(chat(i, [{"role":"user","content":"Почему нет плутона ?"}]))
# print(pull_model('qwen2.5-coder:1.5b'))
# mo = 'gemma3:1b'
# print(show_model(mo))
#print(chat(mo, [{"role":"user","content":"Привет, Перечисли планеты солнечной системы"}]))
#print(chat(mo, [{"role":"user","content":"Почему нет плутона ?"}]))