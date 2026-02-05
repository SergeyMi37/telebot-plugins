# Name Plugin: trans
    # - TRANS:
    #     - desc = Сервис для перевода текста с помощью Ollama и модели Qwen3:14b
# имя плагина TRANS должно совпадать с именем в конфигурации Dynaconf
# имя плагина trans должно быть первым полем от _ в имени файла trans_plugin
# имя файла плагина должен оканчиваться на _plugin
# В модуле должна быть определен класс для регистрации в диспетчере
# class TransPlugin(BasePlugin):
#    def setup_handlers(self, dp):
# --------- ISO 639-1 - код языка
# Китайский	Chinese	zh
# Английский	English	en
# Арабский	Arabic	ar
# Хинди	Hindi	hi
# Испанский	Spanish	es
# Французский	French	fr
# Русский	Russian	ru
# Португальский	Portuguese	pt
# Бенгальский	Bengali	bn
# Немецкий	German	de
# Японский	Japanese	ja
# ----- Хорошо работают и без GPU
# --model "lauchacarro/qwen2.5-translator:latest" 
# --model "SimonPu/Hunyuan-MT-Chimera-7B:Q8" 
# --model "icky/translate:latest" 
import requests
import json
import argparse
import sys
import codecs
import logging

# Установка кодировки UTF-8 для вывода в консоль
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# python tgbot/plugins/trans_plugin.py --text "Привет, мир!" --from "ru" --to "en" --model "lauchacarro/qwen2.5-translator:latest"
# python tgbot/plugins/trans_plugin.py -t "Bonjour le monde"
def translate_with_ollama(text, model="lauchacarro/qwen2.5-translator:latest", src_lang="auto", target_lang="ru",url_ollama="http://127.0.0.1:11434"):
    """
    Функция для перевода текста с помощью Ollama
    """
    try:
        # URL для API Ollama
        url = url_ollama + "/api/generate"
        
        # Подготовка данных для запроса
        data = {
            "model": model,
            "prompt": f"Translate the following text from {src_lang} to {target_lang}: {text}",
            "stream": False
        }
        
        # Отправка запроса
        response = requests.post(url, json=data,timeout=30000)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Успешный перевод с {src_lang} на {target_lang}" )
            return result.get("response", "Не удалось получить перевод")
        else:
            logger.error(f"Ошибка при обращении к Ollama: {response.status_code} {response.text}")
            return f"Ошибка при обращении к Ollama: {response.text}"
    except Exception as e:
        logger.error(f"Ошибка при переводе: {str(e)}")
        return f"Ошибка при переводе: {str(e)}"

if __name__ != "__main__":
    from telegram import ParseMode, Update
    from telegram.ext import CallbackContext
    # from dtb.settings import get_plugins_for_roles
    # from dtb.settings import logger
    from tgbot.handlers.utils.info import get_tele_command
    from tgbot.handlers.utils.decorators import check_groupe_user
    from users.models import User
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
    from tgbot.plugins.base_plugin import BasePlugin
    from dtb.settings import unblock_plugins
    
    plugins = unblock_plugins.get('TRANS')
    MODEL = 'lauchacarro/qwen2.5-translator:latest' if not plugins else plugins.get("MODEL")
    URL_OLLAMA = '' if not plugins else plugins.get("URL_OLLAMA",'')

    from tgbot.plugins.chat_plugin import chat_ollama
    url=URL_OLLAMA + "/api/generate"

    plugin_cmd = "trans"
    CODE_INPUT = range(1)
    plugin_help = f'Перевести текст. 🔸/help /{plugin_cmd} /{plugin_cmd}_ - введите текст для перевода' 


    def request_pp(update: Update, context):
        """Запрашиваем у пользователя """
        upms = get_tele_command(update)
        upms.reply_text(f"Введите текст для перевода или /cancel_{plugin_cmd} - отмена")
        return CODE_INPUT


    def check_p(update: Update, context):
        upms = get_tele_command(update)
        _in = upms.text
        if not _in:
            _out = f'Нечего не введено {_in}\n\r🔸/help /{plugin_cmd}_ ' 
        else:
            upms.reply_text("...ждите, идет перевод")
            # вызов функции перевода с помощью Ollama
            translation = translate_with_ollama(_in,model=MODEL,url_ollama=URL_OLLAMA)
            _out = f'Результат перевода:\n\r{translation}\n\r🔸/help /{plugin_cmd}_' 
        context.bot.send_message(
            chat_id=upms.chat.id,
            text=_out,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END


    def cancel_p(update: Update, context):
        """Завершаем диалог"""
        upms = get_tele_command(update)
        upms.reply_text("Разговор завершен.")
        return ConversationHandler.END


    class TransPlugin(BasePlugin):
        def setup_handlers(self, dp):
            conv_handler = ConversationHandler(
                entry_points=[CommandHandler(f'{plugin_cmd}_', request_pp)],
                states={
                    CODE_INPUT: [
                        MessageHandler(Filters.text & (~Filters.command), check_p),
                    ],
                },
                fallbacks=[
                    CommandHandler(f'cancel_{plugin_cmd}', cancel_p),
                ]
            )
            dp.add_handler(conv_handler)
            dp.add_handler(MessageHandler(Filters.regex(rf'^/{plugin_cmd}(/s)?.*'), commands))
            dp.add_handler(CallbackQueryHandler(button, pattern=f"^button_{plugin_cmd}"))


    @check_groupe_user
    def button(update: Update, context: CallbackContext) -> None:
        '''
        plugin TRANS
        '''
        #user_id = extract_user_data_from_update(update)['user_id']
        u = User.get_user(update, context)
        upms = get_tele_command(update)
        text = "Введите ..."
        text += plugin_help
        context.bot.edit_message_text(
            text=text,
            chat_id=upms.chat.id, #  u.user_id,
            message_id=update.callback_query.message.message_id,
            parse_mode=ParseMode.HTML
        )


    @check_groupe_user
    def commands(update: Update, context: CallbackContext) -> None:
        '''
        plugin TRANS
        '''
        #u = User.get_user(update, context)
        upms = get_tele_command(update)
        telecmd = upms.text
        #if telecmd == '/':
        _out = plugin_help
        context.bot.send_message(
            chat_id=upms.chat.id,
            text=_out,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML
        )


def main():
    parser = argparse.ArgumentParser(description='Перевод текста с помощью Ollama и модели lauchacarro/qwen2.5-translator:latest')
    parser.add_argument('--text', '-t', required=True, help='Текст для перевода')
    parser.add_argument('--model', '-m', default='lauchacarro/qwen2.5-translator:latest', help='Модель Ollama для перевода (по умолчанию: lauchacarro/qwen2.5-translator:latest)')
    parser.add_argument('--from', '-f', dest='src_lang', default='auto', help='Исходный язык (по умолчанию: auto)')
    parser.add_argument('--to', '-to', default='ru', help='Целевой язык (по умолчанию: ru)')
    parser.add_argument('--no-log', action='store_true', help='Отключить логгирование')
    parser.add_argument('--url', '-u', dest='url_ollama', default='http://localhost:11434', help='Адрес Ollama (по умолчанию: http://localhost:11434)')

    args = parser.parse_args()
    
    # Получаем перевод
    translation = translate_with_ollama(args.text, args.model, args.src_lang, args.to, args.url_ollama)
    
    # Выводим результат
    if not args.no_log:
        print(f"Перевод с {args.src_lang} на {args.to} с использованием модели {args.model}:")
    print(translation)


if __name__ == "__main__":
    main()