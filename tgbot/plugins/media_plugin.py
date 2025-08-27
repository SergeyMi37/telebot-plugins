# Name Plugin: MEDIA
    # - MEDIA:
    #     - desc = Сервис для скачивания роликов с Ютуба и ВкВидео и обмена ссылками между пользователями бота
# Применяется утилита youtube-dl
# https://ostechnix.com/yt-dlp-tutorial/
# https://habr.com/ru/articles/857964/
# https://github.com/oleksis/youtube-dl-gui/releases/tag/v1.8.2
# интересные проекты
# https://github.com/Algram/ytdl-webserver
# https://github.com/marcopiovanello/yt-dlp-web-ui
# https://github.com/oleksis/youtube-dl-gui
# https://github.com/BKSalman/ytdlp-gui
# имя плагина MEDIA должно совпадать с именем в конфигурации Dynaconf
# имя плагина media должно быть первым полем от _ в имени файла media_plugin
# имя файла плагина должно окачиваться на _plugin
# В модуле должна быть опрделн класс для регистрации в диспетчере
# class MEFIAPlugin(BasePlugin):
#    def setup_handlers(self, dp):

from telegram import ParseMode, Update
from telegram.ext import CallbackContext
# from dtb.settings import get_plugins_for_roles
# from dtb.settings import logger
from tgbot.handlers.utils.info import get_tele_command
from tgbot.handlers.utils.decorators import check_groupe_user
from users.models import User,Updates
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
from tgbot.plugins.base_plugin import BasePlugin
from datetime import date
from tgbot.handlers.admin.utils import _get_csv_from_qs_values

# Добавить проверку на роль ''
#plugin_wiki = get_plugins_for_roles('').get('WIKI')

plugin_cmd = "media"
CODE_INPUT = range(1)
plugin_help = f'Загрузка роликов с ютуба. 🔸/help /{plugin_cmd} /media_get_yt /{plugin_cmd}_ - диалог для загрузки роликов с ютуба' 

def request_p(update: Update, context):
    """Запрашиваем у пользователя"""
    upms = get_tele_command(update)
    upms.reply_text(f"Введите урл или /cancel_{plugin_cmd} - отмена")
    return CODE_INPUT

def check_p(update: Update, context):
    upms = get_tele_command(update)
    _in = upms.text
    _out = f'Будет загрузка {_in}\n\r🔸/help /{plugin_cmd}_' 
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

# def error(update, context):
#     logger.warning('Update "%s" caused error "%s"', update, context.error)

class PPlugin(BasePlugin):
    def setup_handlers(self, dp):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler(f'{plugin_cmd}_', request_p)],
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
    u = User.get_user(update, context)
    upms = get_tele_command(update)
    telecmd = upms.text
    if telecmd == '/media_get_yt':
        http = Updates.objects.filter(
            message__startswith='https://youtu',
            from_id=u.user_id
        ).values()
        csv = _get_csv_from_qs_values(http,'url_http')
        upms.reply_document(csv)
    # updates_with_http_links = Updates.objects.filter(message__startswith='https')

    # Укажите конкретные даты начала и конца периода
    # start_date = date(2023, 1, 1)
    # end_date = date(2023, 12, 31)

    # # Запрос с фильтрацией сообщений, начинающихся с "https", и ограничением по диапазону дат
    # updates_with_http_and_date_range = Updates.objects.filter(
    #     message__startswith='https',
    #     date__range=(start_date, end_date)
    # )
    
    _out = plugin_help
    context.bot.send_message(
        chat_id=upms.chat.id,
        text=_out,
        disable_web_page_preview=True,
        parse_mode=ParseMode.HTML
    )

# -----------------------------------------
# import os
# from telegram import Update
# from telegram.ext import Updater, CommandHandler, CallbackContext

# # Загрузить необходимые библиотеки
# import youtube_dl  # Для скачивания видео с YouTube
# from pyrogram.telegram_client import TelegramClient


def start(update: Update) -> None:
    update.message.reply_text('Привет! Я бот для загрузки роликов с YouTube в ваш чат.')


def download_video(url, output_path):
    ytdl_format_options = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(title)s.%(ext)s'
    }

    with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
        ydl.download([url])
        
    # Переместить загруженный файл в нужную папку
    os.system(f'mv {output_path} /путь/к/целевой/папке')
    update.message.reply_text('Видео скачано и перенесено в целевую папку!')


def download_command(update: Update, context) -> None:
    if len(context.args) > 0 and 'https://www.youtube.com/watch' in context.args[0]:
        video_url = " ".join(context.args)
        output_path = f"video_{context.chat.id}"
        
        # Скачиваем видео
        download_video(video_url, output_path)
    else:
        update.message.reply_text('Введите корректный URL на YouTube.')


def main() -> None:
    updater = Updater("YOUR_API_TOKEN", use_context=True)
    
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("download", download_command))
    
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()