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
# Долгое время отвечают - больше минуты на моем ПК
# gemma3:27b gpt-oss:120b llama3.2:latest qwen3:30b gpt-oss:20b qwen3:4b qwen3:8b deepseek-r1:8b
# deepseek-r1:1.5b                                         e0979632db5a    1.1 GB    4 hours ago
# qwen2.5-coder:1.5b                                       d7372fd82851    986 MB    2 days ago 
# deepseek-coder:6.7b                                      ce298d984115    3.8 GB    3 days ago 
# huggingface.co/IlyaGusev/saiga_mistral_7b_gguf:latest    8e1d1e7be53f    3.1 GB    3 days ago 
# sqlcoder:latest                                          77ac14348387    4.1 GB    3 days ago 
# gemma3:1b                       

from telegram import ParseMode, Update
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
from dtb.settings import unblock_plugins
from dtb.settings import logger
from tgbot.handlers.utils.decorators import check_groupe_user
from tgbot.handlers.utils.info import get_tele_command
from users.models import User, UsersOptions
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from tgbot.plugins.base_plugin import BasePlugin
import pprint as pp
import requests, json, base64
from pathlib import Path

chat_help = 'Диалог с ГигаЧат от Сбера /chat_giga_ \nи другими моделями ollama /chat_list \n/chat_sys_ - установка системного параметра роли'
plugins = unblock_plugins.get('CHAT')
GIGA_TOKEN = '' if not plugins else plugins.get("GIGA_CHAT")
URL_OLLAMA = '' if not plugins else plugins.get("URL_OLLAMA",'')
MODEL_NAME = {}

def format_time(duration):
    # Преобразуем длительность из наносекунд в секунды
    seconds = duration / 1_000_000_000
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = round(seconds % 60, 2)
    
    return f"{hours}h {minutes}m {seconds}s"

def ask_giga(prompt, messages):
    if not GIGA_TOKEN:
        return "Токен для GigaChat не опрделен"

    giga = GigaChat(
        # Для авторизации запросов используйте ключ, полученный в проекте GigaChat API
        credentials=GIGA_TOKEN,
        verify_ssl_certs=False,
    )

    messages.append(HumanMessage(content=prompt))
    try:
        res = giga.invoke(messages)
        messages.append(res)
        return res.content
    except Exception as e:
        return e.args.__repr__()

CODE_INPUT = range(1)
CODE_INPUT2 = range(1)
CODE_INPUT_SYS = range(1)
def request_chat_sys(update: Update, context):
    upms = get_tele_command(update)
    u = User.get_user(update, context)
    curr_model = MODEL_NAME.get(u.user_id, 'default')
    role_sys = 'Ты бот супер программист на питон, который помогает пользователю производить эфективные программы.'
    ques_user = 'Что ты умеешь ? Можешь ли сгенерировать картинку ?'
    try:
        uo = UsersOptions.get_by_name_and_category(user_id=u.user_id,name='sys_role_'+curr_model)
        if uo:
            if uo.value != '':
                role_sys = uo.value
        uoq = UsersOptions.get_by_name_and_category(user_id=u.user_id,name='sys_ques_'+curr_model)
        if uoq:
            if uoq.value != '':
                ques_user = uoq.value
    except Exception as e:
        print(e)
    msg=(f"😎Для текущей модели <b>{curr_model}</b>\nВведите :<b>Системный параметр \
          роли|Вопрос о модели</b>.\n Текущий: <code>{role_sys}|{ques_user}</code>\n/cancel_chat_sys - не изменять")
    context.bot.send_message(
        chat_id=upms.chat.id,
        text = msg,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
    return CODE_INPUT_SYS

def check_chat_sys(update: Update, context):
    upms = get_tele_command(update)
    u = User.get_user(update, context)
    curr_model = MODEL_NAME.get(u.user_id, 'default')
    role = upms.text
    ques = ''
    if '|' in role:
        ques = role.split('|')[1]
        role = role.split('|')[0]
    
    try:
        instance, created = UsersOptions.objects.update_or_create(
                    user=u,
                    name='sys_role_'+curr_model,
                    defaults={
                        'description': 'Системный параметр роли для {"role": "system", "content": sys_msg}',
                        'category': "model_option",
                        'type': "text",
                        'value': role,
                        'enabled': True
                    }
                )
        instance, created = UsersOptions.objects.update_or_create(
                    user=u,
                    name='sys_ques_'+curr_model,
                    defaults={
                        'description': 'Вопрос к модели - параметр роли для {"role": "user", "content": sys_msg}',
                        'category': "model_option",
                        'type': "text",
                        'value': ques,
                        'enabled': True
                    }
                )
        msg = (f"Для текущей модели <b>{curr_model}</b>\nСохранили.: <code>{role}|{ques}</code>")
    except Exception as e:
        msg = (f"Ошибка сохранения: {e}")
    msg += (f"\n\n🔸/help /chat_list /chat_sys_")
    context.bot.send_message(
        chat_id=upms.chat.id,
        text = msg,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

def cancel_chat_sys(update: Update, context):
    """Завершаем диалог"""
    upms = get_tele_command(update)
    upms.reply_text("диалог закончен \n\r🔸/help /chat /chat_sys_ /chat_giga_ - начать новый диалог")
    return ConversationHandler.END

def request_chat_ollama(update: Update, context):
    upms = get_tele_command(update)
    u = User.get_user(update, context)
    if '/chat_ollama_' in upms.text:
        num = upms.text.replace('/chat_ollama_','')
        ret, list_model, dict_models  = get_models()
        if num.isdigit():
            name = dict_models.get(int(num))
            if name:
                MODEL_NAME.update({ u.user_id:name }) # запоминаем текущую модель для пользователя
   
    upms.reply_text(f"😎Введите вопрос к Модели: '{MODEL_NAME.get(u.user_id)}'. /cancel_ollama - конец диалога")
    return CODE_INPUT2

def check_chat_ollama(update: Update, context):
    upms = get_tele_command(update)
    u = User.get_user(update, context)
    print('---',upms.text,MODEL_NAME)
    name = MODEL_NAME.get(u.user_id)
    role = 'Ты бот супер программист на питон, который помогает пользователю производить эфективные программы.'
    try:
        uo = UsersOptions.get_by_name_and_category(user_id=u.user_id,name='sys_role_'+name)
        if uo:
            if "|" in uo.value:
                if uo.value.split('|')[0]:
                    role = uo.value.split('|')[0]
    except Exception as e:
        print(e)
    output = f"<b>{upms.text}...Разговор с моделью '{name}'</b>\n"
    # запоминать контекст ? где хранить ?
    upms.reply_text("🕒.один момент..")
    output += chat_ollama_model(name, upms.text,sys_msg = role)
    CONST = 4090
    ot=0
    do=CONST
    while True:
        context.bot.send_message(
            chat_id=upms.chat.id,
            text = output[ot:do], # выводим в телегу порциями по :4090]
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML
        )
        ot += CONST
        do += CONST
        if output[ot:do]=='':
            break
    request_chat_ollama(update, context) # зацикливаем диалог

def cancel_chat_ollama(update: Update, context):
    """Завершаем диалог """
    upms = get_tele_command(update)
    upms.reply_text("диалог c моделью закончен \n\r🔸/help /chat /chat_list /chat_sys_ /chat_ollama_ - начать новый диалог")
    return ConversationHandler.END

def request_chat(update: Update, context):
    upms = get_tele_command(update)
    upms.reply_text("😎Введите вопрос к ГигаЧату. /cancel_giga - конец диалога")
    return CODE_INPUT

def check_chat(update: Update, context):
    upms = get_tele_command(update)
    _input = upms.text
    upms.reply_text("🕒.секундочку..")
    u = User.get_user(update, context)
    MODEL_NAME.update({ u.user_id:'giga' })
    role = f"Ты бот супер программист на питон, который помогает пользователю проводить время с пользой."
    try:
        uo = UsersOptions.get_by_name_and_category(user_id=u.user_id,name='sys_role_giga')
        if uo:
            if uo.value !='':
                role = uo.value
    except Exception as e:
        print(e)
    messages = [
        SystemMessage(
            # content="Ты внимательный бот-психолог, который помогает пользователю решить его проблемы."
            # content="Ты бот-собеседник, который помогает пользователю провести время с пользой."
            content=f"{role}"
        )
    ]
    _output = ask_giga(_input, messages)
    
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
    upms.reply_text("диалог закончен \n\r🔸/help /chat /chat_sys_ /chat_giga_ - начать новый диалог")
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
            conversation_timeout=300,
            fallbacks=[
                CommandHandler('cancel_giga', cancel_chat),
            ]
        )
        conv_handler_ollama = ConversationHandler(
            entry_points=[MessageHandler(Filters.regex(rf'^/chat_ollama_(/s)?.*'), request_chat_ollama)],
            states={
                CODE_INPUT2: [
                    MessageHandler(Filters.text & (~Filters.command), check_chat_ollama),
                ],
            },
            conversation_timeout=300,
            fallbacks=[
                CommandHandler('cancel_ollama', cancel_chat_ollama),
            ]
        )
        conv_handler_sys = ConversationHandler(
            entry_points=[CommandHandler('chat_sys_', request_chat_sys)],
            states={
                CODE_INPUT_SYS: [
                    MessageHandler(Filters.text & (~Filters.command), check_chat_sys),
                ],
            },
            conversation_timeout=300,
            fallbacks=[
                CommandHandler('cancel_chat_sys', cancel_chat_sys),
            ]
        )
        dp.add_handler(conv_handler_sys)
        dp.add_handler(conv_handler_ollama)
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

def chat_ollama_model(name,msg,sys_msg="Ты разговариваешь с пользователем, чтобы помочь ему с чем-то."):
    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": msg},
    ]
    # output = f'<b>{msg}</b>\n'
    # upms.reply_text(f"🕒..секундочку..")
    text, res = chat_ollama(name, messages)
    if text == None:
        output = str(res)
    else:
        if "<" in text:
            text = text.replace('<', '&lt;').replace('>', '&gt;')
        output = text+ f"\n**Общая продолжительность: {format_time(res['total_duration'])}** "            
    # output += f"\n\r🔸/help /chat_list /chat_sys_ /chat_ollama_{num} - диалог с этой моделью"
    pp.pprint(res)
    return output


@check_groupe_user
def commands_chat(update: Update, context: CallbackContext) -> None:
    #u = User.get_user(update, context)
    upms = get_tele_command(update)
    u = User.get_user(update, context)
    output = ''
    telecmd = upms.text
    if telecmd == "/chat":
        upms.reply_text(chat_help)
        return None
    ret, list_model, dict_models  = get_models()
    if not list_model:
        upms.reply_text(f"❌ {ret}")
        return None
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
            if not name:
                upms.reply_text("❌..неверный номер модели..")
                return None

            msg = "Какая ты модель и что ты можешь ? Умеешь ли ты сгенерировать картинку ?"
            try:
                uo = UsersOptions.get_by_name_and_category(user_id=u.user_id,name='sys_ques_'+str(name))
                if uo:
                    if uo.value != '':
                        msg = uo.value
            except Exception as e:
                print(e)
            MODEL_NAME.update({u.user_id:name }) # запоминаем имя модели
            output = f"<b>{msg}. Вопрос к '{name}'</b>\n"
            upms.reply_text("🕒.один момент..")
            output += chat_ollama_model(name,msg)
            output += f"\n\r🔸/help /chat /chat_list /chat_sys_ /chat_ollama_{num} - начать диалог с этой моделью"

    elif '/chat_ollama_' in telecmd:
        if telecmd == "/chat_ollama_":
            output = chat_help
        else:
            num = int(telecmd.replace('/chat_ollama_',''))
            name = dict_models.get(num)
            output = f'...Диалог с моделью !!!! {name}\n'
            
    elif '/chat_oi_' in telecmd:
        if telecmd == "/chat_oi_":
            output = chat_help
        else:
            num = int(telecmd.replace('/chat_oi_',''))
            name = dict_models.get(num)
            output = f"😎**Модель {name}**\n"
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
    try: 
        r = requests.get(f"{URL_OLLAMA}/api/tags",timeout=1)
        r.raise_for_status()
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
    except Exception as e:
        msg = f"{e}".replace(URL_OLLAMA.split("://")[1].split(':')[0] ,"URL_OLLAMA")
        print(msg)
        return msg, [], {}
    
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
        return None, f"{e}".replace(URL_OLLAMA.split("://")[1].split(':')[0] ,"URL_OLLAMA")

def main() -> None:
    print(URL_OLLAMA)

if __name__ == '__main__':
    main()